# Severity Experience Engine — Formula Register

This document registers every mathematical and actuarial formula actually used in the Severity Experience Engine.

---

## 1. Expected Severity (Baseline Model)
* **Mathematical Formula**:
  $$\text{Expected\_Severity} = \text{base\_expected\_severity} \times \text{rel}_{\text{product}} \times \text{rel}_{\text{age}} \times \text{rel}_{\text{region}} \times \text{rel}_{\text{category}} \times \text{rel}_{\text{hospital}} \times \text{Trend\_Factor}$$
  *Equivalent Log-Link Linear Predictor Form*:
  $$\log(\text{Expected\_Severity}) = \log(\text{base\_expected\_severity}) + \beta_{\text{product}} + \beta_{\text{age}} + \beta_{\text{region}} + \beta_{\text{category}} + \beta_{\text{hospital}} + \beta_{\text{trend}}$$
  where each $\beta = \log(\text{relativity})$.
* **Purpose**: Computes baseline pricing expected claim severity for a given claim record before anomalies.
* **Input Fields**:
  - `Product` (string)
  - `Age_Group` (string)
  - `Region` (string)
  - `Claim_Category` (string)
  - `Hospital_Type` (string)
  - `Year` (integer)
  - `Month` (integer)
* **Output**: Baseline expected claim amount (float)
* **Code File**: [generate_datasets.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/data/generate_datasets.py)
* **Function Name**: `calculate_expected_severity`
* **Assumptions**: Base expected severity is 5000; relativities are fixed in [severity_model.yaml](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/config/severity_model.yaml).
* **Known Limitations**: Does not support dynamic interaction terms between attributes.

---

## 2. Expected Annual Trend & Monthly Trend Conversion
* **Mathematical Formula**:
  $$\text{monthly\_rate} = (1 + \text{annual\_rate})^{1/12} - 1$$
* **Purpose**: Converts the configured expected annual trend (5%) to a compounding monthly trend rate.
* **Input Fields**: `expected_annual_trend` (from config)
* **Output**: Monthly trend rate (float)
* **Code File**: [generate_datasets.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/data/generate_datasets.py)
* **Function Name**: `calculate_expected_severity`
* **Assumptions**: Trend compounds continuously on a monthly discrete basis.
* **Known Limitations**: None.

---

## 3. Expected Severity Calendar Adjustment (Elapsed Months)
* **Mathematical Formula**:
  $$t = (\text{Year} - 2022) \times 12 + (\text{Month} - 1)$$
  $$\text{Trend\_Factor} = (1 + \text{monthly\_rate})^t$$
* **Purpose**: Compounds monthly trend rate starting from the baseline epoch of January 2022 ($t=0$).
* **Input Fields**: `Year`, `Month` (integers)
* **Output**: Cumulative trend multiplier (float)
* **Code File**: [generate_datasets.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/data/generate_datasets.py)
* **Function Name**: `calculate_expected_severity`
* **Assumptions**: Baseline epoch starts at 2022-01. Trend compounds indefinitely across years without resetting in January.
* **Known Limitations**: The start year of 2022 is hardcoded in the generator.

---

## 4. Lognormal Claim Amount Generation (Mean Calibration)
* **Mathematical Formula**:
  $$\mu = \log(\text{actual\_expected\_severity}) - \frac{\sigma^2}{2}$$
  $$\text{Actual\_Claim\_Amount} \sim \text{LogNormal}(\mu, \sigma)$$
* **Purpose**: Stochastically generates claim cost ensuring the arithmetic mean of the distribution exactly equals the adjusted expected severity.
* **Input Fields**:
  - `actual_expected_severity` (target mean, float)
  - `sigma` (category volatility, float)
* **Output**: Simulated claim amount (float)
* **Code File**: [generate_datasets.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/data/generate_datasets.py)
* **Function Name**: `generate_dataset`
* **Assumptions**: Claims follow a lognormal distribution; $E[X] = \exp(\mu + \sigma^2/2)$.
* **Known Limitations**: Lognormal tail might generate extremely high costs if volatility is high.

---

