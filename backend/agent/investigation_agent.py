import pandas as pd
import numpy as np
from typing import Any, Dict, List
from langchain_core.messages import SystemMessage, HumanMessage
import json
import math
from pydantic import BaseModel, Field
from agent.state import InvestigationState
from tools.feature_ranker import StatisticalFeatureRanker
from tools.drift_detector import StatisticalAnalyticsEngine
from engines.severity_engine import SeverityAnalyticsEngine
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logger import get_logger
logger = get_logger()

class Phase2Analysis(BaseModel):
    summary: str = Field(description="A concise summary of why the identified segment is anomalous based on the profile shifts.")
    recommended_action: str = Field(description="A brief recommendation for the next step based on the findings.")

# =====================================================================
# FREQUENCY INVESTIGATION WORKFLOW (Original unmodified behavior)
# =====================================================================

def investigate_phase_1(df: pd.DataFrame, current_path: str = "Root", depth: int = 0, max_depth: int = 2, min_exposure: float = 500, min_expected_claims: float = 10) -> Dict[str, Any]:
    exposure = df['Exposure'].sum() if 'Exposure' in df.columns else float(len(df))
    if exposure < min_exposure:
        return {}
        
    expected_claims = (df['Expected_Frequency'] * df['Exposure']).sum() if 'Expected_Frequency' in df.columns else df['Expected_Frequency'].sum()
    if expected_claims < min_expected_claims:
        return {}
        
    actual_f = df['Claim'].sum() / exposure
    expected_f = expected_claims / exposure
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
        
    ranker = StatisticalFeatureRanker(min_exposure=min_exposure)
    # Exclude post-claim attributes from Phase 1 rankings
    available_features = ['Product', 'Age_Group', 'Region', 'Gender', 'Distribution_Channel', 'Plan_Type']
    available_features = [f for f in available_features if f not in current_path]
    
    if not available_features:
        return node
        
    rankings = ranker.rank_portfolio_features(df, features=available_features)
    
    # Filter out features already in the path (extra safety)
    rankings = [r for r in rankings if r['feature'] not in current_path]
    
    if not rankings:
        return node
        
    best_feature = rankings[0]
    
    if best_feature['score'] < 1e-6 or best_feature['confidence'] < 0.80:
        return node
        
    feature_name = best_feature['feature']
    node["split_feature"] = feature_name
    node["confidence"] = best_feature.get('confidence', 0)
    node["contribution"] = best_feature.get('contribution', 0)
    
    # Drill down into all segments of this feature
    for segment_val, group in df.groupby(feature_name):
        child_path = f"{current_path} -> {feature_name}:{segment_val}"
        child_node = investigate_phase_1(group, child_path, depth + 1, max_depth, min_exposure, min_expected_claims)
        if child_node:
            node["children"].append(child_node)
            
    # Sort children by absolute drift
    node["children"].sort(key=lambda x: abs(x.get('drift', 0)), reverse=True)
    return node

def extract_worst_leaf(node: Dict[str, Any]) -> Dict[str, Any]:
    if not node.get("children"):
        return node
    # Slices are sorted so children[0] is the worst
    return extract_worst_leaf(node["children"][0])

def investigate_phase_2(df: pd.DataFrame, worst_leaf_path: str, latest_year: int, state: InvestigationState) -> Dict[str, Any]:
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
            logger.error(f"Error initializing LLM: {e}")
            pass
            
    if llm:
        try:
            analysis_input = f"Segment: {worst_leaf_path}. Profile Shifts: {json.dumps(shifts[:5])}"
            analysis = llm.invoke([HumanMessage(content=f"Analyze these claim profile shifts: {analysis_input}")])
            return {"worst_segment": worst_leaf_path, "profile_shifts": shifts, "llm_analysis": analysis.dict()}
        except Exception as e:
            logger.error(f"Error invoking LLM in investigate_phase_2: {e}")

    return {"worst_segment": worst_leaf_path, "profile_shifts": shifts}


# =====================================================================
# SEVERITY INVESTIGATION WORKFLOW
# =====================================================================

