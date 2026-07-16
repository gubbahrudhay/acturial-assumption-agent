import numpy as np
import pandas as pd
from typing import Dict, Any, List

class CombinedAnalyticsEngine:
    def __init__(self, relative_drift_threshold: float = 0.05):
        self.relative_drift_threshold = relative_drift_threshold

    def calculate_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates portfolio-wide combined metrics and cost decomposition."""
        if df.empty:
            return {
                "expected_claims": 0.0,
                "actual_claims": 0,
                "exposure": 0.0,
                "expected_total_cost": 0.0,
                "observed_total_cost": 0.0,
                "expected_avg_severity": 0.0,
                "observed_avg_severity": 0.0,
                "combined_oe": 1.0,
                "combined_drift": 0.0,
                "excess_cost": 0.0,
                "positive_excess_cost": 0.0,
                "incidence_effect": 0.0,
                "severity_effect": 0.0,
                "mix_effect": 0.0
            }

        # Source variables
        exposure = df['Exposure'].sum() if 'Exposure' in df.columns else float(len(df))
        actual_claims = int(df['Claim'].sum())
        
        # Expected claims
        expected_claims = (df['Expected_Frequency'] * df['Exposure']).sum() if 'Expected_Frequency' in df.columns else df['Expected_Frequency'].sum()
        
        # Expected Total Claim Cost: SUM(Exposure_i * Expected_Frequency_i * Expected_Severity_i)
        if 'Expected_Severity' in df.columns:
            expected_total_cost = (df['Exposure'] * df['Expected_Frequency'] * df['Expected_Severity']).sum()
        else:
            expected_total_cost = 0.0
            
        observed_total_cost = df['Actual_Claim_Amount'].sum() if 'Actual_Claim_Amount' in df.columns else 0.0
        
        # Average severities
        expected_avg_severity = expected_total_cost / expected_claims if expected_claims > 0 else 0.0
        observed_avg_severity = observed_total_cost / actual_claims if actual_claims > 0 else 0.0
        
        # Combined Cost O/E
        combined_oe = observed_total_cost / expected_total_cost if expected_total_cost > 0 else 1.0
        combined_drift = combined_oe - 1.0
        
        # Excess Claim Cost
        excess_cost = observed_total_cost - expected_total_cost
        positive_excess_cost = max(excess_cost, 0.0)
        
        # Decomposition (Method B: Three-Factor Interaction-Isolated Bilinear Decomposition)
        incidence_effect = (actual_claims - expected_claims) * expected_avg_severity
        severity_effect = expected_claims * (observed_avg_severity - expected_avg_severity)
        mix_effect = (actual_claims - expected_claims) * (observed_avg_severity - expected_avg_severity)
        
        # Invariant check (float tolerance)
        total_change = observed_total_cost - expected_total_cost
        decomp_sum = incidence_effect + severity_effect + mix_effect
        assert abs(total_change - decomp_sum) < 1e-2, f"Decomposition does not reconcile! Total change: {total_change}, Sum: {decomp_sum}"

        return {
            "expected_claims": float(expected_claims),
            "actual_claims": int(actual_claims),
            "exposure": float(exposure),
            "expected_total_cost": float(expected_total_cost),
            "observed_total_cost": float(observed_total_cost),
            "expected_avg_severity": float(expected_avg_severity),
            "observed_avg_severity": float(observed_avg_severity),
            "combined_oe": float(combined_oe),
            "combined_drift": float(combined_drift),
            "excess_cost": float(excess_cost),
            "positive_excess_cost": float(positive_excess_cost),
            "incidence_effect": float(incidence_effect),
            "severity_effect": float(severity_effect),
            "mix_effect": float(mix_effect)
        }

    def calculate_segment_metrics(self, df: pd.DataFrame, portfolio_pec: float = 0.0) -> List[Dict[str, Any]]:
        """Calculates segment-level combined experience metrics across pre-claim dimensions."""
        pre_claim_dimensions = ['Product', 'Region', 'Age_Group', 'Gender', 'Distribution_Channel']
        segment_records = []
        
        for dim in pre_claim_dimensions:
            if dim not in df.columns:
                continue
                
            for val, group in df.groupby(dim):
                seg_metrics = self.calculate_metrics(group)
                
                # Calculate contribution share to portfolio PEC
                contribution_share = 0.0
                if portfolio_pec > 0.0 and seg_metrics["positive_excess_cost"] > 0.0:
                    contribution_share = seg_metrics["positive_excess_cost"] / portfolio_pec
                    
                # Calculate standalone frequency metrics for convenience
                freq_oe = seg_metrics["actual_claims"] / seg_metrics["expected_claims"] if seg_metrics["expected_claims"] > 0 else 1.0
                
                segment_records.append({
                    "dimension": dim,
                    "segment": str(val),
                    "exposure": seg_metrics["exposure"],
                    "expected_claims": seg_metrics["expected_claims"],
                    "actual_claims": seg_metrics["actual_claims"],
                    "frequency_oe": freq_oe,
                    "expected_claim_cost": seg_metrics["expected_total_cost"],
                    "observed_claim_cost": seg_metrics["observed_total_cost"],
                    "combined_oe": seg_metrics["combined_oe"],
                    "excess_claim_cost": seg_metrics["excess_cost"],
                    "positive_excess_claim_cost": seg_metrics["positive_excess_cost"],
                    "contribution_share": contribution_share
                })
                
        # Sort segment records by positive excess cost to bubble up key drivers
        segment_records.sort(key=lambda x: x["positive_excess_claim_cost"], reverse=True)
        return segment_records

    def classify_pattern(self, metrics: Dict[str, Any], freq_triggered: bool, sev_triggered: bool) -> str:
        """Deterministically classifies combined experience into a statistical deterioration pattern."""
        excess_cost = metrics.get("excess_cost", 0.0)
        
        if excess_cost <= 0.0:
            return "No Material Combined Deterioration"
            
        incidence_eff = metrics.get("incidence_effect", 0.0)
        severity_eff = metrics.get("severity_effect", 0.0)
        
        # Dual trigger case
        if freq_triggered and sev_triggered:
            return "Frequency and Severity Deterioration"
            
        # Standalone trigger cases
        if freq_triggered and not sev_triggered:
            if incidence_eff > severity_eff:
                return "Frequency-Led Deterioration"
            else:
                return "Mix / Interaction Deterioration"
                
        if sev_triggered and not freq_triggered:
            if severity_eff > incidence_eff:
                return "Severity-Led Deterioration"
            else:
                return "Mix / Interaction Deterioration"
                
        # Neither gate triggered portfolio-wide but excess cost exists
        return "Mix / Interaction Deterioration"
