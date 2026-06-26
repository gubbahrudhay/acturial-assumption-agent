import pandas as pd
from tools.feature_ranker import rank_features

df = pd.read_csv("data/scenario_2_senior_cancer_north.csv")
latest_year = df['Year'].max()
df = df[df['Year'] == latest_year]

print("Root:")
rankings = rank_features(df, features=['Product', 'Age_Group', 'Region', 'Gender', 'Distribution_Channel', 'Plan_Type', 'Claim_Category', 'Hospital_Type'])
for r in rankings[:3]: print(f"  {r['feature']}: {r['score']:.6f}")

df = df[df['Region'] == 'North']
print("\nRegion:North:")
rankings = rank_features(df, features=['Product', 'Age_Group', 'Gender', 'Distribution_Channel', 'Plan_Type', 'Claim_Category', 'Hospital_Type'])
for r in rankings[:3]: print(f"  {r['feature']}: {r['score']:.6f}")

df = df[df['Age_Group'] == '60+']
print("\nRegion:North -> Age_Group:60+:")
rankings = rank_features(df, features=['Product', 'Gender', 'Distribution_Channel', 'Plan_Type', 'Claim_Category', 'Hospital_Type'])
for r in rankings[:3]: print(f"  {r['feature']}: {r['score']:.6f}")
