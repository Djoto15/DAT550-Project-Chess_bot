import pandas as pd

# Replace this with the path to your actual CSV file
csv_file = 'positions.csv'

# Load the CSV file into a DataFrame
df = pd.read_csv(csv_file)

# Count
phase_counts = df['phase'].value_counts()
opening_counts = df['eco'].value_counts()

print(f"Number of positions for each phase: {phase_counts}")
print(f"Total number of different openings: {opening_counts.shape[0]}")
print(f"\nCount of games for each opening: {opening_counts}")

