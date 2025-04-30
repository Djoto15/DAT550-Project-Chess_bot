import pandas as pd
import numpy as np
import chess
import chess.engine
import random
from tqdm import tqdm
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from collections import defaultdict

class BaseBot:
    def __init__(self, engine, dataset_path="data/data/dataset3.csv", max_depth=5):
        self.engine = engine
        self.dataset = pd.read_csv(dataset_path)
        self.features = ["material", "mobility", "white_king_safety", "black_king_safety",
                         "white_center_control", "black_center_control", "phase"]
        self.classifier = RandomForestClassifier(max_depth=max_depth, n_estimators=100)
        self.label_encoder = LabelEncoder()
        self.model_fitted = False
        self.position_counts = defaultdict(int)

    def fit(self):
        df = self.dataset.dropna(subset=["best_move", "evaluation_cp"])
        X = df[self.features]
        y = self.label_encoder.fit_transform(df["best_move"])
        print("Training classifier on best moves...")
        self.classifier.fit(X, y)
        self.model_fitted = True

    def extract_features(self, board, phase="middlegame"):
        def material_count(b):
            values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                      chess.ROOK: 5, chess.QUEEN: 9}
            return sum(len(b.pieces(pt, chess.WHITE)) * v +
                       len(b.pieces(pt, chess.BLACK)) * v
                       for pt, v in values.items())

        def mobility(b): return len(list(b.legal_moves))
        def king_safety(b, color): return 0 if b.king(color) is None else len(b.attackers(not color, b.king(color)))
        def center_control(b, color): return sum(b.is_attacked_by(color, sq) for sq in [chess.D4, chess.E4, chess.D5, chess.E5])

        return [
            material_count(board),
            mobility(board),
            king_safety(board, chess.WHITE),
            king_safety(board, chess.BLACK),
            center_control(board, chess.WHITE),
            center_control(board, chess.BLACK),
            {"opening": 0, "middlegame": 1, "endgame": 2}[phase]
        ]

    def predict(self, phase="middlegame", depth=2):
        if not self.model_fitted:
            raise RuntimeError("Model not trained. Run fit() first.")

        board = self.engine.board
        features = self.extract_features(board, phase=phase)
        features_df = pd.DataFrame([features], columns=self.features)
        probas = self.classifier.predict_proba(features_df)[0]

        # Top 3 predicted moves
        top_indices = np.argsort(probas)[::-1][:3]
        top_moves = self.label_encoder.inverse_transform(top_indices)

        legal_uci = [move.uci() for move in board.legal_moves]
        valid_moves = [uci for uci in top_moves if uci in legal_uci]

        if not valid_moves:
            # fallback: random legal move
            return random.choice(list(board.legal_moves))

        best_score = -np.inf if board.turn == chess.WHITE else np.inf
        best_move = None

        for uci in valid_moves:
            move = chess.Move.from_uci(uci)
            board.push(move)
            score = self.minimax(board, depth - 1, -np.inf, np.inf, not board.turn)
            board.pop()

            if (board.turn == chess.WHITE and score > best_score) or \
               (board.turn == chess.BLACK and score < best_score):
                best_score = score
                best_move = move

        return best_move

    def evaluate(self, board):
        if board.is_checkmate():
            return float('inf') if board.turn == chess.BLACK else float('-inf')
        elif board.is_stalemate() or board.is_insufficient_material():
            return 0

        # Optional: use a real engine
        # info = self.engine.analyse(board, chess.engine.Limit(depth=10))
        # return info["score"].relative.score(mate_score=10000)

        # Or fallback to probability as a weak eval
        features = self.extract_features(board)
        features_df = pd.DataFrame([features], columns=self.features)
        return self.classifier.predict_proba(features_df)[0].max()


    def minimax(self, board, depth, alpha, beta, maximizing_player):
        if depth == 0 or board.is_game_over():
            return self.evaluate(board)

        if maximizing_player:
            max_eval = -np.inf
            for move in board.legal_moves:
                board.push(move)
                score = self.minimax(board, depth - 1, alpha, beta, False)
                board.pop()
                max_eval = max(max_eval, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = np.inf
            for move in board.legal_moves:
                board.push(move)
                score = self.minimax(board, depth - 1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return min_eval
