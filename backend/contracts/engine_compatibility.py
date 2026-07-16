from typing import Dict, Any, List
import pandas as pd
import yaml
import os
import logging
from .contract_registry import registry

logger = logging.getLogger(__name__)

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'system_config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

class EngineCompatibility:
    @staticmethod
    def assess(df: pd.DataFrame, contract_type: str) -> Dict[str, Any]:
        columns = set(df.columns)
        config = load_config()
        capabilities = config.get("engine_capabilities", {})
        
        engines = list(capabilities.keys())
        supported = []
        not_supported = {}
        
        is_claim_level_only = False
        if "Claim" in columns:
            unique_claims = df["Claim"].dropna().unique()
            if len(unique_claims) == 1 and unique_claims[0] == 1:
                is_claim_level_only = True
                
        logger.info(f"Assessing compatibility for dataset. Claim-level only: {is_claim_level_only}")

        # Check requirements for each engine dynamically
        for engine_name, rules in capabilities.items():
            required_cols = rules.get("required_columns", [])
            required_engines = rules.get("required_engines", [])
            allow_claim_level = rules.get("allow_claim_level_only", True)
            
            # Check Column Dependencies
            has_cols = all(col in columns for col in required_cols)
            
            # Check Engine Dependencies (e.g. Combined requires Frequency and Severity)
            has_engines = all(eng in supported for eng in required_engines)
            
            # Check Row Constraints
            row_constraint_met = True
            if is_claim_level_only and not allow_claim_level:
                row_constraint_met = False
                
            if has_cols and has_engines and row_constraint_met:
                supported.append(engine_name)
            else:
                if not row_constraint_met:
                    not_supported[engine_name] = rules.get("claim_only_reason", "Row constraint failed")
                else:
                    not_supported[engine_name] = rules.get("missing_reason", "Missing components")

        logger.info(f"Compatibility assessment complete. Supported: {supported}, Not Supported: {not_supported}")

        # Recommendation logic
        recommended_engine = "Unknown"
        if contract_type in supported:
            recommended_engine = contract_type
        elif "Frequency" in supported:
            recommended_engine = "Frequency"
            
        # Build capability matrix for UI
        capability_matrix = []
        for eng in engines:
            if eng in supported:
                capability_matrix.append({
                    "Investigation": eng,
                    "Status": "Ready",
                    "Reason": "Required fields present"
                })
            else:
                capability_matrix.append({
                    "Investigation": eng,
                    "Status": "Not Ready",
                    "Reason": not_supported.get(eng, "Missing requirements")
                })

        return {
            "supported_engines": supported,
            "recommended_engine": recommended_engine,
            "capability_matrix": capability_matrix,
            "unsupported_reasons": not_supported
        }
