import os
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agent.state import InvestigationState

# Analytical tool imports
from tools.validator import validate_data
from tools.frequency_calculator import calculate_frequency
from tools.drift_detector import StatisticalAnalyticsEngine
from tools.feature_ranker import StatisticalFeatureRanker
from tools.investigation import recursive_investigate
from engines.severity_engine import SeverityAnalyticsEngine

def planner_node(state: InvestigationState) -> InvestigationState:
    """
    The core planner that decides what to do based on current state.
    Uses scientific reasoning cycle.
    """
    state["investigation_status"] = "planner"
    active_engine = state.get("engine_context", {}).get("active_engine", "Frequency")
    
    # Check if Layer 2 calculations exist
    if not state.get("drift_metrics"):
        state["planner_notebook"].append({
            "observation": f"Initiating {active_engine} investigation cycle. Need foundational statistical metrics.",
            "hypothesis": "Layer 2 analytics required to determine if drift exists.",
            "decision": f"Route to {active_engine} Analytics Engine."
        })
        return state
        
    # Check if drift requires investigation
    if state["drift_metrics"].get("requires_investigation") and not state.get("investigation_tree"):
        state["planner_notebook"].append({
            "observation": f"Significant statistical {active_engine.lower()} drift detected.",
            "hypothesis": "A latent business event may be driving this. Need to isolate the demographic and cost profile.",
            "decision": "Route to Phase 1 & 2 Investigation Agent."
        })
        return state
        
    # If tree exists but no business impact
    if state.get("investigation_tree") and not state.get("business_impact"):
        state["planner_notebook"].append({
            "observation": "Investigation tree isolated the anomalous segments.",
            "hypothesis": "Need to quantify operational and financial impact before recommending action.",
            "decision": "Route to Business Impact module."
        })
        return state

    # If impact exists but no decision support
    if state.get("business_impact") and not state.get("decision_options"):
        state["planner_notebook"].append({
            "observation": "Business impact quantified.",
            "hypothesis": "Actuary requires structured options to mitigate this drift.",
            "decision": "Route to Decision Support module."
        })
        return state
        
    # Explainability
    if state.get("decision_options") and not state.get("explainability_report"):
        state["planner_notebook"].append({
            "observation": "Decision support options generated.",
            "hypothesis": "Need to compute final explainability score and deterministic justification.",
            "decision": "Route to Explainability Engine."
        })
        return state
        
    # Final report
    if state.get("explainability_report") and not state.get("final_report"):
        state["planner_notebook"].append({
            "observation": "Explainability report generated.",
            "hypothesis": "Investigation cycle is complete. Compiling findings.",
            "decision": "Route to Report Agent."
        })
        return state
        
    return state

def determine_next_node(state: InvestigationState) -> str:
    """
    Conditional edge logic to route to the correct node based on planner's decision.
    """
    if not state.get("drift_metrics"):
        return "drift_detector"
    if state["drift_metrics"].get("requires_investigation") and not state.get("investigation_tree"):
        return "investigation_agent"
    if not state["drift_metrics"].get("requires_investigation") and not state.get("final_report"):
        return "report_agent"
    if state.get("investigation_tree") and not state.get("business_impact"):
        return "business_impact_agent"
    if state.get("business_impact") and not state.get("decision_options"):
        return "decision_support_agent"
    if state.get("decision_options") and not state.get("explainability_report"):
        return "explainability_node"
    if state.get("explainability_report") and not state.get("final_report"):
        return "report_agent"
    return END

