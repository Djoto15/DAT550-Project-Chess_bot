import chess
import chess.pgn
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

# Add parent directory to path to import engine and bots
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine import Engine
from baseline_model import Stockfish

class Evaluation:
    def __init__(self, engine, white_player, black_player, stockfish_engine_path="/usr/games/stockfish"):
        self.white = white_player
        self.black = black_player
        self.engine = engine
        self.stockfish_engine_path = stockfish_engine_path

    def evaluate_board(self, board, stockfish):
        return stockfish.evaluate(board)
    
    def evaluate_game(self, game_path):
        # Load PGN game
        with open(game_path) as pgn:
            game = chess.pgn.read_game(pgn)

        board = game.board()
        evaluations = []

        for i, move in enumerate(game.mainline_moves()):
            board.push(move)

            with Stockfish(self.stockfish_engine_path, elo=200) as stockfish:
                eval_info = self.evaluate_board(board, stockfish)
                evaluations.append(eval_info)

        self.draw_scores(evaluations)




    def play_game(self):
        board = self.engine.board
        scores = []
        print("Game has begun...")
        MAX_MOVES = 60
        moves = 0

        with Stockfish(self.stockfish_engine_path, elo=200) as stockfish:
            while not board.is_game_over() and moves < MAX_MOVES:
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
                moves += 1


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
