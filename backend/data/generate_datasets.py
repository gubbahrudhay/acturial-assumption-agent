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

with open(config_path, 'r') as file:
    config = yaml.safe_load(file)
    
with open(events_path, 'r') as file:
    events_config = yaml.safe_load(file)

# Seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

class ExperienceSimulationEngine:
    def __init__(self, config, events_config):
        self.config = config
        self.events_config = events_config
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
        
        return {
            "Policy_ID": f"POL-{uuid4().hex[:8].upper()}",
            "Customer_ID": f"CUST-{uuid4().hex[:8].upper()}",
            "Product": product,
            "Age_Group": age_group,
            "Region": region,
            "Gender": gender,
            "Plan_Type": plan_type,
            "Distribution_Channel": dist_channel,
            "Exposure": 1.0
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
        """Applies gradual business events to the logit if the record matches."""
        current_logit = base_logit
        target_diseases = []
        
        for event in active_events:
            if not event.get('enabled', True):
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

    def simulate_claim(self, probability, target_diseases, month, year):
        """Simulates claim occurrence and assigns attributes ONLY if claim is True."""
        is_claim = 1 if random.random() < probability else 0
        
        if not is_claim:
            return 0, None, None, None, None
            
        # Assign Date
        day = random.randint(1, 28)
        claim_date = f"{year}-{month:02d}-{day:02d}"
        
        # Assign Disease (Weighted by target_diseases to simulate the event's impact on disease distribution)
        diseases = self.config['disease_categories']
        weights = [1] * len(diseases)
        
        for i, d in enumerate(diseases):
            if d in target_diseases:
                weights[i] = 10 # Massive weight shift towards the target disease if an event applies
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
        status_weights = [0.85, 0.10, 0.05] # Approved, Rejected, Pending
        claim_status = random.choices(["Approved", "Rejected", "Pending"], weights=status_weights)[0]
        
        return 1, claim_category, hospital_type, claim_status, claim_date

    def generate_dataset(self, filename, active_event_names=None):
        records = []
        
        # Filter active events
        active_events = []
        if active_event_names:
            active_events = [e for e in self.events_config['events'] if e['event_name'] in active_event_names]
            
        for year in self.config['years']:
            for month in self.config['months']:
                num_policies = self.config['num_policies_per_month']
                quarter = (month - 1) // 3 + 1
                
                for _ in range(num_policies):
                    record = self.generate_portfolio_record()
                    record["Year"] = year
                    record["Month"] = month
                    record["Quarter"] = f"Q{quarter}"
                    
                    # Expected Frequency (Standard Actuarial Base)
                    exp_prob, base_logit = self.calculate_expected_frequency(record, month)
                    record["Expected_Frequency"] = exp_prob
                    
                    # Business Event Adjustment (Actual Physics of the Simulation)
                    actual_prob, target_diseases = self.apply_business_events(record, base_logit, year, month, active_events)
                    
                    # Claim Simulation
                    claim, claim_cat, hosp_type, status, date = self.simulate_claim(actual_prob, target_diseases, month, year)
                    
                    record["Claim"] = claim
                    record["Claim_Category"] = claim_cat
                    record["Hospital_Type"] = hosp_type
                    record["Claim_Status"] = status
                    record["Claim_Date"] = date
                    
                    records.append(record)
                    
        df = pd.DataFrame(records)
        output_path = os.path.join(os.path.dirname(__file__), filename)
        df.to_csv(output_path, index=False)
        print(f"Generated {filename} ({len(df)} rows)")

if __name__ == "__main__":
    print("Initializing Experience Simulation Engine...")
    engine = ExperienceSimulationEngine(config, events_config)
    
    # Generate Baseline
    engine.generate_dataset('experience_baseline.csv', active_event_names=[])
    
    # Generate Scenario A (Cancer & Ortho Events)
    engine.generate_dataset('experience_scenario_a.csv', active_event_names=["Northern Oncology Growth", "Southern Orthopedic Shift"])
    
    print("\nDatasets generated successfully!")
