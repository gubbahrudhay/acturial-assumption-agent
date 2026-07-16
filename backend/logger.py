import logging
import json
import uuid
import time
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "execution_id": getattr(record, "execution_id", "N/A"),
            "investigation_id": getattr(record, "investigation_id", "N/A"),
            "dataset": getattr(record, "dataset", "N/A"),
            "engine": getattr(record, "engine", "N/A"),
            "duration_ms": getattr(record, "duration_ms", "N/A"),
            "severity": getattr(record, "severity", "N/A"),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def get_logger(name="actuarial_agent"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    return logger

def get_execution_context():
    return {
        "execution_id": str(uuid.uuid4()),
        "investigation_id": "N/A",
        "dataset": "N/A",
        "engine": "FastAPI",
        "start_time": time.time()
    }
