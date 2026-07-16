# Frequency Experience Engine — Formula Register

This document registers every mathematical and actuarial formula used in the Frequency Experience Engine (v1).

---

## 1. Expected Frequency (Individual Probability)
* **Mathematical Formula**:
  $$p_i = \text{logit}^{-1}(\text{logit}_i)$$
  $$\text{logit}_i = \text{intercept} + \beta_{\text{product}, i} + \beta_{\text{age}, i} + \beta_{\text{region}, i} + \beta_{\text{season}, i}$$
* **Purpose**: Computes expected pricing probability of claim for a given policyholder record before anomalies.
* **Numerator**: None
* **Denominator**: None
* **Unit**: Probability (decimal interval $[0, 1]$)
* **Population**: Individual policyholder record $i$
* **Time Basis**: Policyholder-month / policyholder-year
* **Weighting Method**: None
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: Base intercept is -2.94; seasonality bump is +0.15; Product, Age Group, and Region coefficients are additive on the log-odds (logit) scale.
* **Implementation File**: [generate_datasets.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/data/generate_datasets.py)
* **Implementation Function**: `calculate_expected_frequency`
* **Known Limitations**: **Under the current synthetic generator contract, Expected_Frequency represents a binary annual claim probability, NOT a general recurrent claim frequency rate.** The model generates at most one claim per policyholder per year (`Claim` $\in \{0,1\}$). Therefore, Expected_Frequency represents the probability of at least one claim, not the expected count of recurrent claims.

---

## 2. Expected Claims
* **Mathematical Formula**:
  $$\text{Expected Claims} = \sum_{i=1}^N (p_i \cdot w_i)$$
  where $w_i$ is individual policy exposure.
* **Purpose**: Estimates expected claim count for a cohort under the baseline pricing assumptions.
* **Numerator**: Sum of exposure-weighted expected individual claim probabilities
* **Denominator**: None
* **Unit**: Count of claims (float)
* **Population**: Cohort of $N$ policyholder records
* **Time Basis**: Cohort experience period (e.g. current year)
* **Weighting Method**: Exposure weighted
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: Claims are independent heterogeneous Bernoulli events.
* **Implementation File**: [drift_detector.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/drift_detector.py)
* **Implementation Function**: `calculate_metrics`
* **Known Limitations**: Assumes unit exposure ($w_i = 1.0$) for all records in the current synthetic configuration.

---

## 3. Actual Claims
* **Mathematical Formula**:
  $$\text{Actual Claims} = \sum_{i=1}^N \text{Claim}_i$$
* **Purpose**: Measures total observed claim count in a cohort.
* **Numerator**: Sum of binary claim indicators (where $\text{Claim}_i \in \{0, 1\}$)
* **Denominator**: None
* **Unit**: Count of claims (integer)
* **Population**: Cohort of $N$ policyholder records
* **Time Basis**: Cohort experience period
* **Weighting Method**: Unweighted sum
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: Claim indicators are Bernoulli trials.
* **Implementation File**: [drift_detector.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/drift_detector.py)
* **Implementation Function**: `calculate_metrics`
* **Known Limitations**: None.

---

## 4. Exposure
* **Mathematical Formula**:
  $$E = \sum_{i=1}^N w_i$$
* **Purpose**: Aggregates total exposure volume for a cohort.
* **Numerator**: Sum of policyholder exposure units ($w_i$)
* **Denominator**: None
* **Unit**: Policyholder-years (float)
* **Population**: Cohort of $N$ policyholder records
* **Time Basis**: Cohort experience period
* **Weighting Method**: None
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: Exposure represents earned policy-years.
* **Implementation File**: [drift_detector.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/drift_detector.py)
* **Implementation Function**: `calculate_metrics`
* **Known Limitations**: **Frequency v1 assumes unit policyholder exposure ($w_i = 1.0$) for all records. Fractional or variable exposure is not supported by the Z-test and will trigger compatibility warnings.**

