import chess
import matplotlib.pyplot as plt
import numpy as np

import sys
import os

# Add parent directory to path to import engine and bots
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine import Engine
from bot import Stockfish, Classifier, Regression

class Evaluation():
    def __init__(self, engine, white_player, black_player):
        self.white = white_player
        self.black = black_player
        self.engine = engine
        self.stockfish = Stockfish(self.engine, elo=200)

    def evaluate_board(self, board):
        """
        Evaluate the current board state using Stockfish evaluate method. 
            Positive score -> white's advantage 
            Negative score -> black's advantage
        """
        return self.stockfish.evaluate(board)

    def play_game(self):
        """
        Plays a game between white and black and return a list of score.
        """
        board = self.engine.board
        scores = []
        print("Game has begun...")

        while not board.is_game_over():
            # White's turn
            if board.turn == chess.WHITE:
                white_move = self.white.predict()[0]
                if white_move is None:
                    print("No move left for white to play.")
                    break
                board.push(white_move)
                scores.append(self.stockfish.evaluate(board))

            else:       # black's turn
                black_move = self.black.predict()[0]
                if black_move is None:
                    print("No move left for black to play.")
                    break
                board.push(black_move)
                scores.append(self.stockfish.evaluate(board))

        print("Game is finished.")
        self.stockfish.close()
        return scores
    
    def draw_scores(self, scores):

        plt.figure(figsize=(10, 4), facecolor='#1e1e1e')  # Chess.com-style dark background

        scores = np.array(scores)
        max_cp = 100
        clipped_scores = np.clip(scores, -max_cp, max_cp)

        ax = plt.gca()
        ax.set_facecolor('#1e1e1e')  # Dark plot area

        # Fill areas for white and black advantage
        plt.fill_between(range(len(clipped_scores)), clipped_scores, 0,
                        where=(clipped_scores >= 0),
                        facecolor='#f0f0f0', interpolate=True, label="White advantage")  # Light area

        plt.fill_between(range(len(clipped_scores)), clipped_scores, 0,
                        where=(clipped_scores < 0),
                        facecolor='#111111', interpolate=True, label="Black advantage")  # Dark area

        # Line showing the curve
        plt.plot(clipped_scores, color='#999999', linewidth=1.5)

        # 0 line
        plt.axhline(0, color="#999999", linestyle="--", linewidth=0.8)

        # Labels and styling
        plt.ylim(-max_cp, max_cp)
        plt.xlabel("Move Number", color='#dddddd')
        plt.ylabel("Evaluation (centipawns)", color='#dddddd')
        plt.title("Game Evaluation Over Time", color='#dddddd')
        plt.grid(True, linestyle='--', color='#444444', alpha=0.5)

        # Style the ticks
        ax.tick_params(colors='#bbbbbb')

        plt.tight_layout()
        plt.show()






# # Initialize bots
# engine = Engine()
# simple_bot = Classifier(engine, "white")
# simple_bot.fit("data/1800thresh_1448.pgn")

# stockfish_bot = Stockfish(engine, elo=200)  # Adjustable strength

# simple_chess_bot = Regression(engine)
# simple_chess_bot.fit("data/1800thresh_1448.pgn")

# evaluator = Evaluation(engine, white_player=simple_bot, black_player=stockfish_bot)

# # Evaluate game
# scores = evaluator.play_game()
# # print(scores)
# evaluator.draw_scores(scores)
# stockfish_bot.close()