import os
import unittest
import pandas as pd
import numpy as np
from engines.combined_engine import CombinedAnalyticsEngine
from agent.combined_coordinator import CombinedCoordinator

class TestCombinedAcceptance(unittest.TestCase):
    def setUp(self):
        self.backend_dir = os.path.dirname(os.path.abspath(__file__))
        self.baseline_path = os.path.join(self.backend_dir, 'data', 'experience_baseline.csv')
        self.scenario_a_path = os.path.join(self.backend_dir, 'data', 'experience_scenario_a.csv')
        
        self.df_base = pd.read_csv(self.baseline_path)
        self.df_scen = pd.read_csv(self.scenario_a_path)
        self.engine = CombinedAnalyticsEngine()
        self.coordinator = CombinedCoordinator()

    # ---------------------------------------------------------
    # DATA GRAIN & INVARIANT TESTS (Issues 1-5)
    # ---------------------------------------------------------

    def test_invariant_1_row_grain_exposure(self):
        # Exposure must equal 1.0 for every policy-year record in Combined v1
        self.assertTrue((self.df_base['Exposure'] == 1.0).all())
        self.assertTrue((self.df_scen['Exposure'] == 1.0).all())

    def test_invariant_2_expected_severity_non_null(self):
        # Expected_Severity contains no null values in Combined v1 (prospectively defined)
        self.assertTrue(self.df_base['Expected_Severity'].notnull().all())
        self.assertTrue(self.df_scen['Expected_Severity'].notnull().all())

    def test_invariant_3_actual_claim_amount_non_claims(self):
        # Actual_Claim_Amount must equal 0.0 for Claim == 0
        non_claims_base = self.df_base[self.df_base['Claim'] == 0]
        non_claims_scen = self.df_scen[self.df_scen['Claim'] == 0]
        self.assertTrue((non_claims_base['Actual_Claim_Amount'] == 0.0).all())
        self.assertTrue((non_claims_scen['Actual_Claim_Amount'] == 0.0).all())

    def test_invariant_4_expected_severity_claim_independence(self):
        # Expected_Severity must not depend on whether a claim occurred stochastically.
        # For any demographic slice in a given month/year, average expected severity of claim vs non-claim rows must be identical.
        demographic_cols = ['Product', 'Region', 'Age_Group', 'Year', 'Month']
        grouped_claim = self.df_base.groupby(demographic_cols + ['Claim'])['Expected_Severity'].mean().unstack()
        # Drop any groups that don't have both Claim == 0 and Claim == 1 to avoid NaN comparisons
        grouped_claim = grouped_claim.dropna()
        # Verify difference is extremely close to zero (allowing for minor float rounding in dataset file)
        diff = (grouped_claim[1] - grouped_claim[0]).abs()
        self.assertTrue((diff < 1e-2).all(), f"Expected_Severity depends on realized Claim indicator! Diff: {diff}")

    def test_invariant_5_actual_claim_amount_claims(self):
        # Actual_Claim_Amount must be strictly positive for Claim == 1
        claims_base = self.df_base[self.df_base['Claim'] == 1]
        self.assertTrue((claims_base['Actual_Claim_Amount'] > 0.0).all())

    # ---------------------------------------------------------
    # ISSUE 5: PROSPECTIVE EXPECTED SEVERITY INVARIANT AUDIT
    # ---------------------------------------------------------

    def test_invariant_5a_expected_frequency_non_null(self):
        """Expected_Frequency contains no null values."""
        self.assertEqual(self.df_base['Expected_Frequency'].isnull().sum(), 0)
        self.assertEqual(self.df_scen['Expected_Frequency'].isnull().sum(), 0)

    def test_invariant_5b_expected_severity_non_null_count(self):
        """Expected_Severity has zero nulls across entire dataset."""
        self.assertEqual(self.df_base['Expected_Severity'].isnull().sum(), 0)
        self.assertEqual(self.df_scen['Expected_Severity'].isnull().sum(), 0)

    def test_invariant_5c_non_claim_rows_zero_actual_cost(self):
        """Non-claim rows must have exactly zero Actual_Claim_Amount."""
        nc_base = self.df_base[self.df_base['Claim'] == 0]
        nc_scen = self.df_scen[self.df_scen['Claim'] == 0]
        bad_base = (nc_base['Actual_Claim_Amount'] != 0.0).sum()
        bad_scen = (nc_scen['Actual_Claim_Amount'] != 0.0).sum()
        self.assertEqual(bad_base, 0, f"Baseline has {bad_base} non-claim rows with non-zero Actual_Claim_Amount")
        self.assertEqual(bad_scen, 0, f"Scenario has {bad_scen} non-claim rows with non-zero Actual_Claim_Amount")

    def test_invariant_5d_claim_rows_positive_actual_cost(self):
        """Claim rows must have strictly positive Actual_Claim_Amount."""
        c_base = self.df_base[self.df_base['Claim'] == 1]
        c_scen = self.df_scen[self.df_scen['Claim'] == 1]
        bad_base = (c_base['Actual_Claim_Amount'] <= 0.0).sum()
        bad_scen = (c_scen['Actual_Claim_Amount'] <= 0.0).sum()
        self.assertEqual(bad_base, 0, f"Baseline has {bad_base} claim rows with non-positive Actual_Claim_Amount")
        self.assertEqual(bad_scen, 0, f"Scenario has {bad_scen} claim rows with non-positive Actual_Claim_Amount")

    def test_invariant_5e_expected_claim_cost_reconstruction(self):
        """Expected_Claim_Cost = Exposure * Expected_Frequency * Expected_Severity within float tolerance."""
        reconstructed = self.df_base['Exposure'] * self.df_base['Expected_Frequency'] * self.df_base['Expected_Severity']
        engine_total = reconstructed.sum()
        metrics = self.engine.calculate_metrics(self.df_base)
        max_error = abs(engine_total - metrics['expected_total_cost'])
        self.assertLess(max_error, 1.0, f"Max Expected Claim Cost reconstruction error: {max_error}")

    def test_invariant_5f_expected_severity_positive(self):
        """Expected_Severity must be strictly positive for all rows."""
        self.assertTrue((self.df_base['Expected_Severity'] > 0.0).all())
        self.assertTrue((self.df_scen['Expected_Severity'] > 0.0).all())

    # ---------------------------------------------------------
    # CORE ACTUARIAL MODEL INVARIANTS
    # ---------------------------------------------------------

    def test_invariant_6_expected_total_claim_cost(self):
        # Expected total claim cost is mathematically sum(Exposure * expected_frequency * expected_severity)
        calc_cost = (self.df_base['Exposure'] * self.df_base['Expected_Frequency'] * self.df_base['Expected_Severity']).sum()
        metrics = self.engine.calculate_metrics(self.df_base)
        self.assertAlmostEqual(calc_cost, metrics['expected_total_cost'], places=2)

    def test_invariant_7_observed_total_claim_cost(self):
        # Observed total cost is sum of actual claim amounts
        calc_cost = self.df_base['Actual_Claim_Amount'].sum()
        metrics = self.engine.calculate_metrics(self.df_base)
        self.assertAlmostEqual(calc_cost, metrics['observed_total_cost'], places=2)

    # ---------------------------------------------------------
    # DECOMPOSITION RECONCILIATION INVARIANTS (Issue 4c)
    # ---------------------------------------------------------

    def test_invariant_8_decomposition_exact_bridge_baseline(self):
        # Incidence + Severity + Mix Interaction = Observed Cost - Expected Cost (within float tolerance)
        metrics = self.engine.calculate_metrics(self.df_base)
        total_drift = metrics['observed_total_cost'] - metrics['expected_total_cost']
        decomp_sum = metrics['incidence_effect'] + metrics['severity_effect'] + metrics['mix_effect']
        self.assertAlmostEqual(total_drift, decomp_sum, delta=1.0)

    def test_invariant_9_decomposition_exact_bridge_scenario(self):
        metrics = self.engine.calculate_metrics(self.df_scen)
        total_drift = metrics['observed_total_cost'] - metrics['expected_total_cost']
        decomp_sum = metrics['incidence_effect'] + metrics['severity_effect'] + metrics['mix_effect']
        self.assertAlmostEqual(total_drift, decomp_sum, delta=1.0)

    def test_invariant_10_sequential_decomposition_order_dependence(self):
        # Verify that changing order in sequential method produces different effects (order dependence)
        # Expected claims & severity
        n_exp = (self.df_scen['Expected_Frequency'] * self.df_scen['Exposure']).sum()
        n_obs = self.df_scen['Claim'].sum()
        s_exp = (self.df_scen['Exposure'] * self.df_scen['Expected_Frequency'] * self.df_scen['Expected_Severity']).sum() / n_exp
        s_obs = self.df_scen['Actual_Claim_Amount'].sum() / n_obs

        # Incidence-first sequential effects
        inc_eff_seq1 = (n_obs - n_exp) * s_exp
        sev_eff_seq1 = n_obs * (s_obs - s_exp)

        # Severity-first sequential effects
        sev_eff_seq2 = n_exp * (s_obs - s_exp)
        inc_eff_seq2 = (n_obs - n_exp) * s_obs

        # Under scenario a, they must differ because of interaction term
        self.assertNotEqual(inc_eff_seq1, inc_eff_seq2)
        self.assertNotEqual(sev_eff_seq1, sev_eff_seq2)

    def test_invariant_10b_decomposition_100_subportfolios(self):
        """Independently reconstruct decomposition for 100+ random sub-portfolios and verify reconciliation."""
        np.random.seed(42)
        max_abs_error = 0.0
        max_rel_error = 0.0
        sum_abs_error = 0.0
        n_checks = 0
        
        for i in range(120):
            # Sample a random sub-portfolio (10%-50% of rows)
            frac = np.random.uniform(0.1, 0.5)
            sub = self.df_base.sample(frac=frac, random_state=i)
            
            if sub['Claim'].sum() == 0:
                continue
            
            metrics = self.engine.calculate_metrics(sub)
            total_drift = metrics['observed_total_cost'] - metrics['expected_total_cost']
            decomp_sum = metrics['incidence_effect'] + metrics['severity_effect'] + metrics['mix_effect']
            
            abs_error = abs(total_drift - decomp_sum)
            rel_error = abs_error / max(abs(total_drift), 1.0)
            
            max_abs_error = max(max_abs_error, abs_error)
            max_rel_error = max(max_rel_error, rel_error)
            sum_abs_error += abs_error
            n_checks += 1
        
        mean_abs_error = sum_abs_error / n_checks if n_checks > 0 else 0.0
        
        # All reconciliation errors must be within float tolerance
        self.assertLess(max_abs_error, 0.01, f"Max absolute reconciliation error: {max_abs_error}")
        self.assertLess(mean_abs_error, 0.001, f"Mean absolute reconciliation error: {mean_abs_error}")
        self.assertLess(max_rel_error, 1e-6, f"Max relative reconciliation error: {max_rel_error}")
        self.assertGreaterEqual(n_checks, 100, f"Only {n_checks} valid sub-portfolios checked")

    def test_invariant_10c_bilinear_vs_sequential_comparison(self):
        """Show numerically that sequential decomposition is order-dependent and bilinear is not."""
        df = self.df_scen
        n_exp = (df['Expected_Frequency'] * df['Exposure']).sum()
        n_obs = float(df['Claim'].sum())
        s_exp = (df['Exposure'] * df['Expected_Frequency'] * df['Expected_Severity']).sum() / n_exp
        s_obs = df['Actual_Claim_Amount'].sum() / n_obs
        
        delta_n = n_obs - n_exp
        delta_s = s_obs - s_exp
        total_change = n_obs * s_obs - n_exp * s_exp
        
        # Sequential: Frequency-first
        seq1_inc = delta_n * s_exp
        seq1_sev = n_obs * delta_s
        
        # Sequential: Severity-first
        seq2_sev = n_exp * delta_s
        seq2_inc = delta_n * s_obs
        
        # Bilinear (production)
        bilinear_inc = delta_n * s_exp
        bilinear_sev = n_exp * delta_s
        bilinear_mix = delta_n * delta_s
        
        # All three methods reconcile to the same total
        self.assertAlmostEqual(seq1_inc + seq1_sev, total_change, delta=0.01)
        self.assertAlmostEqual(seq2_sev + seq2_inc, total_change, delta=0.01)
        self.assertAlmostEqual(bilinear_inc + bilinear_sev + bilinear_mix, total_change, delta=0.01)
        
        # Sequential methods produce different component allocations
        self.assertNotAlmostEqual(seq1_inc, seq2_inc, delta=0.01)
        self.assertNotAlmostEqual(seq1_sev, seq2_sev, delta=0.01)
        
        # Bilinear incidence matches freq-first incidence (both use S_exp)
        self.assertAlmostEqual(bilinear_inc, seq1_inc, delta=0.01)
        # Bilinear severity matches sev-first severity (both use N_exp)
        self.assertAlmostEqual(bilinear_sev, seq2_sev, delta=0.01)
        # The difference between sequential methods IS the interaction term
        self.assertAlmostEqual(seq1_sev - seq2_sev, bilinear_mix, delta=0.01)

    # ---------------------------------------------------------
    # PATTERN CLASSIFICATION INVARIANTS
    # ---------------------------------------------------------

    def test_invariant_11_pattern_no_deterioration(self):
        # If excess cost is negative/zero, pattern is "No Material Combined Deterioration"
        mock_metrics = {"excess_cost": -100.0, "incidence_effect": -50.0, "severity_effect": -50.0}
        pattern = self.engine.classify_pattern(mock_metrics, True, True)
        self.assertEqual(pattern, "No Material Combined Deterioration")

    def test_invariant_12_pattern_frequency_led(self):
        mock_metrics = {"excess_cost": 5000.0, "incidence_effect": 4000.0, "severity_effect": 500.0}
        pattern = self.engine.classify_pattern(mock_metrics, True, False)
        self.assertEqual(pattern, "Frequency-Led Deterioration")

    def test_invariant_13_pattern_severity_led(self):
        mock_metrics = {"excess_cost": 5000.0, "incidence_effect": 500.0, "severity_effect": 4000.0}
        pattern = self.engine.classify_pattern(mock_metrics, False, True)
        self.assertEqual(pattern, "Severity-Led Deterioration")

    def test_invariant_14_pattern_dual_trigger(self):
        mock_metrics = {"excess_cost": 5000.0, "incidence_effect": 2500.0, "severity_effect": 2500.0}
        pattern = self.engine.classify_pattern(mock_metrics, True, True)
        self.assertEqual(pattern, "Frequency and Severity Deterioration")

    def test_invariant_15_pattern_mix_interaction(self):
        mock_metrics = {"excess_cost": 5000.0, "incidence_effect": 1000.0, "severity_effect": 1000.0, "mix_effect": 3000.0}
        pattern = self.engine.classify_pattern(mock_metrics, False, False)
        self.assertEqual(pattern, "Mix / Interaction Deterioration")

    # ---------------------------------------------------------
    # SEGMENT SURVEILLANCE & DRILLED DOWN METRICS
    # ---------------------------------------------------------

    def test_invariant_16_segment_contributions(self):
        # Verify segment positive excess cost is less than or equal to portfolio total positive excess cost
        metrics = self.engine.calculate_metrics(self.df_scen)
        port_pec = metrics["positive_excess_cost"]
        segments = self.engine.calculate_segment_metrics(self.df_scen, port_pec)
        
        for seg in segments:
            self.assertTrue(seg["positive_excess_claim_cost"] <= port_pec)
            self.assertTrue(seg["contribution_share"] <= 1.0)

    # ---------------------------------------------------------
    # ISSUE 6: FREQUENCY x SEVERITY O/E COUNTEREXAMPLE
    # ---------------------------------------------------------

    def test_invariant_17_freq_times_sev_oe_not_equal_combined_oe(self):
        """
        Deterministic counterexample proving Freq_OE * Sev_OE != Combined_Cost_OE.
        
        5-policyholder portfolio with heterogeneous expected severity:
        
        Policyholder | Exp_Freq | Exp_Sev | Claim | Actual_Amount
        A            | 0.10     | 500     | 0     | 0
        B            | 0.10     | 500     | 0     | 0
        C            | 0.10     | 500     | 1     | 600
        D            | 0.10     | 5000    | 1     | 5500
        E            | 0.10     | 5000    | 0     | 0
        
        Expected Claims = 0.5
        Actual Claims = 2
        Freq O/E = 2/0.5 = 4.0
        
        Severity O/E (over actual claimants C,D):
          Observed = 600 + 5500 = 6100
          Expected (conditional) = 500 + 5000 = 5500
          Sev_OE = 6100/5500 = 1.109...
        
        Combined Cost O/E:
          Expected_Total = 0.1*500 + 0.1*500 + 0.1*500 + 0.1*5000 + 0.1*5000 = 1150
          Observed_Total = 6100
          Combined_OE = 6100/1150 = 5.304...
        
        Freq_OE * Sev_OE = 4.0 * 1.109... = 4.436...
        Combined_OE = 5.304...
        
        4.436... != 5.304...  (QED)
        
        The inequality arises because Severity O/E uses conditional expected severity
        over actual claimants (who are disproportionately high-severity), while
        Combined O/E uses prospective expected cost over all policyholders.
        """
        df_counter = pd.DataFrame({
            'Exposure': [1.0, 1.0, 1.0, 1.0, 1.0],
            'Expected_Frequency': [0.10, 0.10, 0.10, 0.10, 0.10],
            'Expected_Severity': [500.0, 500.0, 500.0, 5000.0, 5000.0],
            'Claim': [0, 0, 1, 1, 0],
            'Actual_Claim_Amount': [0.0, 0.0, 600.0, 5500.0, 0.0]
        })
        
        # Frequency O/E
        expected_claims = df_counter['Expected_Frequency'].sum()  # 0.5
        actual_claims = df_counter['Claim'].sum()  # 2
        freq_oe = actual_claims / expected_claims  # 4.0
        
        # Severity O/E (over actual claimants only)
        claimants = df_counter[df_counter['Claim'] == 1]
        sev_obs = claimants['Actual_Claim_Amount'].sum()  # 6100
        sev_exp = claimants['Expected_Severity'].sum()  # 5500
        sev_oe = sev_obs / sev_exp  # 1.1090909...
        
        # Combined Cost O/E
        expected_total_cost = (df_counter['Exposure'] * df_counter['Expected_Frequency'] * df_counter['Expected_Severity']).sum()  # 1150
        observed_total_cost = df_counter['Actual_Claim_Amount'].sum()  # 6100
        combined_oe = observed_total_cost / expected_total_cost  # 5.3043...
        
        freq_times_sev = freq_oe * sev_oe  # 4.4363...
        
        # The key assertion: Freq_OE * Sev_OE != Combined_Cost_OE
        self.assertNotAlmostEqual(freq_times_sev, combined_oe, places=2,
            msg=f"Freq_OE*Sev_OE={freq_times_sev:.4f} should NOT equal Combined_OE={combined_oe:.4f}")
        
        # Verify via engine
        metrics = self.engine.calculate_metrics(df_counter)
        self.assertAlmostEqual(metrics['combined_oe'], combined_oe, places=4)
        
        # Verify decomposition still reconciles for this counterexample
        total_drift = metrics['observed_total_cost'] - metrics['expected_total_cost']
        decomp_sum = metrics['incidence_effect'] + metrics['severity_effect'] + metrics['mix_effect']
        self.assertAlmostEqual(total_drift, decomp_sum, delta=0.01)

    # ---------------------------------------------------------
    # ISSUE 7: CROSS-ENGINE ALIGNMENT TESTS
    # ---------------------------------------------------------

    def test_invariant_18_cross_engine_alignment_positive(self):
        """
        Positive test: matching (dimension, segment) in both engines produces alignment.
        Frequency Region:North + Severity Region:North -> cross_engine_alignment = True
        """
        import datetime
        mock_state = {
            "freq_surveillance": {
                "triggered": True,
                "segment_metrics": {
                    "candidates": [{
                        "dimension": "Region",
                        "segment": "North",
                        "fdr_significant": True,
                        "observed_rate": 0.08,
                        "expected_rate": 0.06,
                        "q_value": 0.01,
                        "contribution_share": 0.5
                    }]
                }
            },
            "sev_surveillance": {
                "triggered": True,
                "segment_metrics": {
                    "candidates": [{
                        "dimension": "Region",
                        "segment": "North",
                        "fdr_significant": True,
                        "observed_severity": 1500.0,
                        "expected_severity": 1200.0,
                        "oe_ratio": 1.25,
                        "q_value": 0.02,
                        "contribution_share": 0.4
                    }]
                }
            },
            "comb_segments": []
        }
        
        evidence = self.coordinator.generate_normalized_evidence(mock_state)
        
        # There should be exactly 2 evidence records (1 freq + 1 sev), both aligned
        freq_ev = [e for e in evidence if e["engine_source"] == "frequency"]
        sev_ev = [e for e in evidence if e["engine_source"] == "severity"]
        
        self.assertEqual(len(freq_ev), 1)
        self.assertEqual(len(sev_ev), 1)
        self.assertTrue(freq_ev[0]["cross_engine_alignment"], 
            "Frequency evidence should be aligned when matching Severity segment")
        self.assertTrue(sev_ev[0]["cross_engine_alignment"],
            "Severity evidence should be aligned when matching Frequency segment")

    def test_invariant_19_cross_engine_alignment_negative(self):
        """
        Negative test: different (dimension, segment) must NOT produce alignment.
        Frequency Region:North + Severity Age_Group:60+ -> cross_engine_alignment = False
        """
        import datetime
        mock_state = {
            "freq_surveillance": {
                "triggered": True,
                "segment_metrics": {
                    "candidates": [{
                        "dimension": "Region",
                        "segment": "North",
                        "fdr_significant": True,
                        "observed_rate": 0.08,
                        "expected_rate": 0.06,
                        "q_value": 0.01,
                        "contribution_share": 0.5
                    }]
                }
            },
            "sev_surveillance": {
                "triggered": True,
                "segment_metrics": {
                    "candidates": [{
                        "dimension": "Age_Group",
                        "segment": "60+",
                        "fdr_significant": True,
                        "observed_severity": 1800.0,
                        "expected_severity": 1200.0,
                        "oe_ratio": 1.50,
                        "q_value": 0.02,
                        "contribution_share": 0.6
                    }]
                }
            },
            "comb_segments": []
        }
        
        evidence = self.coordinator.generate_normalized_evidence(mock_state)
        
        freq_ev = [e for e in evidence if e["engine_source"] == "frequency"]
        sev_ev = [e for e in evidence if e["engine_source"] == "severity"]
        
        self.assertEqual(len(freq_ev), 1)
        self.assertEqual(len(sev_ev), 1)
        self.assertFalse(freq_ev[0]["cross_engine_alignment"],
            "Frequency Region:North must NOT align with Severity Age_Group:60+")
        self.assertFalse(sev_ev[0]["cross_engine_alignment"],
            "Severity Age_Group:60+ must NOT align with Frequency Region:North")

    def test_invariant_20_cross_engine_alignment_semantics_documented(self):
        """
        Verify alignment uses exact (dimension, segment) tuple equality, not string containment.
        """
        mock_state = {
            "freq_surveillance": {
                "triggered": True,
                "segment_metrics": {
                    "candidates": [{
                        "dimension": "Region",
                        "segment": "North",
                        "fdr_significant": True,
                        "observed_rate": 0.08,
                        "expected_rate": 0.06,
                        "q_value": 0.01,
                        "contribution_share": 0.5
                    }]
                }
            },
            "sev_surveillance": {
                "triggered": True,
                "segment_metrics": {
                    "candidates": [{
                        "dimension": "Region",
                        "segment": "Northeast",  # Contains "North" but is NOT the same
                        "fdr_significant": True,
                        "observed_severity": 1500.0,
                        "expected_severity": 1200.0,
                        "oe_ratio": 1.25,
                        "q_value": 0.02,
                        "contribution_share": 0.4
                    }]
                }
            },
            "comb_segments": []
        }
        
        evidence = self.coordinator.generate_normalized_evidence(mock_state)
        
        for ev in evidence:
            self.assertFalse(ev["cross_engine_alignment"],
                f"Region:North must NOT align with Region:Northeast (substring match is invalid)")


if __name__ == '__main__':
    unittest.main()
