# A simple chess bot using decision tree and not trained on a database

import chess
import random
import numpy as np
from sklearn.tree import DecisionTreeRegressor

class ChessBot:
    def __init__(self):
        self.model = DecisionTreeRegressor()
        self.train_dummy_model()

    def play(self, board: chess.Board):
        """Returns the best move based on the trained decision tree."""
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        best_score = -float('inf')
        best_move = random.choice(legal_moves)

        for move in legal_moves:
            board.push(move)
            features = self.extract_features(board)
            score = self.model.predict([features])[0]
            board.pop()

            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def extract_features(self, board: chess.Board):
        """Extracts features from the board: material balance and turn."""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0  # King has no material value for this simple model
        }

        white_material = sum(
            len(board.pieces(piece_type, chess.WHITE)) * value
            for piece_type, value in piece_values.items()
        )

        black_material = sum(
            len(board.pieces(piece_type, chess.BLACK)) * value
            for piece_type, value in piece_values.items()
        )

        material_balance = white_material - black_material
        turn = 1 if board.turn == chess.WHITE else 0

        return np.array([material_balance, turn])

    def train_dummy_model(self):
        """Trains the decision tree on random positions using material balance as label."""
        X = []
        y = []

        for _ in range(500):  # Generate 500 training samples
            board = chess.Board()
            for _ in range(random.randint(0, 20)):  # Play a few random moves
                if board.is_game_over():
                    break
                legal = list(board.legal_moves)
                board.push(random.choice(legal))

            features = self.extract_features(board)
            label = features[0]  # Label = material balance
            X.append(features)
            y.append(label)

        self.model.fit(X, y)

# Example usage (play a single move)
if __name__ == "__main__":
    board = chess.Board()
    bot = ChessBot()

    print("Current board:")
    print(board)

    move = bot.play(board)
    print(f"\nBot chooses move: {move}")
