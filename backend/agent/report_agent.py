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
    active_engine = state.get("engine_context", {}).get("active_engine", "Frequency")
    
    state["planner_notebook"].append({
        "observation": f"Initiating final {active_engine.lower()} report compilation.",
        "hypothesis": "All necessary evidence, impact, and options have been gathered.",
        "decision": "Generate deterministic markdown report from structured data."
    })
    
    if active_engine == "Severity":
        report = _generate_severity_report(metrics, impact, event_reconstruction, options)
    elif active_engine == "Combined":
        report = _generate_combined_report(metrics, impact, event_reconstruction, options)
    else:
        report = _generate_frequency_report(metrics, impact, event_reconstruction, options)
        
    state["final_report"] = report
    state["investigation_status"] = "complete"
    state["messages"].append(SystemMessage(content=f"Report Agent: Final actuarial {active_engine.lower()} report generated."))
    
    return state

def _generate_combined_report(metrics: dict, impact: dict, event: str, options: list) -> str:
    report = (
        "# AI Actuarial Experience Investigation Report (Combined)\n\n"
        "## Executive Summary\n"
        f"A relative combined cost drift of {metrics.get('combined_drift', 0)*100:.2f}% was detected with a Combined O/E ratio of {metrics.get('combined_oe', 0.0):.2f}.\n"
        f"- **Deterioration Pattern**: {metrics.get('deterioration_pattern', 'Unknown')}\n"
        f"- **Excess Claim Cost**: {metrics.get('excess_cost', 0.0):,.2f}\n"
        f"- **Risk Level**: {impact.get('risk_level', 'Unknown')}\n\n"
        "## Cost Decomposition Bridge\n"
        f"- Expected Total Claim Cost: {metrics.get('expected_total_cost', 0.0):,.2f}\n"
        f"- Claim Incidence Effect: {metrics.get('incidence_effect', 0.0):+,.2f}\n"
        f"- Claim Severity Effect: {metrics.get('severity_effect', 0.0):+,.2f}\n"
        f"- Mix / Interaction Effect: {metrics.get('mix_effect', 0.0):+,.2f}\n"
        f"- Observed Total Claim Cost: {metrics.get('observed_total_cost', 0.0):,.2f}\n\n"
        "## Event Reconstruction\n"
        f"{event}\n\n"
        "## Decision Support Options\n"
        "The following structured options have been pre-populated to assist the actuarial judgement:\n"
    )
    for opt in options:
        report += f"- **{opt.get('possible_action')}** (Priority: {opt.get('suggested_priority', 'Unknown')})\n"
        report += f"  - Benefits: {opt.get('benefits', '')}\n"
        report += f"  - Risks: {opt.get('risks', '')}\n"
        report += f"  - Supporting Evidence: {', '.join(opt.get('supporting_evidence', []))}\n"
    return report

def _generate_frequency_report(metrics: dict, impact: dict, event: str, options: list) -> str:
    report = (
        "# AI Actuarial Experience Investigation Report (Frequency)\n\n"
        "## Executive Summary\n"
        f"A relative frequency drift of {metrics.get('relative_drift', 0)*100:.2f}% was detected with a Z-Score of {metrics.get('z_score', 0):.2f}.\n\n"
        "## Event Reconstruction\n"
        f"{event}\n\n"
        "## Business Impact & Experience Measures\n"
        f"- Observed Claims: {metrics.get('actual_claims', 0)}\n"
        f"- Expected Claims: {metrics.get('expected_claims', 0.0):.2f}\n"
        f"- Additional Claims: {impact.get('additional_claims', 0)}\n"
        f"- Positive Excess Claims: {metrics.get('positive_excess_claims', 0.0):.2f}\n"
        f"- Affected Exposure: {impact.get('affected_exposure', 0.0):,.2f}\n"
        f"- Risk Level: {impact.get('risk_level', 'Unknown')}\n"
        f"- Most Impacted Portfolio: {impact.get('most_impacted_portfolio', 'Unknown')}\n\n"
        "## Decision Options\n"
        "The following structured options have been pre-populated to assist the actuarial judgement:\n"
    )
    for opt in options:
        report += f"- **{opt.get('possible_action')}** (Priority: {opt.get('suggested_priority', 'Unknown')})\n"
        report += f"  - Benefits: {opt.get('benefits', '')}\n"
        report += f"  - Risks: {opt.get('risks', '')}\n"
        report += f"  - Supporting Evidence: {', '.join(opt.get('supporting_evidence', []))}\n"
    return report

