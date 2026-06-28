from typing import Dict, Any

class EngineContextBuilder:
    @staticmethod
    def build(dataset_type: str, schema_version: str, recommended_engine: str) -> Dict[str, Any]:
        
        # Base config
        context = {
            "dataset_type": dataset_type,
            "schema_version": schema_version,
            "active_engine": recommended_engine,
            "investigation_configuration": {},
            "business_rule_configuration": {},
            "statistical_configuration": {},
            "planner_configuration": {}
        }
        
        if recommended_engine == "Frequency":
            context["investigation_configuration"] = {
                "drift_threshold": 0.05,
                "credibility_threshold": 0.8,
                "minimum_exposure": 100
            }
            context["business_rule_configuration"] = {
                "rules": ["exposure_positive", "frequency_bounds"]
            }
            context["statistical_configuration"] = {
                "tests": ["z_score", "chi_square"],
                "confidence_level": 0.95
            }
            context["planner_configuration"] = {
                "focus": "frequency",
                "goal": "Identify root causes of frequency drift"
            }
        elif recommended_engine == "Severity":
            context["investigation_configuration"] = {
                "severity_threshold": 0.1,
                "cost_threshold": 10000,
                "minimum_exposure": 50
            }
            context["business_rule_configuration"] = {
                "rules": ["claim_amount_positive"]
            }
            context["statistical_configuration"] = {
                "tests": ["t_test", "anova"],
                "confidence_level": 0.90
            }
            context["planner_configuration"] = {
                "focus": "severity",
                "goal": "Identify root causes of severity drift"
            }
        elif recommended_engine == "Combined":
            context["investigation_configuration"] = {
                "drift_threshold": 0.05,
                "credibility_threshold": 0.8,
                "minimum_exposure": 100
            }
            context["business_rule_configuration"] = {
                "rules": ["exposure_positive", "frequency_bounds", "claim_amount_positive"]
            }
            context["statistical_configuration"] = {
                "tests": ["z_score", "t_test"],
                "confidence_level": 0.95
            }
            context["planner_configuration"] = {
                "focus": "combined",
                "goal": "Identify root causes of frequency and severity drift"
            }

        return context
