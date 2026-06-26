import os
import json
from datetime import datetime
from typing import Dict, Any

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'decision_log.jsonl')

def log_investigation_run(state: Dict[str, Any]):
    """
    Appends an audit trail entry for the investigation run.
    """
    df_path = state.get("df_path", "")
    dataset = os.path.basename(df_path) if df_path else "Unknown"
    
    drift_info = state.get("drift_info", {})
    impact = state.get("business_impact", {})
    options = state.get("decision_options", [])
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dataset": dataset,
        "drift_detected": drift_info.get("drift_detected", False),
        "primary_driver": impact.get("largest_driver", "None"),
        "business_impact_level": impact.get("risk_level", "Low"),
        "options_generated": len(options),
        "planner_decisions_logged": len(state.get("planner_reasoning", []))
    }
    
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Failed to write decision log: {e}")
