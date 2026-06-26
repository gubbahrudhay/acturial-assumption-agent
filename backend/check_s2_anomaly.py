import pandas as pd

df = pd.read_csv("data/scenario_2_senior_cancer_north.csv")
latest_year = df['Year'].max()
df = df[df['Year'] == latest_year]

# True anomaly segment
segment = df[(df['Region'] == 'North') & (df['Age_Group'] == '60+') & (df['Claim_Category'] == 'Cancer')]

expected_claims = (segment['Expected_Frequency'] * segment['Exposure']).sum()
actual_claims = segment['Claim'].sum()
exposure = segment['Exposure'].sum()

print(f"Exposure: {exposure}")
print(f"Expected Freq: {expected_claims/exposure:.4f}")
print(f"Actual Freq: {actual_claims/exposure:.4f}")
print(f"Relative Drift: {(actual_claims - expected_claims) / expected_claims * 100:.2f}%")

