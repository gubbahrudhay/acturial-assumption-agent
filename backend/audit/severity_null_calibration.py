import os
import sys
import numpy as np
import pandas as pd
import yaml
import math
import scipy.stats as stats
import concurrent.futures
from typing import Dict, Any, List, Tuple

# Add backend to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(backend_dir)

from engines.severity_engine import SeverityAnalyticsEngine

# Global dictionary to cache YAML configurations in child processes
_config_cache = {}

def load_configs():
    if not _config_cache:
        config_path = os.path.join(backend_dir, 'data', 'generation_config.yaml')
        events_path = os.path.join(backend_dir, 'data', 'business_events.yaml')
        severity_config_path = os.path.join(backend_dir, 'config', 'severity_model.yaml')
        
        with open(config_path, 'r') as file:
            _config_cache["config"] = yaml.safe_load(file)
        with open(events_path, 'r') as file:
            _config_cache["events_config"] = yaml.safe_load(file)
        with open(severity_config_path, 'r') as file:
            _config_cache["severity_config"] = yaml.safe_load(file)
    return _config_cache["config"], _config_cache["events_config"], _config_cache["severity_config"]

def run_single_simulation(args: Tuple[int, List[str], str]) -> Dict[str, Any]:
    """Highly optimized vectorized simulation of the portfolio claims and surveillance gate."""
    seed, active_events, method = args
    np.random.seed(seed)
    
    n_policies = 180000
    
    # 1. Product weights: Standard Care 0.6, Senior Care Gold 0.2, Family Plus 0.2
    prod_choices = ["Standard Care", "Senior Care Gold", "Family Plus"]
    prods = np.random.choice(prod_choices, size=n_policies, p=[0.6, 0.2, 0.2])
    
    # 2. Age group based on product
    age_groups = np.empty(n_policies, dtype=object)
    scg_mask = (prods == "Senior Care Gold")
    fp_mask = (prods == "Family Plus")
    std_mask = (prods == "Standard Care")
    
    age_groups[scg_mask] = np.random.choice(["18-35", "36-59", "60+"], size=scg_mask.sum(), p=[0.05, 0.15, 0.80])
    age_groups[fp_mask] = np.random.choice(["18-35", "36-59", "60+"], size=fp_mask.sum(), p=[0.20, 0.70, 0.10])
    age_groups[std_mask] = np.random.choice(["18-35", "36-59", "60+"], size=std_mask.sum(), p=[0.40, 0.40, 0.20])
    
    # 3. Region: North 0.25, South 0.25, East 0.25, West 0.25
    regions = np.random.choice(["North", "South", "East", "West"], size=n_policies, p=[0.25, 0.25, 0.25, 0.25])
    
    # 4. Gender: M 0.5, F 0.5
    genders = np.random.choice(["M", "F"], size=n_policies, p=[0.5, 0.5])
    
    # 5. Distribution Channel: Broker 0.5, Direct 0.3, Bancassurance 0.2
    channels = np.random.choice(["Broker", "Direct", "Bancassurance"], size=n_policies, p=[0.5, 0.3, 0.2])
    
    # 6. Year and Month (assign uniformly across 36 months, 5000 per month)
    months = np.tile(np.repeat(np.arange(1, 13), 5000), 3)
    years = np.repeat([2022, 2023, 2024], 60000)
    
    # 7. Calculate claim probability in vectorized form
    logit = np.full(n_policies, -2.94)
    
    # Product effect: Standard Care 0.0, Senior Care Gold 0.8, Family Plus 0.2
    prod_eff = np.zeros(n_policies)
    prod_eff[prods == "Senior Care Gold"] = 0.8
    prod_eff[prods == "Family Plus"] = 0.2
    logit += prod_eff
    
    # Age effect: 18-35 -0.2, 36-59 0.0, 60+ 0.6
    age_eff = np.zeros(n_policies)
    age_eff[age_groups == "18-35"] = -0.2
    age_eff[age_groups == "60+"] = 0.6
    logit += age_eff
    
    # Region effect: North 0.1, South -0.1, East 0.0, West -0.05
    region_eff = np.zeros(n_policies)
    region_eff[regions == "North"] = 0.1
    region_eff[regions == "South"] = -0.1
    region_eff[regions == "West"] = -0.05
    logit += region_eff
    
    # Season effect: winter months (12, 1, 2) get +0.15
    winter_mask = np.isin(months, [12, 1, 2])
    logit[winter_mask] += 0.15
    
    probabilities = 1.0 / (1.0 + np.exp(-logit))
    
    # Simulate claim occurrences
    claims = (np.random.random(n_policies) < probabilities).astype(int)
    claim_indices = np.where(claims == 1)[0]
    n_claims = len(claim_indices)
    
    if n_claims == 0:
        return {"triggered": False, "portfolio_oe": 1.0, "portfolio_relative_drift": 0.0, "portfolio_trigger": False, "seed": seed}
        
    # Extract claim-level attributes
    claim_prods = prods[claim_indices]
    claim_age_groups = age_groups[claim_indices]
    claim_regions = regions[claim_indices]
    claim_genders = genders[claim_indices]
    claim_channels = channels[claim_indices]
    claim_months = months[claim_indices]
    claim_years = years[claim_indices]
    
    # Assign Claim Category (Respiratory is index 1. Winter Respiratory gets weight 3, others weight 1)
    category_weights = np.ones((n_claims, 5))
    winter_claims = np.isin(claim_months, [12, 1, 2])
    category_weights[winter_claims, 1] = 3
    
    norm_weights = category_weights / category_weights.sum(axis=1, keepdims=True)
    cum_weights = norm_weights.cumsum(axis=1)
    r_cat = np.random.random(n_claims)[:, None]
    cat_indices = (r_cat > cum_weights).sum(axis=1)
    claim_categories = np.array(["Cardiac", "Respiratory", "Cancer", "Orthopedic", "General"])[cat_indices]
    
    # Assign Hospital Type
    hosp_types = np.empty(n_claims, dtype=object)
    is_card_canc = np.isin(claim_categories, ["Cancer", "Cardiac"])
    n_cc = is_card_canc.sum()
    n_other = n_claims - n_cc
    
    hosp_types[is_card_canc] = np.random.choice(["Public", "Private", "Specialist"], size=n_cc, p=[0.2, 0.6, 0.2])
    hosp_types[~is_card_canc] = np.random.choice(["Public", "Private", "Specialist"], size=n_other, p=[0.5, 0.3, 0.2])
    
    # Expected Severity calculations
    base_sev = 5000
    intercept = math.log(base_sev)
    
    rel_prod = {"Standard Care": 1.0, "Senior Care Gold": 1.3, "Family Plus": 1.1}
    rel_age = {"18-35": 0.9, "36-59": 1.0, "60+": 1.4}
    rel_reg = {"North": 1.05, "South": 0.95, "East": 1.0, "West": 1.0}
    rel_cat = {"Cardiac": 1.5, "Cancer": 2.0, "Respiratory": 1.1, "Orthopedic": 1.3, "General": 0.8}
    rel_hosp = {"Public": 0.8, "Private": 1.4, "Specialist": 1.6}
    
    beta_prod = np.log([rel_prod[p] for p in claim_prods])
    beta_age = np.log([rel_age[a] for a in claim_age_groups])
    beta_region = np.log([rel_reg[rg] for rg in claim_regions])
    beta_cat = np.log([rel_cat[c] for c in claim_categories])
    beta_hosp = np.log([rel_hosp[h] for h in hosp_types])
    
    expected_monthly_rate = (1.0 + 0.05) ** (1.0 / 12.0) - 1.0
    t_months = (claim_years - 2022) * 12 + (claim_months - 1)
    beta_trend = t_months * math.log(1.0 + expected_monthly_rate)
    
    exp_sevs = np.exp(intercept + beta_prod + beta_age + beta_region + beta_cat + beta_hosp + beta_trend)
    
    # Apply Business Event adjustments stochastically
    actual_expected_sevs = exp_sevs.copy()
    outlier_multipliers = np.ones(n_claims)
    
    if active_events:
        for event_name in active_events:
            if event_name == "Gradual Medical Inflation":
                # Gradual inflation compounding rate of 8% annually
                inflation_annual = 0.08
                inflation_monthly = (1.0 + inflation_annual) ** (1.0 / 12.0) - 1.0
                active_mask = (claim_years == 2024)
                months_active = claim_months[active_mask]
                actual_expected_sevs[active_mask] *= (1.0 + inflation_monthly) ** months_active
                
            elif event_name == "Oncology Treatment Cost Shift":
                # 35% linear progression cost shift on oncology claims in North Region
                active_mask = (claim_years == 2024) & (claim_regions == "North") & (claim_categories == "Cancer")
                months_active = claim_months[active_mask]
                progression = np.minimum(months_active / 12.0, 1.0)
                actual_expected_sevs[active_mask] *= (1.0 + 0.35 * progression)
                
            elif event_name == "Private Hospital Cost Escalation":
                # 20% linear progression escalation on private hospital claims
                active_mask = (claim_years == 2024) & (hosp_types == "Private")
                months_active = claim_months[active_mask]
                progression = np.minimum(months_active / 12.0, 1.0)
                actual_expected_sevs[active_mask] *= (1.0 + 0.20 * progression)
                
            elif event_name == "High-Cost Claim Concentration":
                # 10x outlier multipliers with 4% probability on Cardiac claims in North
                active_mask = (claim_years == 2024) & (claim_regions == "North") & (claim_categories == "Cardiac")
                n_active = active_mask.sum()
                if n_active > 0:
                    outliers = np.random.random(n_active) < 0.04
                    outlier_multipliers[active_mask] = np.where(outliers, 10.0, 1.0)
                    
    # Generate actual amounts stochastically from Lognormal
    volatilities = {"Cardiac": 0.40, "Cancer": 0.70, "Respiratory": 0.50, "Orthopedic": 0.40, "General": 0.30}
    sigmas = np.array([volatilities[c] for c in claim_categories])
    mus = np.log(actual_expected_sevs) - (sigmas ** 2) / 2.0
    actual_amounts = np.random.lognormal(mus, sigmas) * outlier_multipliers
    
    # Build dataframe for current claims only (which is Year == 2024)
    # We only run surveillance on the current claims
    current_mask = (claim_years == 2024)
    n_curr = current_mask.sum()
    
    if n_curr == 0:
        return {"triggered": False, "portfolio_oe": 1.0, "portfolio_relative_drift": 0.0, "portfolio_trigger": False, "seed": seed}
        
    curr_actuals = actual_amounts[current_mask]
    curr_expecteds = exp_sevs[current_mask]
    
    obs_total = curr_actuals.sum()
    exp_total = curr_expecteds.sum()
    port_oe = obs_total / exp_total if exp_total > 0 else 1.0
    port_drift = (obs_total - exp_total) / exp_total if exp_total > 0 else 0.0
    
    # Portfolio level bootstrap CI
    np.random.seed(42)
    boot_idx = np.random.randint(0, n_curr, size=(500, n_curr))
    boot_actuals = curr_actuals[boot_idx].sum(axis=1)
    boot_expecteds = curr_expecteds[boot_idx].sum(axis=1)
    boot_oes = np.sort(boot_actuals / boot_expecteds)
    
    alpha = 0.05
    lower_idx = int(round((alpha / 2.0) * 500))
    lower_bound = float(boot_oes[max(0, lower_idx)])
    
    portfolio_trigger = (port_drift >= 0.05) and (lower_bound > 1.00)
    
    # Demographic Segment Surveillance
    demographic_dimensions = ['Product', 'Region', 'Age_Group', 'Gender', 'Distribution_Channel']
    candidates = []
    
    # Fast grouping dictionary
    grouping_attributes = {
        'Product': claim_prods[current_mask],
        'Region': claim_regions[current_mask],
        'Age_Group': claim_age_groups[current_mask],
        'Gender': claim_genders[current_mask],
        'Distribution_Channel': claim_channels[current_mask]
    }
    
    for dim in demographic_dimensions:
        attrs = grouping_attributes[dim]
        for val in np.unique(attrs):
            seg_mask = (attrs == val)
            n_seg = seg_mask.sum()
            if n_seg < 30:
                continue
                
            obs = curr_actuals[seg_mask].sum()
            exp = curr_expecteds[seg_mask].sum()
            oe = obs / exp if exp > 0 else 0.0
            drift = (obs - exp) / exp if exp > 0 else 0.0
            
            actuals_seg = curr_actuals[seg_mask]
            expecteds_seg = curr_expecteds[seg_mask]
            
            np.random.seed(42)
            seg_boot_idx = np.random.randint(0, n_seg, size=(500, n_seg))
            seg_boot_actuals = actuals_seg[seg_boot_idx].sum(axis=1)
            seg_boot_expecteds = expecteds_seg[seg_boot_idx].sum(axis=1)
            seg_boot_oes = seg_boot_actuals / seg_boot_expecteds
            
            se = np.std(seg_boot_oes)
            
            if method == 'production':
                if se > 0:
                    z = (oe - 1.00) / se
                    p_val = float(1.0 - stats.norm.cdf(z))
                else:
                    p_val = 1.0 if oe <= 1.00 else 0.0
            elif method == 'null_centered_bootstrap':
                count = sum(1 for v in seg_boot_oes if v >= 2.0 * oe - 1.00)
                p_val = (count + 1.0) / (501.0)
            else:
                p_val = 0.5
                
            candidates.append({
                "dimension": dim,
                "segment": str(val),
                "claim_count": int(n_seg),
                "oe_ratio": float(oe),
                "relative_drift": float(drift),
                "raw_p_value": float(p_val),
                "adjusted_p_value": 1.0,
                "fdr_significant": False
            })
            
    m = len(candidates)
    if m == 0:
        return {
            "triggered": False, 
            "portfolio_oe": float(port_oe), 
            "portfolio_relative_drift": float(port_drift), 
            "portfolio_trigger": bool(portfolio_trigger),
            "hypothesis_family_size": 0,
            "raw_significant_count": 0,
            "fdr_significant_count": 0,
            "material_fdr_significant_count": 0,
            "triggered_segments": [],
            "trigger_source": "none",
            "seed": seed,
            "candidates": []
        }
        
    # BH procedure
    candidates.sort(key=lambda x: x["raw_p_value"])
    k_selected = -1
    for i in range(m):
        rank = i + 1
        threshold = (rank / m) * 0.05
        if candidates[i]["raw_p_value"] <= threshold:
            k_selected = i
            
    raw_sig_count = 0
    fdr_sig_count = 0
    material_fdr_sig_count = 0
    triggered_segments = []
    
    for i in range(m):
        is_fdr_sig = (i <= k_selected)
        candidates[i]["fdr_significant"] = is_fdr_sig
        
        if candidates[i]["raw_p_value"] <= 0.05:
            raw_sig_count += 1
        if is_fdr_sig:
            fdr_sig_count += 1
            if candidates[i]["relative_drift"] >= 0.05:
                material_fdr_sig_count += 1
                triggered_segments.append(f"{candidates[i]['dimension']}:{candidates[i]['segment']}")
                
    # Compute q-values
    prev_adj = candidates[-1]["raw_p_value"]
    candidates[-1]["adjusted_p_value"] = prev_adj
    for i in range(m - 2, -1, -1):
        rank = i + 1
        adj = candidates[i]["raw_p_value"] * m / rank
        adj = min(adj, prev_adj)
        adj = min(adj, 1.0)
        candidates[i]["adjusted_p_value"] = adj
        prev_adj = adj
        
    segment_triggered = len(triggered_segments) > 0
    requires_investigation = portfolio_trigger or segment_triggered
    trigger_source = "none"
    if portfolio_trigger:
        trigger_source = "portfolio"
    elif segment_triggered:
        trigger_source = "segment_surveillance"
        
    return {
        "triggered": bool(requires_investigation),
        "portfolio_oe": float(port_oe),
        "portfolio_relative_drift": float(port_drift),
        "portfolio_trigger": bool(portfolio_trigger),
        "hypothesis_family_size": int(m),
        "raw_significant_count": int(raw_sig_count),
        "fdr_significant_count": int(fdr_sig_count),
        "material_fdr_significant_count": int(material_fdr_sig_count),
        "triggered_segments": triggered_segments,
        "trigger_source": trigger_source,
        "seed": seed,
        "candidates": candidates
    }

