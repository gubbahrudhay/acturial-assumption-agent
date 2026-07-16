import pandas as pd
import numpy as np
from typing import Dict, Any, List

class SeverityAnalyticsEngine:
    """
    Severity Analytics Engine.
    Performs purely deterministic actuarial and statistical calculations for Claim Severity.
    Now includes cost-band distribution diagnostics and pre-planner segment surveillance.
    """
    
    def __init__(
        self, 
        materiality_threshold: float = 0.05, 
        minimum_claims: int = 30, 
        bootstrap_iterations: int = 500, 
        confidence_level: float = 0.95,
        baseline_years: List[int] = None,
        current_years: List[int] = None,
        fdr_target: float = 0.05
    ):
        self.materiality_threshold = materiality_threshold
        self.minimum_claims = minimum_claims
        self.bootstrap_iterations = bootstrap_iterations
        self.confidence_level = confidence_level
        self.baseline_years = baseline_years or [2022, 2023]
        self.current_years = current_years or [2024]
        self.fdr_target = fdr_target
        
    def filter_claims(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filters dataset to claim records containing valid severity data."""
        if df.empty:
            return df
            
        # If 'Claim' column exists, filter to Claim == 1
        if 'Claim' in df.columns:
            claims_df = df[df['Claim'] == 1].copy()
        else:
            claims_df = df.copy()
            
        required = ['Actual_Claim_Amount', 'Expected_Severity']
        for col in required:
            if col not in claims_df.columns:
                return pd.DataFrame()
                
        claims_df = claims_df.dropna(subset=required)
        return claims_df

    def calculate_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates aggregate severity metrics, bootstrap confidence intervals, and outlier sensitivity."""
        claims_df = self.filter_claims(df)
        
        if claims_df.empty:
            return {"error": "No claim records with valid severity data found."}
            
        # Separate into Baseline and Current periods
        if 'Year' in claims_df.columns:
            baseline_claims = claims_df[claims_df['Year'].isin(self.baseline_years)]
            current_claims = claims_df[claims_df['Year'].isin(self.current_years)]
        else:
            baseline_claims = claims_df
            current_claims = claims_df

        claim_count = len(current_claims)
        is_credible = claim_count >= self.minimum_claims
        
        if claim_count == 0:
            return {
                "requires_investigation": False,
                "claim_count": 0,
                "is_credible": False,
                "error": "No claims in current period."
            }
            
        # Observed and Expected Costs
        observed_cost = current_claims['Actual_Claim_Amount'].sum()
        expected_cost = current_claims['Expected_Severity'].sum()
        
        observed_severity = observed_cost / claim_count
        expected_severity = expected_cost / claim_count
        
        # Severity O/E Ratio
        oe_ratio = observed_cost / expected_cost if expected_cost > 0 else 0.0
        relative_drift = (observed_severity - expected_severity) / expected_severity if expected_severity > 0 else 0.0
        excess_cost = observed_cost - expected_cost
        
        # Bootstrap Significance Testing
        np.random.seed(42)
        bootstrap_oes = []
        
        if claim_count > 1:
            for _ in range(self.bootstrap_iterations):
                sample_idx = np.random.choice(current_claims.index, size=claim_count, replace=True)
                sample = current_claims.loc[sample_idx]
                boot_obs = sample['Actual_Claim_Amount'].sum()
                boot_exp = sample['Expected_Severity'].sum()
                boot_oe = boot_obs / boot_exp if boot_exp > 0 else 1.0
                bootstrap_oes.append(boot_oe)
                
            bootstrap_oes = np.sort(bootstrap_oes)
            alpha = 1.0 - self.confidence_level
            lower_idx = int(round((alpha / 2.0) * self.bootstrap_iterations))
            upper_idx = int(round((1.0 - alpha / 2.0) * self.bootstrap_iterations)) - 1
            
            lower_bound = float(bootstrap_oes[max(0, lower_idx)])
            upper_bound = float(bootstrap_oes[min(self.bootstrap_iterations - 1, upper_idx)])
        else:
            lower_bound = oe_ratio
            upper_bound = oe_ratio
            
        is_significant = lower_bound > 1.00
        
        # --- ISSUE 1: Cost Band Distribution Diagnostics ---
        # Derive historical baseline thresholds: P50, P90, P99
        ref_claims = baseline_claims if not baseline_claims.empty else current_claims
        p50 = float(ref_claims['Actual_Claim_Amount'].quantile(0.50))
        p90 = float(ref_claims['Actual_Claim_Amount'].quantile(0.90))
        p99 = float(ref_claims['Actual_Claim_Amount'].quantile(0.99))
        
        # Assign current claims to cost bands
        band0_df = current_claims[current_claims['Actual_Claim_Amount'] <= p50]
        band1_df = current_claims[(current_claims['Actual_Claim_Amount'] > p50) & (current_claims['Actual_Claim_Amount'] <= p90)]
        band2_df = current_claims[(current_claims['Actual_Claim_Amount'] > p90) & (current_claims['Actual_Claim_Amount'] <= p99)]
        band3_df = current_claims[current_claims['Actual_Claim_Amount'] > p99]
        
        band_dfs = {
            "P0_P50": band0_df,
            "P50_P90": band1_df,
            "P90_P99": band2_df,
            "P99_plus": band3_df
        }
        
        bands_data = {}
        total_pos_excess = 0.0
        
        for key, bdf in band_dfs.items():
            b_obs = float(bdf['Actual_Claim_Amount'].sum())
            b_exp = float(bdf['Expected_Severity'].sum())
            b_oe = b_obs / b_exp if b_exp > 0 else 0.0
            b_excess = b_obs - b_exp
            pos_excess = max(b_excess, 0.0)
            total_pos_excess += pos_excess
            
            bands_data[key] = {
                "claim_count": len(bdf),
                "observed_cost": b_obs,
                "expected_cost": b_exp,
                "oe_ratio": b_oe,
                "excess_cost": b_excess,
                "excess_share": 0.0 # Will populate after sum is known
            }
            
        for key in bands_data:
            if total_pos_excess > 0:
                bands_data[key]["excess_share"] = max(bands_data[key]["excess_cost"], 0.0) / total_pos_excess
                
        # Actuarial Trigger Check (Significance AND Materiality)
        requires_investigation = (
            is_significant and 
            relative_drift >= self.materiality_threshold and 
            is_credible
        )
        
        # Deterministic classification rules based on excess cost shares
        if requires_investigation:
            share_p99_plus = bands_data["P99_plus"]["excess_share"]
            share_p90_p99 = bands_data["P90_P99"]["excess_share"]
            share_normals = bands_data["P0_P50"]["excess_share"] + bands_data["P50_P90"]["excess_share"]
            
            if share_p99_plus >= 0.60:
                classification = "High-Cost Concentration"
            elif (share_p90_p99 + share_p99_plus) >= 0.60 and share_p99_plus < 0.60:
                classification = "Upper-Tail Deterioration"
            elif share_normals >= 0.50 and share_p99_plus < 0.30:
                classification = "Broad Deterioration"
            else:
                classification = "Mixed Deterioration"
        else:
            classification = "No Significant Deterioration"
            
        # Descriptive high-cost monitoring (preserve baseline P99 metric)
        high_cost_threshold = p99
        high_cost_claims = current_claims[current_claims['Actual_Claim_Amount'] > high_cost_threshold]
        high_cost_count = len(high_cost_claims)
        high_cost_cost = high_cost_claims['Actual_Claim_Amount'].sum()
        high_cost_share = high_cost_cost / observed_cost if observed_cost > 0 else 0.0
        
        normal_claims = current_claims[current_claims['Actual_Claim_Amount'] <= high_cost_threshold]
        normal_obs_cost = normal_claims['Actual_Claim_Amount'].sum()
        normal_exp_cost = normal_claims['Expected_Severity'].sum()
        normal_oe_ratio = normal_obs_cost / normal_exp_cost if normal_exp_cost > 0 else 0.0
        
        # Actuarial Score (Materiality + Confidence 0-100)
        materiality_score = min(abs(relative_drift) / 0.20 * 50, 50)
        confidence_val = (lower_bound - 1.0) / 0.10 * 50 if lower_bound > 1.0 else 0.0
        confidence_score = min(max(confidence_val, 0.0), 50.0)
        drift_score = float(materiality_score + confidence_score) if is_credible else 0.0
        
        return {
            "requires_investigation": bool(requires_investigation),
            "claim_count": int(claim_count),
            "is_credible": bool(is_credible),
            "observed_severity": float(observed_severity),
            "expected_severity": float(expected_severity),
            "oe_ratio": float(oe_ratio),
            "relative_drift": float(relative_drift),
            "excess_cost": float(excess_cost),
            "bootstrap_lower_bound": float(lower_bound),
            "bootstrap_upper_bound": float(upper_bound),
            "is_significant": bool(is_significant),
            "high_cost_threshold": float(high_cost_threshold),
            "high_cost_count": int(high_cost_count),
            "high_cost_cost": float(high_cost_cost),
            "high_cost_share": float(high_cost_share),
            "oe_excluding_high_cost": float(normal_oe_ratio),
            "deterioration_classification": classification,
            "drift_score": float(drift_score),
            "observed_cost": float(observed_cost),
            "expected_cost": float(expected_cost),
            "distribution_bands": bands_data,
            "baseline_thresholds": {
                "P50": p50,
                "P90": p90,
                "P99": p99
            }
        }

    def run_segment_surveillance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        ISSUE 2: Pre-Planner Segment Surveillance.
        Evaluates demographic dimensions to detect material localized deterioration.
        Claim attributes (Claim_Category, Hospital_Type, Claim_Status) are strictly EXCLUDED.
        Controls False Discovery Rate using Benjamini-Hochberg procedure.
        """
        import scipy.stats as stats
        claims_df = self.filter_claims(df)
        if claims_df.empty:
            return {"triggered": False}
            
        if 'Year' in claims_df.columns:
            current_claims = claims_df[claims_df['Year'].isin(self.current_years)]
        else:
            current_claims = claims_df
            
        demographic_dimensions = ['Product', 'Region', 'Age_Group', 'Gender', 'Distribution_Channel']
        candidates = []
        
        # 1. Collect all candidates with sufficient volume (Hypothesis Family: pooled across all demographic dimensions)
        for dim in demographic_dimensions:
            if dim not in current_claims.columns:
                continue
                
            for val, group in current_claims.groupby(dim):
                n_claims = len(group)
                if n_claims < self.minimum_claims:
                    continue
                    
                obs = group['Actual_Claim_Amount'].sum()
                exp = group['Expected_Severity'].sum()
                oe = obs / exp if exp > 0 else 0.0
                drift = (obs - exp) / exp if exp > 0 else 0.0
                excess = obs - exp
                
                # Run Bootstrap to calculate standard error of O/E
                np.random.seed(42)
                boot_oes = []
                for _ in range(self.bootstrap_iterations):
                    idx = np.random.choice(group.index, size=n_claims, replace=True)
                    sample = group.loc[idx]
                    boot_oes.append(sample['Actual_Claim_Amount'].sum() / sample['Expected_Severity'].sum())
                    
                boot_oes = np.sort(boot_oes)
                alpha = 1.0 - self.confidence_level
                lower_idx = int(round((alpha / 2.0) * self.bootstrap_iterations))
                lower_bound = float(boot_oes[max(0, lower_idx)])
                upper_bound = float(boot_oes[min(self.bootstrap_iterations - 1, int(round((1.0 - alpha / 2.0) * self.bootstrap_iterations)) - 1)])
                
                # Calculate standard error of the bootstrap O/E values
                se = np.std(boot_oes)
                if se > 0:
                    z = (oe - 1.00) / se
                    p_val = float(1.0 - stats.norm.cdf(z))
                else:
                    p_val = 1.0 if oe <= 1.00 else 0.0
                
                candidates.append({
                    "dimension": dim,
                    "segment": str(val),
                    "claim_count": n_claims,
                    "observed_cost": obs,
                    "expected_cost": exp,
                    "oe_ratio": oe,
                    "relative_drift": drift,
                    "excess_cost": excess,
                    "bootstrap_lower_bound": lower_bound,
                    "bootstrap_upper_bound": upper_bound,
                    "raw_p_value": p_val,
                    "adjusted_p_value": 1.0,
                    "fdr_significant": False,
                    "hypothesis_rank": 0
                })
                
        m = len(candidates)
        if m == 0:
            return {"triggered": False}
            
        # 2. Apply Benjamini-Hochberg FDR control using shared utility
        p_vals = [c["raw_p_value"] for c in candidates]
        hyp_ids = list(range(m))
        
        from statistics_utils.multiple_testing import benjamini_hochberg
        bh_results = benjamini_hochberg(p_vals, hyp_ids, fdr_target=self.fdr_target)
        
        for idx, res in enumerate(bh_results):
            candidates[idx]["adjusted_p_value"] = res["adjusted_q_value"]
            candidates[idx]["fdr_significant"] = res["fdr_significant"]
            candidates[idx]["hypothesis_rank"] = res["bh_rank"]
            
        # 3. Filter to segments that satisfy triggering conditions:
        # Materiality AND Volume AND FDR Significance
        triggered_segments = []
        for c in candidates:
            # Check segment trigger conditions
            if (
                c["relative_drift"] >= self.materiality_threshold and
                c["fdr_significant"]
            ):
                triggered_segments.append({
                    "triggered": True,
                    "trigger_source": "segment_surveillance",
                    "trigger_dimension": c["dimension"],
                    "trigger_segment": c["segment"],
                    "segment_metrics": {
                        "claim_count": int(c["claim_count"]),
                        "observed_cost": float(c["observed_cost"]),
                        "expected_cost": float(c["expected_cost"]),
                        "oe_ratio": float(c["oe_ratio"]),
                        "relative_drift": float(c["relative_drift"]),
                        "excess_cost": float(c["excess_cost"]),
                        "bootstrap_lower_bound": float(c["bootstrap_lower_bound"]),
                        "bootstrap_upper_bound": float(c["bootstrap_upper_bound"]),
                        "raw_p_value": float(c["raw_p_value"]),
                        "adjusted_p_value": float(c["adjusted_p_value"]),
                        "fdr_significant": bool(c["fdr_significant"]),
                        "fdr_target": float(self.fdr_target),
                        "hypothesis_family_size": int(m),
                        "hypothesis_rank": int(c["hypothesis_rank"])
                    },
                    "trigger_reason": (
                        f"Demographic segment {c['dimension']}:{c['segment']} exhibits material "
                        f"(Drift: {c['relative_drift']*100:+.2f}%) and FDR-significant "
                        f"(q-val: {c['adjusted_p_value']:.4f} <= target: {self.fdr_target}) severity deterioration."
                    )
                })
                
        if triggered_segments:
            # Sort by absolute excess cost descending, and return the worst segment trigger
            triggered_segments.sort(key=lambda x: x["segment_metrics"]["excess_cost"], reverse=True)
            return triggered_segments[0]
            
        return {"triggered": False}

    def calculate_rolling_trend(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates rolling 3-month aggregate severity trend using weighted sums."""
        claims_df = self.filter_claims(df)
        if claims_df.empty:
            return pd.DataFrame()
            
        grouped = claims_df.groupby(['Year', 'Month']).agg(
            Observed_Cost=('Actual_Claim_Amount', 'sum'),
            Expected_Cost=('Expected_Severity', 'sum'),
            Claims_Count=('Actual_Claim_Amount', 'count')
        ).reset_index()
        
        grouped = grouped.sort_values(['Year', 'Month']).reset_index(drop=True)
        
        grouped['Observed_Severity'] = grouped['Observed_Cost'] / grouped['Claims_Count']
        grouped['Expected_Severity'] = grouped['Expected_Cost'] / grouped['Claims_Count']
        grouped['Monthly_OE'] = grouped['Observed_Cost'] / grouped['Expected_Cost']
        
        rolling_obs_cost = grouped['Observed_Cost'].rolling(window=3, min_periods=1).sum()
        rolling_exp_cost = grouped['Expected_Cost'].rolling(window=3, min_periods=1).sum()
        grouped['Rolling_3M_OE'] = rolling_obs_cost / rolling_exp_cost
        
        grouped['Relative_Drift'] = (grouped['Observed_Severity'] - grouped['Expected_Severity']) / grouped['Expected_Severity']
        grouped['Trend'] = grouped['Relative_Drift'].rolling(window=3, min_periods=1).mean()
        
        return grouped
