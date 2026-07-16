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

from tools.drift_detector import StatisticalAnalyticsEngine
from statistics_utils.multiple_testing import benjamini_hochberg

# Cached configuration dictionary
_config_cache = {}

def load_configs():
    if not _config_cache:
        config_path = os.path.join(backend_dir, 'data', 'generation_config.yaml')
        events_path = os.path.join(backend_dir, 'data', 'business_events.yaml')
        
        with open(config_path, 'r') as file:
            _config_cache["config"] = yaml.safe_load(file)
        with open(events_path, 'r') as file:
            _config_cache["events_config"] = yaml.safe_load(file)
    return _config_cache["config"], _config_cache["events_config"]

def simulate_portfolio_dataset(seed: int, active_event_names: List[str] = None) -> pd.DataFrame:
    """Highly optimized vectorized generation of a single synthetic frequency dataset."""
    np.random.seed(seed)
    config, events_config = load_configs()
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
    
    # Plan type
    plan_types = np.random.choice(["Basic", "Comprehensive"], size=n_policies, p=[0.4, 0.6])
    
    # 7. Calculate baseline logit
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
    
    # Stored expected frequency is probability before events
    expected_freqs = 1.0 / (1.0 + np.exp(-logit))
    
    # Apply active business events to baseline logit
    actual_logit = logit.copy()
    if active_event_names:
        for event in events_config.get("events", []):
            if event["event_name"] in active_event_names and event.get("type", "frequency") == "frequency":
                # Verify match conditions
                match_mask = (years == 2024) & (months >= event["start_month"])
                for k, v in event.get("affected_population", {}).items():
                    if k == "region":
                        match_mask &= (regions == v)
                    elif k == "age_group":
                        match_mask &= (age_groups == v)
                    elif k == "product":
                        match_mask &= (prods == v)
                    elif k == "gender":
                        match_mask &= (genders == v)
                    elif k == "distribution_channel":
                        match_mask &= (channels == v)
                        
                if match_mask.any():
                    # Calculate progression curve
                    months_active = months[match_mask] - event["start_month"] + 1
                    duration = event["duration"]
                    if event.get("progression_curve") == "linear":
                        prog = np.minimum(months_active / duration, 1.0)
                    elif event.get("progression_curve") == "exponential":
                        prog = np.minimum((months_active / duration) ** 2, 1.0)
                    else: # step
                        prog = np.ones_like(months_active)
                        
                    actual_logit[match_mask] += event["effect_size"] * prog
                    
    actual_probabilities = 1.0 / (1.0 + np.exp(-actual_logit))
    
    # Simulate Bernoulli claim occurrences
    claims = (np.random.random(n_policies) < actual_probabilities).astype(int)
    
    df = pd.DataFrame({
        "Product": prods,
        "Age_Group": age_groups,
        "Region": regions,
        "Gender": genders,
        "Distribution_Channel": channels,
        "Plan_Type": plan_types,
        "Exposure": np.ones(n_policies),
        "Claim": claims,
        "Expected_Frequency": expected_freqs,
        "Year": years,
        "Month": months
    })
    return df

