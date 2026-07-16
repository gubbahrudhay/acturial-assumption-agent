import pandas as pd
from typing import Any, Dict, List
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
import json
from agent.state import InvestigationState
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logger import get_logger
logger = get_logger()

class EventInference(BaseModel):
    inference: str = Field(description="A concise sentence inferring the likely real-world business event based on the evidence.")

def construct_event_inference_prompt(worst_segment: str, profile_shifts: list) -> str:
    evidence_text = f"Anomalous Demographic Segment: {worst_segment}\n\n"
    evidence_text += "Observed Shifts in Claim Profile compared to Historical Baseline:\n"
    
    for shift in profile_shifts:
        attr = shift.get("attribute")
        val = shift.get("value")
        hist = shift.get("historical_share", 0) * 100
        curr = shift.get("current_share", 0) * 100
        diff = shift.get("shift", 0) * 100
        if abs(diff) > 2.0:
            direction = "Increased" if diff > 0 else "Decreased"
            evidence_text += f"- {attr} ({val}): {direction} from {hist:.1f}% to {curr:.1f}% (Shift: {diff:+.1f}%)\n"
            
    prompt = f"""You are an expert Chief Actuary investigating unexpected drift in a health insurance portfolio.
Your goal is to infer the most likely underlying real-world business event that explains the observed statistical evidence.

EVIDENCE:
{evidence_text}

INSTRUCTIONS:
1. Review the anomalous demographic segment and the specific shifts in the claim profile.
2. Formulate a single, concise sentence inferring the likely real-world business event. 
3. You must use wording that indicates inference rather than certainty (e.g., "The observed experience is consistent with...", "The evidence suggests...").
4. Keep it highly professional and actuarial. Do not use conversational filler.

OUTPUT FORMAT:
Just the single inference sentence.
"""
    return prompt

