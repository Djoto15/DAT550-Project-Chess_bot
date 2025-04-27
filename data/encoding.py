import pandas as pd


df = pd.read_csv("dataset2.csv")

phase_map = {"opening": 0, "middlegame": 1, "endgame": 2}
df["phase"] = df["phase"].map(phase_map)

df.to_csv("dataset3.csv", index=False)

