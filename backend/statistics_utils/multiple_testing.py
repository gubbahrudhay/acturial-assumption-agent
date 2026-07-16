import numpy as np
from typing import List, Dict, Any, Tuple

def benjamini_hochberg(p_values: List[float], hypothesis_ids: List[Any], fdr_target: float = 0.05) -> List[Dict[str, Any]]:
    """
    Engine-agnostic Benjamini-Hochberg (BH) False Discovery Rate (FDR) control procedure.
    
    Accepts:
        p_values: List of raw p-values.
        hypothesis_ids: List of identifiers for each hypothesis test.
        fdr_target: FDR target rate (q).
        
    Returns:
        A list of dictionaries with ranking, critical value, adjusted q-value, and significance flag.
    """
    M = len(p_values)
    if M == 0:
        return []
        
    # Sort hypotheses by raw p-value
    indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[indices]
    sorted_ids = np.array(hypothesis_ids)[indices]
    
    # Calculate BH critical values: (k / M) * q
    ranks = np.arange(1, M + 1)
    critical_values = (ranks / M) * fdr_target
    
    # Find the largest rank k where p_val <= critical_value
    significant_mask = sorted_p <= critical_values
    if np.any(significant_mask):
        max_sig_rank = ranks[significant_mask][-1]
    else:
        max_sig_rank = 0
        
    # Calculate adjusted q-values:
    # q_k = p_k * M / k, enforcing monotonicity from right to left: q_k = min(q_k, q_{k+1})
    raw_q = sorted_p * M / ranks
    adj_q = np.zeros(M)
    running_min = 1.0
    for k in range(M - 1, -1, -1):
        running_min = min(running_min, raw_q[k])
        adj_q[k] = min(running_min, 1.0)
        
    # Build results list
    results = [None] * M
    for rank_idx, sorted_idx in enumerate(indices):
        rank = rank_idx + 1
        results[sorted_idx] = {
            "hypothesis_id": hypothesis_ids[sorted_idx],
            "raw_p_value": float(p_values[sorted_idx]),
            "bh_rank": int(rank),
            "bh_critical_value": float((rank / M) * fdr_target),
            "adjusted_q_value": float(adj_q[rank_idx]),
            "fdr_significant": bool(rank <= max_sig_rank)
        }
        
    return results

def poisson_binomial_pmf(probabilities: List[float]) -> np.ndarray:
    """
    Computes the exact probability mass function (PMF) of the Poisson-binomial distribution
    (sum of independent heterogeneous Bernoulli trials) using dynamic programming.
    
    Time Complexity: O(N^2) where N is the number of trials. Useful as an audit oracle.
    """
    dist = np.array([1.0])
    for p in probabilities:
        new_dist = np.zeros(len(dist) + 1)
        new_dist[:-1] += dist * (1.0 - p)
        new_dist[1:] += dist * p
        dist = new_dist
    return dist

def poisson_binomial_tail(probabilities: List[float], observed_claims: int) -> float:
    """
    Calculates the exact one-sided upper tail probability P(S >= observed_claims)
    under the Poisson-binomial distribution.
    """
    if observed_claims <= 0:
        return 1.0
    N = len(probabilities)
    if observed_claims > N:
        return 0.0
        
    pmf = poisson_binomial_pmf(probabilities)
    return float(np.sum(pmf[observed_claims:]))
