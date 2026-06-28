from typing import Dict, Any, List
import pandas as pd
from .contract_registry import registry

class EngineCompatibility:
    @staticmethod
    def assess(df: pd.DataFrame, contract_type: str) -> Dict[str, Any]:
        columns = set(df.columns)
        
        engines = ["Frequency", "Severity", "Combined", "Loss Ratio", "Reserve"]
        supported = []
        not_supported = {}
        
        # Check requirements for each engine
        if "Exposure" in columns and "Claim" in columns:
            supported.append("Frequency")
        else:
            not_supported["Frequency"] = "Missing Exposure or Claim"
            
        if "Claim_Amount" in columns:
            supported.append("Severity")
        else:
            not_supported["Severity"] = "Missing Claim Amount"
            
        if "Frequency" in supported and "Severity" in supported:
            supported.append("Combined")
        else:
            not_supported["Combined"] = "Missing Frequency or Severity components"
            
        if "Premium" in columns and "Claim_Amount" in columns:
            supported.append("Loss Ratio")
        else:
            not_supported["Loss Ratio"] = "Missing Premium or Claim Amount"
            
        if "Reserve_Amount" in columns:
            supported.append("Reserve")
        else:
            not_supported["Reserve"] = "Missing Reserve Fields"

        # Recommendation logic
        recommended = "Frequency" if "Frequency" in supported else supported[0] if supported else "None"
        if "Combined" in supported:
            recommended = "Combined"
        elif "Severity" in supported and "Frequency" not in supported:
            recommended = "Severity"
            
        capability_matrix = []
        for eng in engines:
            if eng in supported:
                capability_matrix.append({"Investigation": eng, "Status": "Ready", "Reason": "Required fields present"})
            else:
                capability_matrix.append({"Investigation": eng, "Status": "Not Ready", "Reason": not_supported.get(eng, "Missing requirements")})

        return {
            "supported_engines": supported,
            "recommended_engine": recommended,
            "capability_matrix": capability_matrix
        }
