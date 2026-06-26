import pandas as pd
from typing import Dict, Any, List
from .feature_ranker import rank_features

def recursive_investigate(df: pd.DataFrame, depth: int = 0, max_depth: int = 3, min_exposure: float = 100, current_path: str = "Root", planner_reasoning: List[str] = None) -> Dict[str, Any]:
    """
    Recursively investigates the dataframe to build an investigation tree.
    Stops when max depth is reached or segments become too small.
    """
    if planner_reasoning is None:
        planner_reasoning = []
        
    if df.empty or depth >= max_depth:
        return {"name": current_path, "status": "stopped", "reason": "Max depth or empty", "planner_reasoning": planner_reasoning}
        
    exposure = df['Exposure'].sum()
    if exposure < min_exposure:
        return {"name": current_path, "status": "stopped", "reason": "Insufficient exposure", "planner_reasoning": planner_reasoning}
        
    # Get overall segment drift
    actual_f = df['Claim'].sum() / exposure
    expected_f = (df['Expected_Frequency'] * df['Exposure']).sum() / exposure
    segment_drift = actual_f - expected_f
    
    node = {
        "name": current_path,
        "exposure": float(exposure),
        "actual_frequency": float(actual_f),
        "expected_frequency": float(expected_f),
        "drift": float(segment_drift),
        "children": [],
        "planner_reasoning": planner_reasoning
    }
    
    # Available features to split on
    available_features = ['Product', 'Age_Group', 'Region', 'Gender', 'Distribution_Channel', 'Plan_Type', 'Claim_Category', 'Hospital_Type']
    # If the feature is already in the current path, don't use it again
    available_features = [f for f in available_features if f not in current_path]
    
    if not available_features:
        return node
        
    rankings = rank_features(df, features=available_features)
    
    if not rankings:
        return node
        
    # Log planner reasoning
    reasoning_text = f"Evaluated for segment '{current_path}':\n"
    for r in rankings:
        reasoning_text += f"{r['feature']} (Score: {r['score']:.4f}, Contribution: {r.get('contribution', 0)*100:.1f}%, Confidence: {r.get('confidence', 0)*100:.1f}%)\n"
    
    best_feature = rankings[0]
    feature_name = best_feature['feature']
    
    reasoning_text += f"\n{feature_name} selected.\nReason: Highest contribution score."
    planner_reasoning.append(reasoning_text)
    
    # If the score is very low, it might not be worth splitting
    if best_feature['score'] < 1e-6:
        return node
        
    node["split_feature"] = feature_name
    node["confidence"] = best_feature.get('confidence', 0)
    node["contribution"] = best_feature.get('contribution', 0)
    
    # We only recursively investigate the worst segment(s) to keep the tree manageable,
    # or we can investigate all segments of this feature. Let's investigate all segments
    # but only if their exposure is above threshold.
    
    for segment_val, group in df.groupby(feature_name):
        child_path = f"{current_path} -> {feature_name}:{segment_val}"
        child_node = recursive_investigate(
            df=group,
            depth=depth + 1,
            max_depth=max_depth,
            min_exposure=min_exposure,
            current_path=child_path,
            planner_reasoning=planner_reasoning
        )
        if "exposure" in child_node: # Valid node
            node["children"].append(child_node)
            
    # Sort children by absolute drift to bubble up the most problematic ones
    node["children"].sort(key=lambda x: abs(x.get('drift', 0)), reverse=True)
    
    return node