## 5. Business Event Cost Adjustment (Progression)
* **Mathematical Formula**:
  - *Compound Progression Curve*:
    $$\text{actual\_expected\_severity} = \text{expected\_severity} \times (1 + \text{monthly\_rate}_{\text{event}})^{\text{months\_active}}$$
    where $\text{monthly\_rate}_{\text{event}} = (1 + \text{effect\_size})^{1/12} - 1$.
  - *Linear / Exponential Progression Curves*:
    $$\text{actual\_expected\_severity} = \text{expected\_severity} \times (1 + \text{effect\_size} \times \text{progression})$$
    where $\text{progression} = \frac{\text{months\_active}}{\text{duration}}$ (linear) or $(\frac{\text{months\_active}}{\text{duration}})^2$ (exponential).
* **Purpose**: Adjusts expected severity for actual claims generation based on active business events.
* **Input Fields**:
  - `expected_severity` (baseline, float)
  - `start_month`, `duration`, `progression_curve`, `effect_size` (from config)
* **Output**: Event-adjusted expected severity (float)
* **Code File**: [generate_datasets.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/data/generate_datasets.py)
* **Function Name**: `apply_severity_events`
* **Assumptions**: Business events only affect the actual claims cost process and never modify the baseline Expected Severity.
* **Known Limitations**: Only affects claims from 2024 onwards.

---

## 6. Aggregate Severity O/E
* **Mathematical Formula**:
  $$\text{Severity O/E} = \frac{\sum_{i=1}^N \text{Actual\_Claim\_Amount}_i}{\sum_{i=1}^N \text{Expected\_Severity}_i}$$
* **Purpose**: Computes aggregate ratio-of-sums Observed-to-Expected claim cost.
* **Input Fields**:
  - `Actual_Claim_Amount` (float array)
  - `Expected_Severity` (float array)
* **Output**: O/E ratio (float)
* **Code File**: [severity_engine.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/engines/severity_engine.py)
* **Function Name**: `calculate_metrics`
* **Assumptions**: Calculated only over claims where both fields are not null.
* **Known Limitations**: Prone to skew if a few very large outliers dominate the sums.

---

## 7. Observed & Expected Average Severity
* **Mathematical Formula**:
  $$\text{Observed Average Severity} = \frac{\sum_{i=1}^N \text{Actual\_Claim\_Amount}_i}{N}$$
  $$\text{Expected Average Severity} = \frac{\sum_{i=1}^N \text{Expected\_Severity}_i}{N}$$
* **Purpose**: Calculates simple arithmetic averages of observed and expected claim cost.
* **Input Fields**:
  - `Actual_Claim_Amount` (float array)
  - `Expected_Severity` (float array)
* **Output**: Average amounts (float)
* **Code File**: [severity_engine.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/engines/severity_engine.py)
* **Function Name**: `calculate_metrics`
* **Assumptions**: Standard arithmetic mean.
* **Known Limitations**: Simple averages ignore demographic weighting within the cohort.

---

## 8. Excess Claim Cost & Positive Excess Claim Cost
* **Mathematical Formula**:
  $$\text{Excess Claim Cost} = \sum_{i=1}^N \text{Actual\_Claim\_Amount}_i - \sum_{i=1}^N \text{Expected\_Severity}_i$$
  $$\text{Positive Excess Claim Cost} = \max(\text{Excess Claim Cost}, 0.0)$$
* **Purpose**: Quantifies the absolute financial loss in excess of baseline assumptions.
* **Input Fields**: Observed and Expected cost sums.
* **Output**: Excess cost (float)
* **Code File**: [severity_engine.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/engines/severity_engine.py) & [feature_ranker.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/feature_ranker.py)
* **Function Name**: `calculate_metrics` & `rank_severity_features`
* **Assumptions**: Negative excess cost is treated as 0 for ranking purposes.
* **Known Limitations**: None.

---

## 9. Relative Severity Drift
* **Mathematical Formula**:
  $$\text{Relative Severity Drift} = \frac{\text{Observed Average Severity} - \text{Expected Average Severity}}{\text{Expected Average Severity}}$$
* **Purpose**: Measures the percentage drift of observed costs compared to baseline assumptions.
* **Input Fields**: Observed and Expected average severity.
* **Output**: Drift fraction (float)
* **Code File**: [severity_engine.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/engines/severity_engine.py)
* **Function Name**: `calculate_metrics`
* **Assumptions**: Relative drift is equivalent to $\text{Severity O/E} - 1.00$.
* **Known Limitations**: None.