def _generate_severity_report(metrics: dict, impact: dict, event: str, options: list) -> str:
    report = (
        "# AI Actuarial Experience Investigation Report (Severity)\n\n"
        "## 1. Executive Summary\n"
        f"A relative severity drift of {metrics.get('relative_drift', 0)*100:+.2f}% was detected with an aggregate O/E ratio of {metrics.get('oe_ratio', 0.0):.2f}.\n"
        f"- **Claim Count**: {metrics.get('claim_count', 0)}\n"
        f"- **Excess Claim Cost**: {metrics.get('excess_cost', 0.0):,.2f}\n"
        f"- **Deterioration Classification**: {metrics.get('deterioration_classification', 'Unknown')}\n"
        f"- **Risk Level**: {impact.get('risk_level', 'Unknown')}\n\n"
        "## 2. Expected vs Observed Severity\n"
        f"- **Total Observed Claim Cost**: {metrics.get('observed_cost', 0.0):,.2f}\n"
        f"- **Total Expected Claim Cost (pre-event assumption)**: {metrics.get('expected_cost', 0.0):,.2f}\n"
        f"- **Observed Average Severity**: {metrics.get('observed_severity', 0.0):,.2f}\n"
        f"- **Expected Average Severity**: {metrics.get('expected_severity', 0.0):,.2f}\n\n"
        "## 3. Severity O/E Ratio\n"
        f"The aggregate Severity O/E ratio is **{metrics.get('oe_ratio', 0.0):.2f}**, representing "
        f"actual claims severity running {abs(metrics.get('relative_drift', 0.0))*100:.1f}% "
        f"{'above' if metrics.get('relative_drift', 0.0) >= 0 else 'below'} baseline expectation.\n\n"
        "## 4. Statistical Confidence\n"
        f"A 95% bootstrap confidence interval was computed over {metrics.get('claim_count', 0)} claims:\n"
        f"- **Bootstrap 95% CI bounds**: [{metrics.get('bootstrap_lower_bound', 0.0):.2f}, {metrics.get('bootstrap_upper_bound', 0.0):.2f}]\n"
        f"- **Statistically Significant**: {'Yes (Deterioration is credible)' if metrics.get('is_significant', False) else 'No'}\n\n"
        "## 5. High-Cost Claim Sensitivity\n"
        f"- **Primary High-Cost Threshold (Baseline P99)**: {metrics.get('high_cost_threshold', 0.0):,.2f}\n"
        f"- **Number of High-Cost Outliers**: {metrics.get('high_cost_count', 0)}\n"
        f"- **Outlier Financial Cost**: {metrics.get('high_cost_cost', 0.0):,.2f} ({metrics.get('high_cost_share', 0.0)*100:.1f}% cost share)\n"
        f"- **O/E Excluding High-Cost Outliers**: **{metrics.get('oe_excluding_high_cost', 0.0):.2f}**\n\n"
        "## 6. Severity Root Cause Hypothesis\n"
        f"{event}\n\n"
        "## 7. Decision Options\n"
    )
    for opt in options:
        report += f"- **{opt.get('possible_action')}** (Priority: {opt.get('suggested_priority', 'Unknown')})\n"
        report += f"  - Benefits: {opt.get('benefits', '')}\n"
        report += f"  - Risks: {opt.get('risks', '')}\n"
        report += f"  - Supporting Evidence: {', '.join(opt.get('supporting_evidence', []))}\n"
        
    report += (
        "\n## 8. Actuarial Limitations & Disclosures\n"
        "**Synthetic Demonstration Disclosures**:\n"
        "- The synthetic experience dataset loaded does *not* contain independent partitions for **Paid Claims**, **Case Reserves**, or **Incurred Claims**.\n"
        "- The field `Actual_Claim_Amount` represents the total stochastically simulated claim severity payout. It should *not* be interpreted as an 'Incurred Amount' containing reserving provisions.\n"
        "- The `severity_drift_threshold` is a configurable demonstration assumption used to illustrate the alerting cycle.\n"
        "- The deterioration classification (e.g. Upper-Tail Deterioration) is a description of the statistical distribution of excess cost across bands and does not by itself establish the underlying causal event.\n"
    )
    return report
