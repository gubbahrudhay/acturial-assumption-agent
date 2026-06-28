from typing import Dict, Any

class ReportGenerator:
    def generate(self, schema_results: Dict[str, Any], completeness_results: Dict[str, Any], quality_score: Dict[str, int]) -> Dict[str, Any]:
        
        # Categorize findings
        critical_issues = schema_results.get("details", {}).get("critical", [])
        errors = []
        warnings = []
        info = []
        
        # Check completeness for errors/warnings
        missing_percentages = completeness_results.get("missing_percentages", {})
        for col, pct in missing_percentages.items():
            if pct > 10:
                errors.append(f"{col} is missing {pct:.1f}% of values.")
            elif pct > 0:
                warnings.append(f"{col} is missing {pct:.1f}% of values.")
        
        is_ready = len(critical_issues) == 0
        
        return {
            "dataset_ready": is_ready,
            "overall_score": quality_score["overall"],
            "component_scores": quality_score,
            "findings": {
                "critical": critical_issues,
                "errors": errors,
                "warnings": warnings,
                "info": info
            },
            "completeness": completeness_results
        }
