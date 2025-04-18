import pandas as pd
import chess
import chess.pgn
from sklearn.tree import DecisionTreeRegressor
import numpy as np
from tqdm import tqdm

class RegressionTreeBot:
    def __init__(self, engine, dataset_path="data/dataset.csv"):
        self.model = DecisionTreeRegressor(max_depth=10)
        self.engine = engine
        self.dataset = pd.read_csv(dataset_path)
        self.features = ["material", "mobility", "white_king_safety", "black_king_safety",
                         "white_center_control", "black_center_control"]
        self.model_fitted = False

    def fit(self):
        df = self.dataset.dropna(subset=["evaluation_cp"])  # drop any positions without evaluation
        X = df[self.features]
        y = df["evaluation_cp"]

        print("Training regression model...")
        with tqdm(total=1, desc="Fitting model") as pbar:
            self.model.fit(X, y)
            pbar.update(1)
        self.model_fitted = True

    def extract_features(self, board):
        def material_count(board):
            piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                            chess.ROOK: 5, chess.QUEEN: 9}
            return sum(len(board.pieces(pt, chess.WHITE)) * v +
                       len(board.pieces(pt, chess.BLACK)) * v
                       for pt, v in piece_values.items())

        def mobility(board):
            return len(list(board.legal_moves))

        def king_safety(board, color):
            king_sq = board.king(color)
            return 0 if king_sq is None else len(board.attackers(not color, king_sq))

        def center_control(board, color):
            center = [chess.D4, chess.E4, chess.D5, chess.E5]
            return sum(1 for sq in center if board.is_attacked_by(color, sq))

        return [
            material_count(board),
            mobility(board),
            king_safety(board, chess.WHITE),
            king_safety(board, chess.BLACK),
            center_control(board, chess.WHITE),
            center_control(board, chess.BLACK)
        ]

    def predict(self):
        board = self.engine.board
        if not self.model_fitted:
            raise RuntimeError("Model is not trained. Call fit() before predict().")

        best_move = None
        best_eval = -np.inf if board.turn == chess.WHITE else np.inf

        for move in board.legal_moves:
            board.push(move)
            features = self.extract_features(board)
            features_df = pd.DataFrame([features], columns=self.features)
            prediction = self.model.predict(features_df)[0]
            board.pop()

            if (board.turn == chess.WHITE and prediction > best_eval) or \
               (board.turn == chess.BLACK and prediction < best_eval):
                best_eval = prediction
                best_move = move

        return best_move
