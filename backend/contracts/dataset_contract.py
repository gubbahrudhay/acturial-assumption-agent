from typing import Dict, Any, List
import yaml
import os

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), '..', 'config', 'schemas')

class DatasetContract:
    def __init__(self, contract_type: str, schema_path: str):
        self.contract_type = contract_type
        self.schema_path = schema_path
        self._schema = None

    def load_schema(self) -> Dict[str, Any]:
        if self._schema is None:
            path = os.path.join(SCHEMA_DIR, self.schema_path)
            if not os.path.exists(path):
                raise FileNotFoundError(f"Schema not found for contract {self.contract_type}: {path}")
            with open(path, 'r') as f:
                self._schema = yaml.safe_load(f)
        return self._schema

    @property
    def required_columns(self) -> List[str]:
        return self.load_schema().get('required_columns', [])
