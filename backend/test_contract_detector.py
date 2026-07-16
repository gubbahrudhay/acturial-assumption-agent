import unittest
import pandas as pd
from contracts.contract_detector import ContractDetector
from contracts.engine_compatibility import EngineCompatibility

class TestContractDetector(unittest.TestCase):
    def test_frequency_dataset(self):
        df = pd.DataFrame({
            "Exposure": [1.0, 0.5],
            "Expected_Frequency": [0.05, 0.1],
            "Claim": [0, 1],
            "Policy_ID": ["P1", "P2"]
        })
        contract = ContractDetector.detect(df)
        self.assertEqual(contract, "Frequency")
        
        compat = EngineCompatibility.assess(df, contract)
        self.assertIn("Frequency", compat["supported_engines"])
        self.assertNotIn("Severity", compat["supported_engines"])
        self.assertEqual(compat["recommended_engine"], "Frequency")

    def test_severity_dataset(self):
        df = pd.DataFrame({
            "Exposure": [1.0, 1.0],
            "Expected_Frequency": [0.05, 0.05],
            "Expected_Severity": [5000, 6000],
            "Actual_Claim_Amount": [5500, 6200],
            "Claim_ID": ["CLM1", "CLM2"],
            "Claim_Date": ["2026-01-01", "2026-01-02"],
            "Claim": [1, 1],
            "Premium": [200, 300]
        })
        contract = ContractDetector.detect(df)
        self.assertEqual(contract, "Severity")
        
        compat = EngineCompatibility.assess(df, contract)
        self.assertIn("Severity", compat["supported_engines"])
        self.assertNotIn("Frequency", compat["supported_engines"])
        self.assertEqual(compat["recommended_engine"], "Severity")

    def test_combined_dataset(self):
        df = pd.DataFrame({
            "Exposure": [1.0, 0.5, 1.0],
            "Expected_Frequency": [0.05, 0.1, 0.05],
            "Expected_Severity": [5000, 6000, 5000],
            "Actual_Claim_Amount": [0, 6200, 0],
            "Claim_ID": ["", "CLM2", ""],
            "Claim": [0, 1, 0],
            "Premium": [200, 300, 200]
        })
        contract = ContractDetector.detect(df)
        self.assertEqual(contract, "Combined")
        
        compat = EngineCompatibility.assess(df, contract)
        self.assertIn("Combined", compat["supported_engines"])
        self.assertIn("Frequency", compat["supported_engines"])
        self.assertIn("Severity", compat["supported_engines"])
        self.assertEqual(compat["recommended_engine"], "Combined")

    def test_unknown_dataset(self):
        df = pd.DataFrame({
            "Random_Col": [1, 2],
            "Another": ["A", "B"]
        })
        contract = ContractDetector.detect(df)
        self.assertEqual(contract, "Unknown Contract")

if __name__ == '__main__':
    unittest.main()
