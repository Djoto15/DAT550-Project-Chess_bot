import chess
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

# Add parent directory to path to import engine and bots
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine import Engine
from bot import Stockfish, RegressionTreeBot

class Evaluation:
    def __init__(self, engine, white_player, black_player, stockfish_engine_path="/usr/games/stockfish"):
        self.white = white_player
        self.black = black_player
        self.engine = engine
        self.stockfish_engine_path = stockfish_engine_path

    def evaluate_board(self, board, stockfish):
        return stockfish.evaluate(board)

    def play_game(self):
        board = self.engine.board
        scores = []
        print("Game has begun...")

        with Stockfish(self.stockfish_engine_path, elo=200) as stockfish:
            while not board.is_game_over():
                if board.turn == chess.WHITE:
                    white_move = self.white.predict()
                    if white_move is None:
                        print("No move left for white.")
                        break
                    board.push(white_move)
                    scores.append(self.evaluate_board(board, stockfish))

                else:
                    black_move = self.black.predict()
                    if black_move is None:
                        print("No move left for black.")
                        break
                    board.push(black_move)
                    scores.append(self.evaluate_board(board, stockfish))

        print("Game is finished.")
        return scores

    def draw_scores(self, scores):
        plt.figure(figsize=(10, 4), facecolor='#1e1e1e')

        scores = np.array(scores)
        max_cp = 100
        clipped_scores = np.clip(scores, -max_cp, max_cp)

        ax = plt.gca()
        ax.set_facecolor('#1e1e1e')

        plt.fill_between(range(len(clipped_scores)), clipped_scores, 0,
                         where=(clipped_scores >= 0),
                         facecolor='#f0f0f0', interpolate=True, label="White advantage")

        plt.fill_between(range(len(clipped_scores)), clipped_scores, 0,
                         where=(clipped_scores < 0),
                         facecolor='#111111', interpolate=True, label="Black advantage")

        plt.plot(clipped_scores, color='#999999', linewidth=1.5)
        plt.axhline(0, color="#999999", linestyle="--", linewidth=0.8)

        plt.ylim(-max_cp, max_cp)
        plt.xlabel("Move Number", color='#dddddd')
        plt.ylabel("Evaluation (centipawns)", color='#dddddd')
        plt.title("Game Evaluation Over Time", color='#dddddd')
        plt.grid(True, linestyle='--', color='#444444', alpha=0.5)
        ax.tick_params(colors='#bbbbbb')
        plt.tight_layout()
        plt.show()


# === MAIN ===

# Create engine instance
engine = Engine()

# Choose which bot to test:


# regression_tree_bot = RegressionTreeBot(engine)
# regression_tree_bot.fit()

# # Define stockfish opponent (uses internal engine path)
# stockfish_bot = Stockfish(engine, elo=200)

white = RegressionTreeBot(engine)
black = RegressionTreeBot(engine)

white.fit()
black.fit()

# Run evaluation
evaluator = Evaluation(engine, white_player=white, black_player=black)
scores = evaluator.play_game()
evaluator.draw_scores(scores)
