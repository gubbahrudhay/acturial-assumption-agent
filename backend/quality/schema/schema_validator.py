import pandas as pd
from typing import Dict, Any
from contracts.contract_registry import registry

class SchemaValidator:
    def __init__(self, contract_type: str, schema_version: str):
        self.contract_type = contract_type
        # Assume version matches the registry for now
        self.contract = registry.get_contract(contract_type)
        self.schema = self.contract.load_schema()

    def validate(self, df: pd.DataFrame) -> Dict[str, Any]:
        results = {
            "critical": [],
            "errors": [],
            "warnings": [],
            "info": []
        }
        
        required_cols = self.schema.get("required_columns", [])
        actual_cols = set(df.columns)
        
        missing = [col for col in required_cols if col not in actual_cols]
        if missing:
            results["critical"].append(f"Missing required columns: {missing}")
            
        return {
            "is_valid": len(results["critical"]) == 0,
            "details": results
        }
