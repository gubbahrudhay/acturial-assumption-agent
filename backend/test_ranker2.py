import pandas as pd
from tools.feature_ranker import rank_features

df = pd.read_csv("data/scenario_5_family_respiratory_east.csv")
latest_year = df['Year'].max()
df = df[df['Year'] == latest_year]

print("Root:")
rankings = rank_features(df, features=['Product', 'Age_Group', 'Region', 'Gender', 'Distribution_Channel', 'Plan_Type', 'Claim_Category', 'Hospital_Type'])
for r in rankings[:3]: print(f"  {r['feature']}: {r['score']:.6f}")

df = df[df['Product'] == 'Family Plus']
print("\nProduct:Family Plus:")
rankings = rank_features(df, features=['Age_Group', 'Region', 'Gender', 'Distribution_Channel', 'Plan_Type', 'Claim_Category', 'Hospital_Type'])
for r in rankings[:3]: print(f"  {r['feature']}: {r['score']:.6f}")

df = df[df['Region'] == 'East']
print("\nProduct:Family Plus -> Region:East:")
rankings = rank_features(df, features=['Age_Group', 'Gender', 'Distribution_Channel', 'Plan_Type', 'Claim_Category', 'Hospital_Type'])
for r in rankings[:3]: print(f"  {r['feature']}: {r['score']:.6f}")
