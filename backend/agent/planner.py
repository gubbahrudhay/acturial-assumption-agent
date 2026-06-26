import os
from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

# Load environment variables (e.g., OPENAI_API_KEY)
load_dotenv()

from agent.state import InvestigationState

# We would import the analytical tools here to be used by the agent nodes
from tools.validator import validate_data
from tools.frequency_calculator import calculate_frequency
from tools.drift_detector import detect_drift
from tools.investigation import recursive_investigate

# Global LLM instance removed to support dynamic API keys from requests

def planner_node(state: InvestigationState) -> InvestigationState:
    """
    The core planner that decides what to do based on current state.
    Uses scientific reasoning cycle.
    """
    state["investigation_status"] = "planner"
    
    # Check if Layer 2 calculations exist
    if not state.get("drift_metrics"):
        state["planner_notebook"].append({
            "observation": "Initiating investigation cycle. Need foundational statistical metrics.",
            "hypothesis": "Layer 2 analytics required to determine if drift exists.",
            "decision": "Route to Statistical Analytics Engine."
        })
        return state
        
    # Check if drift requires investigation
    if state["drift_metrics"].get("requires_investigation") and not state.get("investigation_tree"):
        state["planner_notebook"].append({
            "observation": "Significant statistical drift detected.",
            "hypothesis": "A latent business event may be driving this. Need to isolate the demographic and claim profile.",
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
    
    # We add the nodes (which will be implemented in their respective files or here)
    # For simplicity, we are importing them from the other agent files
    from agent.investigation_agent import investigation_node
    from agent.business_impact_agent import business_impact_node
    from agent.decision_support_agent import decision_support_node
    from agent.report_agent import report_node
    
    # Add nodes
    workflow.add_node("planner", planner_node)
    
    # Wrap the tool in a node function
    def drift_node(state: InvestigationState) -> InvestigationState:
        import pandas as pd
        from tools.drift_detector import StatisticalAnalyticsEngine
        
        df = pd.read_csv(state["df_path"])
        if 'Year' in df.columns:
            latest_year = df['Year'].max()
            df = df[df['Year'] == latest_year]
            
        engine = StatisticalAnalyticsEngine()
        state["drift_metrics"] = engine.calculate_metrics(df)
        state["historical_baseline"] = engine.get_historical_claim_profile(df, latest_year)
        
        state["messages"].append(SystemMessage(content="Statistical Engine: Executed Layer 2 analytics."))
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
                return get_worst(max(node["children"], key=lambda x: abs(x.get("drift", 0))))
            worst = get_worst(tree)
            state["primary_root_cause"] = worst.get("name", "Unknown").replace("Root -> ", "")
        else:
            state["primary_root_cause"] = "Unknown"
            
        state["explainability_report"]["explanation_text"] = generate_root_cause_explanation(
            state.get("investigation_tree", {}), 
            state.get("business_impact", {}), 
            state.get("planner_notebook", [])
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
    
    # After each specialized node, return to the planner
    workflow.add_edge("drift_detector", "planner")
    workflow.add_edge("investigation_agent", "planner")
    workflow.add_edge("business_impact_agent", "planner")
    workflow.add_edge("decision_support_agent", "planner")
    workflow.add_edge("explainability_node", "planner")
    workflow.add_edge("report_agent", "planner")
    
    return workflow.compile()

# Example execution
if __name__ == "__main__":
    graph = create_agent_graph()
    initial_state = {
        "api_key": "",
        "df_path": os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'insurance_experience.csv'),
        "drift_info": {},
        "investigation_tree": {},
        "investigation_memory": [],
        "planner_reasoning": [],
        "business_impact": {},
        "decision_options": [],
        "scenario_overrides": {},
        "chat_history": [],
        "final_report": "",
        "current_step": "start",
        "messages": []
    }
