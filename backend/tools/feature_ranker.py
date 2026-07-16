import pandas as pd
import numpy as np
import scipy.stats as stats
from typing import List, Dict, Any

class StatisticalFeatureRanker:
    """
    Evaluates portfolio segments to mathematically determine which dimension contributes 
    most to the observed frequency or severity drift. Used in Phase 1 of Investigation.
    """
    
    def __init__(self, min_exposure=100, min_claims=30):
        self.min_exposure = min_exposure
        self.min_claims = min_claims
        # Demographic features for Phase 1
        self.portfolio_features = ['Product', 'Age_Group', 'Region', 'Gender', 'Distribution_Channel', 'Plan_Type']

    def rank_portfolio_features(self, df: pd.DataFrame, features: List[str] = None) -> List[Dict[str, Any]]:
        """Rank features for Frequency drift."""
        if df.empty:
            return []
            
        features_to_use = features if features is not None else self.portfolio_features
        valid_features = [f for f in features_to_use if f in df.columns and df[f].nunique() > 1]
        
        total_exposure = df['Exposure'].sum() if 'Exposure' in df.columns else float(len(df))
        if total_exposure == 0:
            return []
            
        overall_actual_freq = df['Claim'].sum() / total_exposure
        overall_expected_freq = (df['Expected_Frequency'] * df['Exposure']).sum() / total_exposure if 'Expected_Frequency' in df.columns else 0.0
        overall_drift = overall_actual_freq - overall_expected_freq
        
        # Portfolio total positive excess claims for contribution share
        portfolio_expected_claims = (df['Expected_Frequency'] * df['Exposure']).sum() if 'Expected_Frequency' in df.columns else 0.0
        portfolio_actual_claims = df['Claim'].sum()
        portfolio_excess_claims = max(portfolio_actual_claims - portfolio_expected_claims, 0.0)
        if portfolio_excess_claims == 0:
            portfolio_excess_claims = 1.0 # prevent division by zero
            
        rankings = []
        
        for feature in valid_features:
            segments = df.groupby(feature)
            weighted_variance_sum = 0
            max_segment_drift = 0.0
            max_segment_name = None
            max_segment_z = 0.0
            max_segment_p = 1.0
            max_segment_excess = 0.0
            max_segment_pos_excess = 0.0
            max_segment_contrib = 0.0
            
            for name, group in segments:
                exposure = group['Exposure'].sum() if 'Exposure' in group.columns else float(len(group))
                if exposure < self.min_exposure:
                    continue
                    
                actual_f = group['Claim'].sum() / exposure
                expected_f = (group['Expected_Frequency'] * group['Exposure']).sum() / exposure if 'Expected_Frequency' in group.columns else 0.0
                segment_drift = actual_f - expected_f
                
                # Variance of drift from the mean drift (for backwards compatibility score)
                deviation_from_mean = abs(segment_drift - overall_drift)
                weighted_variance_sum += (exposure / total_exposure) * (deviation_from_mean ** 2)
                
                # Poisson-binomial standard deviation
                if 'Expected_Frequency' in group.columns:
                    p = group['Expected_Frequency']
                    variance = (p * (1.0 - p)).sum()
                else:
                    variance = 0.0
                std_dev = np.sqrt(variance)
                actual_claims = group['Claim'].sum()
                expected_claims = (group['Expected_Frequency'] * group['Exposure']).sum() if 'Expected_Frequency' in group.columns else 0.0
                z = (actual_claims - expected_claims) / std_dev if std_dev > 0 else 0.0
                p_val = float(1.0 - stats.norm.cdf(z))
                
                excess_claims = actual_claims - expected_claims
                pos_excess = max(excess_claims, 0.0)
                contrib_share = pos_excess / portfolio_excess_claims
                
                if abs(segment_drift) > abs(max_segment_drift):
                    max_segment_drift = segment_drift
                    max_segment_name = name
                    max_segment_z = z
                    max_segment_p = p_val
                    max_segment_excess = excess_claims
                    max_segment_pos_excess = pos_excess
                    max_segment_contrib = contrib_share
                    
            if max_segment_name is not None:
                # Expose both anomaly score (Z-score based) and contribution score (excess claims / contribution share)
                rankings.append({
                    "feature": feature,
                    "score": float(weighted_variance_sum), # Backwards compatibility
                    "anomaly_score": float(abs(max_segment_z)),
                    "contribution_score": float(max_segment_contrib),
                    "max_segment": str(max_segment_name),
                    "max_segment_drift": float(max_segment_drift),
                    "max_segment_z": float(max_segment_z),
                    "max_segment_p": float(max_segment_p),
                    "max_segment_excess": float(max_segment_excess),
                    "max_segment_pos_excess": float(max_segment_pos_excess),
                    "max_segment_contribution": float(max_segment_contrib)
                })
                
        # Sort by score descending for backwards compatibility
        rankings.sort(key=lambda x: x['score'], reverse=True)
        
        total_score = sum(r['score'] for r in rankings)
        
        for r in rankings:
            r['contribution'] = (r['score'] / total_score) if total_score > 0 else 0
            # Convert one-sided Z-score to confidence
            p_val = 1.0 - stats.norm.cdf(r['max_segment_z'])
            confidence = 1.0 - p_val
            r['confidence'] = float(confidence)
            
        return rankings

    def rank_severity_features(self, df: pd.DataFrame, total_portfolio_excess_cost: float) -> List[Dict[str, Any]]:
        """
        Rank features for Severity excess cost.
        Prioritizes splits that isolate the largest excess claim cost contributors.
        """
        # Filter to claims only
        if 'Claim' in df.columns:
            claims_df = df[df['Claim'] == 1]
        else:
            claims_df = df
            
        if claims_df.empty or len(claims_df) < self.min_claims:
            return []
            
        valid_features = [f for f in self.portfolio_features if f in claims_df.columns and claims_df[f].nunique() > 1]
        
        rankings = []
        
        for feature in valid_features:
            segments = claims_df.groupby(feature)
            feature_max_excess = 0.0
            feature_max_segment = None
            feature_max_drift = 0.0
            feature_max_t = 0.0
            feature_total_pos_excess = 0.0
            
            # Temporary store for sibling positive excess costs to calculate local contribution
            sibling_excess_costs = []
            
            for name, group in segments:
                claim_count = len(group)
                if claim_count < self.min_claims:
                    continue
                    
                obs_cost = group['Actual_Claim_Amount'].sum()
                exp_cost = group['Expected_Severity'].sum()
                excess = obs_cost - exp_cost
                pos_excess = max(excess, 0.0)
                feature_total_pos_excess += pos_excess
                
                sibling_excess_costs.append((name, excess, pos_excess, obs_cost, exp_cost, claim_count, group))
                
            if not sibling_excess_costs:
                continue
                
            # Find the segment with the largest excess cost
            for name, excess, pos_excess, obs_cost, exp_cost, claim_count, group in sibling_excess_costs:
                if excess > feature_max_excess:
                    feature_max_excess = excess
                    feature_max_segment = name
                    
                    obs_sev = obs_cost / claim_count
                    exp_sev = exp_cost / claim_count
                    feature_max_drift = (obs_sev - exp_sev) / exp_sev if exp_sev > 0 else 0.0
                    
                    # T-statistic approximation for speed in ranking
                    std_dev = group['Actual_Claim_Amount'].std()
                    if pd.isna(std_dev) or std_dev == 0:
                        std_dev = 100.0 # fallback
                    t_stat = (obs_sev - exp_sev) / (std_dev / np.sqrt(claim_count)) if claim_count > 0 else 0.0
                    feature_max_t = t_stat
                    
            if feature_max_segment is not None:
                # Score represents the proportion of positive portfolio excess cost isolated by this feature
                local_contrib = feature_max_excess / feature_total_pos_excess if feature_total_pos_excess > 0 else 0.0
                portfolio_contrib = feature_max_excess / total_portfolio_excess_cost if total_portfolio_excess_cost > 0 else 0.0
                
                rankings.append({
                    "feature": feature,
                    "score": float(feature_max_excess), # Score by absolute excess cost isolated
                    "max_segment": str(feature_max_segment),
                    "max_segment_drift": float(feature_max_drift),
                    "max_segment_t": float(abs(feature_max_t)),
                    "local_contribution": float(local_contrib),
                    "portfolio_contribution": float(portfolio_contrib)
                })
                
        # Sort by score descending
        rankings.sort(key=lambda x: x['score'], reverse=True)
        
        # Calculate confidence probability for each ranking using the T-distribution
        for r in rankings:
            t_val = r.get('max_segment_t', 0.0)
            p_value = 2 * (1 - stats.t.cdf(t_val, df=self.min_claims - 1))
            confidence = 1.0 - p_value
            r['confidence'] = float(confidence)
            
        return rankings

# Backward compatibility wrapper
def rank_features(df: pd.DataFrame, target_col: str = 'Claim', features: List[str] = None) -> List[Dict[str, Any]]:
    ranker = StatisticalFeatureRanker()
    return ranker.rank_portfolio_features(df, features)
