import chess
import pandas as pd
from sklearn.ensemble import RandomForestClassifier  # <-- use RandomForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

class BaseBot3:
    def __init__(self, engine, depth=3):
        self.clf = RandomForestClassifier(random_state=42, n_estimators=100)  # <-- change here
        self.engine = engine
        self.depth = depth
        self.transposition_table = {}
        self.moves = []

    def fit(self):
        """Train the classifier using the precomputed features."""
        data = pd.read_csv("data/data/lowELO_evaluated.csv")

        feature_cols = ['material_diff', 'num_legal_moves', 'is_in_check', 'center_control']
        X = data[feature_cols]
        y = data['move_type']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.clf.fit(X_train, y_train)

        y_pred = self.clf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Training Accuracy: {accuracy * 100:.2f}%")

    def extract_features(self, board):
        """Extract features from a chess board for prediction."""
        material_diff = self.material_value(board)
        num_legal_moves = len(list(board.legal_moves))
        is_in_check = int(board.is_check())
        center_control = self.center_control(board)
        return [material_diff, num_legal_moves, is_in_check, center_control]

    def material_value(self, board):
        """Calculate material difference (white - black)."""
        material = 0
        piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                        chess.ROOK: 5, chess.QUEEN: 9}
        for piece, value in piece_values.items():
            material += len(board.pieces(piece, chess.WHITE)) * value
            material -= len(board.pieces(piece, chess.BLACK)) * value
        return material

    def center_control(self, board):
        """Simple center control measure."""
        center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
        white, black = 0, 0
        for square in center_squares:
            white += len(board.attackers(chess.WHITE, square))
            black += len(board.attackers(chess.BLACK, square))
        return white - black

    def evaluate(self, board):
        """Evaluate the board with material, center control, and punish move repetition manually."""
        material = self.material_value(board)
        center = self.center_control(board)

        # Add bonuses
        mobility = len(list(board.legal_moves))  # More legal moves is usually better
        development_bonus = 0

        for piece_type in [chess.KNIGHT, chess.BISHOP]:
            development_bonus += len(board.pieces(piece_type, chess.WHITE)) - len(board.pieces(piece_type, chess.BLACK))

        # Discourage repeating *positions* or *move patterns*
        repetition_penalty = 0
        if len(self.moves) >= 2:
            if self.moves[-1] == self.moves[-2]:
                repetition_penalty = -1000  # Repeating the same move back and forth
            if len(self.moves) >= 4 and self.moves[-1] == self.moves[-3] and self.moves[-2] == self.moves[-4]:
                repetition_penalty = -1500  # Detects pure move bouncing: A -> B -> A -> B

        evaluation = (
            material
            + 0.5 * center
            + 0.1 * mobility
            + 0.3 * development_bonus
            + repetition_penalty
        )

        return evaluation



    def predict_3moves(self):
        """Return the 3 most promising moves based on classifier prediction probabilities."""
        board = self.engine.board
        move_scores = []

        for move in board.legal_moves:
            # Compute bonuses BEFORE pushing the move
            bonus = 0
            if board.is_capture(move):
                bonus += 0.1
            if board.gives_check(move):
                bonus += 0.1
            if move in self.moves:
                bonus += -1000

            board.push(move)
            features = self.extract_features(board)
            features_df = pd.DataFrame([features], columns=['material_diff', 'num_legal_moves', 'is_in_check', 'center_control'])
            proba = self.clf.predict_proba(features_df)[0][1]  # Probability of move_type=1
            board.pop()

            move_scores.append((move, proba + bonus))

        move_scores.sort(key=lambda x: x[1], reverse=True)
        top_moves = [move for move, _ in move_scores[:3]]
        return top_moves



    def predict(self):
        """Use minimax on the top 3 moves to select the best one."""
        candidate_moves = self.predict_3moves()
        if not candidate_moves:
            return next(iter(self.engine.board.legal_moves), None)

        best_move = None
        best_value = float('-inf') if self.engine.board.turn == chess.WHITE else float('inf')

        # Save who's the current player
        is_white = self.engine.board.turn

        for move in candidate_moves:
            self.engine.board.push(move)
            value = self.minimax(self.depth - 1, not is_white)  # careful here: after one move, the turn flips
            self.engine.board.pop()

            if is_white and value > best_value:
                best_value = value
                best_move = move
            elif not is_white and value < best_value:
                best_value = value
                best_move = move

        if best_move is not None:
            self.moves.append(best_move)
            return best_move
        else:
            fallback = candidate_moves[0]
            self.moves.append(fallback)
            return fallback


    def minimax(self, depth, is_maximizing):
        """Minimax with memoization (transposition table)."""
        board = self.engine.board
        board_key = board.fen()

        if board_key in self.transposition_table:
            return self.transposition_table[board_key]

        if depth == 0 or board.is_game_over():
            evaluation = self.evaluate(board)
            self.transposition_table[board_key] = evaluation
            return evaluation

        if is_maximizing:
            max_eval = float('-inf')
            for move in board.legal_moves:
                board.push(move)
                eval = self.minimax(depth - 1, False)
                board.pop()
                max_eval = max(max_eval, eval)
            self.transposition_table[board_key] = max_eval
            return max_eval
        else:
            min_eval = float('inf')
            for move in board.legal_moves:
                board.push(move)
                eval = self.minimax(depth - 1, True)
                board.pop()
            self.transposition_table[board_key] = min_eval
            return min_eval
