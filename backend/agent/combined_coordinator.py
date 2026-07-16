import os
import uuid
import datetime
import pandas as pd
from typing import Dict, Any, List

from tools.drift_detector import StatisticalAnalyticsEngine as FrequencyEngine
from engines.severity_engine import SeverityAnalyticsEngine
from engines.combined_engine import CombinedAnalyticsEngine

class CombinedCoordinator:
    def __init__(self):
        self.comb_engine = CombinedAnalyticsEngine()

    def coordinate_investigation(self, df: pd.DataFrame, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coordinates Frequency, Severity, and Combined engine outputs,
        routes the appropriate investigation sub-paths, and merges evidence records.
        """
        latest_year = df['Year'].max() if 'Year' in df.columns else 2024
        df_latest = df[df['Year'] == latest_year] if 'Year' in df.columns else df
        
        # 1. Load context settings
        min_exp = state.get("engine_context", {}).get("investigation_configuration", {}).get("minimum_exposure", 500)
        min_exp_claims = state.get("engine_context", {}).get("investigation_configuration", {}).get("minimum_expected_claims", 10)
        fdr_t = state.get("engine_context", {}).get("investigation_configuration", {}).get("fdr_target", 0.05)
        drift_t = state.get("engine_context", {}).get("investigation_configuration", {}).get("drift_threshold", 0.05)
        
        # 2. Run Frequency Analytics & Surveillance
        freq_engine = FrequencyEngine(
            relative_drift_threshold=drift_t,
            min_exposure=min_exp,
            min_expected_claims=min_exp_claims,
            fdr_target=fdr_t
        )
        freq_metrics = freq_engine.calculate_metrics(df_latest)
        freq_surveillance = freq_engine.run_segment_surveillance(df_latest)
        
        # 3. Run Severity Analytics & Surveillance
        min_claims = state.get("engine_context", {}).get("investigation_configuration", {}).get("minimum_claims_for_investigation", 30)
        sev_engine = SeverityAnalyticsEngine(
            materiality_threshold=drift_t,
            minimum_claims=min_claims,
            fdr_target=fdr_t
        )
        # Severity engine expects claim-level data
        df_claims = df[df['Claim'] == 1]
        df_claims_latest = df_claims[df_claims['Year'] == latest_year] if 'Year' in df_claims.columns else df_claims
        
        sev_metrics = sev_engine.calculate_metrics(df_claims_latest)
        sev_surveillance = sev_engine.run_segment_surveillance(df_claims_latest)
        
        # 4. Run Combined Analytics & Cost Decomposition
        comb_metrics = self.comb_engine.calculate_metrics(df_latest)
        
        freq_triggered = freq_metrics.get("requires_investigation", False) or freq_surveillance.get("triggered", False)
        sev_triggered = sev_metrics.get("is_significant", False) or sev_surveillance.get("triggered", False)
        
        pattern = self.comb_engine.classify_pattern(comb_metrics, freq_triggered, sev_triggered)
        comb_metrics["deterioration_pattern"] = pattern
        
        # Run Combined Segment Surveillance/Ranking
        comb_segments = self.comb_engine.calculate_segment_metrics(df_latest, comb_metrics["positive_excess_cost"])
        
        # 5. Route Investigation
        # We determine what paths need deeper investigation based on the triggers
        investigation_paths = []
        if freq_triggered and sev_triggered:
            investigation_paths = ["Frequency", "Severity"]
            state["planner_notebook"].append({
                "observation": "Both Frequency and Severity engines triggered.",
                "hypothesis": "Aligned portfolio deterioration across both frequency and severity dimensions.",
                "decision": "Route to dual engine investigation paths."
            })
        elif freq_triggered:
            investigation_paths = ["Frequency"]
            state["planner_notebook"].append({
                "observation": "Frequency engine triggered.",
                "hypothesis": "Deterioration is driven by increased claim incidence.",
                "decision": "Route to Frequency-only investigation path."
            })
        elif sev_triggered:
            investigation_paths = ["Severity"]
            state["planner_notebook"].append({
                "observation": "Severity engine triggered.",
                "hypothesis": "Deterioration is driven by higher average claims cost.",
                "decision": "Route to Severity-only investigation path."
            })
        elif comb_metrics["excess_cost"] > 0.0:
            investigation_paths = ["Combined"]
            state["planner_notebook"].append({
                "observation": "Combined cost deterioration detected with no standalone engine triggers.",
                "hypothesis": "Deterioration is likely driven by claimant mix shift / interaction.",
                "decision": "Route to Combined interaction investigation path."
            })
        else:
            state["planner_notebook"].append({
                "observation": "No credible combined or standalone deterioration detected.",
                "hypothesis": "Portfolio experience runs within monitored tolerance.",
                "decision": "Conclude and stop monitoring cycle."
            })
            
        # Store metrics back in state for downstream consumption
        state["drift_metrics"] = comb_metrics
        state["freq_metrics"] = freq_metrics
        state["sev_metrics"] = sev_metrics
        state["freq_surveillance"] = freq_surveillance
        state["sev_surveillance"] = sev_surveillance
        state["comb_segments"] = comb_segments
        state["investigation_paths"] = investigation_paths
        
        return state

    def generate_normalized_evidence(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalized evidence records across Frequency, Severity, and Combined engines."""
        evidence_list = []
        timestamp = datetime.datetime.now().isoformat()
        
        # 1. Gather Frequency Evidence from Segment Surveillance
        freq_surv = state.get("freq_surveillance", {})
        if freq_surv.get("triggered"):
            # Check individual candidate tests in the surveillance metadata
            for idx, candidate in enumerate(freq_surv.get("segment_metrics", {}).get("candidates", [])):
                if candidate.get("fdr_significant"):
                    evidence_list.append({
                        "evidence_id": f"E-FREQ-{uuid.uuid4().hex[:6].upper()}",
                        "engine_source": "frequency",
                        "dimension": candidate["dimension"],
                        "segment": str(candidate["segment"]),
                        "metric_name": "Frequency Drift",
                        "observed_value": float(candidate["observed_rate"]),
                        "expected_value": float(candidate["expected_rate"]),
                        "oe_ratio": float(candidate["observed_rate"] / candidate["expected_rate"]) if candidate["expected_rate"] > 0 else 1.0,
                        "statistical_significance": True,
                        "adjusted_q_value": float(candidate.get("q_value", 0.05)),
                        "credibility_status": True,
                        "business_contribution": float(candidate.get("contribution_share", 0.0)),
                        "baseline_comparison": "Historical portfolio average",
                        "investigation_phase": "Phase 1 Surveillance",
                        "timestamp": timestamp,
                        "cross_engine_alignment": False
                    })
                    
        # 2. Gather Severity Evidence from Segment Surveillance
        sev_surv = state.get("sev_surveillance", {})
        if sev_surv.get("triggered"):
            for candidate in sev_surv.get("segment_metrics", {}).get("candidates", []):
                if candidate.get("fdr_significant"):
                    evidence_list.append({
                        "evidence_id": f"E-SEV-{uuid.uuid4().hex[:6].upper()}",
                        "engine_source": "severity",
                        "dimension": candidate["dimension"],
                        "segment": str(candidate["segment"]),
                        "metric_name": "Severity Drift",
                        "observed_value": float(candidate["observed_severity"]),
                        "expected_value": float(candidate["expected_severity"]),
                        "oe_ratio": float(candidate["oe_ratio"]),
                        "statistical_significance": True,
                        "adjusted_q_value": float(candidate.get("q_value", 0.05)),
                        "credibility_status": True,
                        "business_contribution": float(candidate.get("contribution_share", 0.0)),
                        "baseline_comparison": "Historical portfolio average",
                        "investigation_phase": "Phase 1 Surveillance",
                        "timestamp": timestamp,
                        "cross_engine_alignment": False
                    })
                    
        # 3. Gather Combined Evidence from Segment Rankings
        comb_segs = state.get("comb_segments", [])
        for seg in comb_segs[:5]: # Take top 5 contributing segments
            if seg["positive_excess_claim_cost"] > 0.0:
                evidence_list.append({
                    "evidence_id": f"E-COMB-{uuid.uuid4().hex[:6].upper()}",
                    "engine_source": "combined",
                    "dimension": seg["dimension"],
                    "segment": str(seg["segment"]),
                    "metric_name": "Combined Cost Variance",
                    "observed_value": float(seg["observed_claim_cost"]),
                    "expected_value": float(seg["expected_claim_cost"]),
                    "oe_ratio": float(seg["combined_oe"]),
                    "statistical_significance": False, # Combined is deterministic
                    "adjusted_q_value": None,
                    "credibility_status": True,
                    "business_contribution": float(seg["contribution_share"]),
                    "baseline_comparison": "Same-segment baseline",
                    "investigation_phase": "Phase 1 Drill-Down",
                    "timestamp": timestamp,
                    "cross_engine_alignment": False
                })

        # 4. Detect Cross-Engine Alignment
        # Match if both Frequency and Severity found a drift in the exact same segment
        freq_segments = {(e["dimension"], e["segment"]) for e in evidence_list if e["engine_source"] == "frequency"}
        sev_segments = {(e["dimension"], e["segment"]) for e in evidence_list if e["engine_source"] == "severity"}
        aligned_segments = freq_segments.intersection(sev_segments)
        
        for ev in evidence_list:
            if (ev["dimension"], ev["segment"]) in aligned_segments:
                ev["cross_engine_alignment"] = True

        return evidence_list
