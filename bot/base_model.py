import chess
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

class BaseBot:
    def __init__(self, engine):
        self.clf = DecisionTreeClassifier(random_state=42)
        self.engine = engine

    def fit(self):
        """Train the classifier using the precomputed features."""
        # Load the dataset
        data = pd.read_csv("data/data/lowELO_evaluated.csv")
        
        # Extract features (X) and target labels (y)
        feature_cols = ['material_diff', 'num_legal_moves', 'is_in_check', 'center_control']
        X = data[feature_cols]  # Features
        y = data['move_type']  # Target labels

        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train the Decision Tree classifier
        self.clf.fit(X_train, y_train)

        # Evaluate the model
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
        material_count = 0
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
        }
        for piece_type, value in piece_values.items():
            material_count += len(board.pieces(piece_type, chess.WHITE)) * value
            material_count -= len(board.pieces(piece_type, chess.BLACK)) * value
        return material_count

    def center_control(self, board):
        """Simple center control: number of white pieces controlling D4/D5/E4/E5 minus black pieces."""
        center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
        white_control = 0
        black_control = 0
        for square in center_squares:
            attackers_white = board.attackers(chess.WHITE, square)
            attackers_black = board.attackers(chess.BLACK, square)
            white_control += len(attackers_white)
            black_control += len(attackers_black)
        return white_control - black_control

    def predict(self):
        """Predict the best move using the trained classifier."""
        board = self.engine.board
        move_probabilities = []
        
        for move in board.legal_moves:
            board.push(move)
            features = self.extract_features(board)

            # Convert features to a DataFrame with the same column names as used during training
            features_df = pd.DataFrame([features], columns=['material_diff', 'num_legal_moves', 'is_in_check', 'center_control'])

            # Predict using the classifier with the DataFrame
            prediction = self.clf.predict(features_df)
            move_probabilities.append((move, prediction[0]))
            board.pop()

        # Select the move predicted as "good" (move_type=1)
        good_moves = [m for m in move_probabilities if m[1] == 1]
        
        if good_moves:
            # Pick any good move (could improve by picking randomly or using a secondary evaluation)
            return good_moves[0][0]
        else:
            # No move predicted good, fallback: pick any legal move
            return next(iter(board.legal_moves), None)

