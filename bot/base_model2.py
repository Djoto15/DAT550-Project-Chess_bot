import chess
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

class BaseBot2:
    def __init__(self, engine):
        self.clf = DecisionTreeClassifier(random_state=42)
        self.engine = engine
    
    def extract_features(self, fen):
        """Extract features from the FEN string."""
        board = chess.Board(fen)

        # Feature 1: Material count (based on piece values)
        material_count = self.material_value(board)

        # Feature 2: Mobility (number of legal moves for each side)
        mobility = self.mobility(board)

        # Feature 3: White King Safety (number of opponent controlled squares around the white king)
        white_king_safety = self.king_safety(board, chess.WHITE)

        # Feature 4: Black King Safety (number of opponent controlled squares around the black king)
        black_king_safety = self.king_safety(board, chess.BLACK)

        # Feature 5: White Center Control (number of white pieces controlling the center)
        white_center_control = self.center_control(board, chess.WHITE)

        # Feature 6: Black Center Control (number of black pieces controlling the center)
        black_center_control = self.center_control(board, chess.BLACK)

        # Return the feature vector
        return [material_count, mobility, white_king_safety, black_king_safety, white_center_control, black_center_control]
    
    def material_value(self, board):
        """Calculate material value based on piece types."""
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

    def mobility(self, board):
        """Calculate the mobility based on the number of legal moves for each side."""
        return len(list(board.legal_moves))
    
    def king_safety(self, board, color):
        """Estimate king safety by counting the number of opponent-controlled squares around the king."""
        king_square = board.king(color)
        opponent_color = chess.BLACK if color == chess.WHITE else chess.WHITE
        
        # Squares around the king (8 squares around the king)
        king_neighbors = board.attacks(king_square)
        opponent_control = sum(1 for sq in king_neighbors if board.piece_at(sq) and board.piece_at(sq).color == opponent_color)
        
        return opponent_control

    def center_control(self, board, color):
        """Count the number of pieces from a color controlling the center."""
        center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
        control_count = 0
        
        for sq in center_squares:
            if board.piece_at(sq) and board.piece_at(sq).color == color:
                control_count += 1
        
        return control_count

    def fit(self):
        """Train the classifier using the data."""
        data = pd.read_csv("data/data/lowELO_evaluated.csv")
        X = []
        y = []

        # Prepare the features and labels
        for index, row in data.iterrows():
            fen = row['fen']
            next_move = row['next_move']
            move_type = row['move_type']

            # Label as 1 (good) if the move captures a piece
            board = chess.Board(fen)
            move = chess.Move.from_uci(next_move)
            if move.to_square in board.piece_map() and board.piece_at(move.to_square).color != board.turn:
                # If the move captures a piece
                move_type = 1  # Good move (capture)
            else:
                move_type = 0  # Bad move (no capture)

            features = self.extract_features(fen)
            X.append(features)
            y.append(move_type)
        
        X = pd.DataFrame(X)
        y = pd.Series(y)

        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train the Decision Tree classifier
        self.clf.fit(X_train, y_train)

        # Evaluate the model
        y_pred = self.clf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Training Accuracy: {accuracy * 100:.2f}%")

    def predict(self):
        """Predict the best move using the trained classifier."""
        board = self.engine.board
        move_probabilities = []
        legal_moves = list(board.legal_moves)
        visited_positions = set()  # To track previously visited positions

        for move in legal_moves:
            board.push(move)
            board_fen = board.fen()

            # Check if this position has already been visited
            if board_fen in visited_positions:
                board.pop()
                continue

            visited_positions.add(board_fen)  # Mark this position as visited

            move_features = self.extract_features(board_fen)
            prediction = self.clf.predict([move_features])
            move_probabilities.append((move, prediction[0]))
            board.pop()

        # Select the best move based on the classifier's prediction (good move)
        if move_probabilities:
            best_move = max(move_probabilities, key=lambda x: x[1])
            return best_move[0]  # Return the move with the best prediction
        else:
            return None  # In case there are no valid moves (e.g., stalemate)
