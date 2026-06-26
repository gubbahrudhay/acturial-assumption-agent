import pandas as pd
from typing import Dict, Any, List

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
            
    if len(report["issues"]) > 0:
        report["status"] = "warning"
        
    return report

if __name__ == "__main__":
    # Simple test
    import os
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'insurance_experience.csv')
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        print(validate_data(df))
