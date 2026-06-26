from typing import Any, List, Dict
from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field
import json
from agent.state import InvestigationState

class DecisionOption(BaseModel):
    possible_action: str = Field(description="The suggested actuarial or operational action (e.g., 'Review Pricing Assumptions')")
    suggested_priority: str = Field(description="High, Medium, or Low")
    benefits: str = Field(description="Pros/Benefits of this action")
    risks: str = Field(description="Cons/Risks of this action")
    supporting_evidence: List[str] = Field(description="Evidence bullet points reading directly from the Investigation Event Reconstruction or Business Impact")

class DecisionOptionsList(BaseModel):
    options: List[DecisionOption]

def decision_support_node(state: InvestigationState) -> InvestigationState:
    """
    Analyzes the business impact and event reconstruction to generate structured decision options.
    The AI supports actuarial judgement, it does not make the decision.
    """
    impact = state.get("business_impact", {})
    event_reconstruction = state.get("event_reconstruction", "")
    # ---------------------------------------------------------
    # Deterministic Decision Support (No LLMs)
    # ---------------------------------------------------------
    state["planner_notebook"].append({
        "observation": "Initiating Decision Support generation.",
        "hypothesis": "Actuary requires structured options (Action, Benefits, Risks, Evidence, Priority).",
        "decision": "Retrieve deterministically generated options from Knowledge Base."
    })
    
    if not impact:
        state["decision_options"] = []
        return state
        
    kb_options = state.get("kb_decision_options", [])
    if kb_options:
        state["decision_options"] = kb_options
        state["planner_notebook"].append({
            "observation": f"Successfully retrieved {len(kb_options)} structured decision options from Knowledge Base.",
            "hypothesis": "The options are ready for actuary review.",
            "decision": "Store in InvestigationState."
        })
    else:
        state["decision_options"] = _get_fallback_options()
        state["planner_notebook"].append({
            "observation": "No specific KB options found.",
            "hypothesis": "Requires generic fallback options.",
            "decision": "Fell back to static options."
        })
        
    state["messages"].append(SystemMessage(content="Decision Support Agent: Generated structured decision options."))
    
    return state

def _get_fallback_options() -> List[Dict]:
    return [
        {
            "possible_action": "Continue Monitoring",
            "suggested_priority": "Medium",
            "benefits": "No pricing disruption. Avoids overreacting to short-term volatility.",
            "risks": "Risk of assumption deterioration if the trend continues.",
            "supporting_evidence": ["Drift detected in the portfolio."]
        },
        {
            "possible_action": "Review Pricing Assumptions",
            "suggested_priority": "High",
            "benefits": "Better pricing adequacy and profitability.",
            "risks": "May reduce competitiveness in the market.",
            "supporting_evidence": ["High business impact detected in specific segments."]
        }
    ]