class SeverityNullCalibrator:
    def __init__(self, num_simulations: int = 500):
        self.num_simulations = num_simulations
        self.config, self.events_config, self.severity_config = load_configs()
        self.analytics = SeverityAnalyticsEngine(
            materiality_threshold=0.05, 
            minimum_claims=30, 
            fdr_target=0.05
        )

    def run_calibration(self, method: str = 'production', active_events: List[str] = None, num_sims: int = None) -> List[Dict[str, Any]]:
        """Runs the simulations in parallel using concurrent.futures."""
        sims_to_run = num_sims if num_sims is not None else self.num_simulations
        print(f"Running {sims_to_run} simulations for method={method}, active_events={active_events}...")
        
        args_list = [(42 + i, active_events, method) for i in range(sims_to_run)]
        results = []
        
        max_workers = os.cpu_count() or 4
        print(f"Using {max_workers} worker processes...")
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(run_single_simulation, args) for args in args_list]
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                res = future.result()
                results.append(res)
                if (i + 1) % 50 == 0:
                    print(f"  Completed {i + 1}/{sims_to_run} simulations...")
                    
        return results

    def analyze_results(self, null_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates all false alert metrics and calibrates dimensions."""
        n = len(null_results)
        if n == 0:
            return {}
            
        fir = sum(1 for r in null_results if r["triggered"]) / n
        pftr = sum(1 for r in null_results if r["portfolio_trigger"]) / n
        ssftr = sum(1 for r in null_results if r["trigger_source"] == "segment_surveillance") / n
        
        any_fdr_discovery = sum(1 for r in null_results if r["fdr_significant_count"] > 0) / n
        
        avg_raw_sig = np.mean([r["raw_significant_count"] for r in null_results])
        avg_fdr_sig = np.mean([r["fdr_significant_count"] for r in null_results])
        avg_material_fdr_sig = np.mean([r["material_fdr_significant_count"] for r in null_results])
        
        max_drifts = []
        for r in null_results:
            cand_drifts = [c["relative_drift"] for c in r.get("candidates", [])]
            if cand_drifts:
                max_drifts.append(max(cand_drifts))
            else:
                max_drifts.append(0.0)
                
        p50 = np.percentile(max_drifts, 50)
        p90 = np.percentile(max_drifts, 90)
        p95 = np.percentile(max_drifts, 95)
        p99 = np.percentile(max_drifts, 99)
        
        dim_triggers = {"Product": 0, "Region": 0, "Age_Group": 0, "Gender": 0, "Distribution_Channel": 0}
        total_segment_triggers = 0
        for r in null_results:
            if r["trigger_source"] == "segment_surveillance" and r["triggered_segments"]:
                for ts in r["triggered_segments"]:
                    dim = ts.split(":")[0]
                    if dim in dim_triggers:
                        dim_triggers[dim] += 1
                        total_segment_triggers += 1
                        
        dim_shares = {}
        for dim, count in dim_triggers.items():
            dim_shares[dim] = count / total_segment_triggers if total_segment_triggers > 0 else 0.0
            
        return {
            "false_investigation_rate": float(fir),
            "portfolio_false_trigger_rate": float(pftr),
            "segment_surveillance_false_trigger_rate": float(ssftr),
            "any_fdr_discovery_rate": float(any_fdr_discovery),
            "avg_raw_significant_segments": float(avg_raw_sig),
            "avg_fdr_significant_segments": float(avg_fdr_sig),
            "avg_material_fdr_significant_segments": float(avg_material_fdr_sig),
            "drift_percentiles": {"P50": float(p50), "P90": float(p90), "P95": float(p95), "P99": float(p99)},
            "dimension_trigger_shares": dim_shares
        }

    def analyze_segment_calibration(self, null_results: List[Dict[str, Any]]) -> pd.DataFrame:
        """Evaluates calibration for every recurring segment across simulations."""
        n = len(null_results)
        segment_data = {}
        
        for r in null_results:
            for c in r.get("candidates", []):
                key = (c["dimension"], c["segment"])
                if key not in segment_data:
                    segment_data[key] = {
                        "oes": [],
                        "drifts": [],
                        "raw_sigs": [],
                        "fdr_sigs": [],
                        "triggers": []
                    }
                segment_data[key]["oes"].append(c["oe_ratio"])
                segment_data[key]["drifts"].append(c["relative_drift"])
                segment_data[key]["raw_sigs"].append(1 if c["raw_p_value"] <= 0.05 else 0)
                segment_data[key]["fdr_sigs"].append(1 if c["fdr_significant"] else 0)
                
                is_trigger = 1 if (c["relative_drift"] >= 0.05 and c["fdr_significant"]) else 0
                segment_data[key]["triggers"].append(is_trigger)
                
        rows = []
        for key, data in segment_data.items():
            dim, seg = key
            oes = data["oes"]
            drifts = data["drifts"]
            raw_sigs = data["raw_sigs"]
            fdr_sigs = data["fdr_sigs"]
            triggers = data["triggers"]
            
            rows.append({
                "Dimension": dim,
                "Segment": seg,
                "Mean_OE": float(np.mean(oes)),
                "Median_OE": float(np.median(oes)),
                "SD_OE": float(np.std(oes)),
                "Mean_Drift": float(np.mean(drifts)),
                "Prob_OE_gt_1": float(sum(1 for o in oes if o > 1.00) / len(oes)),
                "Prob_Drift_ge_5": float(sum(1 for d in drifts if d >= 0.05) / len(drifts)),
                "Prob_Raw_Sig": float(np.mean(raw_sigs)),
                "Prob_FDR_Sig": float(np.mean(fdr_sigs)),
                "Prob_Final_Trigger": float(np.mean(triggers))
            })
            
        return pd.DataFrame(rows)

    def analyze_pvalue_calibration(self, null_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Inspects raw surveillance p-value distribution under the null."""
        all_pvals = []
        for r in null_results:
            for c in r.get("candidates", []):
                all_pvals.append(c["raw_p_value"])
                
        all_pvals = np.array(all_pvals)
        total = len(all_pvals)
        if total == 0:
            return {}
            
        share_01 = np.sum(all_pvals <= 0.01) / total
        share_05 = np.sum(all_pvals <= 0.05) / total
        share_10 = np.sum(all_pvals <= 0.10) / total
        share_50 = np.sum(all_pvals <= 0.50) / total
        
        # Build histogram
        hist, bin_edges = np.histogram(all_pvals, bins=10, range=(0, 1))
        hist_data = {f"({bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}]": int(hist[i]) for i in range(len(hist))}
        
        return {
            "share_p_le_01": float(share_01),
            "share_p_le_05": float(share_05),
            "share_p_le_10": float(share_10),
            "share_p_le_50": float(share_50),
            "histogram": hist_data
        }

if __name__ == "__main__":
    calibrator = SeverityNullCalibrator(num_simulations=500)
    os.makedirs("scratch", exist_ok=True)
    
    print("==================================================")
    # 1. Null simulations for production method
    null_results_prod = calibrator.run_calibration(method='production', num_sims=500)
    metrics_prod = calibrator.analyze_results(null_results_prod)
    pcal_prod = calibrator.analyze_pvalue_calibration(null_results_prod)
    seg_df_prod = calibrator.analyze_segment_calibration(null_results_prod)
    
    print("\n--- Production Method Results ---")
    print(yaml.dump(metrics_prod))
    print(yaml.dump(pcal_prod))
    
    # 2. Null simulations for null-centered bootstrap method
    null_results_ref = calibrator.run_calibration(method='null_centered_bootstrap', num_sims=500)
    metrics_ref = calibrator.analyze_results(null_results_ref)
    pcal_ref = calibrator.analyze_pvalue_calibration(null_results_ref)
    seg_df_ref = calibrator.analyze_segment_calibration(null_results_ref)
    
    print("\n--- Reference (Null-Centered Bootstrap) Results ---")
    print(yaml.dump(metrics_ref))
    print(yaml.dump(pcal_ref))
    
    # 3. Alternative simulations to check power (50 sims each)
    alternative_scenarios = [
        ("Gradual Medical Inflation", "Medical Inflation"),
        ("Oncology Treatment Cost Shift", "Oncology Shift"),
        ("Private Hospital Cost Escalation", "Private Hospital Escalation"),
        ("High-Cost Claim Concentration", "High-Cost Concentration")
    ]
    
    power_results = {}
    for event_name, name in alternative_scenarios:
        alt_res_prod = calibrator.run_calibration(method='production', active_events=[event_name], num_sims=50)
        power_prod = sum(1 for r in alt_res_prod if r["triggered"]) / len(alt_res_prod)
        
        # For oncology, calculate recovery of Region:North
        onc_recovery = 0.0
        if name == "Oncology Shift":
            onc_recovery = sum(1 for r in alt_res_prod if "Region:North" in r.get("triggered_segments", [])) / len(alt_res_prod)
            
        power_results[name] = {"power": float(power_prod), "oncology_recovery": float(onc_recovery)}
        
    print("\n--- Power Detection Results ---")
    print(yaml.dump(power_results))
    
    # Save segment calibration DataFrame
    seg_df_prod.to_csv("scratch/null_segment_calibration.csv", index=False)
    print("\nSaved null segment calibration summary to scratch/null_segment_calibration.csv")
