import pandas as pd
from typing import Dict, Any

class CompletenessProfiler:
    def profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        total_rows = len(df)
        total_columns = len(df.columns)
        
        missing_counts = df.isnull().sum().to_dict()
        missing_percentages = {col: (count / total_rows) * 100 if total_rows > 0 else 0 
                               for col, count in missing_counts.items()}
        
        duplicates = int(df.duplicated().sum())
        
        return {
            "total_rows": total_rows,
            "total_columns": total_columns,
            "missing_counts": missing_counts,
            "missing_percentages": missing_percentages,
            "duplicate_rows": duplicates
        }
