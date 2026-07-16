import pandas as pd
import numpy as np
from typing import Dict, Any

class StatisticalAnalyticsEngine:
    """
    Layer 2: Statistical Analytics Engine.
    Performs purely deterministic actuarial calculations. No LLMs exist in this layer.
    """
    
    def __init__(self, relative_drift_threshold=0.05, min_exposure=500, z_score_threshold=1.96, min_expected_claims=10, fdr_target=0.05):
        self.relative_drift_threshold = relative_drift_threshold
        self.min_exposure = min_exposure
        self.z_score_threshold = z_score_threshold
        self.min_expected_claims = min_expected_claims
        self.fdr_target = fdr_target

    def calculate_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates foundational metrics (Frequency, Relative Drift, Credibility, Z-Score)."""
        if df.empty:
            return {"error": "Empty dataframe"}
            
        # Verify exposure compatibility (Frequency v1 limitation check)
        if 'Exposure' in df.columns:
            non_unit_mask = (df['Exposure'] - 1.0).abs() > 1e-5
            if non_unit_mask.any():
                return {
                    "error": "Frequency v1 statistical model assumes unit policy-year Bernoulli exposure. Fractional or variable exposure requires a rate/count model.",
                    "requires_investigation": False,
                    "is_credible": False
                }
            
        total_exposure = df['Exposure'].sum() if 'Exposure' in df.columns else float(len(df))
        actual_claims = df['Claim'].sum()
        
        # Expected claims = sum(p_i * w_i)
        if 'Expected_Frequency' in df.columns:
            expected_claims = (df['Expected_Frequency'] * df['Exposure']).sum() if 'Exposure' in df.columns else df['Expected_Frequency'].sum()
        else:
            expected_claims = 0.0
            
        actual_freq = actual_claims / total_exposure if total_exposure > 0 else 0.0
        expected_freq = expected_claims / total_exposure if total_exposure > 0 else 0.0
        
        # 1. Relative Drift
        relative_drift = (actual_freq - expected_freq) / expected_freq if expected_freq > 0 else 0.0
        
        # 2. Credibility (Exposure + Expected Claims check)
        is_credible = total_exposure >= self.min_exposure and expected_claims >= self.min_expected_claims
        
        # 3. Z-Score (Poisson-binomial / heterogeneous Bernoulli normal approximation)
        if 'Expected_Frequency' in df.columns:
            p = df['Expected_Frequency']
            variance = (p * (1.0 - p)).sum()
        else:
            variance = 0.0
            
        std_dev = np.sqrt(variance)
        z_score = (actual_claims - expected_claims) / std_dev if std_dev > 0 else 0.0
        
        # 4. Drift Score (Heuristic actuarial score 0-100)
        # Materiality + Statistical Confidence
        materiality_score = min(abs(relative_drift) / 0.20 * 50, 50.0)  # Capped at 50 points (20% drift is max)
        confidence_score = min(max(z_score, 0.0) / 3.0 * 50, 50.0)      # Capped at 50 points (3.0 z-score is max)
        drift_score = materiality_score + confidence_score if is_credible else 0.0
        
        # Trigger Condition (One-sided deterioration test: H1: AC > EC, i.e. Z >= threshold)
        requires_investigation = (
            relative_drift >= self.relative_drift_threshold and
            z_score >= self.z_score_threshold and
            is_credible
        )
        
        # 5. Experience Measures
        additional_claims = actual_claims - expected_claims
        positive_excess_claims = max(additional_claims, 0.0)
        
        return {
            "requires_investigation": bool(requires_investigation),
            "actual_frequency": float(actual_freq),
            "expected_frequency": float(expected_freq),
            "relative_drift": float(relative_drift),
            "z_score": float(z_score),
            "exposure": float(total_exposure),
            "drift_score": float(drift_score),
            "is_credible": bool(is_credible),
            "actual_claims": int(actual_claims),
            "expected_claims": float(expected_claims),
            "additional_claims": float(additional_claims),
            "positive_excess_claims": float(positive_excess_claims)
        }

    def run_segment_surveillance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Pre-Planner Segment Surveillance Gate for Frequency.
        Scans Product, Region, Age_Group, Gender, Distribution_Channel.
        Strictly excludes post-claim attributes.
        Uses one-sided Poisson-binomial normal approximation with dynamic BH FDR control.
        """
        import scipy.stats as stats
        from statistics_utils.multiple_testing import benjamini_hochberg
        
        if df.empty:
            return {"triggered": False}
            
        demographic_dimensions = ['Product', 'Region', 'Age_Group', 'Gender', 'Distribution_Channel']
        candidates = []
        
        # 1. Collect candidate segments that pass credibility checks (dynamic hypothesis family)
        for dim in demographic_dimensions:
            if dim not in df.columns:
                continue
                
            for val, group in df.groupby(dim):
                exposure = group['Exposure'].sum() if 'Exposure' in group.columns else float(len(group))
                if exposure < self.min_exposure:
                    continue
                    
                expected_claims = (group['Expected_Frequency'] * group['Exposure']).sum() if 'Exposure' in group.columns else group['Expected_Frequency'].sum()
                if expected_claims < self.min_expected_claims:
                    continue
                    
                actual_claims = group['Claim'].sum()
                actual_freq = actual_claims / exposure
                expected_freq = expected_claims / exposure
                drift = (actual_claims - expected_claims) / expected_claims if expected_claims > 0 else 0.0
                
                # Z-score using exact heterogeneous Bernoulli null variance (Case A / Poisson-binomial)
                variance = (group['Expected_Frequency'] * (1.0 - group['Expected_Frequency'])).sum()
                std_dev = np.sqrt(variance)
                z = (actual_claims - expected_claims) / std_dev if std_dev > 0 else 0.0
                
                # One-sided deterioration p-value: H0: AC <= EC vs H1: AC > EC
                p_val = float(1.0 - stats.norm.cdf(z))
                
                candidates.append({
                    "dimension": dim,
                    "segment": str(val),
                    "exposure": exposure,
                    "actual_claims": actual_claims,
                    "expected_claims": expected_claims,
                    "actual_frequency": actual_freq,
                    "expected_frequency": expected_freq,
                    "relative_drift": drift,
                    "z_score": z,
                    "raw_p_value": p_val,
                    "adjusted_p_value": 1.0,
                    "fdr_significant": False,
                    "hypothesis_rank": 0
                })
                
        m = len(candidates)
        if m == 0:
            return {"triggered": False}
            
        # 2. Pool p-values across family and apply BH multiple testing control
        p_vals = [c["raw_p_value"] for c in candidates]
        hyp_ids = list(range(m))
        bh_results = benjamini_hochberg(p_vals, hyp_ids, fdr_target=self.fdr_target)
        
        for idx, res in enumerate(bh_results):
            candidates[idx]["adjusted_p_value"] = res["adjusted_q_value"]
            candidates[idx]["fdr_significant"] = res["fdr_significant"]
            candidates[idx]["hypothesis_rank"] = res["bh_rank"]
            
        # 3. Filter to triggered segments
        triggered_segments = []
        for c in candidates:
            if c["relative_drift"] >= self.relative_drift_threshold and c["fdr_significant"]:
                triggered_segments.append({
                    "triggered": True,
                    "trigger_source": "segment_surveillance",
                    "trigger_dimension": c["dimension"],
                    "trigger_segment": c["segment"],
                    "segment_metrics": {
                        "exposure": float(c["exposure"]),
                        "actual_claims": int(c["actual_claims"]),
                        "expected_claims": float(c["expected_claims"]),
                        "actual_frequency": float(c["actual_frequency"]),
                        "expected_frequency": float(c["expected_frequency"]),
                        "relative_drift": float(c["relative_drift"]),
                        "z_score": float(c["z_score"]),
                        "raw_p_value": float(c["raw_p_value"]),
                        "adjusted_p_value": float(c["adjusted_p_value"]),
                        "fdr_significant": bool(c["fdr_significant"]),
                        "fdr_target": float(self.fdr_target),
                        "hypothesis_family_size": int(m),
                        "hypothesis_rank": int(c["hypothesis_rank"])
                    },
                    "trigger_reason": (
                        f"Demographic segment {c['dimension']}:{c['segment']} exhibits material "
                        f"frequency deterioration (relative drift = +{c['relative_drift']*100:.2f}%, "
                        f"q-value = {c['adjusted_p_value']:.4f})."
                    )
                })
                
        if triggered_segments:
            # Sort by Z-score descending to get the most statistically significant trigger
            triggered_segments.sort(key=lambda x: x["segment_metrics"]["z_score"], reverse=True)
            return triggered_segments[0]
            
        return {"triggered": False}

    def calculate_rolling_drift(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates rolling relative drift over time (Year/Month) using Ratio-of-Sums."""
        # Group by Year, Month
        grouped = df.groupby(['Year', 'Month']).agg(
            Exposure=('Exposure', 'sum'),
            Actual_Claims=('Claim', 'sum'),
            Expected_Claims=pd.NamedAgg(column='Expected_Frequency', aggfunc=lambda x: (x * df.loc[x.index, 'Exposure']).sum() if 'Exposure' in df.columns else x.sum())
        ).reset_index()
        
        # Calculate moving 3-month sums of actual claims, expected claims, and exposure
        rolling_actual = grouped['Actual_Claims'].rolling(window=3, min_periods=1).sum()
        rolling_expected = grouped['Expected_Claims'].rolling(window=3, min_periods=1).sum()
        rolling_exposure = grouped['Exposure'].rolling(window=3, min_periods=1).sum()
        
        # Correctly evaluate rolling frequencies and drift as ratio-of-sums
        grouped['Actual_Freq'] = grouped['Actual_Claims'] / grouped['Exposure']
        grouped['Expected_Freq'] = grouped['Expected_Claims'] / grouped['Exposure']
        
        rolling_obs_freq = rolling_actual / rolling_exposure
        rolling_exp_freq = rolling_expected / rolling_exposure
        
        grouped['Relative_Drift'] = (rolling_obs_freq - rolling_exp_freq) / rolling_exp_freq
        grouped['Trend'] = grouped['Relative_Drift']
        
        return grouped

    def get_historical_claim_profile(self, df: pd.DataFrame, current_year: int) -> Dict[str, Dict[str, float]]:
        """
        Calculates the historical baseline for claim attributes (e.g. what % of claims are Cancer).
        Only looks at records where Claim == 1 and Year < current_year.
        """
        history_df = df[(df['Year'] < current_year) & (df['Claim'] == 1)]
        
        if history_df.empty:
            return {"Claim_Category": {}, "Hospital_Type": {}, "Claim_Status": {}}
            
        total_historical_claims = len(history_df)
        
        disease_dist = (history_df['Claim_Category'].value_counts() / total_historical_claims).to_dict() if 'Claim_Category' in history_df.columns else {}
        hospital_dist = (history_df['Hospital_Type'].value_counts() / total_historical_claims).to_dict() if 'Hospital_Type' in history_df.columns else {}
        status_dist = (history_df['Claim_Status'].value_counts() / total_historical_claims).to_dict() if 'Claim_Status' in history_df.columns else {}
        
        return {
            "Claim_Category": disease_dist,
            "Hospital_Type": hospital_dist,
            "Claim_Status": status_dist
        }

# For backward compatibility with existing code during the refactor
def detect_drift(df: pd.DataFrame) -> Dict[str, Any]:
    engine = StatisticalAnalyticsEngine()
    return engine.calculate_metrics(df)
