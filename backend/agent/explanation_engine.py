from typing import Dict, Any

def generate_root_cause_explanation(investigation_tree: Dict[str, Any], business_impact: Dict[str, Any], planner_notebook: list, active_engine: str = "Frequency") -> str:
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
        # children are sorted so children[0] is the worst
        return get_worst_leaf(node["children"][0])
        
    worst_leaf = get_worst_leaf(investigation_tree)
    path = worst_leaf.get("name", "Unknown Segment")
    clean_path = path.replace('Root -> ', '')
    
    explanation_parts = []
    
    # ---------------------------------------------------------
    # SEVERITY EXPLANATION NARRATIVE
    # ---------------------------------------------------------
    if active_engine == "Severity":
        claim_count = worst_leaf.get("claim_count", 0)
        obs_sev = worst_leaf.get("observed_severity", 0.0)
        exp_sev = worst_leaf.get("expected_severity", 0.0)
        oe_ratio = worst_leaf.get("oe_ratio", 0.0)
        excess_cost = worst_leaf.get("excess_cost", 0.0)
        drift = worst_leaf.get("drift", 0.0)
        
        lower_ci = worst_leaf.get("bootstrap_lower_bound", 1.0)
        upper_ci = worst_leaf.get("bootstrap_upper_bound", 1.0)
        is_sig = worst_leaf.get("is_significant", False)
        
        explanation_parts.append(f"The primary statistical contributor of the severity drift was isolated to the **{clean_path}** segment.")
        explanation_parts.append(
            f"This segment experienced an aggregate Severity O/E ratio of {oe_ratio:.2f} (Observed: {obs_sev:,.2f} vs Expected: {exp_sev:,.2f}), "
            f"representing a relative cost deterioration of {drift*100:+.1f}%."
        )
        
        if is_sig:
            explanation_parts.append(
                f"The deterioration is statistically significant, with a 95% bootstrap confidence interval of [{lower_ci:.2f}, {upper_ci:.2f}] "
                f"which completely excludes 1.00."
            )
        else:
            explanation_parts.append(
                f"The cost deterioration is not statistically significant at the 95% confidence level, "
                f"with a bootstrap interval of [{lower_ci:.2f}, {upper_ci:.2f}]."
            )
            
        explanation_parts.append(f"This cohort accounts for {claim_count} claims and contributed {excess_cost:,.2f} in excess cost.")
        
        # Sibling contribution
        port_contrib = worst_leaf.get("portfolio_contribution", 0.0)
        local_contrib = worst_leaf.get("local_contribution", 0.0)
        if port_contrib > 0:
            explanation_parts.append(
                f"This segment explains {port_contrib*100:.1f}% of the total portfolio-level positive excess cost "
                f"(and {local_contrib*100:.1f}% of its local branch excess cost)."
            )
            
        # Outlier / Profile Shifts
        phase_2 = investigation_tree.get("phase_2", {})
        shifts = phase_2.get("profile_shifts", []) if phase_2 else []
        if shifts:
            top_shift = shifts[0]
            attr = top_shift.get("attribute", "")
            val = top_shift.get("value", "")
            hist = top_shift.get("historical_share", 0.0) * 100
            curr = top_shift.get("current_share", 0.0) * 100
            shift_amt = top_shift.get("shift", 0.0) * 100
            
            explanation_parts.append(
                f"Within this cohort, Phase 2 analysis shows a significant shift in claim profile concentration for {attr} ({val}), "
                f"whose cost share changed from {hist:.1f}% historically to {curr:.1f}% in the current period (Shift: {shift_amt:+.1f}%)."
            )
            
        explanation_parts.append(
            "\nThe observed financial excess is concentrated in upper-tail cost bands. "
            "This describes the distribution of excess cost and does not by itself establish the underlying causal event."
        )
            
    elif active_engine == "Combined":
        pattern = business_impact.get("deterioration_pattern", "Unknown")
        excess_cost = business_impact.get("excess_claim_cost", 0.0)
        drift = business_impact.get("drift_percentage", 0.0)
        most_impacted = business_impact.get("most_impacted_portfolio", "Unknown")
        
        inc_eff = business_impact.get("incidence_effect", 0.0)
        sev_eff = business_impact.get("severity_effect", 0.0)
        mix_eff = business_impact.get("mix_effect", 0.0)
        
        explanation_parts.append(f"The Combined experience engine classified the cost drift as **{pattern}**.")
        explanation_parts.append(
            f"The primary contributing demographic segment is **{most_impacted}**, driving a combined O/E ratio of {1.0+drift:.2f} "
            f"and an Observed vs Expected Claim Cost Variance of ₹{excess_cost:,.2f}."
        )
        explanation_parts.append(
            f"Actuarial cost decomposition explains this variance through three factors: "
            f"Incidence Effect: ₹{inc_eff:,.2f}, Severity Effect: ₹{sev_eff:,.2f}, and Mix / Interaction Effect: ₹{mix_eff:,.2f}."
        )
        
    # ---------------------------------------------------------
    # FREQUENCY EXPLANATION NARRATIVE (Original)
    # ---------------------------------------------------------
    else:
        exposure = worst_leaf.get("exposure", 0)
        actual_freq = worst_leaf.get("actual_frequency", 0)
        expected_freq = worst_leaf.get("expected_frequency", 0)
        total_exposure = investigation_tree.get("exposure", 1)
        exposure_pct = (exposure / total_exposure) * 100 if total_exposure > 0 else 0
        
        explanation_parts.append(f"The primary root cause of the portfolio drift was isolated to the **{clean_path}** segment.")
        drift_diff = (actual_freq - expected_freq) * 100
        explanation_parts.append(
            f"This segment experienced an absolute claim frequency drift of {drift_diff:+.2f}% "
            f"(Actual: {actual_freq*100:.2f}% vs Expected: {expected_freq*100:.2f}%). "
        )
        explanation_parts.append(f"Despite representing only {exposure_pct:.1f}% of the total portfolio exposure, this segment is the primary mathematical driver of the anomaly.")
        
        add_claims = business_impact.get("additional_claims", 0)
        if add_claims > 0:
            explanation_parts.append(f"The variance in this segment resulted in approximately {add_claims:,} unexpected claims.")
            
        planner_insights = [note for note in planner_notebook if "Phase 1 isolated" in note.get("observation", "")]
        if planner_insights:
            explanation_parts.append("The deterministic planner selected this path because each feature split iteratively increased the explanatory power of the model.")
            
        phase_2 = investigation_tree.get("phase_2", {})
        shifts = phase_2.get("profile_shifts", []) if phase_2 else []
        if shifts:
            top_shift = shifts[0]
            attr = top_shift.get("attribute", "")
            val = top_shift.get("value", "")
            hist = top_shift.get("historical_share", 0.0) * 100
            curr = top_shift.get("current_share", 0.0) * 100
            explanation_parts.append(
                f"Compared to historical baselines, the most significant shift within this segment was in {attr} ({val}), "
                f"which changed from {hist:.1f}% to {curr:.1f}% of the segment's claim profile."
            )

    return " ".join(explanation_parts)


