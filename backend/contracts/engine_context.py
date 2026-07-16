from typing import Dict, Any
import yaml
import os
import logging

logger = logging.getLogger(__name__)

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'system_config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

class EngineContextBuilder:
    @staticmethod
    def build(dataset_type: str, schema_version: str, recommended_engine: str) -> Dict[str, Any]:
        config = load_config()
        contexts = config.get("engine_contexts", {})
        
        logger.info(f"Building EngineContext for recommended_engine: {recommended_engine}")

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
        
        if recommended_engine in contexts:
            engine_conf = contexts[recommended_engine]
            context["investigation_configuration"] = engine_conf.get("investigation_configuration", {})
            context["business_rule_configuration"] = engine_conf.get("business_rule_configuration", {})
            context["statistical_configuration"] = engine_conf.get("statistical_configuration", {})
            context["planner_configuration"] = engine_conf.get("planner_configuration", {})
        else:
            logger.warning(f"No configuration found in system_config.yaml for engine: {recommended_engine}")

        return context
