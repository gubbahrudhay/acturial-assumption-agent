import os
import yaml
import pandas as pd
import logging
from typing import Tuple
from .contract_registry import registry

logger = logging.getLogger(__name__)

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'system_config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

class ContractDetector:
    @staticmethod
    def detect(df: pd.DataFrame) -> str:
        columns = set(df.columns)
        config = load_config()
        contracts = config.get('dataset_contracts', {})
        
        is_claim_level_only = False
        if "Claim" in columns:
            unique_claims = df["Claim"].dropna().unique()
            if len(unique_claims) == 1 and unique_claims[0] == 1:
                is_claim_level_only = True

        logger.info(f"Detecting contract. Columns: {list(columns)}, Claim-level only: {is_claim_level_only}")

        # Evaluate Combined first, then Severity, then Frequency
        evaluation_order = ["Combined", "Severity", "Frequency"]
        
        for contract_name in evaluation_order:
            if contract_name not in contracts:
                continue
            
            rules = contracts[contract_name]
            required_cols = rules.get("required_columns", [])
            
            # Check column constraints
            has_all_cols = all(col in columns for col in required_cols)
            
            # Check row-level constraints
            allow_claim_level = rules.get("allow_claim_level_only", True)
            require_claim_level = rules.get("require_claim_level_only", False)
            
            row_constraint_met = True
            if is_claim_level_only and not allow_claim_level:
                row_constraint_met = False
            if require_claim_level and not is_claim_level_only:
                row_constraint_met = False
                
            if has_all_cols and row_constraint_met:
                logger.info(f"Successfully matched contract: {contract_name}")
                return contract_name

        logger.warning("No contract matched. Returning Unknown Contract.")
        return "Unknown Contract"
