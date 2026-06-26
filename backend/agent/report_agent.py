import json
from typing import Any
from langchain_core.messages import SystemMessage
from agent.state import InvestigationState

def report_node(state: InvestigationState) -> InvestigationState:
    """
    Compiles all findings into a final markdown report.
    """
    metrics = state.get("drift_metrics", {})
    tree = state.get("investigation_tree", {})
    impact = state.get("business_impact", {})
    options = state.get("decision_options", [])
    event_reconstruction = state.get("event_reconstruction", "")
    state["planner_notebook"].append({
        "observation": "Initiating final report compilation.",
        "hypothesis": "All necessary evidence, impact, and options have been gathered.",
        "decision": "Generate deterministic markdown report from structured data."
    })
    
    report = _generate_fallback_report(metrics, impact, event_reconstruction, options)
        
    state["final_report"] = report
    state["investigation_status"] = "complete"
    state["messages"].append(SystemMessage(content="Report Agent: Final actuarial report generated."))
    
    return state

def _generate_fallback_report(metrics: dict, impact: dict, event: str, options: list) -> str:
    report = (
        "# AI Actuarial Experience Investigation Report\n\n"
        "## Executive Summary\n"
        f"A relative drift of {metrics.get('relative_drift', 0)*100:.2f}% was detected with a Z-Score of {metrics.get('z_score', 0):.2f}.\n\n"
        "## Event Reconstruction\n"
        f"{event}\n\n"
        "## Business Impact\n"
        f"- Additional Claims: {impact.get('additional_claims', 0)}\n"
        f"- Risk Level: {impact.get('risk_level', 'Unknown')}\n"
        f"- Most Impacted Portfolio: {impact.get('most_impacted_portfolio', 'Unknown')}\n\n"
        "## Decision Options\n"
    )
    for opt in options:
        report += f"- **{opt.get('possible_action')}** (Priority: {opt.get('suggested_priority', 'Unknown')})\n"
        report += f"  - Benefits: {opt.get('benefits', '')}\n"
        report += f"  - Risks: {opt.get('risks', '')}\n"
    return report
