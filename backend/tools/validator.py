import pandas as pd
from typing import Dict, Any, List
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logger import get_logger
logger = get_logger()

def validate_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates the dataset for missing values, duplicate records, and invalid exposures.
    """
    report = {
        "status": "success",
        "total_records": len(df),
        "issues": []
    }
    
    # Check for missing values
    missing = df.isnull().sum()
    if missing.sum() > 0:
        missing_cols = missing[missing > 0].to_dict()
        report["issues"].append({
            "type": "missing_values",
            "details": missing_cols
        })
        
    # Check for duplicate policy/month combinations (assuming Exposure is 1 month per row)
    if 'Policy_ID' in df.columns and 'Year' in df.columns and 'Month' in df.columns:
        duplicates = df.duplicated(subset=['Policy_ID', 'Year', 'Month']).sum()
        if duplicates > 0:
            report["issues"].append({
                "type": "duplicate_records",
                "details": f"{duplicates} duplicate policy-month records found."
            })
            
    # Check for invalid exposures (e.g. negative or > 1)
    if 'Exposure' in df.columns:
        invalid_exposure = df[(df['Exposure'] <= 0) | (df['Exposure'] > 1)]
        if len(invalid_exposure) > 0:
            report["issues"].append({
                "type": "invalid_exposures",
                "details": f"{len(invalid_exposure)} records with exposure <= 0 or > 1 found."
            })
        
        # Check for non-unit exposures (Frequency v1 limitation)
        non_unit_exposure = df[(df['Exposure'] - 1.0).abs() > 1e-5]
        if len(non_unit_exposure) > 0:
            report["issues"].append({
                "type": "non_unit_exposures",
                "details": "Frequency v1 statistical model assumes unit policy-year Bernoulli exposure. Fractional or variable exposure requires a rate/count model."
            })
            
    if len(report["issues"]) > 0:
        report["status"] = "warning"
        
    return report

if __name__ == "__main__":
    # Simple test
    import os
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'insurance_experience.csv')
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        logger.info(validate_data(df))