---

## 10. Bootstrap O/E and Confidence Interval
* **Mathematical Formula**:
  - For $b = 1 \dots B$ (where $B=500$):
    - Draw sample indices $I^{(b)}$ of size $N$ with replacement from claims indices.
    - Calculate resampled O/E:
      $$\text{O/E}^{(b)} = \frac{\sum_{i \in I^{(b)}} \text{Actual\_Claim\_Amount}_i}{\sum_{i \in I^{(b)}} \text{Expected\_Severity}_i}$$
  - Sort resampled O/E values: $\text{O/E}^{(1)} \le \text{O/E}^{(2)} \le \dots \le \text{O/E}^{(B)}$.
  - Compute confidence bounds (95% level):
    - Lower Bound: $\text{O/E}^{(\text{max}(0, \text{round}(0.025 \times B)))}$
    - Upper Bound: $\text{O/E}^{(\text{min}(B-1, \text{round}(0.975 \times B) - 1))}$
* **Purpose**: Evaluates statistical significance of the aggregate O/E ratio without lognormal parametric distribution assumptions.
* **Input Fields**: `Actual_Claim_Amount` and `Expected_Severity` vectors.
* **Output**: Lower and Upper CI bounds (floats)
* **Code File**: [severity_engine.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/engines/severity_engine.py) & [investigation_agent.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/agent/investigation_agent.py)
* **Function Name**: `calculate_metrics` & `run_segment_bootstrap`
* **Assumptions**: Re-sampling occurs at the **individual claim row level** (resampling rows, not pre-aggregated averages or individual O/E ratios). Uses a fixed seed of 42.
* **Known Limitations**: Slow to compute for massive datasets, requiring vectorized optimization.

---

## 11. Historical Baseline P99
* **Mathematical Formula**:
  $$\text{Threshold} = Q_{0.99}(\{\text{Actual\_Claim\_Amount}_i \text{ for baseline period claims}\})$$
  where $Q_{0.99}$ is the 99th percentile quantile function.
* **Purpose**: Defines the historical boundary above which claims are classified as high-cost outliers.
* **Input Fields**: `Actual_Claim_Amount` for claims where `Year` $\in \{2022, 2023\}$.
* **Output**: Outlier cost threshold (float)
* **Code File**: [severity_engine.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/engines/severity_engine.py)
* **Function Name**: `calculate_metrics`
* **Assumptions**: Baseline years are explicitly configured as 2022 and 2023. Falls back to current period P99 if baseline is empty.
* **Known Limitations**: Susceptible to small sample sizes in the baseline period.

---

## 12. High-Cost Claim Cost Share & O/E Excluding High-Cost Claims
* **Mathematical Formula**:
  $$\text{High-Cost Cost Share} = \frac{\sum_{i \in \text{Outliers}} \text{Actual\_Claim\_Amount}_i}{\sum_{i=1}^N \text{Actual\_Claim\_Amount}_i}$$
  $$\text{O/E Excluding High-Cost Claims} = \frac{\sum_{i \notin \text{Outliers}} \text{Actual\_Claim\_Amount}_i}{\sum_{i \notin \text{Outliers}} \text{Expected\_Severity}_i}$$
  where $i \in \text{Outliers}$ if $\text{Actual\_Claim\_Amount}_i > \text{Threshold}$.
* **Purpose**: Isolates the financial and statistical impact of rare, high-cost claims.
* **Input Fields**: Claims amounts and expectations; historical P99 threshold.
* **Output**: Share fraction and normal O/E ratio (floats)
* **Code File**: [severity_engine.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/engines/severity_engine.py)
* **Function Name**: `calculate_metrics`
* **Assumptions**: Normal O/E uses the aggregate ratio-of-sums over claims that do not exceed the threshold.
* **Known Limitations**: If the entire normal cohort experiences severe inflation, normal claims might cross the threshold and be misclassified as outliers.

---

## 13. 3-Month Rolling Average Trends
* **Mathematical Formula**:
  $$\text{Rolling Actual Cost}_m = \sum_{j=m-2}^{m} \text{Observed\_Cost}_j$$
  $$\text{Rolling Expected Cost}_m = \sum_{j=m-2}^{m} \text{Expected\_Cost}_j$$
  $$\text{Rolling 3M O/E}_m = \frac{\text{Rolling Actual Cost}_m}{\text{Rolling Expected Cost}_m}$$