def run_segment_bootstrap(claims_df: pd.DataFrame, iterations=500, confidence_level=0.95) -> tuple:
    """Helper to run deterministic bootstrap O/E bounds on a claims segment."""
    N = len(claims_df)
    if N <= 1:
        return 1.0, 1.0, False
        
    np.random.seed(42)
    bootstrap_oes = []
    
    obs_col = claims_df['Actual_Claim_Amount'].values
    exp_col = claims_df['Expected_Severity'].values
    
    for _ in range(iterations):
        sample_indices = np.random.choice(N, size=N, replace=True)
        boot_obs = obs_col[sample_indices].sum()
        boot_exp = exp_col[sample_indices].sum()
        boot_oe = boot_obs / boot_exp if boot_exp > 0 else 1.0
        bootstrap_oes.append(boot_oe)
        
    bootstrap_oes = np.sort(bootstrap_oes)
    alpha = 1.0 - confidence_level
    lower_idx = int(round((alpha / 2.0) * iterations))
    upper_idx = int(round((1.0 - alpha / 2.0) * iterations)) - 1
    
    lower_bound = bootstrap_oes[max(0, lower_idx)]
    upper_bound = bootstrap_oes[min(iterations - 1, upper_idx)]
    
    is_significant = lower_bound > 1.00
    return float(lower_bound), float(upper_bound), bool(is_significant)


def investigate_severity_phase_1(
    df: pd.DataFrame, 
    current_path: str = "Root", 
    depth: int = 0, 
    max_depth: int = 2, 
    sev_engine: SeverityAnalyticsEngine = None,
    total_portfolio_excess_cost: float = 1.0
) -> Dict[str, Any]:
    """
    Phase 1 (Severity): Demographic Slicing.
    Recursively slices demographics based on positive excess cost contribution.
    """
    if sev_engine is None:
        sev_engine = SeverityAnalyticsEngine()
        
    claims_df = sev_engine.filter_claims(df)
    
    # Filter to current period
    if 'Year' in claims_df.columns:
        current_claims = claims_df[claims_df['Year'].isin(sev_engine.current_years)]
    else:
        current_claims = claims_df
        
    claim_count = len(current_claims)
    
    if current_claims.empty or claim_count < sev_engine.minimum_claims:
        return {}
        
    obs_cost = current_claims['Actual_Claim_Amount'].sum()
    exp_cost = current_claims['Expected_Severity'].sum()
    excess_cost = obs_cost - exp_cost
    
    obs_sev = obs_cost / claim_count
    exp_sev = exp_cost / claim_count
    relative_drift = (obs_sev - exp_sev) / exp_sev if exp_sev > 0 else 0.0
    oe_ratio = obs_cost / exp_cost if exp_cost > 0 else 0.0
    
    # Bootstrap CI for this segment
    lower_bound, upper_bound, is_significant = run_segment_bootstrap(
        current_claims, 
        iterations=sev_engine.bootstrap_iterations, 
        confidence_level=sev_engine.confidence_level
    )
    
    node = {
        "name": current_path,
        "exposure": float(claim_count), # For UI compatibility, use claim count as exposure
        "claim_count": int(claim_count),
        "observed_severity": float(obs_sev),
        "expected_severity": float(exp_sev),
        "drift": float(relative_drift), # Relative drift
        "oe_ratio": float(oe_ratio),
        "excess_cost": float(excess_cost),
        "bootstrap_lower_bound": float(lower_bound),
        "bootstrap_upper_bound": float(upper_bound),
        "is_significant": bool(is_significant),
        "children": []
    }
    
    # Stopping Criteria (Phase 16)
    # 1. Depth limit
    if depth >= max_depth:
        return node
        
    # 2. Confidence interval width check (too wide means unstable)
    ci_width = upper_bound - lower_bound
    if ci_width > 1.5:
        return node
        
    # 3. Excess cost materiality (remaining excess cost is immaterial)
    if excess_cost < 1000:
        return node

    # Feature ranker
    ranker = StatisticalFeatureRanker(min_claims=sev_engine.minimum_claims)
    rankings = ranker.rank_severity_features(current_claims, total_portfolio_excess_cost)
    
    # Filter features already in the path
    rankings = [r for r in rankings if r['feature'] not in current_path]
    
    if not rankings:
        return node
        
    best_feature = rankings[0]
    
    # If the isolated excess cost is immaterial, stop splitting
    if best_feature['score'] < 1000 or best_feature['confidence'] < 0.80:
        return node
        
    feature_name = best_feature['feature']
    node["split_feature"] = feature_name
    node["confidence"] = best_feature.get('confidence', 0)
    node["contribution"] = best_feature.get('portfolio_contribution', 0) # Use portfolio contribution %
    
    # Drill down recursively
    for segment_val, group in current_claims.groupby(feature_name):
        child_path = f"{current_path} -> {feature_name}:{segment_val}"
        child_node = investigate_severity_phase_1(
            group, 
            child_path, 
            depth + 1, 
            max_depth, 
            sev_engine, 
            total_portfolio_excess_cost
        )
        if child_node:
            # Calculate sibling local contribution
            child_node["local_contribution"] = child_node.get("excess_cost", 0.0) / best_feature['score'] if best_feature['score'] > 0 else 0.0
            child_node["portfolio_contribution"] = child_node.get("excess_cost", 0.0) / total_portfolio_excess_cost if total_portfolio_excess_cost > 0 else 0.0
            node["children"].append(child_node)
            
    # Sort children by absolute excess cost isolated descending
    node["children"].sort(key=lambda x: abs(x.get('excess_cost', 0)), reverse=True)
    return node


