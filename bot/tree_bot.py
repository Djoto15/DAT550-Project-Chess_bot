from sklearn.tree import DecisionTreeClassifier
import chess.pgn
import chess
import random

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine import Engine

class TreeBot:
    def __init__(self, engine, color):
        self.clf = DecisionTreeClassifier()
        self.move_map = {}  # maps move to index
        self.reverse_move_map = {}  # reverse mapping
        self.engine = engine
        self.color = color

    def extract_features(self, board):
        """
        Extract material balance feature (difference in piece material value).
        """
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
        }

        # Calculate material balance
        white_material = 0
        black_material = 0
        for piece_type in piece_values:
            white_material += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
            black_material += len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]
        
        material_balance = white_material - black_material

        # Return the material balance as the only feature
        features = [material_balance]

        return features


    def fit(self, pgn_path):
        """Train the decision tree on the PGN games."""
        X = []
        y = []
        move_index = 0
        print("Started training...")

        with open(pgn_path) as pgn:
            while game := chess.pgn.read_game(pgn):
                board = game.board()
                for move in game.mainline_moves():
                    features = self.extract_features(board)
                    move_uci = move.uci()

                    if move_uci not in self.move_map:
                        self.move_map[move_uci] = move_index
                        self.reverse_move_map[move_index] = move_uci
                        move_index += 1

                    X.append(features)
                    y.append(self.move_map[move_uci])
                    board.push(move)

        self.clf.fit(X, y)
        print("Bot training finished.")

    def predict(self):
        """
        Given a board position, predict the best move to decrease the opponent's material balance.
        """
        best_move = None
        best_material_balance_change = float('inf')  # Start with a large positive value
        
        for move in self.engine.legal_moves():
            # Make the move to simulate the result
            self.engine.push(move)
            
            # Extract the material balance after the move
            material_balance_after_move = self.extract_features(self.engine.board)[0]  # Use the material balance feature
            
            # Calculate the change in material balance (how much the opponent's material decreases)
            material_balance_change = material_balance_after_move
            
            # Check if this move decreases the opponent's material more
            if material_balance_change < best_material_balance_change:
                best_material_balance_change = material_balance_change
                best_move = move
            
            # Undo the move after evaluating it
            self.engine.board.pop()
        
        # Return the move that decreases the opponent's material the most
        return best_move


engine = Engine()
bot = TreeBot(engine, "white")
bot.fit("data/1800thresh_1448.pgn")

# Predict a move from the starting position
board = chess.Board()
while not board.is_game_over():
    move = bot.predict()
    print(f"Bot plays: {move}")
    board.push(move)
    print(board)

