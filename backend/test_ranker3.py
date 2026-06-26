import pandas as pd
from tools.feature_ranker import rank_features

df = pd.read_csv("data/scenario_5_family_respiratory_east.csv")
latest_year = df['Year'].max()
df = df[df['Year'] == latest_year]

df = df[(df['Product'] == 'Family Plus') & (df['Region'] == 'East')]

print(df.groupby('Claim_Category').agg(
    exposure=('Exposure', 'sum'),
    claims=('Claim', 'sum'),
    expected=('Expected_Frequency', 'mean')
))

