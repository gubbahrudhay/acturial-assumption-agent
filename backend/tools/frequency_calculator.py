import pandas as pd
from typing import Dict, Any

def calculate_frequency(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculates the actual frequency (Claims / Exposure) and compares it with Expected Frequency.
    Returns metrics aggregated by Year and overall.
    """
    if df.empty:
        return {"error": "Empty dataframe"}
        
    total_claims = df['Claim'].sum()
    total_exposure = df['Exposure'].sum()
    actual_freq = total_claims / total_exposure if total_exposure > 0 else 0
    
    expected_claims = (df['Expected_Frequency'] * df['Exposure']).sum()
    expected_freq = expected_claims / total_exposure if total_exposure > 0 else 0
    
    # Year over year metrics
    yoy_metrics = []
    if 'Year' in df.columns:
        for year, group in df.groupby('Year'):
            claims = group['Claim'].sum()
            exposure = group['Exposure'].sum()
            exp_claims = (group['Expected_Frequency'] * group['Exposure']).sum()
            
            yoy_metrics.append({
                "year": int(year),
                "exposure": float(exposure),
                "actual_claims": int(claims),
                "expected_claims": float(exp_claims),
                "actual_freq": float(claims / exposure if exposure > 0 else 0),
                "expected_freq": float(exp_claims / exposure if exposure > 0 else 0)
            })
            
    return {
        "overall": {
            "exposure": float(total_exposure),
            "actual_claims": int(total_claims),
            "expected_claims": float(expected_claims),
            "actual_frequency": float(actual_freq),
            "expected_frequency": float(expected_freq),
        },
        "yearly": yoy_metrics
    }
