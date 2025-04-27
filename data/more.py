import pandas as pd
import chess
import chess.engine
from tqdm import tqdm

# Path to Stockfish binary
STOCKFISH_PATH = "/usr/games/stockfish"  # Change this if needed

# Load the dataset
df = pd.read_csv("dataset.csv")

# Add a 'best_move' column (initialize with None)
df["best_move"] = None

# Initialize Stockfish engine
engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

# Use tqdm for a progress bar
for i, row in tqdm(df.iterrows(), total=len(df), desc="Analyzing positions"):
    try:
        fen = row["fen"]
        board = chess.Board(fen)
        
        # Skip positions that are already over
        if board.is_game_over():
            continue
        
        # Analyze with Stockfish (depth can be adjusted: 10-15 is good)
        info = engine.analyse(board, chess.engine.Limit(depth=12))
        best_move = info["pv"][0]  # Best move from principal variation
        
        df.at[i, "best_move"] = best_move.uci()
        
    except Exception as e:
        print(f"Error at row {i}: {e}")
        continue

engine.quit()

# Save updated dataset
df.to_csv("dataset2.csv", index=False)
print("✅ Saved dataset2.csv with best_move column added.")
