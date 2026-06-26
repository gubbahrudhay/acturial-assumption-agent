import pandas as pd
from tools.drift_detector import detect_drift

df = pd.read_csv("data/scenario_2_senior_cancer_north.csv")
latest_year = df['Year'].max()
df = df[df['Year'] == latest_year]

print(detect_drift(df))
