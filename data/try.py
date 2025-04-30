import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

df = pd.read_csv("data/dataset.csv")
# print(df.head())
# print(df["phase"].value_counts())

# =============== Opening phase ===============

# opening_df = df[df["phase"] == "opening"]
# eco_counts = opening_df["eco"].value_counts().sort_values(ascending=False)

# # Plot
# plt.figure(figsize=(16, 6))
# sns.barplot(x=eco_counts.index, y=eco_counts.values, palette="viridis")

# plt.title("Opening Position Counts by ECO Code")
# plt.xlabel("ECO Code")
# plt.ylabel("Number of Positions")
# plt.xticks(rotation=90)
# plt.grid(True)
# plt.tight_layout()
# plt.show()

# =============== Moves repartition ===============


# Extract move number (6th field in FEN)
df["move_number"] = df["fen"].apply(lambda fen: int(fen.split()[-1]))

# Plot histograms by phase
plt.figure(figsize=(12, 6))
sns.histplot(data=df, x="move_number", hue="phase", element="step", common_norm=False, bins=30)
plt.title("Move Number Distribution per Phase")
plt.xlabel("Move Number")
plt.ylabel("Number of Positions")
plt.grid(True)
plt.tight_layout()
plt.show()



# =============== Oppening repartition ===============
# opening_df = df[df["phase"] == "opening"].copy()

# # Extract move number (6th field in FEN)
# opening_df["move_number"] = opening_df["fen"].apply(lambda fen: int(fen.split()[-1]))

# # Plot histogram
# plt.figure(figsize=(10, 5))
# sns.histplot(data=opening_df, x="move_number", bins=10, color="skyblue", edgecolor="black")

# plt.title("Opening Positions Move Number Distribution")
# plt.xlabel("Move Number")
# plt.ylabel("Number of Positions")
# plt.grid(True)
# plt.tight_layout()
# plt.show()
