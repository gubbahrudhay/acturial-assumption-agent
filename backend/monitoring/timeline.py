from typing import Dict, Any, List
from datetime import datetime

class TimelineEvent:
    def __init__(self, name: str, component: str):
        self.name = name
        self.component = component
        self.start_time = datetime.now()
        self.end_time = None
        self.status = "running"
        
    def complete(self, status: str = "success"):
        self.end_time = datetime.now()
        self.status = status
        
    def get_duration(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000 # ms
        return 0

class TimelineLogger:
    def __init__(self):
        self.events: List[TimelineEvent] = []
        
    def start_event(self, name: str, component: str) -> TimelineEvent:
        event = TimelineEvent(name, component)
        self.events.append(event)
        return event
        
    def get_timeline(self) -> List[Dict[str, Any]]:
        return [{
            "name": e.name,
            "component": e.component,
            "duration_ms": e.get_duration(),
            "status": e.status,
            "timestamp": e.start_time.isoformat()
        } for e in self.events]
