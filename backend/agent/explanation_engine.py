from typing import Dict, Any

def generate_root_cause_explanation(investigation_tree: Dict[str, Any], business_impact: Dict[str, Any], planner_notebook: list) -> str:
    """
    Deterministically generates the Root Cause Explanation by analyzing the statistical evidence,
    investigation path, and historical baseline comparison.
    """
    
    if not investigation_tree:
        return "No investigation tree available to determine root cause."
        
    # Traverse to worst leaf
    def get_worst_leaf(node):
        if not node.get("children"):
            return node
        worst = max(node["children"], key=lambda x: abs(x.get("drift", 0)))
        return get_worst_leaf(worst)
        
    worst_leaf = get_worst_leaf(investigation_tree)
    path = worst_leaf.get("name", "Unknown Segment")
    
    # Calculate stats
    exposure = worst_leaf.get("exposure", 0)
    actual_freq = worst_leaf.get("actual_frequency", 0)
    expected_freq = worst_leaf.get("expected_frequency", 0)
    
    # Global stats from root
    total_exposure = investigation_tree.get("exposure", 1)
    
    exposure_pct = (exposure / total_exposure) * 100 if total_exposure > 0 else 0
    
    explanation_parts = []
    
    # 1. Investigation Path & Statistical Evidence
    clean_path = path.replace('Root -> ', '')
    explanation_parts.append(f"The primary root cause of the portfolio drift was isolated to the **{clean_path}** segment.")
    
    # 2. Historical Baseline Comparison & Contribution
    drift_diff = (actual_freq - expected_freq) * 100
    explanation_parts.append(
        f"This segment experienced an absolute claim frequency drift of {drift_diff:+.2f}% "
        f"(Actual: {actual_freq*100:.2f}% vs Expected: {expected_freq*100:.2f}%). "
    )
    explanation_parts.append(f"Despite representing only {exposure_pct:.1f}% of the total portfolio exposure, this segment is the primary mathematical driver of the anomaly.")
    
    # 3. Business Impact
    add_claims = business_impact.get("additional_claims", 0)
    if add_claims > 0:
        explanation_parts.append(f"The variance in this segment resulted in approximately {add_claims:,} unexpected claims.")
        
    # 4. Planner Reasoning
    planner_insights = [note for note in planner_notebook if "Phase 1 isolated" in note.get("observation", "")]
    if planner_insights:
        explanation_parts.append("The deterministic planner selected this path because each feature split iteratively increased the explanatory power of the model.")
        
    # 5. Profile Shifts (Phase 2)
    phase_2 = investigation_tree.get("phase_2", {})
    shifts = phase_2.get("profile_shifts", [])
    if shifts:
        top_shift = shifts[0]
        attr = top_shift.get("attribute", "")
        val = top_shift.get("value", "")
        hist = top_shift.get("historical_share", 0) * 100
        curr = top_shift.get("current_share", 0) * 100
        explanation_parts.append(
            f"Compared to historical baselines, the most significant shift within this segment was in {attr} ({val}), "
            f"which changed from {hist:.1f}% to {curr:.1f}% of the segment's claim profile."
        )

    return " ".join(explanation_parts)

def generate_explainability_score(investigation_tree: Dict[str, Any], drift_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates an Explainability Score based on statistical evidence, historical agreement, and contribution strength.
    """
    # Base score
    score = 0
    factors = []
    
    # 1. Statistical Strength (Z-Score)
    z_score = abs(drift_metrics.get("z_score", 0))
    if z_score > 3:
        score += 30
        factors.append({"name": "Statistical Strength", "status": "Strong", "desc": f"Z-score of {z_score:.2f} proves drift is not random noise."})
    elif z_score > 2:
        score += 20
        factors.append({"name": "Statistical Strength", "status": "Moderate", "desc": f"Z-score of {z_score:.2f} indicates possible variance."})
    else:
        factors.append({"name": "Statistical Strength", "status": "Weak", "desc": f"Z-score of {z_score:.2f} is within normal bounds."})

    # 2. Evidence Completeness
    if investigation_tree and "children" in investigation_tree and investigation_tree["children"]:
        score += 30
        factors.append({"name": "Evidence Completeness", "status": "Strong", "desc": "Phase 1 successfully isolated a specific sub-segment."})
    else:
        factors.append({"name": "Evidence Completeness", "status": "Weak", "desc": "No sub-segments could be isolated."})

    # 3. Contribution Strength
    if investigation_tree:
        def get_worst_leaf(node):
            if not node.get("children"):
                return node
            worst = max(node["children"], key=lambda x: abs(x.get("drift", 0)))
            return get_worst_leaf(worst)
        
        worst = get_worst_leaf(investigation_tree)
        node_drift = worst.get("drift", 0)
        port_drift = investigation_tree.get("drift", 0)
        
        if port_drift != 0 and (node_drift / port_drift) > 0.5:
            score += 40
            factors.append({"name": "Contribution Strength", "status": "Strong", "desc": "The root cause explains the majority of the portfolio variance."})
        else:
            score += 15
            factors.append({"name": "Contribution Strength", "status": "Weak", "desc": "The root cause only explains a minor portion of the portfolio variance."})

    return {
        "overall_score": score,
        "factors": factors
    }