---

## 5. Expected Frequency (Aggregate)
* **Mathematical Formula**:
  $$q_{\text{expected}} = \frac{\text{Expected Claims}}{E} = \frac{\sum_{i=1}^N p_i w_i}{\sum_{i=1}^N w_i}$$
* **Purpose**: Calculates the aggregate expected frequency rate for a cohort.
* **Numerator**: Expected claims
* **Denominator**: Exposure
* **Unit**: Rate (decimal fraction)
* **Population**: Cohort of $N$ policyholder records
* **Time Basis**: Cohort experience period
* **Weighting Method**: Exposure weighted
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: None.
* **Implementation File**: [drift_detector.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/drift_detector.py)
* **Implementation Function**: `calculate_metrics`
* **Known Limitations**: Reduces to simple mean of $p_i$ only when all exposure weights $w_i$ are identical.

---

## 6. Observed Frequency
* **Mathematical Formula**:
  $$q_{\text{observed}} = \frac{\text{Actual Claims}}{E} = \frac{\sum_{i=1}^N \text{Claim}_i}{\sum_{i=1}^N w_i}$$
* **Purpose**: Calculates the aggregate actual frequency rate for a cohort.
* **Numerator**: Actual claims
* **Denominator**: Exposure
* **Unit**: Rate (decimal fraction)
* **Population**: Cohort of $N$ policyholder records
* **Time Basis**: Cohort experience period
* **Weighting Method**: Exposure weighted
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: None.
* **Implementation File**: [drift_detector.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/drift_detector.py)
* **Implementation Function**: `calculate_metrics`
* **Known Limitations**: Requires unit exposure for exact Bernoulli interpretation.

---

## 7. Frequency O/E Ratio
* **Mathematical Formula**:
  $$\text{Frequency O/E} = \frac{\text{Actual Claims}}{\text{Expected Claims}} = \frac{\sum \text{Claim}_i}{\sum (p_i w_i)}$$
* **Purpose**: Measures Observed-to-Expected claim ratio as a key actuarial experience indicator.
* **Numerator**: Actual claims
* **Denominator**: Expected claims
* **Unit**: Ratio (float)
* **Population**: Cohort of $N$ policyholder records
* **Time Basis**: Cohort experience period
* **Weighting Method**: Ratio-of-sums
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: Expected claims $> 0$.
* **Implementation File**: [drift_detector.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/drift_detector.py)
* **Implementation Function**: `calculate_metrics`
* **Known Limitations**: Prone to high volatility in small cohorts.

---

## 8. Relative Frequency Drift
* **Mathematical Formula**:
  $$\text{Relative Drift} = \frac{q_{\text{observed}} - q_{\text{expected}}}{q_{\text{expected}}}$$
* **Purpose**: Quantifies percentage deviation of actual frequency from baseline assumptions.
* **Numerator**: $q_{\text{observed}} - q_{\text{expected}}$
* **Denominator**: $q_{\text{expected}}$
* **Unit**: Percentage / decimal fraction
* **Population**: Cohort of $N$ policyholder records
* **Time Basis**: Cohort experience period
* **Weighting Method**: Exposure weighted
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: Expected frequency $> 0$.
* **Implementation File**: [drift_detector.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/drift_detector.py)
* **Implementation Function**: `calculate_metrics`
* **Known Limitations**: Evaluates to $\text{Frequency O/E} - 1.00$ under the same exposure basis.

---

## 9. Absolute Frequency Drift
* **Mathematical Formula**:
  $$\text{Absolute Drift} = q_{\text{observed}} - q_{\text{expected}}$$
* **Purpose**: Measures the raw rate difference between observed and expected frequencies.
* **Numerator**: $q_{\text{observed}} - q_{\text{expected}}$
* **Denominator**: None
* **Unit**: Rate difference (decimal fraction)
* **Population**: Cohort of $N$ policyholder records
* **Time Basis**: Cohort experience period
* **Weighting Method**: Exposure weighted
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: None.
* **Implementation File**: None (derived from aggregate metrics)
* **Implementation Function**: None
* **Known Limitations**: Does not scale with the size of baseline rates.

