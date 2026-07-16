# Combined Experience Engine — Formula Register

This document registers the official mathematical formulas, data grains, and invariants for **Milestone 5: Combined Claim Cost Experience & Portfolio Deterioration Intelligence** (v1).

---

## 1. Data-Grain Invariants

For Combined v1:
* **Row Grain**: One row = one annual Bernoulli claim opportunity / policy-year.
* **Expected_Frequency**: Defined for every policy-year.
* **Expected_Severity**: Defined prospectively for every policy-year, representing the expected value of severity conditional on a claim:
  $$\text{Expected\_Severity}_i = E[\text{Claim Cost}_i | \text{Claim}_i = 1, \text{policy characteristics}_i]$$
* **Independence Invariant**: `Expected_Severity` must **not** depend on the stochastically realized `Claim` indicator (meaning it is identical whether `Claim == 0` or `Claim == 1` for a given policyholder).
* **Claim**: The realized Bernoulli outcome in $\{0, 1\}$.
* **Actual_Claim_Amount**: Represents the realized observed claim severity conditional on `Claim == 1`, and must strictly equal `0` for `Claim == 0`.
* **Expected_Claim_Cost**: Derived deterministically as:
  $$\text{Expected\_Claim\_Cost}_i = \text{Exposure}_i \times \text{Expected\_Frequency}_i \times \text{Expected\_Severity}_i$$

### Prospective Conditional Severity vs. Realized Observed Severity
* **Prospective Expected Conditional Severity** ($Expected\_Severity$): The expected claim amount pricing assumption under the baseline model. It is computed prior to (and independently of) claim simulation by taking the expectation over all baseline claim categories and hospital types.
* **Realized Observed Claim Severity** ($Actual\_Claim\_Amount$): The actual simulated cost payout for a claim. It is only realized if `Claim == 1`, and is stochastically sampled from a lognormal distribution conditional on the realized claim category and hospital type (including active business event effects).

---

## 2. Core Combined Actuarial Formulas

### 1. Expected Total Claim Cost ($C_{\text{expected}}$)
* **Mathematical Formula**:
  $$C_{\text{expected}} = \sum_{i=1}^N \left( \text{Exposure}_i \times \text{Expected\_Frequency}_i \times \text{Expected\_Severity}_i \right)$$
* **Data Grain**: Portfolio or segment aggregate.
* **Unit**: Monetary (e.g. INR / ₹).
* **Assumptions**: Exposure $w_i = 1.0$ under the current generator.

### 2. Observed Total Claim Cost ($C_{\text{observed}}$)
* **Mathematical Formula**:
  $$C_{\text{observed}} = \sum_{i=1}^N \text{Actual\_Claim\_Amount}_i$$
* **Data Grain**: Portfolio or segment aggregate.
* **Unit**: Monetary (e.g. INR / ₹).

### 3. Combined Cost O/E ($OE_{\text{combined}}$)
* **Mathematical Formula**:
  $$OE_{\text{combined}} = \frac{C_{\text{observed}}}{C_{\text{expected}}}$$
* **Denominator**: $C_{\text{expected}}$ (must be $> 0$).
* **Unit**: Ratio.

### 4. Combined Relative Drift ($\text{Drift}_{\text{combined}}$)
* **Mathematical Formula**:
  $$\text{Drift}_{\text{combined}} = OE_{\text{combined}} - 1.0$$
* **Unit**: Percentage (e.g. $+5.1\%$).

### 5. Excess Claim Cost ($EC_{\text{monetary}}$)
* **Mathematical Formula**:
  $$EC_{\text{monetary}} = C_{\text{observed}} - C_{\text{expected}}$$
* **Unit**: Monetary.

### 6. Positive Excess Claim Cost ($PEC_{\text{monetary}}$)
* **Mathematical Formula**:
  $$PEC_{\text{monetary}} = \max(EC_{\text{monetary}}, 0)$$
* **Unit**: Monetary.

### 7. Segment Contribution to Positive Excess Cost
* **Mathematical Formula**:
  $$\text{Segment\_Contribution} = \frac{\text{Positive\_Excess\_Claim\_Cost}_{\text{segment}}}{\text{Positive\_Excess\_Claim\_Cost}_{\text{portfolio}}}$$
* **Unit**: Ratio.

---

## 3. Cost Decomposition Methodologies

To explain the total portfolio monetary drift ($\Delta C = C_{\text{observed}} - C_{\text{expected}}$), we evaluate two methodologies.

### Definitions
Let:
* $N_{\text{exp}} = \sum_i \text{Expected\_Frequency}_i \times \text{Exposure}_i$ (Expected Claims)
* $N_{\text{obs}} = \sum_i \text{Claim}_i$ (Observed Claims)
* $S_{\text{exp}} = C_{\text{expected}} / N_{\text{exp}}$ (Portfolio-wide average expected conditional severity)
* $S_{\text{obs}} = C_{\text{observed}} / N_{\text{obs}}$ (Average observed severity per actual claim; set to 0 if $N_{\text{obs}} = 0$)

---

### Method A: Sequential Decomposition (Order-Dependent)
In a sequential bridge, we change one factor at a time.