def run_calibration_pass(num_simulations=500) -> pd.DataFrame:
    """Runs 500 null simulations and evaluates the 6 credibility thresholds."""
    thresholds = [5, 10, 15, 20, 25, 30]
    
    # Setup cumulative lists to collect metrics per threshold
    results_accumulator = {t: {
        "null_portfolio_triggers": 0,
        "null_segment_triggers": 0,
        "null_investigations": 0,
        "null_p_values": [],
        "null_triggered_count": []
    } for t in thresholds}
    
    # Run null simulations
    print(f"Running {num_simulations} null simulations for Frequency...")
    for seed in range(num_simulations):
        df = simulate_portfolio_dataset(seed)
        df_latest = df[df['Year'] == 2024]
        
        # Evaluate for each threshold
        for t in thresholds:
            engine = StatisticalAnalyticsEngine(
                relative_drift_threshold=0.05,
                min_exposure=500,
                z_score_threshold=1.645,  # 95% one-sided threshold
                min_expected_claims=t,
                fdr_target=0.05
            )
            
            metrics = engine.calculate_metrics(df_latest)
            surveillance = engine.run_segment_surveillance(df_latest)
            
            # Check triggers
            port_trigger = metrics.get("requires_investigation", False)
            seg_trigger = surveillance.get("triggered", False)
            investigation = port_trigger or seg_trigger
            
            acc = results_accumulator[t]
            if port_trigger:
                acc["null_portfolio_triggers"] += 1
            if seg_trigger:
                acc["null_segment_triggers"] += 1
            if investigation:
                acc["null_investigations"] += 1
                
            # Collect p-values for p-value uniformity/calibration check
            # We re-evaluate all demographic segments to collect p-values
            demographic_dimensions = ['Product', 'Region', 'Age_Group', 'Gender', 'Distribution_Channel']
            for dim in demographic_dimensions:
                for val, group in df_latest.groupby(dim):
                    exposure = len(group)
                    if exposure >= 500:
                        expected_claims = group['Expected_Frequency'].sum()
                        if expected_claims >= t:
                            actual_claims = group['Claim'].sum()
                            variance = (group['Expected_Frequency'] * (1 - group['Expected_Frequency'])).sum()
                            std_dev = np.sqrt(variance)
                            z = (actual_claims - expected_claims) / std_dev if std_dev > 0 else 0.0
                            p_val = float(1.0 - stats.norm.cdf(z))
                            acc["null_p_values"].append(p_val)
                            
    # Compile the null metrics
    records = []
    for t in thresholds:
        acc = results_accumulator[t]
        p_vals = np.array(acc["null_p_values"])
        
        # P-value calibrations
        p_le_01 = np.mean(p_vals <= 0.01) if len(p_vals) > 0 else 0.0
        p_le_05 = np.mean(p_vals <= 0.05) if len(p_vals) > 0 else 0.0
        p_le_10 = np.mean(p_vals <= 0.10) if len(p_vals) > 0 else 0.0
        p_le_50 = np.mean(p_vals <= 0.50) if len(p_vals) > 0 else 0.0
        
        fir = acc["null_investigations"] / num_simulations
        pftr = acc["null_portfolio_triggers"] / num_simulations
        ssftr = acc["null_segment_triggers"] / num_simulations
        
        # Calibration classification: Z-test should be conservative or approximately calibrated
        # Target for p_le_05 is 5.0%. If empirical share <= 5.0%, it is conservative.
        if p_le_05 > 0.06:
            calibration_status = "Anti-Conservative"
        elif p_le_05 >= 0.04:
            calibration_status = "Approximately Calibrated"
        else:
            calibration_status = "Conservative"
            
        records.append({
            "Min_Expected_Claims": t,
            "FIR": fir,
            "PFTR": pftr,
            "SSFTR": ssftr,
            "P_le_01": p_le_01,
            "P_le_05": p_le_05,
            "P_le_10": p_le_10,
            "P_le_50": p_le_50,
            "Calibration_Status": calibration_status
        })
        
    df_results = pd.DataFrame(records)
    
    # Run alternative simulations for Power (50 runs per scenario)
    scenarios = [
        {"name": "Northern Oncology Growth", "events": ["Northern Oncology Growth"], "target": ("Region", "North")},
        {"name": "Severe Winter Respiratory Strain", "events": ["Severe Winter Respiratory Strain"], "target": ("Product", "Family Plus")},
        {"name": "Southern Orthopedic Shift", "events": ["Southern Orthopedic Shift"], "target": ("Region", "South")}
    ]
    
    print("\nEvaluating Scenario Detection Power (50 simulations each)...")
    for scen in scenarios:
        scen_name = scen["name"]
        scen_events = scen["events"]
        tgt_dim, tgt_val = scen["target"]
        
        power_accumulator = {t: {"triggered": 0, "correct_recovery": 0} for t in thresholds}
        
        for seed in range(50):
            df_scen = simulate_portfolio_dataset(seed, scen_events)
            df_latest = df_scen[df_scen['Year'] == 2024]
            
            for t in thresholds:
                engine = StatisticalAnalyticsEngine(
                    relative_drift_threshold=0.05,
                    min_exposure=500,
                    z_score_threshold=1.645,
                    min_expected_claims=t,
                    fdr_target=0.05
                )
                
                metrics = engine.calculate_metrics(df_latest)
                surveillance = engine.run_segment_surveillance(df_latest)
                
                port_trigger = metrics.get("requires_investigation", False)
                seg_trigger = surveillance.get("triggered", False)
                investigation = port_trigger or seg_trigger
                
                if investigation:
                    power_accumulator[t]["triggered"] += 1
                    
                # Verify correct demographic recovery rate
                # True if surveillance triggered segment matches the target dimension and value
                if seg_trigger and surveillance.get("trigger_dimension") == tgt_dim and surveillance.get("trigger_segment") == tgt_val:
                    power_accumulator[t]["correct_recovery"] += 1
                    
        # Add power results to the results DataFrame
        power_col = []
        recovery_col = []
        for t in thresholds:
            power_val = power_accumulator[t]["triggered"] / 50.0
            recovery_val = power_accumulator[t]["correct_recovery"] / 50.0
            power_col.append(power_val)
            recovery_col.append(recovery_val)
            
        df_results[f"{scen_name}_Power"] = power_col
        df_results[f"{scen_name}_Recovery"] = recovery_col
        
    os.makedirs(os.path.join(backend_dir, "scratch"), exist_ok=True)
    out_path = os.path.join(backend_dir, "scratch", "null_frequency_calibration.csv")
    df_results.to_csv(out_path, index=False)
    print(f"\nSaved null frequency calibration results to: {out_path}")
    print(df_results.to_string(index=False))
    return df_results

if __name__ == "__main__":
    run_pass = True
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_pass = False
    if run_pass:
        run_calibration_pass()
