import os
import yaml
import pandas as pd
import numpy as np
import random
import math
from uuid import uuid4

# Load configurations
config_path = os.path.join(os.path.dirname(__file__), 'generation_config.yaml')
events_path = os.path.join(os.path.dirname(__file__), 'business_events.yaml')
severity_config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'severity_model.yaml')

with open(config_path, 'r') as file:
    config = yaml.safe_load(file)
    
with open(events_path, 'r') as file:
    events_config = yaml.safe_load(file)

with open(severity_config_path, 'r') as file:
    severity_config = yaml.safe_load(file)

# Seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

class ExperienceSimulationEngine:
    def __init__(self, config, events_config, severity_config):
        self.config = config
        self.events_config = events_config
        self.severity_config = severity_config
        self.intercept = -2.94  # Base logit for roughly 5% baseline frequency

    def generate_portfolio_record(self):
        """Generates a single realistic policyholder with natural correlations."""
        product_dict = random.choices(self.config['products'], weights=[p['weight'] for p in self.config['products']])[0]
        product = product_dict['name']
        
        # Introduce correlations
        if product == "Senior Care Gold":
            age_group = random.choices(["18-35", "36-59", "60+"], weights=[0.05, 0.15, 0.80])[0]
        elif product == "Family Plus":
            age_group = random.choices(["18-35", "36-59", "60+"], weights=[0.20, 0.70, 0.10])[0]
        else:
            age_group = random.choices(["18-35", "36-59", "60+"], weights=[0.40, 0.40, 0.20])[0]
            
        region = random.choices(["North", "South", "East", "West"], weights=[0.25, 0.25, 0.25, 0.25])[0]
        gender = random.choices(["M", "F"], weights=[0.5, 0.5])[0]
        plan_type = random.choices(["Basic", "Comprehensive"], weights=[0.4, 0.6])[0]
        dist_channel = random.choices(["Broker", "Direct", "Bancassurance"], weights=[0.5, 0.3, 0.2])[0]
        
        # Determine Age (integer) based on group for schema compatibility
        if age_group == "18-35":
            age = random.randint(18, 35)
        elif age_group == "36-59":
            age = random.randint(36, 59)
        else:
            age = random.randint(60, 85)

        return {
            "Policy_ID": f"POL-{uuid4().hex[:8].upper()}",
            "Customer_ID": f"CUST-{uuid4().hex[:8].upper()}",
            "Product": product,
            "Age_Group": age_group,
            "Age": age,
            "Region": region,
            "Gender": gender,
            "Plan_Type": plan_type,
            "Distribution_Channel": dist_channel,
            "Exposure": 1.0,
            "Premium": float(random.randint(100, 500)) # Simple premium for loss ratio compatibility
        }

    def calculate_expected_frequency(self, record, month):
        """Calculates expected frequency using an additive logistic model (without anomalies)."""
        logit = self.intercept
        
        # Product effect
        product_effs = {"Standard Care": 0.0, "Senior Care Gold": 0.8, "Family Plus": 0.2}
        logit += product_effs.get(record['Product'], 0)
        
        # Age effect
        age_effs = {"18-35": -0.2, "36-59": 0.0, "60+": 0.6}
        logit += age_effs.get(record['Age_Group'], 0)
        
        # Region effect
        region_effs = {"North": 0.1, "South": -0.1, "East": 0.0, "West": -0.05}
        logit += region_effs.get(record['Region'], 0)
        
        # Season effect (Winter bump)
        if month in self.config['seasons']['Winter']:
            logit += 0.15
            
        probability = 1.0 / (1.0 + math.exp(-logit))
        return probability, logit

    def apply_business_events(self, record, base_logit, year, month, active_events):
        """Applies gradual frequency business events to the logit if the record matches."""
        current_logit = base_logit
        target_diseases = []
        
        for event in active_events:
            if not event.get('enabled', True):
                continue
            if event.get('type', 'frequency') != 'frequency':
                continue
                
            # Assume events happen in 2024 for this simulation
            if year < 2024:
                continue
                
            start_month = event['start_month']
            duration = event['duration']
            
            if month < start_month:
                continue
                
            # Check demographic match
            match = True
            for key, val in event.get('affected_population', {}).items():
                if record.get(key.capitalize()) != val:
                    match = False
                    break
                    
            if match:
                # Calculate progression
                months_active = month - start_month + 1
                if months_active > duration:
                    progression = 1.0
                else:
                    if event['progression_curve'] == 'linear':
                        progression = months_active / duration
                    elif event['progression_curve'] == 'exponential':
                        progression = (months_active / duration) ** 2
                    else: # step
                        progression = 1.0
                        
                effect = event['effect_size'] * progression
                current_logit += effect
                
                if 'target_disease' in event:
                    target_diseases.append(event['target_disease'])
                    
        probability = 1.0 / (1.0 + math.exp(-current_logit))
        return probability, target_diseases

    def calculate_expected_severity(self, record, claim_category, hospital_type, month, year):
        """Calculates expected severity using log-link model from baseline assumptions (no anomalies)."""
        base_sev = self.severity_config['base_expected_severity']
        intercept = math.log(base_sev)
        
        rel = self.severity_config['severity_relativities']
        
        # Product
        beta_product = math.log(rel['product'].get(record['Product'], 1.0))
        
        # Age Group
        beta_age = math.log(rel['age'].get(record['Age_Group'], 1.0))
        
        # Region
        beta_region = math.log(rel['region'].get(record['Region'], 1.0))
        
        # Claim Category
        beta_cat = math.log(rel['claim_category'].get(claim_category, 1.0))
        
        # Hospital Type
        beta_hosp = math.log(rel['hospital_type'].get(hospital_type, 1.0))
        
        # Expected Trend (inflation) - Compounding monthly rate
        expected_annual_trend = self.severity_config.get('expected_annual_trend', 0.05)
        expected_monthly_rate = (1.0 + expected_annual_trend) ** (1.0 / 12.0) - 1.0
        t_months = (year - 2022) * 12 + (month - 1)
        beta_trend = t_months * math.log(1.0 + expected_monthly_rate)
        
        linear_predictor = intercept + beta_product + beta_age + beta_region + beta_cat + beta_hosp + beta_trend
        return math.exp(linear_predictor)

    def calculate_prospective_expected_severity(self, record, month, year):
        """Calculates prospective expected severity as the expectation of expected severity over category and hospital type."""
        base_sev = self.severity_config['base_expected_severity']
        intercept = math.log(base_sev)
        rel = self.severity_config['severity_relativities']
        
        beta_product = math.log(rel['product'].get(record['Product'], 1.0))
        beta_age = math.log(rel['age'].get(record['Age_Group'], 1.0))
        beta_region = math.log(rel['region'].get(record['Region'], 1.0))
        
        expected_annual_trend = self.severity_config.get('expected_annual_trend', 0.05)
        expected_monthly_rate = (1.0 + expected_annual_trend) ** (1.0 / 12.0) - 1.0
        t_months = (year - 2022) * 12 + (month - 1)
        beta_trend = t_months * math.log(1.0 + expected_monthly_rate)
        
        base_factor = math.exp(intercept + beta_product + beta_age + beta_region + beta_trend)
        
        # Calculate expectation of rel_category * rel_hospital
        diseases = self.config['disease_categories']
        is_winter = month in self.config['seasons']['Winter']
        
        if is_winter:
            # Respiratory is 3, others are 1
            disease_weights = {d: (3.0 if d == "Respiratory" else 1.0) for d in diseases}
        else:
            disease_weights = {d: 1.0 for d in diseases}
            
        sum_weights = sum(disease_weights.values())
        disease_probs = {d: w / sum_weights for d, w in disease_weights.items()}
        
        expected_mult = 0.0
        for d in diseases:
            p_d = disease_probs[d]
            r_cat = rel['claim_category'].get(d, 1.0)
            
            if d in ["Cancer", "Cardiac"]:
                hosp_probs = {"Public": 0.2, "Private": 0.6, "Specialist": 0.2}
            else:
                hosp_probs = {"Public": 0.5, "Private": 0.3, "Specialist": 0.2}
                
            for h, p_h in hosp_probs.items():
                r_hosp = rel['hospital_type'].get(h, 1.0)
                expected_mult += p_d * r_cat * p_h * r_hosp
                
        return base_factor * expected_mult

    def apply_severity_events(self, record, expected_severity, claim_category, hospital_type, year, month, active_events):
        """Calculates expected severity for the actual claim cost process after event adjustments."""
        actual_expected_severity = expected_severity
        is_outlier = False
        outlier_multiplier = 1.0
        
        for event in active_events:
            if not event.get('enabled', True):
                continue
                
            if year < 2024:
                continue
                
            # Check target population criteria
            match = True
            for k, v in event.get('affected_population', {}).items():
                if k == 'region' and record.get('Region') != v:
                    match = False
                elif k == 'age_group' and record.get('Age_Group') != v:
                    match = False
                elif k == 'product' and record.get('Product') != v:
                    match = False
                elif k == 'claim_category' and claim_category != v:
                    match = False
                elif k == 'hospital_type' and hospital_type != v:
                    match = False
                    
            if match:
                # Severity events use linear or compound progression
                months_active = month - event.get('start_month', 1) + 1
                duration = event.get('duration', 12)
                
                # Curve progression
                progression = 0.0
                if months_active > 0:
                    if event.get('progression_curve') == 'compound':
                        # compounding monthly trend
                        progression = (1.0 + event['effect_size']) ** (min(months_active, duration) / 12.0) - 1.0
                        actual_expected_severity *= (1.0 + progression)
                        continue
                    elif event.get('progression_curve') == 'linear':
                        progression = min(months_active / duration, 1.0)
                        
                if event['type'] == 'severity':
                    actual_expected_severity *= (1.0 + event['effect_size'] * progression)
                elif event['type'] == 'severity_outlier':
                    is_outlier = True
                    outlier_multiplier = event['effect_size']
                    
        return actual_expected_severity, is_outlier, outlier_multiplier

    def simulate_claim(self, probability, target_diseases, month, year):
        """Simulates claim occurrence and assigns attributes ONLY if claim is True."""
        is_claim = 1 if random.random() < probability else 0
        
        if not is_claim:
            return 0, None, None, None, None
            
        # Assign Date
        day = random.randint(1, 28)
        claim_date = f"{year}-{month:02d}-{day:02d}"
        
        # Assign Disease (Weighted by target_diseases)
        diseases = self.config['disease_categories']
        weights = [1] * len(diseases)
        
        for i, d in enumerate(diseases):
            if d in target_diseases:
                weights[i] = 10 
            elif month in self.config['seasons']['Winter'] and d == "Respiratory":
                weights[i] = 3
                
        claim_category = random.choices(diseases, weights=weights)[0]
        
        # Assign Hospital (Correlations)
        if claim_category in ["Cancer", "Cardiac"]:
            hospital_weights = [0.2, 0.6, 0.2] # More likely Private
        else:
            hospital_weights = [0.5, 0.3, 0.2]
            
        hospital_type = random.choices(["Public", "Private", "Specialist"], weights=hospital_weights)[0]
        
        # Assign Status
        status_weights = [0.85, 0.10, 0.05]
        claim_status = random.choices(["Approved", "Rejected", "Pending"], weights=status_weights)[0]
        
        return 1, claim_category, hospital_type, claim_status, claim_date

    def generate_dataset(self, filename, active_event_names=None, format_type='combined', num_policies_mult=1.0):
        records = []
        
        # Filter active events
        active_events = []
        if active_event_names:
            active_events = [e for e in self.events_config['events'] if e['event_name'] in active_event_names]
            
        for year in self.config['years']:
            for month in self.config['months']:
                num_policies = int(self.config['num_policies_per_month'] * num_policies_mult)
                quarter = (month - 1) // 3 + 1
                
                for _ in range(num_policies):
                    record = self.generate_portfolio_record()
                    record["Year"] = year
                    record["Month"] = month
                    record["Quarter"] = f"Q{quarter}"
                    
                    # Expected Frequency (Standard Actuarial Base)
                    exp_prob, base_logit = self.calculate_expected_frequency(record, month)
                    record["Expected_Frequency"] = exp_prob
                    
                    # Business Event Adjustment
                    actual_prob, target_diseases = self.apply_business_events(record, base_logit, year, month, active_events)
                    
                    # Claim Simulation
                    claim, claim_cat, hosp_type, status, date = self.simulate_claim(actual_prob, target_diseases, month, year)
                    
                    # Prospective Expected Severity (independent of realized Claim indicator)
                    prospective_exp_sev = self.calculate_prospective_expected_severity(record, month, year)
                    
                    if claim == 1:
                        # Conditional expected severity used only for actual amount generation
                        cond_exp_sev = self.calculate_expected_severity(record, claim_cat, hosp_type, month, year)
                        actual_expected_sev, is_outlier, outlier_mult = self.apply_severity_events(
                            record, cond_exp_sev, claim_cat, hosp_type, year, month, active_events
                        )
                        
                        # Sample stochastically from Lognormal distribution
                        sigma = self.severity_config['category_volatility'].get(claim_cat, 0.40)
                        mu = math.log(actual_expected_sev) - (sigma ** 2) / 2.0
                        actual_amount = np.random.lognormal(mu, sigma)
                        
                        if is_outlier:
                            actual_amount *= outlier_mult
                            
                        record["Claim"] = 1
                        record["Claim_ID"] = f"CLM-{uuid4().hex[:8].upper()}"
                        record["Claim_Category"] = claim_cat
                        record["Hospital_Type"] = hosp_type
                        record["Claim_Status"] = status
                        record["Claim_Date"] = date
                        record["Actual_Claim_Amount"] = float(round(actual_amount, 2))
                        
                        if format_type == 'severity':
                            record["Expected_Severity"] = float(round(cond_exp_sev, 2))
                        else:
                            record["Expected_Severity"] = float(round(prospective_exp_sev, 2))
                    else:
                        record["Claim"] = 0
                        record["Claim_ID"] = None
                        record["Claim_Category"] = None
                        record["Hospital_Type"] = None
                        record["Claim_Status"] = None
                        record["Claim_Date"] = None
                        record["Actual_Claim_Amount"] = 0.0
                        record["Expected_Severity"] = float(round(prospective_exp_sev, 2))
                        
                    # Filter output format
                    if format_type == 'severity':
                        # Claim level dataset, only rows with Claim == 1
                        if record["Claim"] == 1:
                            records.append(record)
                    else:
                        # Combined format - keep all records
                        records.append(record)
                        
        df = pd.DataFrame(records)
        output_path = os.path.join(os.path.dirname(__file__), filename)
        df.to_csv(output_path, index=False)
        print(f"Generated {filename} ({len(df)} rows, Format: {format_type})")

