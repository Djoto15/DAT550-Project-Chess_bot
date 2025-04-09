import chess
import chess.pgn
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
import numpy as np

# Piece value calculation
def piece_value(piece):
    """Return value of a piece."""
    if piece.piece_type == chess.PAWN:
        return 1
    elif piece.piece_type == chess.KNIGHT:
        return 3
    elif piece.piece_type == chess.BISHOP:
        return 3
    elif piece.piece_type == chess.ROOK:
        return 5
    elif piece.piece_type == chess.QUEEN:
        return 9
    return 0

# Central control (whether a piece is in the center of the board)
def is_central(square):
    """Check if a square is in the center of the board."""
    return square in [chess.D4, chess.D5, chess.E4, chess.E5]

# Feature extraction
def get_features(board):
    """Generate features from the current chess board."""
    material_balance = 0
    central_control = 0
    piece_activity = 0
    king_safety = 0
    
    # Calculate material balance and central control
    for square, piece in board.piece_map().items():
        material_balance += piece_value(piece)
        if is_central(square):
            central_control += 1
    
    # Count legal moves (piece activity)
    piece_activity = len(list(board.legal_moves))
    
    # Check king safety (whether the king is in check)
    king_safety = 1 if board.is_check() else 0
    
    # Return features (in a list)
    return [material_balance, central_control, piece_activity, king_safety]

# Load chess games from a PGN file
def load_games(pgn_file):
    """Load games from a PGN file."""
    games = []
    with open(pgn_file, 'r') as f:
        game = chess.pgn.read_game(f)
        while game:
            games.append(game)
            game = chess.pgn.read_game(f)
    return games

# Generate features and labels from games
def generate_data(games):
    """Generate training data (features and labels) from chess games."""
    data = []
    labels = []
    for game in games:
        board = game.board()
        for move in game.mainline_moves():
            features = get_features(board)
            data.append(features)
            labels.append(move.uci())  # Best move as label
            board.push(move)  # Update the board after the move
    return data, labels

# Train decision tree and predict the best move
def train_and_predict(pgn_file):
    """Train a decision tree and predict the best move for a given board."""
    # Load and process games
    games = load_games(pgn_file)
    data, labels = generate_data(games)

    # Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, random_state=42)

    # Train a decision tree classifier
    clf = DecisionTreeClassifier(random_state=42)
    clf.fit(X_train, y_train)

    # Evaluate the classifier
    print(f"Accuracy on test set: {clf.score(X_test, y_test):.4f}")

    # Predict the best move for the current board
    board = chess.Board()  # Starting from the initial board position
    features = get_features(board)
    predicted_move_uci = clf.predict([features])[0]
    predicted_move = chess.Move.from_uci(predicted_move_uci)
    print(f"Predicted move for the initial board: {predicted_move}")

    return clf

# Main function
if __name__ == "__main__":
    # Specify the PGN file containing the chess games
    pgn_file = "chess_games.pgn"  # Replace with the actual path to your PGN file

    # Train the model and predict a move
    clf = train_and_predict(pgn_file)
