import pandas as pd
import chess
from sklearn.tree import DecisionTreeRegressor
import numpy as np
import collections
from tqdm import tqdm

class BaseBot:
    def __init__(self, engine, dataset_path="data/dataset.csv", max_depth=3):
        # Regression model and initial setup
        self.model = DecisionTreeRegressor(max_depth=max_depth)
        self.engine = engine
        self.dataset = pd.read_csv(dataset_path)
        self.features = ["material", "mobility", "white_king_safety", "black_king_safety",
                         "white_center_control", "black_center_control"]
        self.model_fitted = False
        self.position_counts = collections.defaultdict(int)  # Track repeated positions

    def fit(self):
        # Training the regression model using dataset
        df = self.dataset.dropna(subset=["evaluation_cp"])  # drop any positions without evaluation
        X = df[self.features]
        y = df["evaluation_cp"]

        print("Training regression model...")
        with tqdm(total=1, desc="Fitting model") as pbar:
            self.model.fit(X, y)
            pbar.update(1)
        self.model_fitted = True

    def extract_features(self, board):
        """Extract features from the board for the regression model."""
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

    def evaluate(self, board):
        """Evaluate the board using the regression model."""
        features = self.extract_features(board)
        features_df = pd.DataFrame([features], columns=self.features)
        return self.model.predict(features_df)[0]

    def minimax(self, board, depth, alpha, beta, maximizing_player):
        """Minimax with alpha-beta pruning."""
        # Base case: if we've reached the leaf node or the game is over
        if depth == 0 or board.is_game_over():
            return self.evaluate(board), None

        best_move = None
        if maximizing_player:
            max_eval = -np.inf
            for move in board.legal_moves:
                board.push(move)
                eval_score, _ = self.minimax(board, depth - 1, alpha, beta, False)
                board.pop()
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = np.inf
            for move in board.legal_moves:
                board.push(move)
                eval_score, _ = self.minimax(board, depth - 1, alpha, beta, True)
                board.pop()
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move

    def predict(self):
        """Predict the best move for the bot using minimax."""
        board = self.engine.board
        if not self.model_fitted:
            raise RuntimeError("Model is not trained. Call fit() before predict().")

        best_move = None
        best_eval = -np.inf if board.turn == chess.WHITE else np.inf

        # Track position and avoid repetition
        fen = board.board_fen()
        self.position_counts[fen] += 1

        candidate_moves = []

        # Minimax search for the best move
        evaluation, move = self.minimax(board, depth=3, alpha=-np.inf, beta=np.inf, maximizing_player=True)
        best_move = move

        return best_move

    def is_progressive_move(self, board, move):
        """Checks if the move is progressive (i.e., leads to development or captures)."""
        if not board.is_legal(move):  # Ensure the move is legal before processing
            return False

        board.push(move)
        is_progressive = False
        for legal_move in board.legal_moves:
            # Check if move results in piece development or capture
            if board.piece_type_at(legal_move.to_square) is not None or \
            board.is_attacked_by(board.turn, legal_move.to_square):
                is_progressive = True
                break
        board.pop()
        return is_progressive
