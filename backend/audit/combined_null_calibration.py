"""
Combined Experience Engine — Full Production Pipeline Null Calibration & Alternative Scenario Power.

Runs 500 null simulations through the COMPLETE production pipeline:
- Frequency portfolio gate + segment surveillance
- Severity portfolio gate + segment surveillance
- Combined cost assessment, routing, and pattern classification
- Cross-engine alignment detection

Then runs 50 simulations each for 6 alternative scenarios measuring detection power.
"""

import os
import sys
import numpy as np
import pandas as pd
import yaml
import math
import json
import scipy.stats as stats
from typing import Dict, Any, List, Tuple

# Add backend to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(backend_dir)

from tools.drift_detector import StatisticalAnalyticsEngine as FrequencyEngine
from engines.severity_engine import SeverityAnalyticsEngine
from engines.combined_engine import CombinedAnalyticsEngine
from agent.combined_coordinator import CombinedCoordinator
from audit.frequency_null_calibration import simulate_portfolio_dataset, load_configs


def binomial_ci(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Wilson score interval for binomial proportion."""
    if n == 0:
        return (0.0, 1.0)
    p_hat = k / n
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    denom = 1 + z**2 / n
    centre = (p_hat + z**2 / (2 * n)) / denom
    spread = z * math.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denom
    return (max(0.0, centre - spread), min(1.0, centre + spread))


def rule_of_three_upper(n: int, confidence: float = 0.95) -> float:
    """Upper confidence bound when k=0 events observed in n trials."""
    return 1 - (1 - confidence) ** (1.0 / n) if n > 0 else 1.0


def simulate_combined_dataset(seed: int, active_event_names: List[str] = None,
                               severity_multiplier: float = 1.0,
                               severity_affected_pop: Dict = None,
                               mix_shift: bool = False) -> pd.DataFrame:
    """
    Simulates a fully unified portfolio experience dataset with:
    - Prospective expected severities (claim-independent)
    - Stochastic claim amounts from lognormal distributions
    - Optional severity-only deterioration (multiplier on realized amounts)
    - Optional claimant mix shift mechanism
    """
    df = simulate_portfolio_dataset(seed, active_event_names)
    n_policies = len(df)
    
    # Use a DIFFERENT seed for severity simulation to avoid correlation with frequency
    np.random.seed(seed + 10000)
    
    config, events_config = load_configs()
    
    severity_config = {
        'base_expected_severity': 1200.0,
        'expected_annual_trend': 0.05,
        'category_volatility': {
            'Cancer': 0.50, 'Cardiac': 0.45, 'Respiratory': 0.35,
            'Orthopedic': 0.40, 'General': 0.30
        },
        'severity_relativities': {
            'product': {'Standard Care': 1.0, 'Senior Care Gold': 1.4, 'Family Plus': 1.1},
            'age': {'18-35': 0.8, '36-59': 1.0, '60+': 1.5},
            'region': {'North': 1.0, 'South': 0.95, 'East': 1.1, 'West': 1.05},
            'claim_category': {'Cancer': 2.0, 'Cardiac': 1.6, 'Respiratory': 1.0, 'Orthopedic': 1.2, 'General': 0.8},
            'hospital_type': {'Public': 0.8, 'Private': 1.3, 'Specialist': 1.5}
        }
    }
    
    base_sev = severity_config['base_expected_severity']
    rel = severity_config['severity_relativities']
    
    # Pre-calculate demographic factors
    prod_rel = np.array([rel['product'].get(p, 1.0) for p in df['Product']])
    age_rel = np.array([rel['age'].get(a, 1.0) for a in df['Age_Group']])
    reg_rel = np.array([rel['region'].get(r, 1.0) for r in df['Region']])
    
    expected_annual_trend = severity_config.get('expected_annual_trend', 0.05)
    expected_monthly_rate = (1.0 + expected_annual_trend) ** (1.0 / 12.0) - 1.0
    t_months = (df['Year'].values - 2022) * 12 + (df['Month'].values - 1)
    trend_rel = (1.0 + expected_monthly_rate) ** t_months
    
    base_factor = base_sev * prod_rel * age_rel * reg_rel * trend_rel
    
    # Prospective Expected Severity multiplier
    diseases = ["Cancer", "Cardiac", "Respiratory", "Orthopedic", "General"]
    winter_mask = np.isin(df['Month'].values, [12, 1, 2])
    
    exp_mult_non_winter = 0.0
    for d in diseases:
        p_d = 1.0 / 5.0
        r_cat = rel['claim_category'].get(d, 1.0)
        h_probs = np.array([0.2, 0.6, 0.2]) if d in ["Cancer", "Cardiac"] else np.array([0.5, 0.3, 0.2])
        r_hosp = np.array([rel['hospital_type'].get(h, 1.0) for h in ["Public", "Private", "Specialist"]])
        exp_mult_non_winter += p_d * r_cat * (h_probs * r_hosp).sum()
        
    exp_mult_winter = 0.0
    for d in diseases:
        p_d = 3.0 / 7.0 if d == "Respiratory" else 1.0 / 7.0
        r_cat = rel['claim_category'].get(d, 1.0)
        h_probs = np.array([0.2, 0.6, 0.2]) if d in ["Cancer", "Cardiac"] else np.array([0.5, 0.3, 0.2])
        r_hosp = np.array([rel['hospital_type'].get(h, 1.0) for h in ["Public", "Private", "Specialist"]])
        exp_mult_winter += p_d * r_cat * (h_probs * r_hosp).sum()
        
    prospective_multipliers = np.where(winter_mask, exp_mult_winter, exp_mult_non_winter)
    prospective_exp_severities = np.round(base_factor * prospective_multipliers, 2)
    
    # Simulate post-claim attributes for Claim == 1 rows
    actual_claims = df['Claim'].values
    actual_amounts = np.zeros(n_policies)
    claim_categories = np.empty(n_policies, dtype=object)
    hospital_types = np.empty(n_policies, dtype=object)
    
    claim_indices = np.where(actual_claims == 1)[0]
    
    if len(claim_indices) > 0:
        for real_idx in claim_indices:
            month = df['Month'].values[real_idx]
            weights = np.ones(len(diseases))
            if month in [12, 1, 2]:
                weights[2] = 3  # Respiratory in winter
            probs = weights / weights.sum()
            claim_cat = np.random.choice(diseases, p=probs)
            claim_categories[real_idx] = claim_cat
            
            if claim_cat in ["Cancer", "Cardiac"]:
                h_prob = [0.2, 0.6, 0.2]
            else:
                h_prob = [0.5, 0.3, 0.2]
            hosp_type = np.random.choice(["Public", "Private", "Specialist"], p=h_prob)
            hospital_types[real_idx] = hosp_type
            
            r_cat = rel['claim_category'].get(claim_cat, 1.0)
            r_hosp = rel['hospital_type'].get(hosp_type, 1.0)
            cond_exp_sev = base_factor[real_idx] * r_cat * r_hosp
            
            sigma = severity_config['category_volatility'].get(claim_cat, 0.40)
            mu = math.log(cond_exp_sev) - (sigma ** 2) / 2.0
            actual_amount = np.random.lognormal(mu, sigma)
            
            # Apply severity multiplier (for Scenario B)
            apply_mult = True
            if severity_affected_pop and severity_multiplier != 1.0:
                apply_mult = True
                for k, v in severity_affected_pop.items():
                    if k == 'region' and df['Region'].values[real_idx] != v:
                        apply_mult = False
                    elif k == 'age_group' and df['Age_Group'].values[real_idx] != v:
                        apply_mult = False
                    elif k == 'product' and df['Product'].values[real_idx] != v:
                        apply_mult = False
                if apply_mult and df['Year'].values[real_idx] == 2024:
                    actual_amount *= severity_multiplier
            elif severity_multiplier != 1.0 and severity_affected_pop is None:
                if df['Year'].values[real_idx] == 2024:
                    actual_amount *= severity_multiplier
            
            actual_amounts[real_idx] = np.round(actual_amount, 2)
            
    df["Expected_Severity"] = prospective_exp_severities
    df["Actual_Claim_Amount"] = actual_amounts
    df["Claim_Category"] = claim_categories
    df["Hospital_Type"] = hospital_types
    return df


def simulate_mix_shift_dataset(seed: int) -> pd.DataFrame:
    """
    SCENARIO E: Claimant Mix Shift Mechanism.
    
    High-severity policyholders (Senior Care Gold, Age 60+) claim at elevated rates.
    Low-severity policyholders (Standard Care, Age 18-35) claim at reduced rates.
    
    Overall portfolio frequency is approximately stable, but the realized claimant pool
    shifts toward policyholders with materially higher prospective Expected_Severity.
    This generates a genuine mathematical ΔN·ΔS interaction term.
    """
    np.random.seed(seed)
    config, events_config = load_configs()
    n_policies = 180000
    
    prod_choices = ["Standard Care", "Senior Care Gold", "Family Plus"]
    prods = np.random.choice(prod_choices, size=n_policies, p=[0.6, 0.2, 0.2])
    
    age_groups = np.empty(n_policies, dtype=object)
    scg_mask = (prods == "Senior Care Gold")
    fp_mask = (prods == "Family Plus")
    std_mask = (prods == "Standard Care")
    
    age_groups[scg_mask] = np.random.choice(["18-35", "36-59", "60+"], size=scg_mask.sum(), p=[0.05, 0.15, 0.80])
    age_groups[fp_mask] = np.random.choice(["18-35", "36-59", "60+"], size=fp_mask.sum(), p=[0.20, 0.70, 0.10])
    age_groups[std_mask] = np.random.choice(["18-35", "36-59", "60+"], size=std_mask.sum(), p=[0.40, 0.40, 0.20])
    
    regions = np.random.choice(["North", "South", "East", "West"], size=n_policies, p=[0.25, 0.25, 0.25, 0.25])
    genders = np.random.choice(["M", "F"], size=n_policies, p=[0.5, 0.5])
    channels = np.random.choice(["Broker", "Direct", "Bancassurance"], size=n_policies, p=[0.5, 0.3, 0.2])
    plan_types = np.random.choice(["Basic", "Comprehensive"], size=n_policies, p=[0.4, 0.6])
    
    months = np.tile(np.repeat(np.arange(1, 13), 5000), 3)
    years = np.repeat([2022, 2023, 2024], 60000)
    
    # Calculate baseline logit (expected frequencies)
    logit = np.full(n_policies, -2.94)
    prod_eff = np.zeros(n_policies)
    prod_eff[prods == "Senior Care Gold"] = 0.8
    prod_eff[prods == "Family Plus"] = 0.2
    logit += prod_eff
    
    age_eff = np.zeros(n_policies)
    age_eff[age_groups == "18-35"] = -0.2
    age_eff[age_groups == "60+"] = 0.6
    logit += age_eff
    
    region_eff = np.zeros(n_policies)
    region_eff[regions == "North"] = 0.1
    region_eff[regions == "South"] = -0.1
    region_eff[regions == "West"] = -0.05
    logit += region_eff
    
    winter_mask = np.isin(months, [12, 1, 2])
    logit[winter_mask] += 0.15
    
    expected_freqs = 1.0 / (1.0 + np.exp(-logit))
    
    # CLAIMANT MIX SHIFT for 2024:
    # High-severity policyholders (SCG + 60+) get +0.3 logit boost
    # Low-severity policyholders (Standard Care + 18-35) get -0.3 logit reduction
    # This shifts the claimant pool toward expensive policyholders
    actual_logit = logit.copy()
    year_2024_mask = (years == 2024)
    high_sev_mask = year_2024_mask & (prods == "Senior Care Gold") & (age_groups == "60+")
    low_sev_mask = year_2024_mask & (prods == "Standard Care") & (age_groups == "18-35")
    
    actual_logit[high_sev_mask] += 0.3
    actual_logit[low_sev_mask] -= 0.3
    
    actual_probabilities = 1.0 / (1.0 + np.exp(-actual_logit))
    claims = (np.random.random(n_policies) < actual_probabilities).astype(int)
    
    df = pd.DataFrame({
        "Product": prods, "Age_Group": age_groups, "Region": regions,
        "Gender": genders, "Distribution_Channel": channels, "Plan_Type": plan_types,
        "Exposure": np.ones(n_policies), "Claim": claims,
        "Expected_Frequency": expected_freqs, "Year": years, "Month": months
    })
    
    # Now add severity using the same mechanism as simulate_combined_dataset
    np.random.seed(seed + 20000)
    severity_config = {
        'base_expected_severity': 1200.0,
        'expected_annual_trend': 0.05,
        'category_volatility': {
            'Cancer': 0.50, 'Cardiac': 0.45, 'Respiratory': 0.35,
            'Orthopedic': 0.40, 'General': 0.30
        },
        'severity_relativities': {
            'product': {'Standard Care': 1.0, 'Senior Care Gold': 1.4, 'Family Plus': 1.1},
            'age': {'18-35': 0.8, '36-59': 1.0, '60+': 1.5},
            'region': {'North': 1.0, 'South': 0.95, 'East': 1.1, 'West': 1.05},
            'claim_category': {'Cancer': 2.0, 'Cardiac': 1.6, 'Respiratory': 1.0, 'Orthopedic': 1.2, 'General': 0.8},
            'hospital_type': {'Public': 0.8, 'Private': 1.3, 'Specialist': 1.5}
        }
    }
    
    base_sev = severity_config['base_expected_severity']
    rel = severity_config['severity_relativities']
    prod_rel = np.array([rel['product'].get(p, 1.0) for p in df['Product']])
    age_rel = np.array([rel['age'].get(a, 1.0) for a in df['Age_Group']])
    reg_rel = np.array([rel['region'].get(r, 1.0) for r in df['Region']])
    expected_monthly_rate = (1.0 + 0.05) ** (1.0 / 12.0) - 1.0
    t_months = (df['Year'].values - 2022) * 12 + (df['Month'].values - 1)
    trend_rel = (1.0 + expected_monthly_rate) ** t_months
    base_factor = base_sev * prod_rel * age_rel * reg_rel * trend_rel
    
    diseases = ["Cancer", "Cardiac", "Respiratory", "Orthopedic", "General"]
    winter_m = np.isin(df['Month'].values, [12, 1, 2])
    
    exp_mult_nw = sum(1.0/5.0 * rel['claim_category'].get(d, 1.0) * 
        (np.array([0.2,0.6,0.2] if d in ["Cancer","Cardiac"] else [0.5,0.3,0.2]) * 
         np.array([rel['hospital_type'][h] for h in ["Public","Private","Specialist"]])).sum()
        for d in diseases)
    exp_mult_w = sum((3.0/7.0 if d=="Respiratory" else 1.0/7.0) * rel['claim_category'].get(d, 1.0) *
        (np.array([0.2,0.6,0.2] if d in ["Cancer","Cardiac"] else [0.5,0.3,0.2]) *
         np.array([rel['hospital_type'][h] for h in ["Public","Private","Specialist"]])).sum()
        for d in diseases)
    
    prosp_mult = np.where(winter_m, exp_mult_w, exp_mult_nw)
    prosp_sev = np.round(base_factor * prosp_mult, 2)
    
    actual_amounts = np.zeros(n_policies)
    claim_cats = np.empty(n_policies, dtype=object)
    hosp_types = np.empty(n_policies, dtype=object)
    
    claim_idxs = np.where(claims == 1)[0]
    for idx in claim_idxs:
        month = months[idx]
        w = np.ones(5)
        if month in [12, 1, 2]:
            w[2] = 3
        p = w / w.sum()
        cc = np.random.choice(diseases, p=p)
        claim_cats[idx] = cc
        hp = [0.2, 0.6, 0.2] if cc in ["Cancer", "Cardiac"] else [0.5, 0.3, 0.2]
        ht = np.random.choice(["Public", "Private", "Specialist"], p=hp)
        hosp_types[idx] = ht
        rc = rel['claim_category'].get(cc, 1.0)
        rh = rel['hospital_type'].get(ht, 1.0)
        ces = base_factor[idx] * rc * rh
        sig = severity_config['category_volatility'].get(cc, 0.40)
        mu = math.log(ces) - sig**2 / 2.0
        actual_amounts[idx] = np.round(np.random.lognormal(mu, sig), 2)
    
    df["Expected_Severity"] = prosp_sev
    df["Actual_Claim_Amount"] = actual_amounts
    df["Claim_Category"] = claim_cats
    df["Hospital_Type"] = hosp_types
    return df


def run_full_pipeline(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run the COMPLETE production pipeline on a dataset and return all trigger/classification state.
    """
    latest_year = df['Year'].max()
    df_latest = df[df['Year'] == latest_year]
    
    # 1. Frequency Engine
    freq_engine = FrequencyEngine(
        relative_drift_threshold=0.05, min_exposure=500,
        z_score_threshold=1.645, min_expected_claims=10, fdr_target=0.05
    )
    freq_metrics = freq_engine.calculate_metrics(df_latest)
    freq_surveillance = freq_engine.run_segment_surveillance(df_latest)
    
    freq_portfolio_trigger = freq_metrics.get("requires_investigation", False)
    freq_segment_trigger = freq_surveillance.get("triggered", False)
    freq_triggered = freq_portfolio_trigger or freq_segment_trigger
    
    # 2. Severity Engine
    sev_engine = SeverityAnalyticsEngine(materiality_threshold=0.05, minimum_claims=30, fdr_target=0.05)
    df_claims = df[df['Claim'] == 1]
    df_claims_latest = df_claims[df_claims['Year'] == latest_year]
    
    sev_metrics = sev_engine.calculate_metrics(df_claims_latest)
    sev_surveillance = sev_engine.run_segment_surveillance(df_claims_latest)
    
    sev_portfolio_trigger = sev_metrics.get("is_significant", False) if not sev_metrics.get("error") else False
    sev_segment_trigger = sev_surveillance.get("triggered", False)
    sev_triggered = sev_portfolio_trigger or sev_segment_trigger
    
    # 3. Combined Engine
    comb_engine = CombinedAnalyticsEngine()
    comb_metrics = comb_engine.calculate_metrics(df_latest)
    pattern = comb_engine.classify_pattern(comb_metrics, freq_triggered, sev_triggered)
    comb_metrics["deterioration_pattern"] = pattern
    
    # 4. Investigation trigger (any path triggered)
    any_investigation = freq_triggered or sev_triggered or (comb_metrics["excess_cost"] > 0 and pattern != "No Material Combined Deterioration")
    
    # 5. Cross-engine alignment (via evidence generation)
    # Build minimal state for evidence generation
    mock_state = {
        "freq_surveillance": freq_surveillance,
        "sev_surveillance": sev_surveillance,
        "comb_segments": comb_engine.calculate_segment_metrics(df_latest, comb_metrics.get("positive_excess_cost", 0.0))
    }
    coordinator = CombinedCoordinator()
    evidence = coordinator.generate_normalized_evidence(mock_state)
    has_alignment = any(e.get("cross_engine_alignment", False) for e in evidence)
    
    # Identify triggered segments
    freq_trigger_seg = None
    sev_trigger_seg = None
    if freq_segment_trigger:
        freq_trigger_seg = (freq_surveillance.get("trigger_dimension"), freq_surveillance.get("trigger_segment"))
    if sev_segment_trigger:
        sev_trigger_seg = (sev_surveillance.get("trigger_dimension"), sev_surveillance.get("trigger_segment"))
    
    return {
        "freq_portfolio_trigger": freq_portfolio_trigger,
        "freq_segment_trigger": freq_segment_trigger,
        "freq_triggered": freq_triggered,
        "sev_portfolio_trigger": sev_portfolio_trigger,
        "sev_segment_trigger": sev_segment_trigger,
        "sev_triggered": sev_triggered,
        "any_investigation": any_investigation,
        "pattern": pattern,
        "combined_oe": comb_metrics["combined_oe"],
        "excess_cost": comb_metrics["excess_cost"],
        "incidence_effect": comb_metrics["incidence_effect"],
        "severity_effect": comb_metrics["severity_effect"],
        "mix_effect": comb_metrics["mix_effect"],
        "has_alignment": has_alignment,
        "freq_trigger_seg": freq_trigger_seg,
        "sev_trigger_seg": sev_trigger_seg
    }


def run_null_calibration(num_simulations: int = 500) -> Dict[str, Any]:
    """Run 500 null simulations through the full production pipeline."""
    print(f"=== COMBINED NULL CALIBRATION: {num_simulations} simulations ===\n")
    
    results = []
    for seed in range(num_simulations):
        if (seed + 1) % 50 == 0:
            print(f"  Null simulation {seed + 1}/{num_simulations}...")
        df = simulate_combined_dataset(seed)
        r = run_full_pipeline(df)
        results.append(r)
    
    n = num_simulations
    
    # 1. CFIR: any investigation triggered
    cfir_k = sum(1 for r in results if r["any_investigation"])
    cfir = cfir_k / n
    cfir_ci = binomial_ci(cfir_k, n)
    
    # 2. CPFTR: freq portfolio OR sev portfolio triggers
    cpftr_k = sum(1 for r in results if r["freq_portfolio_trigger"] or r["sev_portfolio_trigger"])
    cpftr = cpftr_k / n
    cpftr_ci = binomial_ci(cpftr_k, n)
    
    # 3. Frequency local FTR
    freq_ftr_k = sum(1 for r in results if r["freq_triggered"])
    freq_ftr = freq_ftr_k / n
    freq_ftr_ci = binomial_ci(freq_ftr_k, n)
    
    # 4. Severity local FTR
    sev_ftr_k = sum(1 for r in results if r["sev_triggered"])
    sev_ftr = sev_ftr_k / n
    sev_ftr_ci = binomial_ci(sev_ftr_k, n)
    
    # 5. Mix/Interaction false classification rate
    mix_false_k = sum(1 for r in results if r["pattern"] == "Mix / Interaction Deterioration")
    mix_false = mix_false_k / n
    mix_false_ci = binomial_ci(mix_false_k, n)
    
    # 6. Cross-engine false alignment rate
    align_false_k = sum(1 for r in results if r["has_alignment"])
    align_false = align_false_k / n
    align_false_ci = binomial_ci(align_false_k, n)
    
    # 7. No-material pattern accuracy
    no_mat_k = sum(1 for r in results if r["pattern"] == "No Material Combined Deterioration")
    no_mat_acc = no_mat_k / n
    no_mat_ci = binomial_ci(no_mat_k, n)
    
    # 8-10. Distributions
    combined_oes = [r["combined_oe"] for r in results]
    excess_costs = [r["excess_cost"] for r in results]
    inc_effects = [r["incidence_effect"] for r in results]
    sev_effects = [r["severity_effect"] for r in results]
    mix_effects = [r["mix_effect"] for r in results]
    
    # Rule-of-three for zero-event rates
    r3_bounds = {}
    for name, k_val in [("CPFTR", cpftr_k), ("Alignment", align_false_k), ("Mix_False", mix_false_k)]:
        if k_val == 0:
            r3_bounds[name] = rule_of_three_upper(n)
    
    null_summary = {
        "num_simulations": n,
        "CFIR": {"k": cfir_k, "rate": cfir, "ci_95": cfir_ci},
        "CPFTR": {"k": cpftr_k, "rate": cpftr, "ci_95": cpftr_ci},
        "Freq_FTR": {"k": freq_ftr_k, "rate": freq_ftr, "ci_95": freq_ftr_ci},
        "Sev_FTR": {"k": sev_ftr_k, "rate": sev_ftr, "ci_95": sev_ftr_ci},
        "Mix_False_Classification": {"k": mix_false_k, "rate": mix_false, "ci_95": mix_false_ci},
        "Cross_Engine_False_Alignment": {"k": align_false_k, "rate": align_false, "ci_95": align_false_ci},
        "No_Material_Pattern_Accuracy": {"k": no_mat_k, "rate": no_mat_acc, "ci_95": no_mat_ci},
        "rule_of_three_upper_bounds": r3_bounds,
        "Combined_OE_Distribution": {
            "mean": float(np.mean(combined_oes)), "std": float(np.std(combined_oes)),
            "min": float(np.min(combined_oes)), "max": float(np.max(combined_oes)),
            "p5": float(np.percentile(combined_oes, 5)), "p50": float(np.percentile(combined_oes, 50)),
            "p95": float(np.percentile(combined_oes, 95))
        },
        "Excess_Cost_Distribution": {
            "mean": float(np.mean(excess_costs)), "std": float(np.std(excess_costs)),
            "min": float(np.min(excess_costs)), "max": float(np.max(excess_costs))
        },
        "Decomposition_Distributions": {
            "Incidence_Effect": {"mean": float(np.mean(inc_effects)), "std": float(np.std(inc_effects))},
            "Severity_Effect": {"mean": float(np.mean(sev_effects)), "std": float(np.std(sev_effects))},
            "Mix_Effect": {"mean": float(np.mean(mix_effects)), "std": float(np.std(mix_effects))}
        }
    }
    
    print("\n--- NULL CALIBRATION RESULTS ---")
    print(f"CFIR:                         {cfir_k}/{n} = {cfir*100:.1f}%  95%CI [{cfir_ci[0]*100:.1f}%, {cfir_ci[1]*100:.1f}%]")
    print(f"CPFTR:                        {cpftr_k}/{n} = {cpftr*100:.1f}%  95%CI [{cpftr_ci[0]*100:.1f}%, {cpftr_ci[1]*100:.1f}%]")
    print(f"Frequency Local FTR:          {freq_ftr_k}/{n} = {freq_ftr*100:.1f}%  95%CI [{freq_ftr_ci[0]*100:.1f}%, {freq_ftr_ci[1]*100:.1f}%]")
    print(f"Severity Local FTR:           {sev_ftr_k}/{n} = {sev_ftr*100:.1f}%  95%CI [{sev_ftr_ci[0]*100:.1f}%, {sev_ftr_ci[1]*100:.1f}%]")
    print(f"Mix False Classification:     {mix_false_k}/{n} = {mix_false*100:.1f}%  95%CI [{mix_false_ci[0]*100:.1f}%, {mix_false_ci[1]*100:.1f}%]")
    print(f"Cross-Engine False Alignment: {align_false_k}/{n} = {align_false*100:.1f}%  95%CI [{align_false_ci[0]*100:.1f}%, {align_false_ci[1]*100:.1f}%]")
    print(f"No-Material Pattern Accuracy: {no_mat_k}/{n} = {no_mat_acc*100:.1f}%  95%CI [{no_mat_ci[0]*100:.1f}%, {no_mat_ci[1]*100:.1f}%]")
    for name, bound in r3_bounds.items():
        print(f"  Rule-of-three upper bound ({name}): {bound*100:.2f}%")
    print(f"\nCombined O/E: mean={np.mean(combined_oes):.4f} std={np.std(combined_oes):.4f} [P5={np.percentile(combined_oes,5):.4f}, P50={np.percentile(combined_oes,50):.4f}, P95={np.percentile(combined_oes,95):.4f}]")
    print(f"Excess Cost: mean=₹{np.mean(excess_costs):+,.0f} std=₹{np.std(excess_costs):,.0f}")
    
    return null_summary


def run_scenario_power(num_per_scenario: int = 50) -> Dict[str, Any]:
    """Run 50 simulations each for 6 alternative scenarios."""
    print(f"\n=== ALTERNATIVE SCENARIO POWER: {num_per_scenario} runs each ===\n")
    
    scenarios = {}
    
    # SCENARIO A: Frequency-Only Deterioration (Northern Oncology Growth)
    print("Scenario A: Frequency-Only Deterioration...")
    scen_a = []
    for seed in range(num_per_scenario):
        df = simulate_combined_dataset(seed, active_event_names=["Northern Oncology Growth"])
        r = run_full_pipeline(df)
        scen_a.append(r)
    
    a_power = sum(1 for r in scen_a if r["any_investigation"]) / num_per_scenario
    a_pattern_acc = sum(1 for r in scen_a if r["pattern"] in ["Frequency-Led Deterioration", "Frequency and Severity Deterioration"]) / num_per_scenario
    a_seg_recovery = sum(1 for r in scen_a if r["freq_trigger_seg"] and r["freq_trigger_seg"][0] == "Region" and r["freq_trigger_seg"][1] == "North") / num_per_scenario
    scenarios["A_Frequency_Only"] = {
        "power": a_power, "pattern_accuracy": a_pattern_acc, "segment_recovery": a_seg_recovery,
        "ci_power": binomial_ci(int(a_power * num_per_scenario), num_per_scenario)
    }
    print(f"  Power: {a_power*100:.0f}%  Pattern Acc: {a_pattern_acc*100:.0f}%  Segment Recovery: {a_seg_recovery*100:.0f}%")
    
    # SCENARIO B: Severity-Only Deterioration (15% severity inflation, no frequency change)
    print("Scenario B: Severity-Only Deterioration...")
    scen_b = []
    for seed in range(num_per_scenario):
        df = simulate_combined_dataset(seed, severity_multiplier=1.15)
        r = run_full_pipeline(df)
        scen_b.append(r)
    
    b_power = sum(1 for r in scen_b if r["any_investigation"]) / num_per_scenario
    b_pattern_acc = sum(1 for r in scen_b if r["pattern"] in ["Severity-Led Deterioration", "Frequency and Severity Deterioration"]) / num_per_scenario
    scenarios["B_Severity_Only"] = {
        "power": b_power, "pattern_accuracy": b_pattern_acc,
        "ci_power": binomial_ci(int(b_power * num_per_scenario), num_per_scenario)
    }
    print(f"  Power: {b_power*100:.0f}%  Pattern Acc: {b_pattern_acc*100:.0f}%")
    
    # SCENARIO C: Aligned Freq+Sev (Same Segment - Region:North)
    print("Scenario C: Aligned Frequency + Severity (Region:North)...")
    scen_c = []
    for seed in range(num_per_scenario):
        df = simulate_combined_dataset(seed,
            active_event_names=["Northern Oncology Growth"],
            severity_multiplier=1.15,
            severity_affected_pop={"region": "North"})
        r = run_full_pipeline(df)
        scen_c.append(r)
    
    c_power = sum(1 for r in scen_c if r["any_investigation"]) / num_per_scenario
    c_pattern_acc = sum(1 for r in scen_c if r["pattern"] == "Frequency and Severity Deterioration") / num_per_scenario
    c_alignment_recall = sum(1 for r in scen_c if r["has_alignment"]) / num_per_scenario
    c_seg_recovery = sum(1 for r in scen_c if r["freq_trigger_seg"] and r["freq_trigger_seg"][1] == "North") / num_per_scenario
    scenarios["C_Aligned_Same_Segment"] = {
        "power": c_power, "pattern_accuracy": c_pattern_acc,
        "alignment_recall": c_alignment_recall, "segment_recovery": c_seg_recovery,
        "ci_power": binomial_ci(int(c_power * num_per_scenario), num_per_scenario)
    }
    print(f"  Power: {c_power*100:.0f}%  Pattern Acc: {c_pattern_acc*100:.0f}%  Alignment Recall: {c_alignment_recall*100:.0f}%")
    
    # SCENARIO D: Different-Segment Freq + Sev
    print("Scenario D: Different-Segment Frequency + Severity...")
    scen_d = []
    for seed in range(num_per_scenario):
        df = simulate_combined_dataset(seed,
            active_event_names=["Northern Oncology Growth"],
            severity_multiplier=1.20,
            severity_affected_pop={"age_group": "60+"})
        r = run_full_pipeline(df)
        scen_d.append(r)
    
    d_power = sum(1 for r in scen_d if r["any_investigation"]) / num_per_scenario
    d_false_alignment = sum(1 for r in scen_d if r["has_alignment"]) / num_per_scenario
    d_freq_recovery = sum(1 for r in scen_d if r["freq_trigger_seg"] and r["freq_trigger_seg"][1] == "North") / num_per_scenario
    d_sev_recovery = sum(1 for r in scen_d if r["sev_trigger_seg"] and r["sev_trigger_seg"][1] == "60+") / num_per_scenario
    scenarios["D_Different_Segment"] = {
        "power": d_power, "false_alignment_rate": d_false_alignment,
        "freq_segment_recovery": d_freq_recovery, "sev_segment_recovery": d_sev_recovery,
        "ci_power": binomial_ci(int(d_power * num_per_scenario), num_per_scenario)
    }
    print(f"  Power: {d_power*100:.0f}%  False Alignment: {d_false_alignment*100:.0f}%  Freq Recovery: {d_freq_recovery*100:.0f}%  Sev Recovery: {d_sev_recovery*100:.0f}%")
    
    # SCENARIO E: Mix / Interaction Deterioration (Claimant Mix Shift)
    print("Scenario E: Mix / Interaction Deterioration (Claimant Mix Shift)...")
    scen_e = []
    scen_e_details = []
    for seed in range(num_per_scenario):
        df = simulate_mix_shift_dataset(seed)
        r = run_full_pipeline(df)
        scen_e.append(r)
        
        # Collect detailed decomposition for first run
        if seed == 0:
            df_latest = df[df['Year'] == 2024]
            eng = CombinedAnalyticsEngine()
            m = eng.calculate_metrics(df_latest)
            scen_e_details.append(m)
    
    e_power = sum(1 for r in scen_e if r["any_investigation"]) / num_per_scenario
    e_mix_patterns = sum(1 for r in scen_e if "Mix" in r["pattern"] or "Interaction" in r["pattern"]) / num_per_scenario
    e_mix_material = sum(1 for r in scen_e if abs(r["mix_effect"]) > 1000) / num_per_scenario
    scenarios["E_Mix_Interaction"] = {
        "power": e_power, "mix_pattern_rate": e_mix_patterns,
        "mix_material_rate": e_mix_material,
        "ci_power": binomial_ci(int(e_power * num_per_scenario), num_per_scenario),
        "example_decomposition": scen_e_details[0] if scen_e_details else None
    }
    print(f"  Power: {e_power*100:.0f}%  Mix Pattern: {e_mix_patterns*100:.0f}%  Material Mix Effect: {e_mix_material*100:.0f}%")
    
    # SCENARIO F: Low-Credibility Local Deterioration
    # Inject deterioration into a tiny segment that won't meet credibility thresholds
    print("Scenario F: Low-Credibility Local Deterioration...")
    scen_f = []
    for seed in range(num_per_scenario):
        # Use a normal null dataset but check if the engine properly suppresses small segments
        df = simulate_combined_dataset(seed)
        # Inject a huge but very localized deterioration (only 50 policies)
        df_latest = df[df['Year'] == 2024].copy()
        small_seg = df_latest.head(50).copy()
        small_seg['Claim'] = 1
        small_seg['Actual_Claim_Amount'] = small_seg['Expected_Severity'] * 5.0  # 5x severity
        df_mod = pd.concat([df_latest.iloc[50:], small_seg], ignore_index=True)
        df_mod_full = pd.concat([df[df['Year'] != 2024], df_mod])
        
        r = run_full_pipeline(df_mod_full)
        scen_f.append(r)
    
    f_suppression = sum(1 for r in scen_f if not r["any_investigation"]) / num_per_scenario
    f_false_escalation = sum(1 for r in scen_f if r["any_investigation"]) / num_per_scenario
    scenarios["F_Low_Credibility"] = {
        "suppression_rate": f_suppression, "false_escalation_rate": f_false_escalation,
        "ci_suppression": binomial_ci(int(f_suppression * num_per_scenario), num_per_scenario)
    }
    print(f"  Suppression Rate: {f_suppression*100:.0f}%  False Escalation: {f_false_escalation*100:.0f}%")
    
    return scenarios


def run_combined_calibration():
    """Main entry point: runs null calibration + scenario power + saves results."""
    
    # 1. Null calibration
    null_results = run_null_calibration(500)
    
    # 2. Scenario power
    scenario_results = run_scenario_power(50)
    
    # Save combined results
    os.makedirs(os.path.join(backend_dir, "scratch"), exist_ok=True)
    out_path = os.path.join(backend_dir, "scratch", "combined_calibration_summary.json")
    
    output = {
        "null_calibration": null_results,
        "scenario_power": {}
    }
    
    for k, v in scenario_results.items():
        # Convert tuples to lists for JSON serialization
        serializable = {}
        for k2, v2 in v.items():
            if isinstance(v2, tuple):
                serializable[k2] = list(v2)
            elif isinstance(v2, dict):
                serializable[k2] = {k3: (list(v3) if isinstance(v3, tuple) else v3) for k3, v3 in v2.items()}
            else:
                serializable[k2] = v2
        output["scenario_power"][k] = serializable
    
    # Convert null calibration tuples too
    for key in output["null_calibration"]:
        if isinstance(output["null_calibration"][key], dict):
            for k2 in output["null_calibration"][key]:
                if isinstance(output["null_calibration"][key][k2], tuple):
                    output["null_calibration"][key][k2] = list(output["null_calibration"][key][k2])
    
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
        
    print(f"\nSaved combined calibration results to: {out_path}")
    return output


if __name__ == "__main__":
    run_combined_calibration()