---

## 10. Additional Claims
* **Mathematical Formula**:
  $$\text{Additional Claims} = \text{Actual Claims} - \text{Expected Claims} = \sum \text{Claim}_i - \sum (p_i w_i)$$
* **Purpose**: Calculates signed count of claims above (or below) expected baseline assumptions.
* **Numerator**: None
* **Denominator**: None
* **Unit**: Count of claims (float, signed)
* **Population**: Cohort of $N$ policyholder records
* **Time Basis**: Cohort experience period
* **Weighting Method**: None
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: None.
* **Implementation File**: [drift_detector.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/drift_detector.py)
* **Implementation Function**: `calculate_metrics`
* **Known Limitations**: Allows negative values when actual claims are fewer than expected.

---

## 11. Positive Excess Claims
* **Mathematical Formula**:
  $$\text{Positive Excess Claims} = \max(\text{Actual Claims} - \text{Expected Claims}, 0.0)$$
* **Purpose**: Calculates adverse deviation claim count for risk reporting and prioritizations.
* **Numerator**: None
* **Denominator**: None
* **Unit**: Count of claims (float, non-negative)
* **Population**: Cohort of $N$ policyholder records
* **Time Basis**: Cohort experience period
* **Weighting Method**: Clipped at 0
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: None.
* **Implementation File**: [drift_detector.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/drift_detector.py)
* **Implementation Function**: `calculate_metrics`
* **Known Limitations**: Ignores favorable deviations.

---

## 12. Poisson-Binomial Normal Approximation Z-Score
* **Mathematical Formula**:
  $$Z = \frac{\text{Actual Claims} - \text{Expected Claims}}{\sqrt{\sum_{i=1}^N w_i^2 p_i (1-p_i)}}$$
  *(Under the unit exposure contract $w_i = 1.0$, this corresponds to Case A)*:
  $$Z = \frac{AC - EC}{\sqrt{\sum_{i=1}^N p_i (1-p_i)}}$$
* **Purpose**: Measures statistical significance of claims deviation using exact Bernoulli null variance.
* **Numerator**: $\text{Actual Claims} - \text{Expected Claims}$
* **Denominator**: $\sqrt{\sum p_i (1-p_i)}$ (Standard deviation of heterogeneous Bernoulli sum)
* **Unit**: Standardized score (float)
* **Population**: Cohort of $N$ policyholder records
* **Time Basis**: Cohort experience period
* **Weighting Method**: Variance aggregation
* **Null Hypothesis**: $H_0: \text{Actual Claims} \le \text{Expected Claims}$
* **Alternative Hypothesis**: $H_1: \text{Actual Claims} > \text{Expected Claims}$ (One-sided upward drift)
* **Assumptions**: Claim occurrences are independent random variables conditional on $p_i$. The number of policies is large enough that the normal approximation to the Poisson-binomial distribution holds.
* **Implementation File**: [drift_detector.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/drift_detector.py)
* **Implementation Function**: `calculate_metrics`
* **Known Limitations**: Underestimates tail probabilities when sample sizes are small or probabilities are highly skewed.

---

## 13. Z-Test One-Sided P-Value
* **Mathematical Formula**:
  $$p\text{-value} = 1 - \Phi(Z)$$
  where $\Phi$ is the standard normal cumulative distribution function.
* **Purpose**: Calculates the probability of observing a claim count at least as extreme under the null hypothesis.
* **Numerator**: None
* **Denominator**: None
* **Unit**: Probability (decimal fraction $[0, 1]$)
* **Population**: Cohort of $N$ policyholder records
* **Time Basis**: Cohort experience period
* **Weighting Method**: None
* **Null Hypothesis**: $H_0: \text{Actual Claims} \le \text{Expected Claims}$
* **Alternative Hypothesis**: $H_1: \text{Actual Claims} > \text{Expected Claims}$
* **Assumptions**: Standard normal distribution of $Z$ under the null.
* **Implementation File**: [drift_detector.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/drift_detector.py)
* **Implementation Function**: `calculate_metrics`
* **Known Limitations**: Normal tail approximation is less reliable at the far extremes.