* **Purpose**: Smooths monthly noise to show short-term rolling trends without simple average bias.
* **Input Fields**: Monthly cost sums.
* **Output**: Rolling O/E ratio (float)
* **Code File**: [severity_engine.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/engines/severity_engine.py)
* **Function Name**: `calculate_rolling_trend`
* **Assumptions**: Uses aggregate ratio-of-sums over the 3-month window, not $\text{mean}(\text{monthly O/E})$.
* **Known Limitations**: At start months ($m < 3$), uses the available months (min_periods=1).

---

## 14. Contribution Mathematics (Phase 1 Portfolio Slicing)
* **Mathematical Formula**:
  - *Segment Excess Cost*:
    $$\text{Excess}_k = \sum_{i \in \text{Segment}_k} \text{Actual\_Claim\_Amount}_i - \sum_{i \in \text{Segment}_k} \text{Expected\_Severity}_i$$
  - *Positive Segment Excess Cost*:
    $$\text{Pos\_Excess}_k = \max(\text{Excess}_k, 0.0)$$
  - *Local Contribution*:
    $$\text{Local\_Contribution}_k = \frac{\text{Pos\_Excess}_k}{\sum_{j \in \text{Siblings}} \text{Pos\_Excess}_j}$$
  - *Portfolio Contribution*:
    $$\text{Portfolio\_Contribution}_k = \frac{\text{Pos\_Excess}_k}{\text{Total\_Portfolio\_Positive\_Excess}}$$
* **Purpose**: Slices the portfolio recursively based on where the excess cost is isolated.
* **Input Fields**: Segment costs and total portfolio excess cost.
* **Output**: Contribution percentages (floats)
* **Code File**: [feature_ranker.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/feature_ranker.py) & [investigation_agent.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/agent/investigation_agent.py)
* **Function Name**: `rank_severity_features` & `investigate_severity_phase_1`
* **Assumptions**: Ignores negative excess segments (favorable segments) during slicing prioritization.
* **Known Limitations**: Sibling splits ignore features already split higher up in the path.

---

## 15. Parametric T-Statistic (Slicing Screening Diagnostic)
* **Mathematical Formula**:
  $$t = \frac{\bar{S}_{\text{obs}} - \bar{S}_{\text{exp}}}{s / \sqrt{n}}$$
  where:
  - $\bar{S}_{\text{obs}}$ is Observed Average Severity of the segment.
  - $\bar{S}_{\text{exp}}$ is Expected Average Severity of the segment.
  - $s$ is the sample standard deviation of `Actual_Claim_Amount` in the segment.
  - $n$ is the segment claim count.
* **Purpose**: Performs a fast screening diagnostic of significance during slicing to rank features.
* **Input Fields**: Segment claims costs.
* **Output**: T-statistic value (float)
* **Code File**: [feature_ranker.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/tools/feature_ranker.py)
* **Function Name**: `rank_severity_features`
* **Assumptions**: Approximates significance using standard t-distribution cumulative probability (with degrees of freedom $d.f. = n-1$).
* **Known Limitations**: Skewed lognormal claims violate normality assumptions, making the raw T-statistic unstable. **Its use is strictly restricted to a ranking/screening guide; it is NEVER used as the final significance gate.**

---

## 16. Cost-Band Excess Cost Shares and Deterioration Classification
* **Mathematical Formula**:
  - *Historical baseline percentile thresholds*: $P_{50}, P_{90}, P_{99}$ derived from baseline claims $\{X_i\}_{i \in \text{Baseline}}$.
  - *Current claims grouping*:
    - $Band_0 \text{ (P0-P50)}: \{X_j \le P_{50}\}$
    - $Band_1 \text{ (P50-P90)}: \{P_{50} < X_j \le P_{90}\}$
    - $Band_2 \text{ (P90-P99)}: \{P_{90} < X_j \le P_{99}\}$
    - $Band_3 \text{ (P99+)}: \{X_j > P_{99}\}$
  - *Band Excess Cost*:
    $$E_b = \sum_{j \in Band_b} \text{Actual}_j - \sum_{j \in Band_b} \text{Expected}_j$$
  - *Positive Excess Share*:
    $$\text{Share}_b = \frac{\max(E_b, 0.0)}{\sum_{k=0}^{3} \max(E_k, 0.0)}$$
  - *Deterioration Classification Rules*:
    - **High-Cost Concentration**: If $\text{Share}_{Band3} \ge 0.60$
    - **Upper-Tail Deterioration**: If $(\text{Share}_{Band2} + \text{Share}_{Band3}) \ge 0.60$ and $\text{Share}_{Band3} < 0.60$
    - **Broad Deterioration**: If $(\text{Share}_{Band0} + \text{Share}_{Band1}) \ge 0.50$ and $\text{Share}_{Band3} < 0.30$
    - **Mixed Deterioration**: Fallback for any other triggered state.
