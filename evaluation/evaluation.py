import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import chess.engine
from bot import TreeBot, RandomBot
from engine import Engine


# Path to your Stockfish binary (you can specify the version and location)
STOCKFISH_PATH = "/usr/games/stockfish"  # Replace with your Stockfish binary path

# Define the path to the PGN file
pgn_path = "data/1800thresh_1448.pgn"

def evaluate_bot_against_stockfish(tree_bot, max_moves=200, elo=1600):
    """
    Evaluate the tree bot against Stockfish at the specified ELO level.
    """
    board = tree_bot.engine.board
    tree_color = tree_bot.color
    total_moves = 0
    illegal_predictions = 0
    tree_moves = 0

    # Start the Stockfish engine
    with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
        # Set Stockfish's strength based on the given ELO
        engine.configure({"Skill Level": elo // 100})  # Scale Stockfish's skill level
        print(f"Stockfish set to ELO: {elo}")

        while not board.is_game_over() and total_moves < max_moves:
            if board.turn == tree_color:
                move = tree_bot.predict()
                board.push(move)
                tree_moves += 1
            else:
                # Let Stockfish make a move
                result = engine.play(board, chess.engine.Limit(time=2.0))  # Stockfish plays within a 2-second limit
                board.push(result.move)

            total_moves += 1

    print("\n=== Evaluation Results ===")
    print(f"Total moves: {total_moves}")
    print(f"Game result: {board.result()}")

def evaluate(elo=1600):
    engine = Engine()
    tree_bot = TreeBot(engine, "white")
    # tree_bot.fit(pgn_path)


    # Evaluate against Stockfish at the desired ELO
    evaluate_bot_against_stockfish(tree_bot, elo=elo)

if __name__ == "__main__":
    # You can set the ELO level here (e.g., 1600, 1800, 2000)
    elo_level = 200  # Change this to set the desired ELO level
    evaluate(elo=elo_level)