---

## 14. Credibility
* **Mathematical Formula**:
  $$\text{Is Credible} = (E \ge \text{min\_exposure}) \land (\text{Expected Claims} \ge \text{min\_expected\_claims})$$
* **Purpose**: Filters out small or volatile cohorts to prevent false alarms.
* **Numerator**: None
* **Denominator**: None
* **Unit**: Boolean
* **Population**: Cohort of $N$ policyholder records
* **Time Basis**: Cohort experience period
* **Weighting Method**: Logical conjunction
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: Base defaults are $\text{min\_exposure} = 500$ and $\text{min\_expected\_claims} = 10$ (empirically calibrated).
* **Implementation File**: [drift_detector.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/drift_detector.py)
* **Implementation Function**: `calculate_metrics`
* **Known Limitations**: Does not implement fractional credibility weights.

---

## 15. Drift Score
* **Mathematical Formula**:
  $$\text{Drift Score} = \text{Materiality Score} + \text{Confidence Score}$$
  $$\text{Materiality Score} = \min\left(\frac{|\text{Relative Drift}|}{0.20} \times 50, 50.0\right)$$
  $$\text{Confidence Score} = \min\left(\frac{Z}{3.0} \times 50, 50.0\right) \quad (\text{for } Z > 0)$$
* **Purpose**: Provides a standardized actuarial heuristic score from $0$ to $100$.
* **Numerator**: None
* **Denominator**: None
* **Unit**: Index score (float $[0, 100]$)
* **Population**: Cohort of $N$ policyholder records
* **Time Basis**: Cohort experience period
* **Weighting Method**: None
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: Drift score is set to 0 if the segment is not credible.
* **Implementation File**: [drift_detector.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/drift_detector.py)
* **Implementation Function**: `calculate_metrics`
* **Known Limitations**: Simple linear interpolation of drift and Z-score.

---

## 16. Segment Contribution Share
* **Mathematical Formula**:
  $$\text{Contribution Share}_k = \frac{\text{Positive Excess Claims}_k}{\text{Total Portfolio Positive Excess Claims}}$$
* **Purpose**: Measures the proportion of overall portfolio adverse claims deviation isolated by segment $k$.
* **Numerator**: $\text{Positive Excess Claims}_k$
* **Denominator**: $\sum \text{Positive Excess Claims}_{\text{portfolio}}$
* **Unit**: Share percentage (decimal fraction)
* **Population**: Demographic segment $k$ vs. total portfolio
* **Time Basis**: Cohort experience period
* **Weighting Method**: Slicing proportion
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: Total positive excess claims $> 0$.
* **Implementation File**: [feature_ranker.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/feature_ranker.py)
* **Implementation Function**: `rank_portfolio_features`
* **Known Limitations**: Ignores dimensions with negative deviations.

---

## 17. Feature Anomaly Score (Ranking)
* **Mathematical Formula**:
  $$\text{Feature Anomaly Score} = \max_{v \in \text{values}} |Z_v|$$
  where $Z_v$ is the Poisson-binomial Z-score of segment value $v$ for that feature.
* **Purpose**: Identifies the demographic feature that exhibits the most statistically anomalous segment.
* **Numerator**: None
* **Denominator**: None
* **Unit**: Absolute Z-score (float)
* **Population**: Feature dimensions
* **Time Basis**: Cohort experience period
* **Weighting Method**: Max value extraction
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: None.
* **Implementation File**: [feature_ranker.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/feature_ranker.py)
* **Implementation Function**: `rank_portfolio_features`
* **Known Limitations**: Measures pure statistical abnormality, independent of cohort volume.

