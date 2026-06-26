import pandas as pd
from typing import Any, Dict, List
from langchain_core.messages import SystemMessage, HumanMessage
import json
from pydantic import BaseModel, Field
from agent.state import InvestigationState
from tools.feature_ranker import StatisticalFeatureRanker
from tools.drift_detector import StatisticalAnalyticsEngine

class Phase2Analysis(BaseModel):
    summary: str = Field(description="A concise summary of why the identified segment is anomalous based on the profile shifts.")
    recommended_action: str = Field(description="A brief recommendation for the next step based on the findings.")

def investigate_phase_1(df: pd.DataFrame, current_path: str = "Root", depth: int = 0, max_depth: int = 2) -> Dict[str, Any]:
    """
    Phase 1: Portfolio Investigation
    Recursively drills down into demographic attributes to isolate the anomalous segment.
    """
    exposure = df['Exposure'].sum()
    if exposure == 0:
        return {}
        
    actual_f = df['Claim'].sum() / exposure
    expected_f = (df['Expected_Frequency'] * df['Exposure']).sum() / exposure
    segment_drift = actual_f - expected_f
    
    node = {
        "name": current_path,
        "exposure": float(exposure),
        "actual_frequency": float(actual_f),
        "expected_frequency": float(expected_f),
        "drift": float(segment_drift),
        "children": []
    }
    
    if depth >= max_depth:
        return node
        
    ranker = StatisticalFeatureRanker(min_exposure=100)
    rankings = ranker.rank_portfolio_features(df)
    
    # Filter out features already in the path
    rankings = [r for r in rankings if r['feature'] not in current_path]
    
    if not rankings:
        return node
        
    best_feature = rankings[0]
    
    if best_feature['score'] < 1e-6 or best_feature['confidence'] < 0.80:
        return node # Not statistically significant enough to continue splitting
        
    feature_name = best_feature['feature']
    node["split_feature"] = feature_name
    node["confidence"] = best_feature.get('confidence', 0)
    node["contribution"] = best_feature.get('contribution', 0)
    
    # Drill down into all segments of this feature
    for segment_val, group in df.groupby(feature_name):
        child_path = f"{current_path} -> {feature_name}:{segment_val}"
        child_node = investigate_phase_1(group, child_path, depth + 1, max_depth)
        if child_node:
            node["children"].append(child_node)
            
    # Sort children by absolute drift
    node["children"].sort(key=lambda x: abs(x.get('drift', 0)), reverse=True)
    return node

def extract_worst_leaf(node: Dict[str, Any]) -> Dict[str, Any]:
    """Traverses the Phase 1 tree to find the most anomalous leaf node."""
    if not node.get("children"):
        return node
    worst_child = max(node["children"], key=lambda x: abs(x.get("drift", 0)))
    return extract_worst_leaf(worst_child)

def investigate_phase_2(df: pd.DataFrame, worst_leaf_path: str, latest_year: int, state: InvestigationState) -> Dict[str, Any]:
    """
    Phase 2: Claim Profile Investigation
    Isolates the data for the worst leaf node and compares its claim profile against the historical baseline.
    """
    # Parse the worst leaf path to filter the dataframe
    parts = worst_leaf_path.split(" -> ")
    filtered_df = df.copy()
    for part in parts:
        if part == "Root":
            continue
        feat, val = part.split(":")
        filtered_df = filtered_df[filtered_df[feat] == val]
        
    engine = StatisticalAnalyticsEngine()
    baseline = engine.get_historical_claim_profile(filtered_df, latest_year)
    current_df = filtered_df[filtered_df['Year'] == latest_year]
    current = engine.get_historical_claim_profile(current_df, latest_year + 1)
    
    shifts = []
    for attribute in ["Claim_Category", "Hospital_Type", "Claim_Status"]:
        base_dist = baseline.get(attribute, {})
        curr_dist = current.get(attribute, {})
        
        all_keys = set(list(base_dist.keys()) + list(curr_dist.keys()))
        for key in all_keys:
            if key is None: continue
            b_val = base_dist.get(key, 0)
            c_val = curr_dist.get(key, 0)
            shift = c_val - b_val
            shifts.append({
                "attribute": attribute,
                "value": key,
                "historical_share": b_val,
                "current_share": c_val,
                "shift": shift
            })
            
    shifts.sort(key=lambda x: x["shift"], reverse=True)
    
    api_key = state.get("api_key", "")
    llm = None
    if api_key:
        try:
            if api_key.startswith("sk-"):
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(model="gpt-4o", api_key=api_key)
            else:
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, max_retries=0)
            llm = llm.with_structured_output(Phase2Analysis)
        except Exception as e:
            print(f"Error initializing LLM: {e}")
            pass
            
    if llm:
        try:
            analysis_input = f"Segment: {worst_leaf_path}. Profile Shifts: {json.dumps(shifts[:5])}"
            analysis = llm.invoke([HumanMessage(content=f"Analyze these claim profile shifts: {analysis_input}")])
            return {"worst_segment": worst_leaf_path, "profile_shifts": shifts, "llm_analysis": analysis.dict()}
        except Exception as e:
            print(f"Error invoking LLM in investigate_phase_2: {e}")

    return {"worst_segment": worst_leaf_path, "profile_shifts": shifts}

def investigation_node(state: InvestigationState) -> InvestigationState:
    """
    Executes the Two-Phase Investigation.
    """
    df = pd.read_csv(state["df_path"])
    latest_year = df['Year'].max() if 'Year' in df.columns else 2024
    
    state["planner_notebook"].append({
        "observation": "Initiating Phase 1 Portfolio Investigation.",
        "hypothesis": "A specific demographic segment is driving the overall portfolio drift.",
        "decision": "Use StatisticalFeatureRanker to recursively drill down."
    })
    
    df_latest = df[df['Year'] == latest_year] if 'Year' in df.columns else df
    
    # Phase 1
    tree = investigate_phase_1(df_latest)
    state["investigation_tree"] = tree
    
    worst_leaf = extract_worst_leaf(tree)
    worst_path = worst_leaf.get("name", "Root")
    
    state["planner_notebook"].append({
        "observation": f"Phase 1 isolated anomalous segment: {worst_path}.",
        "hypothesis": "Claim attributes within this segment have shifted compared to historical baselines.",
        "decision": "Initiate Phase 2 Claim Profile Investigation."
    })
    
    # Phase 2
    phase_2_results = investigate_phase_2(df, worst_path, latest_year, state)
    
    # Store Phase 2 results in the state tree for the UI to render
    state["investigation_tree"]["phase_2"] = phase_2_results
    
    state["messages"].append(SystemMessage(content="Investigation Agent: Completed 2-Phase Investigation."))
    return state
