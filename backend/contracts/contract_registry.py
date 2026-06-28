from typing import Dict, Any
from .dataset_contract import DatasetContract

class ContractRegistry:
    def __init__(self):
        self._contracts: Dict[str, DatasetContract] = {}
        self._supported_engines: Dict[str, list] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register("Frequency", "frequency_v1.yaml", ["Frequency"])
        self.register("Severity", "severity_v1.yaml", ["Severity"])
        self.register("Combined", "combined_v1.yaml", ["Frequency", "Severity", "Combined", "Loss Ratio"])

    def register(self, contract_type: str, schema_path: str, supported_engines: list):
        self._contracts[contract_type] = DatasetContract(contract_type, schema_path)
        self._supported_engines[contract_type] = supported_engines

    def get_contract(self, contract_type: str) -> DatasetContract:
        if contract_type not in self._contracts:
            raise ValueError(f"Unknown contract type: {contract_type}")
        return self._contracts[contract_type]

    def get_supported_engines(self, contract_type: str) -> list:
        return self._supported_engines.get(contract_type, [])

# Singleton instance
registry = ContractRegistry()