---

## 18. Feature Contribution Score (Ranking)
* **Mathematical Formula**:
  $$\text{Feature Contribution Score} = \max_{v} \text{Contribution Share}_v$$
* **Purpose**: Identifies the demographic feature that contains the largest business driver of excess claims.
* **Numerator**: None
* **Denominator**: None
* **Unit**: Share fraction (float $[0, 1]$)
* **Population**: Feature dimensions
* **Time Basis**: Cohort experience period
* **Weighting Method**: Max value extraction
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: None.
* **Implementation File**: [feature_ranker.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/feature_ranker.py)
* **Implementation Function**: `rank_portfolio_features`
* **Known Limitations**: Does not measure statistical significance.

---

## 19. Frequency Segment Surveillance Gate Trigger & FDR Control
* **Mathematical Formula**:
  - For each candidate segment in coarse demographic dimensions $d \in \{\text{Product}, \text{Region}, \text{Age\_Group}, \text{Gender}, \text{Distribution\_Channel}\}$ that passes eligibility checks:
    - Compute observed O/E and relative drift.
    - Calculate Poisson-binomial Z-score and raw one-sided p-value $p = 1 - \Phi(Z)$.
  - Pool all eligible raw p-values as a family of size $M$.
  - Apply the Benjamini-Hochberg procedure at $q = 0.05$ to find FDR-significant segments.
  - A segment triggers if:
    - Eligible: passes minimum exposure and minimum expected claims.
    - Material: $\text{Relative Drift} \ge \text{materiality\_threshold}$ (default: 5%).
    - FDR Significant: $q\text{-value} \le 0.05$.
* **Purpose**: Bypasses the portfolio-level investigation gate to identify material local demographic deterioration before the AI Planner runs, while controlling the False Discovery Rate.
* **Numerator**: None
* **Denominator**: None
* **Unit**: Boolean
* **Population**: Pools all eligible demographic segments $M$
* **Time Basis**: Cohort experience period
* **Weighting Method**: Multiple testing FDR control
* **Null Hypothesis**: $H_{0, k}: \text{Actual Claims}_k \le \text{Expected Claims}_k$
* **Alternative Hypothesis**: $H_{1, k}: \text{Actual Claims}_k > \text{Expected Claims}_k$
* **Assumptions**: Dynamic hypothesis family size $M$.
* **Implementation File**: [drift_detector.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/drift_detector.py)
* **Implementation Function**: `run_segment_surveillance`
* **Known Limitations**: Dependent hypothesis family under demographic overlaps.

---

## 20. Portfolio Trigger Gate
* **Mathematical Formula**:
  $$\text{Portfolio Trigger} = (\text{Relative Drift} \ge \text{materiality\_threshold}) \land (Z \ge \text{significance\_threshold}) \land (\text{Is Credible})$$
* **Purpose**: Deterministically checks if the overall portfolio experience exhibits material and significant adverse drift.
* **Numerator**: None
* **Denominator**: None
* **Unit**: Boolean
* **Population**: Whole portfolio
* **Time Basis**: Current period vs. expected model
* **Weighting Method**: None
* **Null Hypothesis**: $H_0: \text{Actual Claims} \le \text{Expected Claims}$
* **Alternative Hypothesis**: $H_1: \text{Actual Claims} > \text{Expected Claims}$
* **Assumptions**: Significance threshold corresponds to Z-score limit (e.g. 1.645 for 95% one-sided confidence).
* **Implementation File**: [drift_detector.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/drift_detector.py)
* **Implementation Function**: `calculate_metrics`
* **Known Limitations**: Prone to portfolio masking under localized drifts.

---

## 21. Rolling Observed Frequency
* **Mathematical Formula**:
  $$\text{Rolling Observed Frequency}_m = \frac{\sum_{j=m-2}^m \text{Actual Claims}_j}{\sum_{j=m-2}^m \text{Exposure}_j}$$