def create_agent_graph():
    """
    Creates and compiles the LangGraph.
    """
    workflow = StateGraph(InvestigationState)
    
    # Specialized node functions
    from agent.investigation_agent import investigation_node
    from agent.business_impact_agent import business_impact_node
    from agent.decision_support_agent import decision_support_node
    from agent.report_agent import report_node
    
    workflow.add_node("planner", planner_node)
    
    def drift_node(state: InvestigationState) -> InvestigationState:
        import pandas as pd
        active_engine = state.get("engine_context", {}).get("active_engine", "Frequency")
        
        df = pd.read_csv(state["df_path"])
        
        if active_engine == "Severity":
            # Severity
            if 'Year' in df.columns:
                latest_year = df['Year'].max()
                df_claims = df[(df['Claim'] == 1) & (df['Year'] == latest_year)]
            else:
                df_claims = df[df['Claim'] == 1]
                
            min_claims = state.get("engine_context", {}).get("investigation_configuration", {}).get("minimum_claims_for_investigation", 30)
            fdr_target = state.get("engine_context", {}).get("investigation_configuration", {}).get("fdr_target", 0.05)
            
            engine = SeverityAnalyticsEngine(
                materiality_threshold=state.get("engine_context", {}).get("investigation_configuration", {}).get("severity_drift_threshold", 0.05),
                minimum_claims=min_claims,
                fdr_target=fdr_target
            )
            metrics = engine.calculate_metrics(df)
            state["drift_metrics"] = metrics
            
            # Attach actual rolling trend data
            trend_df = engine.calculate_rolling_trend(df)
            state["drift_metrics"]["trend_data"] = trend_df.to_dict(orient="records") if not trend_df.empty else []
            
            # Segment Surveillance Gate
            state["trigger_source"] = "portfolio"
            surveillance = engine.run_segment_surveillance(df)
            if metrics.get("requires_investigation"):
                state["trigger_source"] = "portfolio"
            elif surveillance.get("triggered", False):
                state["drift_metrics"]["requires_investigation"] = True
                state["trigger_source"] = "segment_surveillance"
                state["trigger_dimension"] = surveillance["trigger_dimension"]
                state["trigger_segment"] = surveillance["trigger_segment"]
                state["segment_metrics"] = surveillance["segment_metrics"]
                state["trigger_reason"] = surveillance["trigger_reason"]
            
            # Populate basic baseline claims profile
            claims_df = engine.filter_claims(df)
            baseline_claims = claims_df[claims_df['Year'].isin([2022, 2023])]
            
            if not baseline_claims.empty:
                total_base = len(baseline_claims)
                disease_dist = (baseline_claims['Claim_Category'].value_counts() / total_base).to_dict() if 'Claim_Category' in baseline_claims.columns else {}
                hospital_dist = (baseline_claims['Hospital_Type'].value_counts() / total_base).to_dict() if 'Hospital_Type' in baseline_claims.columns else {}
                status_dist = (baseline_claims['Claim_Status'].value_counts() / total_base).to_dict() if 'Claim_Status' in baseline_claims.columns else {}
                state["historical_baseline"] = {
                    "Claim_Category": disease_dist,
                    "Hospital_Type": hospital_dist,
                    "Claim_Status": status_dist
                }
            else:
                state["historical_baseline"] = {"Claim_Category": {}, "Hospital_Type": {}, "Claim_Status": {}}
                
            state["messages"].append(SystemMessage(content="Statistical Engine: Executed Layer 2 Severity analytics."))
        elif active_engine == "Combined":
            if 'Year' in df.columns:
                latest_year = df['Year'].max()
                df_latest = df[df['Year'] == latest_year]
            else:
                latest_year = 2024
                df_latest = df
                
            from agent.combined_coordinator import CombinedCoordinator
            coordinator = CombinedCoordinator()
            state = coordinator.coordinate_investigation(df, state)
            
            # Set historical baseline for UI/agent queries (using frequency engine's helper)
            from tools.drift_detector import StatisticalAnalyticsEngine as FrequencyEngine
            freq_eng = FrequencyEngine()
            state["historical_baseline"] = freq_eng.get_historical_claim_profile(df, latest_year)
            
            # Determine if investigation is needed
            requires_investigation = (state["drift_metrics"]["deterioration_pattern"] != "No Material Combined Deterioration")
            state["drift_metrics"]["requires_investigation"] = requires_investigation
            
            # Set trigger source and copy surveillance flags for routing
            state["trigger_source"] = "portfolio"
            if state["freq_surveillance"].get("triggered") or state["sev_surveillance"].get("triggered"):
                state["trigger_source"] = "segment_surveillance"
                
            state["messages"].append(SystemMessage(content="Statistical Engine: Executed Layer 2 Combined analytics."))
        else:
            # Frequency
            if 'Year' in df.columns:
                latest_year = df['Year'].max()
                df_latest = df[df['Year'] == latest_year]
            else:
                latest_year = 2024
                df_latest = df
                
            min_exp = state.get("engine_context", {}).get("investigation_configuration", {}).get("minimum_exposure", 500)
            min_exp_claims = state.get("engine_context", {}).get("investigation_configuration", {}).get("minimum_expected_claims", 10)
            drift_thresh = state.get("engine_context", {}).get("investigation_configuration", {}).get("drift_threshold", 0.05)
            fdr_t = state.get("engine_context", {}).get("investigation_configuration", {}).get("fdr_target", 0.05)
            
            engine = StatisticalAnalyticsEngine(
                relative_drift_threshold=drift_thresh,
                min_exposure=min_exp,
                min_expected_claims=min_exp_claims,
                fdr_target=fdr_t
            )
            
            metrics = engine.calculate_metrics(df_latest)
            state["drift_metrics"] = metrics
            
            # Attach actual rolling trend data
            trend_df = engine.calculate_rolling_drift(df)
            state["drift_metrics"]["trend_data"] = trend_df.to_dict(orient="records") if not trend_df.empty else []
            
            state["historical_baseline"] = engine.get_historical_claim_profile(df, latest_year)
            
            # Segment Surveillance Gate
            state["trigger_source"] = "portfolio"
            surveillance = engine.run_segment_surveillance(df_latest)
            if metrics.get("requires_investigation"):
                state["trigger_source"] = "portfolio"
            elif surveillance.get("triggered", False):
                state["drift_metrics"]["requires_investigation"] = True
                state["trigger_source"] = "segment_surveillance"
                state["trigger_dimension"] = surveillance["trigger_dimension"]
                state["trigger_segment"] = surveillance["trigger_segment"]
                state["segment_metrics"] = surveillance["segment_metrics"]
                state["trigger_reason"] = surveillance["trigger_reason"]
                
            state["messages"].append(SystemMessage(content="Statistical Engine: Executed Layer 2 Frequency analytics."))
            
        return state
        
    workflow.add_node("drift_detector", drift_node)
    workflow.add_node("investigation_agent", investigation_node)
    workflow.add_node("business_impact_agent", business_impact_node)
    workflow.add_node("decision_support_agent", decision_support_node)
    
    def explainability_node(state: InvestigationState) -> InvestigationState:
        from agent.explanation_engine import generate_root_cause_explanation, generate_explainability_score
        
        state["explainability_report"] = generate_explainability_score(state.get("investigation_tree", {}), state.get("drift_metrics", {}))
        
        tree = state.get("investigation_tree", {})
        if tree and "children" in tree and tree["children"]:
            def get_worst(node):
                if not node.get("children"): return node
                # Sibling children are sorted: children[0] is the worst
                return get_worst(node["children"][0])
            worst = get_worst(tree)
            state["primary_root_cause"] = worst.get("name", "Unknown").replace("Root -> ", "")
        else:
            state["primary_root_cause"] = "Unknown"
            
        state["explainability_report"]["explanation_text"] = generate_root_cause_explanation(
            state.get("investigation_tree", {}), 
            state.get("business_impact", {}), 
            state.get("planner_notebook", []),
            state.get("engine_context", {}).get("active_engine", "Frequency")
        )
        return state
        
    workflow.add_node("explainability_node", explainability_node)
    workflow.add_node("report_agent", report_node)
    
    # Define edges
    workflow.set_entry_point("planner")
    
    workflow.add_conditional_edges(
        "planner",
        determine_next_node,
        {
            "drift_detector": "drift_detector",
            "investigation_agent": "investigation_agent",
            "business_impact_agent": "business_impact_agent",
            "decision_support_agent": "decision_support_agent",
            "explainability_node": "explainability_node",
            "report_agent": "report_agent",
            END: END
        }
    )
    
    workflow.add_edge("drift_detector", "planner")
    workflow.add_edge("investigation_agent", "planner")
    workflow.add_edge("business_impact_agent", "planner")
    workflow.add_edge("decision_support_agent", "planner")
    workflow.add_edge("explainability_node", "planner")
    workflow.add_edge("report_agent", "planner")
    
    return workflow.compile()
