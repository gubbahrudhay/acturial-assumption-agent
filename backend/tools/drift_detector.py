import pandas as pd
import numpy as np
from typing import Dict, Any

class StatisticalAnalyticsEngine:
    """
    Layer 2: Statistical Analytics Engine.
    Performs purely deterministic actuarial calculations. No LLMs exist in this layer.
    """
    
    def __init__(self, relative_drift_threshold=0.05, min_exposure=500, z_score_threshold=1.96):
        self.relative_drift_threshold = relative_drift_threshold
        self.min_exposure = min_exposure
        self.z_score_threshold = z_score_threshold

    def calculate_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates foundational metrics (Frequency, Relative Drift, Credibility, Z-Score)."""
        if df.empty:
            return {"error": "Empty dataframe"}
            
        total_exposure = df['Exposure'].sum()
        actual_claims = df['Claim'].sum()
        expected_claims = (df['Expected_Frequency'] * df['Exposure']).sum()
        
        actual_freq = actual_claims / total_exposure if total_exposure > 0 else 0
        expected_freq = expected_claims / total_exposure if total_exposure > 0 else 0
        
        # 1. Relative Drift
        relative_drift = (actual_freq - expected_freq) / expected_freq if expected_freq > 0 else 0
        
        # 2. Credibility (Exposure check)
        is_credible = total_exposure >= self.min_exposure
        
        # 3. Z-Score (Statistical Confidence)
        variance = (expected_freq * (1 - expected_freq)) / total_exposure if total_exposure > 0 else 0
        std_dev = np.sqrt(variance)
        z_score = (actual_freq - expected_freq) / std_dev if std_dev > 0 else 0
        
        # 4. Drift Score (Heuristic actuarial score 0-100)
        # Materiality + Statistical Confidence
        materiality_score = min(abs(relative_drift) / 0.20 * 50, 50)  # Capped at 50 points (20% drift is max)
        confidence_score = min(abs(z_score) / 3.0 * 50, 50)           # Capped at 50 points (3.0 z-score is max)
        drift_score = materiality_score + confidence_score if is_credible else 0
        
        # Trigger Condition
        requires_investigation = (
            abs(relative_drift) >= self.relative_drift_threshold and
            abs(z_score) >= self.z_score_threshold and
            is_credible
        )
        
        return {
            "requires_investigation": bool(requires_investigation),
            "actual_frequency": float(actual_freq),
            "expected_frequency": float(expected_freq),
            "relative_drift": float(relative_drift),
            "z_score": float(z_score),
            "exposure": float(total_exposure),
            "drift_score": float(drift_score),
            "is_credible": bool(is_credible)
        }

    def calculate_rolling_drift(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates rolling relative drift over time (Year/Month)."""
        # Group by Year, Month
        grouped = df.groupby(['Year', 'Month']).agg(
            Exposure=('Exposure', 'sum'),
            Actual_Claims=('Claim', 'sum'),
            Expected_Claims=pd.NamedAgg(column='Expected_Frequency', aggfunc=lambda x: (x * df.loc[x.index, 'Exposure']).sum())
        ).reset_index()
        
        grouped['Actual_Freq'] = grouped['Actual_Claims'] / grouped['Exposure']
        grouped['Expected_Freq'] = grouped['Expected_Claims'] / grouped['Exposure']
        grouped['Relative_Drift'] = (grouped['Actual_Freq'] - grouped['Expected_Freq']) / grouped['Expected_Freq']
        
        # Calculate a simple trend line (Moving Average)
        grouped['Trend'] = grouped['Relative_Drift'].rolling(window=3, min_periods=1).mean()
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
