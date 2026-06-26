import pandas as pd
from typing import Any
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
import json
from agent.state import InvestigationState

class EventInference(BaseModel):
    inference: str = Field(description="A concise sentence inferring the likely real-world business event based on the evidence.")

def construct_event_inference_prompt(worst_segment: str, profile_shifts: list) -> str:
    """Creates the prompt for the LLM to infer the underlying business event."""
    
    # Format the evidence
    evidence_text = f"Anomalous Demographic Segment: {worst_segment}\n\n"
    evidence_text += "Observed Shifts in Claim Profile compared to Historical Baseline:\n"
    
    for shift in profile_shifts:
        attr = shift.get("attribute")
        val = shift.get("value")
        hist = shift.get("historical_share", 0) * 100
        curr = shift.get("current_share", 0) * 100
        diff = shift.get("shift", 0) * 100
        if abs(diff) > 2.0: # Only highlight material shifts > 2%
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
    Calculates operational business impact and reconstructs the underlying business event using LLM inference.
    """
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
    
    # Analyze tree to get affected exposure
    tree = state.get("investigation_tree", {})
    phase_2 = tree.get("phase_2", {})
    worst_segment = phase_2.get("worst_segment", "Multiple")
    
    affected_exposure = 0
    if worst_segment != "Multiple":
        # Parse path to filter dataframe for affected exposure
        parts = worst_segment.split(" -> ")
        temp_df = df_latest.copy()
        for p in parts:
            if ":" in p:
                key, val = p.split(":", 1)
                if key in temp_df.columns:
                    temp_df = temp_df[temp_df[key] == val]
        affected_exposure = temp_df['Exposure'].sum()
        
    affected_policies_pct = affected_exposure / total_exposure if total_exposure > 0 else 0
    
    # Risk Level calculation based on materiality thresholds
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
    
    # ---------------------------------------------------------
    # Deterministic Knowledge Base Matching (No LLMs)
    # ---------------------------------------------------------
    state["planner_notebook"].append({
        "observation": f"Calculated business impact: {int(round(additional_claims))} unexpected claims, Risk Level: {risk_level}.",
        "hypothesis": "Searching Internal Actuarial Knowledge Base for historical precedents.",
        "decision": "Execute deterministic pattern matching."
    })
    
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
            # e.g. worst_segment = "Product:Family Plus -> Region:East"
            if worst_segment != "Multiple":
                for part in worst_segment.replace("Root -> ", "").split(" -> "):
                    if ":" in part:
                        k, v = part.split(":", 1)
                        features[k] = v
                        
            # Add top profile shifts to features
            for shift in phase_2.get("profile_shifts", []):
                if shift.get("shift", 0) > 0.05: # Only consider material positive shifts
                    features[shift["attribute"]] = shift["value"]
                    
            # Match against KB
            for event in kb.get("business_events", []):
                pattern = event.get("pattern", {})
                # Check if all keys in pattern match our features
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
        print(f"Error reading knowledge base: {e}")
        event_reconstruction = "Error reading internal knowledge base."
        
    state["event_reconstruction"] = event_reconstruction
    # Stash these so decision support can use them
    state["kb_decision_options"] = decision_options

    state["planner_notebook"].append({
        "observation": f"Event Reconstruction complete: {state['event_reconstruction']}",
        "hypothesis": "Investigation phase is fully concluded.",
        "decision": "Proceed to Decision Support."
    })
    
    state["messages"].append(SystemMessage(content=f"Business Impact Agent: Assessed impact and reconstructed latent event."))
    
    return state
