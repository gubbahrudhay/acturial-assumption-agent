from typing import Dict, Any
import pandas as pd
from .schema.schema_validator import SchemaValidator
from .profiling.completeness import CompletenessProfiler
from .readiness.quality_score import QualityScoreCalculator
from .reports.report_generator import ReportGenerator

class DataReadinessValidator:
    def __init__(self, engine_context: Dict[str, Any]):
        self.engine_context = engine_context
        self.schema_version = engine_context.get("schema_version")
        self.contract_type = engine_context.get("dataset_type")

    def validate(self, df: pd.DataFrame) -> Dict[str, Any]:
        # 1. Schema Validation
        schema_validator = SchemaValidator(self.contract_type, self.schema_version)
        schema_results = schema_validator.validate(df)
        
        # 2. Profiling
        completeness_profiler = CompletenessProfiler()
        completeness_results = completeness_profiler.profile(df)
        
        # 3. Quality Score
        score_calculator = QualityScoreCalculator()
        quality_score = score_calculator.calculate(schema_results, completeness_results)
        
        # 4. Report Generation
        report_generator = ReportGenerator()
        report = report_generator.generate(
            schema_results=schema_results,
            completeness_results=completeness_results,
            quality_score=quality_score
        )
        
        return report