* **Purpose**: Classifies the shape and distribution of severity deterioration across historical cost bands to distinguish outliers from broad medical inflation without selection bias.
* **Input Fields**: Baseline and Current claims vectors.
* **Output**: Band data dictionaries and classification string.
* **Code File**: [severity_engine.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/engines/severity_engine.py)
* **Function Name**: `calculate_metrics`
* **Assumptions**: Baseline thresholds remain static during current period evaluation.
* **Known Limitations**: Relies on a non-empty baseline set.

---

## 17. Demographic Segment Surveillance Gate Trigger (One-Sided Normal Approximation Test with Bootstrap-Estimated Standard Error) & FDR Control
* **Statistical Method**: One-Sided Normal Approximation Test with Bootstrap-Estimated Standard Error
* **Mathematical Formula**:
  - For each candidate segment in coarse demographic dimensions $d \in \{\text{Product}, \text{Region}, \text{Age\_Group}, \text{Gender}, \text{Distribution\_Channel}\}$ with $N_{d,v} \ge \text{minimum\_claims}$ (where the total number of candidate segments is $m$):
    - Compute the observed O/E: $oe = \frac{\sum \text{Actual}_i}{\sum \text{Expected}_i}$.
    - Draw $B$ bootstrap samples, computing $oe^{(b)}$ for each.
    - Estimate the standard error of O/E as the sample standard deviation of bootstrap O/E values:
      $$se = \text{std}(\{oe^{(b)}\}_{b=1}^B)$$
    - Perform a one-sided Z-test of $H_0: \text{O/E} \le 1.00$ vs $H_1: \text{O/E} > 1.00$:
      $$Z = \frac{oe - 1.00}{se}$$
    - Calculate the raw one-sided p-value:
      $$p = 1 - \Phi(Z)$$
  - Pool raw p-values across all candidate segments as a single family of size $m$.
  - Apply the Benjamini-Hochberg False Discovery Rate (FDR) procedure:
    - Sort candidate segments by raw p-value ascending: $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$.
    - Find the largest rank $k$ such that:
      $$p_{(k)} \le \frac{k}{m} \times q$$
      where $q$ is the target FDR threshold (`fdr_target` from EngineContext).
    - Declare all candidate segments with rank $i \le k$ as FDR-significant (`fdr_significant = True`).
    - Compute monotonic adjusted p-values (q-values) as:
      $$q_{(i)} = \min\left(1.0, \min_{j \ge i} \left( p_{(j)} \times \frac{m}{j} \right) \right)$$
  - A segment triggers if:
    - Volume check: $N_{d,v} \ge \text{minimum\_claims}$
    - Materiality check: $Drift_{d,v} \ge \text{materiality\_threshold}$
    - FDR Significance: `fdr_significant == True`
* **Purpose**: Bypasses the portfolio-level investigation gate to identify material local demographic deterioration before the AI Planner runs, while controlling the False Discovery Rate.
* **Input Fields**: Current claims, demographic dimensions, and EngineContext thresholds.
* **Output**: Surveillance trigger flag, worst segment info, and metrics.
* **Code File**: [severity_engine.py](file:///Users/hrudhay_gubba/Assumption-Monitoring-Agent/backend/engines/severity_engine.py)
* **Function Name**: `run_segment_surveillance`
* **Assumptions**: Strictly excludes claim attributes (category, hospital type) to prevent premature classification.
* **Known Limitations**: Z-test assumes asymptotic normality of the O/E ratio under the bootstrap standard error.