#### 1. Incidence First, then Severity
1. **Incidence Effect**: Change claims from expected to observed, holding severity at expected:
   $$\text{Incidence\_Effect}^{(1)} = (N_{\text{obs}} - N_{\text{exp}}) \times S_{\text{exp}}$$
2. **Severity Effect**: Change average severity from expected to observed, holding claims at observed:
   $$\text{Severity\_Effect}^{(1)} = N_{\text{obs}} \times (S_{\text{obs}} - S_{\text{exp}})$$
* **Reconciliation Invariant**:
  $$\text{Incidence\_Effect}^{(1)} + \text{Severity\_Effect}^{(1)} = N_{\text{obs}} S_{\text{obs}} - N_{\text{exp}} S_{\text{exp}} = C_{\text{observed}} - C_{\text{expected}}$$

#### 2. Severity First, then Incidence
1. **Severity Effect**: Change average severity from expected to observed, holding claims at expected:
   $$\text{Severity\_Effect}^{(2)} = N_{\text{exp}} \times (S_{\text{obs}} - S_{\text{exp}})$$
2. **Incidence Effect**: Change claims from expected to observed, holding severity at observed:
   $$\text{Incidence\_Effect}^{(2)} = (N_{\text{obs}} - N_{\text{exp}}) \times S_{\text{obs}}$$
* **Order Dependence Limitation**: The sequential method allocates the interaction term $(N_{\text{obs}} - N_{\text{exp}})(S_{\text{obs}} - S_{\text{exp}})$ to whichever factor is evaluated second. This makes the results arbitrary based on the selected execution sequence.

---

### Method B: Three-Factor Interaction-Isolated Bilinear Decomposition (Selected Production Method)
This method separates the standalone effects of incidence and severity using the algebraic identity of bilinear products, explicitly isolating the joint interaction remainder.

1. **Claim Incidence Effect**:
   $$\text{Incidence\_Effect} = (N_{\text{obs}} - N_{\text{exp}}) \times S_{\text{exp}}$$
2. **Claim Severity Effect**:
   $$\text{Severity\_Effect} = N_{\text{exp}} \times (S_{\text{obs}} - S_{\text{exp}})$$
3. **Mix / Interaction Effect**:
   $$\text{Mix\_Interaction\_Effect} = (N_{\text{obs}} - N_{\text{exp}}) \times (S_{\text{obs}} - S_{\text{exp}})$$

#### Reconciliation Invariant
$$\text{Incidence\_Effect} + \text{Severity\_Effect} + \text{Mix\_Interaction\_Effect} \equiv C_{\text{observed}} - C_{\text{expected}}$$
This Interaction-Isolated Bilinear formulation is selected for production because it is **order-independent** and explicitly labels the **interaction effect** when both frequency and severity assumptions drift concurrently.

> **Terminology Note**: This is NOT a Shapley decomposition. A true two-factor Shapley value decomposition averages over both sequential orderings:
>
> $$\phi_N = \frac{1}{2}\left[\Delta N \cdot S_{\text{exp}} + \Delta N \cdot S_{\text{obs}}\right] = \Delta N \cdot \frac{S_{\text{exp}} + S_{\text{obs}}}{2}$$
>
> $$\phi_S = \frac{1}{2}\left[N_{\text{exp}} \cdot \Delta S + N_{\text{obs}} \cdot \Delta S\right] = \Delta S \cdot \frac{N_{\text{exp}} + N_{\text{obs}}}{2}$$
>
> The Shapley approach reconciles ($\phi_N + \phi_S = \Delta C$) but **splits the interaction term $\Delta N \cdot \Delta S$ equally (50/50) between incidence and severity effects**, making the interaction invisible.
>
> Combined v1 intentionally retains the bilinear decomposition because the explicit $\Delta N \cdot \Delta S$ term is analytically useful for identifying interaction patterns where both frequency and severity drift concurrently. The interaction term triggers the "Mix / Interaction Deterioration" classification label.

---

## 4. Combined Deterioration Pattern Labels

Combined portfolio experience is classified into one of 5 mutually exclusive patterns based on the three-factor decomposition and engine signals:

1. **Frequency-Led Deterioration**:
   * *Criteria*: $\text{Excess\_Claim\_Cost} > 0$, $\text{Incidence\_Effect} > \text{Severity\_Effect}$, and Frequency v1 triggers.
2. **Severity-Led Deterioration**:
   * *Criteria*: $\text{Excess\_Claim\_Cost} > 0$, $\text{Severity\_Effect} > \text{Incidence\_Effect}$, and Severity v1 triggers.
3. **Frequency and Severity Deterioration**:
   * *Criteria*: $\text{Excess\_Claim\_Cost} > 0$, and BOTH Frequency v1 and Severity v1 engines trigger.
4. **Mix / Interaction Deterioration**:
   * *Criteria*: $\text{Excess\_Claim\_Cost} > 0$, neither standalone engine triggers portfolio-wide, but $\text{Mix\_Interaction\_Effect}$ is positive.
5. **No Material Combined Deterioration**:
   * *Criteria*: $\text{Excess\_Claim\_Cost} \le 0$ or neither gate triggers.
