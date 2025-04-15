import chess
import chess.pgn
import numpy as np
from tqdm import tqdm
from sklearn.tree import DecisionTreeRegressor

class Regression:
    def __init__(self, engine):
        self.engine = engine
        self.model = DecisionTreeRegressor()

    def extract_features(self, board: chess.Board):
        """
        Extract handcrafted features from a board state.
        Returns a feature vector: [material_balance, king_safety, minor_development, board_control]
        """
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }

        material_balance = 0
        minor_development = 0
        board_control_white = 0
        board_control_black = 0
        king_safety = 0

        # Material and minor piece development
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = piece_values[piece.piece_type]
                if piece.color == chess.WHITE:
                    material_balance += value
                    if piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                        if square not in [chess.B1, chess.G1, chess.C1, chess.F1]:
                            minor_development += 1
                else:
                    material_balance -= value
                    if piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                        if square not in [chess.B8, chess.G8, chess.C8, chess.F8]:
                            minor_development -= 1

        # King safety (number of enemy attackers near the king)
        for color in [chess.WHITE, chess.BLACK]:
            king_square = board.king(color)
            if king_square is not None:
                danger_zone = chess.SquareSet(chess.BB_KING_ATTACKS[king_square])
                attackers = sum(board.is_attacked_by(not color, sq) for sq in danger_zone)
                king_safety += (-attackers if color == chess.WHITE else attackers)

        # Board control (number of attacked squares)
        board_control_white = sum(len(board.attacks(square)) for square in board.pieces(chess.PAWN, chess.WHITE))
        board_control_black = sum(len(board.attacks(square)) for square in board.pieces(chess.PAWN, chess.BLACK))
        board_control = board_control_white - board_control_black

        return [material_balance, king_safety, minor_development, board_control]
    
    def evaluate_board(self, board):
        """
        Evaluate the board based on handcrafted features.
        Combines feature values into a single evaluation score (like centipawns).
        """
        material, king_safety, development, control = self.extract_features(board)
        
        # Simple weighted evaluation formula (tweak weights as needed)
        score = (
            100 * material +         # material is the main factor
            -20 * king_safety +      # negative: danger near your king
            10 * development +       # encourage minor development
            0.5 * control            # board control is helpful
        )
        
        return score

    def fit(self, pgn_path, num_games=1448):
        """
        Train the bot on a PGN file using handcrafted features and custom evaluation function.
        """
        features = []
        labels = []

        with open(pgn_path, 'r') as pgn_file:
            game_count = 0
            pbar = tqdm(total=num_games, desc="Training Progress")

            while game_count < num_games:
                pgn = chess.pgn.read_game(pgn_file)
                if pgn is None:
                    break

                board = pgn.board()
                for move in pgn.mainline_moves():
                    board.push(move)
                    feature_vector = self.extract_features(board)
                    label = self.evaluate_board(board)
                    features.append(feature_vector)
                    labels.append(label)

                game_count += 1
                pbar.update(1)

            pbar.close()

        features = np.array(features)
        labels = np.array(labels)

        self.model.fit(features, labels)


    def predict(self):
        """
        Predict the best move for the current board state by evaluating all legal moves.
        """
        best_score = -float("inf")
        best_move = None

        for move in self.engine.board.legal_moves:
            self.engine.board.push(move)
            features = np.array(self.extract_features(self.engine.board)).reshape(1, -1)
            score = self.model.predict(features)[0]
            self.engine.board.pop()

            if score > best_score:
                best_score = score
                best_move = move

        return [best_move]