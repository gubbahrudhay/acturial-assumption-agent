import os
import sys
import numpy as np
import pandas as pd
import yaml
import math
from uuid import uuid4

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.generate_datasets import ExperienceSimulationEngine

config_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'generation_config.yaml')
events_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'business_events.yaml')
severity_config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'severity_model.yaml')

with open(config_path, 'r') as file:
    config = yaml.safe_load(file)
with open(events_path, 'r') as file:
    events = yaml.safe_load(file)
with open(severity_config_path, 'r') as file:
    sev_config = yaml.safe_load(file)

engine = ExperienceSimulationEngine(config, events, sev_config)

# Run 50 null simulations with different seeds
east_oes = []
broker_oes = []

print("Running 50 null simulations...")
for seed in range(100, 150):
    np.random.seed(seed)
    import random
    random.seed(seed)
    
    # We can run a fast inline simulation of just the claims
    records = []
    for year in config['years']:
        for month in config['months']:
            num_policies = config['num_policies_per_month']
            for _ in range(num_policies):
                record = engine.generate_portfolio_record()
                record["Year"] = year
                record["Month"] = month
                exp_prob, base_logit = engine.calculate_expected_frequency(record, month)
                claim, claim_cat, hosp_type, status, date = engine.simulate_claim(exp_prob, [], month, year)
                if claim == 1:
                    exp_sev = engine.calculate_expected_severity(record, claim_cat, hosp_type, month, year)
                    sigma = sev_config['category_volatility'].get(claim_cat, 0.40)
                    mu = math.log(exp_sev) - (sigma ** 2) / 2.0
                    actual_amount = np.random.lognormal(mu, sigma)
                    record["Expected_Severity"] = exp_sev
                    record["Actual_Claim_Amount"] = actual_amount
                    records.append(record)
                    
    df = pd.DataFrame(records)
    
    # East Region O/E
    east = df[df['Region'] == 'East']
    east_oe = east['Actual_Claim_Amount'].sum() / east['Expected_Severity'].sum()
    east_oes.append(east_oe)
    
    # Broker O/E
    broker = df[df['Distribution_Channel'] == 'Broker']
    broker_oe = broker['Actual_Claim_Amount'].sum() / broker['Expected_Severity'].sum()
    broker_oes.append(broker_oe)

print(f"East Region O/E - Mean: {np.mean(east_oes):.4f}, Std: {np.std(east_oes):.4f}, Min: {np.min(east_oes):.4f}, Max: {np.max(east_oes):.4f}")
print(f"Broker Channel O/E - Mean: {np.mean(broker_oes):.4f}, Std: {np.std(broker_oes):.4f}, Min: {np.min(broker_oes):.4f}, Max: {np.max(broker_oes):.4f}")
