import pandas as pd
import numpy as np
import scipy.stats as stats
from typing import List, Dict, Any

class StatisticalFeatureRanker:
    """
    Evaluates portfolio segments to mathematically determine which dimension contributes 
    most to the observed frequency drift. Used in Phase 1 of Investigation.
    """
    
    def __init__(self, min_exposure=100):
        self.min_exposure = min_exposure
        # Only evaluate Phase 1 Portfolio Demographic Features
        self.portfolio_features = ['Product', 'Age_Group', 'Region', 'Gender', 'Distribution_Channel', 'Plan_Type']

    def rank_portfolio_features(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        if df.empty:
            return []
            
        valid_features = [f for f in self.portfolio_features if f in df.columns and df[f].nunique() > 1]
        
        total_exposure = df['Exposure'].sum()
        if total_exposure == 0:
            return []
            
        overall_actual_freq = df['Claim'].sum() / total_exposure
        overall_expected_freq = (df['Expected_Frequency'] * df['Exposure']).sum() / total_exposure
        overall_drift = overall_actual_freq - overall_expected_freq
        
        rankings = []
        
        for feature in valid_features:
            segments = df.groupby(feature)
            weighted_variance_sum = 0
            max_segment_drift = 0
            max_segment_name = None
            max_segment_z = 0
            
            for name, group in segments:
                exposure = group['Exposure'].sum()
                if exposure < self.min_exposure:
                    continue
                    
                actual_f = group['Claim'].sum() / exposure
                expected_f = (group['Expected_Frequency'] * group['Exposure']).sum() / exposure
                segment_drift = actual_f - expected_f
                
                # Variance of drift from the mean drift (how well this segment explains the total variance)
                deviation_from_mean = abs(segment_drift - overall_drift)
                weighted_variance_sum += (exposure / total_exposure) * (deviation_from_mean ** 2)
                
                if abs(segment_drift) > abs(max_segment_drift):
                    max_segment_drift = segment_drift
                    max_segment_name = name
                    
                    # Calculate true statistical Z-score for this segment
                    variance = (expected_f * (1 - expected_f)) / exposure if exposure > 0 else 0
                    std_dev = np.sqrt(variance)
                    max_segment_z = (actual_f - expected_f) / std_dev if std_dev > 0 else 0
                    
            if max_segment_name is not None:
                rankings.append({
                    "feature": feature,
                    "score": float(weighted_variance_sum),
                    "max_segment": str(max_segment_name),
                    "max_segment_drift": float(max_segment_drift),
                    "max_segment_z": float(abs(max_segment_z))
                })
                
        # Sort by score descending
        rankings.sort(key=lambda x: x['score'], reverse=True)
        
        total_score = sum(r['score'] for r in rankings)
        
        for r in rankings:
            r['contribution'] = (r['score'] / total_score) if total_score > 0 else 0
            # Convert Z-score to a confidence probability (using normal CDF)
            # p-value = 2 * (1 - CDF(|z|))
            # confidence = 1 - p-value
            p_value = 2 * (1 - stats.norm.cdf(r['max_segment_z']))
            confidence = 1.0 - p_value
            r['confidence'] = float(confidence)
            
        return rankings

# Backward compatibility wrapper
def rank_features(df: pd.DataFrame, target_col: str = 'Claim', features: List[str] = None) -> List[Dict[str, Any]]:
    ranker = StatisticalFeatureRanker()
    return ranker.rank_portfolio_features(df)