def generate_explainability_score(investigation_tree: Dict[str, Any], drift_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates an Explainability Score based on statistical evidence, historical agreement, and contribution strength.
    """
    score = 0
    factors = []
    
    # 1. Statistical Strength (Z-Score or Bootstrap CI)
    # Check if bootstrap bounds are present
    if "bootstrap_lower_bound" in drift_metrics:
        # Severity
        lower_bound = drift_metrics.get("bootstrap_lower_bound", 1.0)
        is_significant = drift_metrics.get("is_significant", False)
        
        if is_significant and lower_bound > 1.05:
            score += 30
            factors.append({
                "name": "Statistical Strength", 
                "status": "Strong", 
                "desc": f"Bootstrap Lower CI of {lower_bound:.2f} proves severity drift is highly significant."
            })
        elif is_significant:
            score += 20
            factors.append({
                "name": "Statistical Strength", 
                "status": "Moderate", 
                "desc": f"Bootstrap CI confirms significant severity drift, but lower bound is near 1.0."
            })
        else:
            factors.append({
                "name": "Statistical Strength", 
                "status": "Weak", 
                "desc": "Bootstrap CI includes 1.0, suggesting drift could be random noise."
            })
    else:
        # Frequency
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
            return get_worst_leaf(node["children"][0])
        
        worst = get_worst_leaf(investigation_tree)
        
        # Check if severity or frequency
        if "excess_cost" in worst:
            # Severity
            port_contrib = worst.get("portfolio_contribution", 0.0)
            if port_contrib > 0.40:
                score += 40
                factors.append({"name": "Contribution Strength", "status": "Strong", "desc": f"Primary statistical contributor explains {port_contrib*100:.1f}% of total positive portfolio excess cost."})
            else:
                score += 15
                factors.append({"name": "Contribution Strength", "status": "Weak", "desc": f"Primary statistical contributor only explains {port_contrib*100:.1f}% of total excess cost."})
        else:
            # Frequency
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
