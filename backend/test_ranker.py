import pandas as pd
from tools.feature_ranker import rank_features

df = pd.read_csv("data/scenario_5_family_respiratory_east.csv")
latest_year = df['Year'].max()
df = df[df['Year'] == latest_year]

rankings = rank_features(df, features=['Product', 'Age_Group', 'Region', 'Gender', 'Distribution_Channel', 'Plan_Type', 'Claim_Category', 'Hospital_Type'])
for r in rankings:
    print(f"{r['feature']}: {r['score']:.6f}")
