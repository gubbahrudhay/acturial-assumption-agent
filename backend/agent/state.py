from typing import Dict, Any, List, TypedDict

class InvestigationState(TypedDict):
    """
    Central single source of truth for the entire AI Copilot application.
    All modules read and write exclusively through this object.
    """
    investigation_id: str
    df_path: str
    dataset_metadata: Dict[str, Any]
    api_key: str
    
    # Layer 2 Outputs
    drift_metrics: Dict[str, Any]
    historical_baseline: Dict[str, Any]
    
    # Layer 3 Outputs
    investigation_tree: Dict[str, Any]
    planner_notebook: List[Dict[str, Any]] # Stores Observation -> Hypothesis -> Tool -> Evidence -> Decision
    event_reconstruction: str
    business_impact: Dict[str, Any]
    decision_options: List[Dict[str, Any]]
    
    # Explainability & Metrics
    primary_root_cause: str
    explainability_report: Dict[str, Any]
    
    # UI / Presentation Context
    scenario_overrides: Dict[str, Any]
    chat_history: List[Any]
    final_report: str
    
    # Graph State
    investigation_status: str
    messages: List[Any]