if __name__ == "__main__":
    print("Initializing Experience Simulation Engine...")
    engine = ExperienceSimulationEngine(config, events_config, severity_config)
    
    # 1. Combined Baseline Dataset (covers Frequency and Severity baseline)
    engine.generate_dataset('experience_baseline.csv', active_event_names=[], format_type='combined')
    
    # Copy experience_baseline.csv to insurance_experience.csv to serve as active dataset
    import shutil
    base_src = os.path.join(os.path.dirname(__file__), 'experience_baseline.csv')
    base_dst = os.path.join(os.path.dirname(__file__), 'insurance_experience.csv')
    shutil.copyfile(base_src, base_dst)
    print("Copied experience_baseline.csv to insurance_experience.csv")
    
    # 2. Combined Scenario A (Frequency Drift)
    engine.generate_dataset('experience_scenario_a.csv', active_event_names=["Northern Oncology Growth", "Southern Orthopedic Shift"], format_type='combined')
    
    # 3. Standalone Severity Baseline (only claims, no anomalies)
    engine.generate_dataset('severity_baseline.csv', active_event_names=[], format_type='severity')
    
    # 4. Standalone Severity Gradual Medical Inflation (compounding trend uplift)
    engine.generate_dataset('severity_medical_inflation.csv', active_event_names=["Gradual Medical Inflation"], format_type='severity')
    
    # 5. Standalone Severity Private Hospital Cost Escalation
    engine.generate_dataset('severity_private_hospital_escalation.csv', active_event_names=["Private Hospital Cost Escalation"], format_type='severity')
    
    # 6. Standalone Severity Oncology Shift (North Cancer escalation)
    engine.generate_dataset('severity_oncology_shift.csv', active_event_names=["Oncology Treatment Cost Shift"], format_type='severity')
    
    # 7. Standalone Severity High-Cost Claim Concentration (outliers in North)
    engine.generate_dataset('severity_high_cost_concentration.csv', active_event_names=["High-Cost Claim Concentration"], format_type='severity')
    
    # 8. Standalone Severity Low-Credibility (tiny sample size)
    engine.generate_dataset('severity_low_credibility.csv', active_event_names=[], format_type='severity', num_policies_mult=0.04)
    
    print("\nDatasets generated successfully!")
