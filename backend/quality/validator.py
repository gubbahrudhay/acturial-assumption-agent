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
        self.rules = engine_context.get("business_rule_configuration", {}).get("rules", [])

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
        
        # --- Inject Custom Business Rules for Severity ---
        findings = report.setdefault("findings", {"critical": [], "errors": [], "warnings": [], "info": []})
        
        columns = set(df.columns)
        
        # Filter to claim records if Claim column exists, else entire df
        if 'Claim' in columns:
            claims_df = df[df['Claim'] == 1]
        else:
            claims_df = df
            
        # Check rule: claim_amount_positive
        if "claim_amount_positive" in self.rules and "Actual_Claim_Amount" in columns:
            invalid_claims = claims_df[claims_df["Actual_Claim_Amount"] < 0]
            if not invalid_claims.empty:
                findings["critical"].append(
                    f"Found {len(invalid_claims)} claim records with negative Actual_Claim_Amount values."
                )
                report["dataset_ready"] = False
                
        # Check rule: expected_severity_positive
        if "expected_severity_positive" in self.rules and "Expected_Severity" in columns:
            # Expected severity should be strictly positive for claims
            invalid_expected = claims_df[claims_df["Expected_Severity"] <= 0]
            if not invalid_expected.empty:
                findings["critical"].append(
                    f"Found {len(invalid_expected)} claim records with non-positive Expected_Severity values."
                )
                report["dataset_ready"] = False
                
        # Check rule: time_coverage_valid
        if "time_coverage_valid" in self.rules and "Year" in columns and "Month" in columns:
            num_months = len(df.groupby(["Year", "Month"]))
            if num_months < 6:
                findings["warnings"].append(
                    f"Time coverage is low: only {num_months} periods found. Trend analysis requires at least 6 periods."
                )
                
        # Missing values profile check
        if "Actual_Claim_Amount" in columns and "Expected_Severity" in columns:
            # Check if expected severity has missing values for actual claims
            null_exp_claims = claims_df["Expected_Severity"].isnull().sum()
            if null_exp_claims > 0:
                pct = (null_exp_claims / len(claims_df)) * 100 if len(claims_df) > 0 else 0
                findings["errors"].append(
                    f"Expected_Severity is missing on {pct:.1f}% ({null_exp_claims}) of actual claim records."
                )
                report["dataset_ready"] = False
                
            # Profile claim concentration
            total_cost = claims_df["Actual_Claim_Amount"].sum()
            if total_cost > 0:
                top_claim = claims_df["Actual_Claim_Amount"].max()
                pct_top = (top_claim / total_cost) * 100
                if pct_top > 25:
                    findings["warnings"].append(
                        f"High claim concentration: largest single claim explains {pct_top:.1f}% of total claims cost."
                    )
                    
        return report
