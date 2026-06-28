from typing import Dict, Any
from datetime import datetime

class ExecutionContext:
    def __init__(self, execution_id: str, investigation_id: str, dataset_id: str, engine_context: Dict[str, Any]):
        self.execution_id = execution_id
        self.investigation_id = investigation_id
        self.dataset_id = dataset_id
        self.engine_context = engine_context
        self.start_time = datetime.now()
        self.end_time = None
        self.status = "running"
        self.timeline = []
        self.metrics = {}
        
    def complete(self):
        self.end_time = datetime.now()
        self.status = "completed"
        
    def get_duration(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