def business_impact_node(state: InvestigationState) -> InvestigationState:
    """
    Calculates operational/financial business impact and matches against the knowledge base.
    """
    active_engine = state.get("engine_context", {}).get("active_engine", "Frequency")
    
    # Read worst segment path for pattern matching
    tree = state.get("investigation_tree", {})
    phase_2 = tree.get("phase_2", {}) if tree else {}
    worst_segment = phase_2.get("worst_segment", "Multiple") if phase_2 else "Multiple"
    
    # ---------------------------------------------------------
    # SEVERITY BUSINESS IMPACT WORKFLOW
    # ---------------------------------------------------------
    if active_engine == "Severity":
        metrics = state.get("drift_metrics", {})
        
        # Extract variables from drift_metrics (calculated by Severity Engine)
        expected_severity = metrics.get("expected_severity", 0.0)
        observed_severity = metrics.get("observed_severity", 0.0)
        relative_drift = metrics.get("relative_drift", 0.0)
        excess_cost = metrics.get("excess_cost", 0.0)
        claim_count = metrics.get("claim_count", 0)
        high_cost_share = metrics.get("high_cost_share", 0.0)
        
        # Risk classification based on absolute excess cost and drift materiality
        risk_level = "Low"
        if excess_cost >= 50000 or relative_drift >= 0.15:
            risk_level = "High"
        elif excess_cost >= 15000 or relative_drift >= 0.05:
            risk_level = "Medium"
            
        business_impact = {
            "expected_severity": float(expected_severity),
            "observed_severity": float(observed_severity),
            "drift_percentage": float(relative_drift), # Map to drift_percentage for UI compatibility
            "excess_cost": float(excess_cost),
            "additional_claims": int(round(excess_cost / expected_severity)) if expected_severity > 0 else 0, # compatibility
            "claim_count": int(claim_count),
            "high_cost_share": float(high_cost_share),
            "most_impacted_portfolio": worst_segment.replace("Root -> ", ""),
            "risk_level": risk_level
        }
        state["business_impact"] = business_impact
        
        # Log to planner notebook
        state["planner_notebook"].append({
            "observation": f"Calculated Severity business impact: Excess claim cost is {excess_cost:,.2f}, Risk Level: {risk_level}.",
            "hypothesis": "Searching Internal Actuarial Knowledge Base for historical precedents.",
            "decision": "Execute deterministic pattern matching on claim category and segment features."
        })
        
    # ---------------------------------------------------------
    # COMBINED BUSINESS IMPACT WORKFLOW
    # ---------------------------------------------------------
    elif active_engine == "Combined":
        metrics = state.get("drift_metrics", {})
        expected_cost = metrics.get("expected_total_cost", 0.0)
        observed_cost = metrics.get("observed_total_cost", 0.0)
        excess_cost = metrics.get("excess_cost", 0.0)
        combined_drift = metrics.get("combined_drift", 0.0)
        
        # Find worst segment from combined segments
        comb_segs = state.get("comb_segments", [])
        if comb_segs:
            worst_seg_rec = comb_segs[0]
            worst_segment = f"{worst_seg_rec['dimension']}:{worst_seg_rec['segment']}"
        else:
            worst_segment = "Multiple"
            
        risk_level = "Low"
        if excess_cost >= 100000 or combined_drift >= 0.10:
            risk_level = "High"
        elif excess_cost >= 30000 or combined_drift >= 0.05:
            risk_level = "Medium"
            
        business_impact = {
            "expected_claim_cost": float(expected_cost),
            "observed_claim_cost": float(observed_cost),
            "excess_claim_cost": float(excess_cost),
            "drift_percentage": float(combined_drift),
            "most_impacted_portfolio": worst_segment,
            "risk_level": risk_level,
            "incidence_effect": float(metrics.get("incidence_effect", 0.0)),
            "severity_effect": float(metrics.get("severity_effect", 0.0)),
            "mix_effect": float(metrics.get("mix_effect", 0.0)),
            "deterioration_pattern": metrics.get("deterioration_pattern", "Unknown")
        }
        state["business_impact"] = business_impact
        
        state["planner_notebook"].append({
            "observation": f"Calculated Combined business impact: Excess Claim Cost is {excess_cost:,.2f}, Risk Level: {risk_level}.",
            "hypothesis": "Searching Internal Actuarial Knowledge Base for historical precedents.",
            "decision": "Execute deterministic pattern matching on the primary contributing segment."
        })
        
    # ---------------------------------------------------------
    # FREQUENCY BUSINESS IMPACT WORKFLOW
    # ---------------------------------------------------------
    else:
        df = pd.read_csv(state["df_path"])
        latest_year = df['Year'].max() if 'Year' in df.columns else 2024
        df_latest = df[df['Year'] == latest_year] if 'Year' in df.columns else df
        
        total_exposure = df_latest['Exposure'].sum()
        if total_exposure == 0:
            return state
            
        overall_actual = df_latest['Claim'].sum()
        overall_expected = (df_latest['Expected_Frequency'] * df_latest['Exposure']).sum()
        
        overall_actual_freq = overall_actual / total_exposure
        overall_expected_freq = overall_expected / total_exposure
        
        drift_pct = (overall_actual_freq - overall_expected_freq) / overall_expected_freq if overall_expected_freq > 0 else 0
        additional_claims = overall_actual - overall_expected
        
        worst_segment = phase_2.get("worst_segment", "Multiple") if phase_2 else "Multiple"
        
        affected_exposure = 0
        if worst_segment != "Multiple":
            parts = worst_segment.split(" -> ")
            temp_df = df_latest.copy()
            for p in parts:
                if ":" in p:
                    key, val = p.split(":", 1)
                    if key in temp_df.columns:
                        temp_df = temp_df[temp_df[key] == val]
            affected_exposure = temp_df['Exposure'].sum()
            
        affected_policies_pct = affected_exposure / total_exposure if total_exposure > 0 else 0
        
        risk_level = "Low"
        if drift_pct > 0.10 or additional_claims > 150:
            risk_level = "High"
        elif drift_pct > 0.05 or additional_claims > 50:
            risk_level = "Medium"
            
        business_impact = {
            "expected_frequency": float(overall_expected_freq),
            "observed_frequency": float(overall_actual_freq),
            "drift_percentage": float(drift_pct),
            "additional_claims": int(round(additional_claims)),
            "affected_exposure": float(affected_exposure),
            "affected_policies_percentage": float(affected_policies_pct),
            "most_impacted_portfolio": worst_segment.replace("Root -> ", ""),
            "risk_level": risk_level
        }
        state["business_impact"] = business_impact
        
        state["planner_notebook"].append({
            "observation": f"Calculated business impact: {int(round(additional_claims))} unexpected claims, Risk Level: {risk_level}.",
            "hypothesis": "Searching Internal Actuarial Knowledge Base for historical precedents.",
            "decision": "Execute deterministic pattern matching."
        })
        
    # ---------------------------------------------------------
    # DETERMINISTIC KNOWLEDGE BASE PATTERN MATCHING
    # ---------------------------------------------------------
    event_reconstruction = "No matching historical precedent found in knowledge base."
    decision_options = []
    
    try:
        import os
        kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'actuarial_knowledge.json')
        if os.path.exists(kb_path):
            with open(kb_path, 'r') as f:
                kb = json.load(f)
                
            # Extract features from worst_segment and top shifts
            features = {}
            if worst_segment != "Multiple":
                for part in worst_segment.replace("Root -> ", "").split(" -> "):
                    if ":" in part:
                        k, v = part.split(":", 1)
                        # Translate 'Age_Group' key value or match it
                        features[k] = v
                        
            # Map segment values for robust pattern matching
            if 'Age_Group' in features and features['Age_Group'] == '60+':
                features['Age_Group'] = 'Senior'
            elif 'Age_Group' in features and features['Age_Group'] == '18-35':
                features['Age_Group'] = 'Young Adult'
                
            # Add top profile shifts to features (claims characteristics)
            tree = state.get("investigation_tree", {})
            phase_2 = tree.get("phase_2", {}) if tree else {}
            for shift in phase_2.get("profile_shifts", []):
                if shift.get("shift", 0.0) > 0.05: # Only consider material positive shifts
                    features[shift["attribute"]] = shift["value"]
                    
            # Match against KB catalog
            for event in kb.get("business_events", []):
                pattern = event.get("pattern", {})
                is_match = True
                for pk, pv in pattern.items():
                    if features.get(pk) != pv:
                        is_match = False
                        break
                        
                if is_match:
                    event_reconstruction = f"Historical Precedent Found: {event['event_name']}. {event['description']}"
                    
                    # Pre-populate decision options deterministically
                    for action in event.get("recommended_actions", []):
                        decision_options.append({
                            "possible_action": action,
                            "suggested_priority": event.get("risk_level", "Medium"),
                            "benefits": "Aligned with historical best practices.",
                            "risks": "Standard execution risks apply.",
                            "supporting_evidence": ["Matched internal knowledge base pattern."]
                        })
                    break # Stop on first match
    except Exception as e:
        logger.error(f"Error reading knowledge base: {e}")
        event_reconstruction = "Error reading internal knowledge base."
        
    state["event_reconstruction"] = event_reconstruction
    state["kb_decision_options"] = decision_options

    state["planner_notebook"].append({
        "observation": f"Event Reconstruction complete: {state['event_reconstruction']}",
        "hypothesis": "Investigation phase is fully concluded.",
        "decision": "Proceed to Decision Support."
    })
    
    state["messages"].append(SystemMessage(content="Business Impact Agent: Assessed impact and reconstructed latent event."))
    
    return state