* **Purpose**: Smooths monthly actual frequency rate over a 3-month rolling window.
* **Numerator**: Rolling 3-month sum of actual claims
* **Denominator**: Rolling 3-month sum of exposure
* **Unit**: Rate (decimal fraction)
* **Population**: Cohort of claims
* **Time Basis**: 3-month moving window
* **Weighting Method**: Ratio-of-sums
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: Exposure $> 0$.
* **Implementation File**: [drift_detector.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/drift_detector.py)
* **Implementation Function**: `calculate_rolling_drift`
* **Known Limitations**: Min periods = 1 at start boundaries.

---

## 22. Rolling Expected Frequency
* **Mathematical Formula**:
  $$\text{Rolling Expected Frequency}_m = \frac{\sum_{j=m-2}^m \text{Expected Claims}_j}{\sum_{j=m-2}^m \text{Exposure}_j}$$
* **Purpose**: Smooths monthly expected frequency rate over a 3-month rolling window.
* **Numerator**: Rolling 3-month sum of expected claims
* **Denominator**: Rolling 3-month sum of exposure
* **Unit**: Rate (decimal fraction)
* **Population**: Cohort of claims
* **Time Basis**: 3-month moving window
* **Weighting Method**: Ratio-of-sums
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: Exposure $> 0$.
* **Implementation File**: [drift_detector.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/drift_detector.py)
* **Implementation Function**: `calculate_rolling_drift`
* **Known Limitations**: Min periods = 1 at start boundaries.

---

## 23. Rolling Relative Drift
* **Mathematical Formula**:
  $$\text{Rolling Drift}_m = \frac{\text{Rolling Observed Frequency}_m - \text{Rolling Expected Frequency}_m}{\text{Rolling Expected Frequency}_m}$$
* **Purpose**: Calculates smoothed relative drift over a 3-month moving window.
* **Numerator**: Rolling Observed Frequency - Rolling Expected Frequency
* **Denominator**: Rolling Expected Frequency
* **Unit**: Percentage / decimal fraction
* **Population**: Cohort of claims
* **Time Basis**: 3-month moving window
* **Weighting Method**: Ratio-of-sums
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: None.
* **Implementation File**: [drift_detector.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/drift_detector.py)
* **Implementation Function**: `calculate_rolling_drift`
* **Known Limitations**: Avoids taking simple averages of monthly relative drifts.

---

## 24. Historical vs. Current Segment Profile Share (Phase 2)
* **Mathematical Formula**:
  $$\text{Historical Profile Share}_{k, \text{attr}} = \frac{\text{Historical Claims}_{k, \text{attr}}}{\text{Historical Total Claims}_k}$$
  $$\text{Current Profile Share}_{k, \text{attr}} = \frac{\text{Current Claims}_{k, \text{attr}}}{\text{Current Total Claims}_k}$$
  $$\text{Profile Shift}_{k, \text{attr}} = \text{Current Profile Share}_{k, \text{attr}} - \text{Historical Profile Share}_{k, \text{attr}}$$
* **Purpose**: Compares post-claim attribute share distributions (e.g. Cancer claim share) in segment $k$ comparing current period (2024) to historical baseline (2022-2023).
* **Numerator**: Count of claims with specific attribute value in segment $k$
* **Denominator**: Total claims in segment $k$
* **Unit**: Share difference (decimal fraction)
* **Population**: Selected demographic segment $k$ claims
* **Time Basis**: Current period vs. historical baseline period
* **Weighting Method**: Same-segment filtering
* **Null Hypothesis**: None
* **Alternative Hypothesis**: None
* **Assumptions**: Strictly labeled as **descriptive profile shifts**, not statistically significant shifts (as no statistical test is executed on Phase 2 profile shares).
* **Implementation File**: [drift_detector.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/drift_detector.py)
* **Implementation Function**: `get_historical_claim_profile`
* **Known Limitations**: Zero denominators are handled gracefully by returning empty profiles.
