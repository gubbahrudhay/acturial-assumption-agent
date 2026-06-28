import pandas as pd
from typing import Tuple
from .contract_registry import registry

class ContractDetector:
    @staticmethod
    def detect(df: pd.DataFrame) -> str:
        columns = set(df.columns)
        
        has_exposure = "Exposure" in columns
        has_freq = "Expected_Frequency" in columns or "Claim" in columns
        has_claim_amount = "Claim_Amount" in columns
        has_severity = "Expected_Severity" in columns
        
        if has_exposure and has_freq and has_claim_amount and has_severity:
            return "Combined"
        elif has_claim_amount and (has_severity or not has_exposure):
            return "Severity"
        elif has_exposure and has_freq:
            return "Frequency"
        else:
            return "Unknown"