def investigate_severity_phase_2(df: pd.DataFrame, worst_leaf_path: str, sev_engine: SeverityAnalyticsEngine, state: InvestigationState) -> Dict[str, Any]:
    """
    Phase 2 (Severity): Claim Cost Profile.
    Compares the worst segment's claim characteristics against its own segment baseline.
    """
    parts = worst_leaf_path.split(" -> ")
    filtered_df = df.copy()
    for part in parts:
        if part == "Root":
            continue
        feat, val = part.split(":")
        filtered_df = filtered_df[filtered_df[feat] == val]
        
    # Standardize filtering of claims
    claims_df = sev_engine.filter_claims(filtered_df)
    
    baseline_claims = claims_df[claims_df['Year'].isin(sev_engine.baseline_years)]
    current_claims = claims_df[claims_df['Year'].isin(sev_engine.current_years)]
    
    baseline_total_cost = baseline_claims['Actual_Claim_Amount'].sum()
    current_total_cost = current_claims['Actual_Claim_Amount'].sum()
    
    shifts = []
    attributes = ["Claim_Category", "Hospital_Type", "Claim_Status"]
    
    for attr in attributes:
        if attr not in current_claims.columns:
            continue
            
        base_vals = baseline_claims[attr].value_counts().index
        curr_vals = current_claims[attr].value_counts().index
        all_keys = set(list(base_vals) + list(curr_vals))
        
        for val in all_keys:
            if val is None:
                continue
                
            # Historical and Current Segment Cost Shares
            base_cost = baseline_claims[baseline_claims[attr] == val]['Actual_Claim_Amount'].sum() if not baseline_claims.empty else 0.0
            curr_cost = current_claims[current_claims[attr] == val]['Actual_Claim_Amount'].sum()
            
            hist_share = base_cost / baseline_total_cost if baseline_total_cost > 0 else 0.0
            curr_share = curr_cost / current_total_cost if current_total_cost > 0 else 0.0
            shift_val = curr_share - hist_share
            
            # Recalculate excess cost for this claim attribute
            attr_expected = current_claims[current_claims[attr] == val]['Expected_Severity'].sum()
            excess_cost = curr_cost - attr_expected
            
            shifts.append({
                "attribute": attr,
                "value": val,
                "historical_share": float(hist_share),
                "current_share": float(curr_share),
                "shift": float(shift_val),
                "excess_cost": float(excess_cost)
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
            logger.error(f"Error initializing LLM: {e}")
            pass
            
    if llm:
        try:
            analysis_input = f"Segment: {worst_leaf_path}. Profile Shifts: {json.dumps(shifts[:5])}"
            analysis = llm.invoke([HumanMessage(content=f"Analyze these claim cost profile shifts: {analysis_input}")])
            return {"worst_segment": worst_leaf_path, "profile_shifts": shifts, "llm_analysis": analysis.dict()}
        except Exception as e:
            logger.error(f"Error invoking LLM in investigate_severity_phase_2: {e}")

    return {"worst_segment": worst_leaf_path, "profile_shifts": shifts}


# =====================================================================
# AGENT LANGGRAPH NODE FUNCTION
# =====================================================================

def investigation_node(state: InvestigationState) -> InvestigationState:
    """
    Executes the Two-Phase Investigation (Frequency, Severity, or Combined).
    """
    active_engine = state.get("engine_context", {}).get("active_engine", "Frequency")
    
    df = pd.read_csv(state["df_path"])
    
    if active_engine == "Severity":
        # Load severity engine context parameters
        threshold = state.get("engine_context", {}).get("investigation_configuration", {}).get("severity_drift_threshold", 0.05)
        min_claims = state.get("engine_context", {}).get("investigation_configuration", {}).get("minimum_claims_for_investigation", 30)
        boot_iters = state.get("engine_context", {}).get("investigation_configuration", {}).get("bootstrap_iterations", 500)
        conf_level = state.get("engine_context", {}).get("investigation_configuration", {}).get("confidence_level", 0.95)
        
        # Historical baseline explicit periods
        baseline_years = [2022, 2023]
        current_years = [2024]
        
        sev_engine = SeverityAnalyticsEngine(
            materiality_threshold=threshold,
            minimum_claims=min_claims,
            bootstrap_iterations=boot_iters,
            confidence_level=conf_level,
            baseline_years=baseline_years,
            current_years=current_years
        )
        
        # Run Severity metrics for portfolio total excess cost
        metrics = state.get("drift_metrics", {})
        total_portfolio_excess_cost = max(metrics.get("excess_cost", 1000.0), 1.0)
        
        state["planner_notebook"].append({
            "observation": "Initiating Phase 1 Severity Portfolio Slicing.",
            "hypothesis": "A specific demographic segment is driving the overall portfolio excess cost.",
            "decision": "Use StatisticalFeatureRanker to recursively drill down on positive excess cost contribution."
        })
        
        # Severity Phase 1
        tree = investigate_severity_phase_1(
            df=df,
            current_path="Root",
            depth=0,
            max_depth=2,
            sev_engine=sev_engine,
            total_portfolio_excess_cost=total_portfolio_excess_cost
        )
        state["investigation_tree"] = tree
        
        # Find worst leaf
        worst_leaf = extract_worst_leaf(tree)
        worst_path = worst_leaf.get("name", "Root")
        
        state["planner_notebook"].append({
            "observation": f"Phase 1 isolated primary statistical contributor: {worst_path}.",
            "hypothesis": "Claim cost profile within this segment has shifted compared to historical baseline.",
            "decision": "Initiate Phase 2 Claim Cost Profile Investigation."
        })
        
        # Severity Phase 2
        phase_2_results = investigate_severity_phase_2(
            df=df,
            worst_leaf_path=worst_path,
            sev_engine=sev_engine,
            state=state
        )
        state["investigation_tree"]["phase_2"] = phase_2_results
        state["messages"].append(SystemMessage(content="Investigation Agent: Completed Severity 2-Phase Investigation."))
        
    elif active_engine == "Combined":
        paths = state.get("investigation_paths", ["Combined"])
        latest_year = df['Year'].max() if 'Year' in df.columns else 2024
        merged_tree = {"name": "Root", "children": []}
        
        if "Frequency" in paths:
            min_exposure = state.get("engine_context", {}).get("investigation_configuration", {}).get("minimum_exposure", 500)
            min_expected_claims = state.get("engine_context", {}).get("investigation_configuration", {}).get("minimum_expected_claims", 10)
            df_latest = df[df['Year'] == latest_year] if 'Year' in df.columns else df
            freq_tree = investigate_phase_1(df_latest, min_exposure=min_exposure, min_expected_claims=min_expected_claims)
            
            # Find worst leaf
            worst_leaf = extract_worst_leaf(freq_tree)
            worst_path = worst_leaf.get("name", "Root")
            p2 = investigate_phase_2(df, worst_path, latest_year, state)
            freq_tree["phase_2"] = p2
            freq_tree["engine_source"] = "frequency"
            merged_tree["children"].append(freq_tree)
            
        if "Severity" in paths:
            threshold = state.get("engine_context", {}).get("investigation_configuration", {}).get("severity_drift_threshold", 0.05)
            min_claims = state.get("engine_context", {}).get("investigation_configuration", {}).get("minimum_claims_for_investigation", 30)
            boot_iters = state.get("engine_context", {}).get("investigation_configuration", {}).get("bootstrap_iterations", 500)
            conf_level = state.get("engine_context", {}).get("investigation_configuration", {}).get("confidence_level", 0.95)
            
            sev_engine = SeverityAnalyticsEngine(
                materiality_threshold=threshold,
                minimum_claims=min_claims,
                bootstrap_iterations=boot_iters,
                confidence_level=conf_level,
                baseline_years=[2022, 2023],
                current_years=[2024]
            )
            
            total_portfolio_excess_cost = max(state.get("drift_metrics", {}).get("excess_cost", 1000.0), 1.0)
            sev_tree = investigate_severity_phase_1(
                df=df,
                current_path="Root",
                depth=0,
                max_depth=2,
                sev_engine=sev_engine,
                total_portfolio_excess_cost=total_portfolio_excess_cost
            )
            
            worst_leaf = extract_worst_leaf(sev_tree)
            worst_path = worst_leaf.get("name", "Root")
            p2 = investigate_severity_phase_2(df, worst_path, sev_engine, state)
            sev_tree["phase_2"] = p2
            sev_tree["engine_source"] = "severity"
            merged_tree["children"].append(sev_tree)
            
        # Always run claimant profile shift for top contributing segment under Combined
        comb_segs = state.get("comb_segments", [])
        if comb_segs:
            top_seg = comb_segs[0]
            worst_path = f"Root -> {top_seg['dimension']}:{top_seg['segment']}"
        else:
            worst_path = "Root"
            
        p2 = investigate_phase_2(df, worst_path, latest_year, state)
        merged_tree["phase_2"] = p2
        merged_tree["engine_source"] = "combined"
        
        state["investigation_tree"] = merged_tree
        
        # Merge evidence & generate decision options from KB pattern matching
        from agent.combined_coordinator import CombinedCoordinator
        coordinator = CombinedCoordinator()
        state["decision_options"] = coordinator.generate_normalized_evidence(state)
        
        # Run pattern-matching decision supporto pre-population
        state = business_impact_node(state) # recalculate KB options for worst segment
        
        state["messages"].append(SystemMessage(content="Investigation Agent: Completed Combined multi-engine investigation."))
        
    else:
        # FREQUENCY WORKFLOW (Original)
        latest_year = df['Year'].max() if 'Year' in df.columns else 2024
        
        # Load Frequency config parameters from state or engine_context
        min_exposure = state.get("engine_context", {}).get("investigation_configuration", {}).get("minimum_exposure", 500)
        min_expected_claims = state.get("engine_context", {}).get("investigation_configuration", {}).get("minimum_expected_claims", 10)
        
        state["planner_notebook"].append({
            "observation": "Initiating Phase 1 Portfolio Investigation.",
            "hypothesis": "A specific demographic segment is driving the overall portfolio drift.",
            "decision": "Use StatisticalFeatureRanker to recursively drill down."
        })
        
        df_latest = df[df['Year'] == latest_year] if 'Year' in df.columns else df
        
        # Phase 1
        tree = investigate_phase_1(df_latest, min_exposure=min_exposure, min_expected_claims=min_expected_claims)
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
        state["investigation_tree"]["phase_2"] = phase_2_results
        state["messages"].append(SystemMessage(content="Investigation Agent: Completed 2-Phase Investigation."))
        
    return state
