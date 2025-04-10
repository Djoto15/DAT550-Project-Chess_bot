from sklearn.tree import DecisionTreeClassifier
import chess.pgn
import chess
import numpy as np

class TreeBot:
    def __init__(self, engine):
        self.clf = DecisionTreeClassifier()
        self.move_map = {}  # maps move to index
        self.reverse_move_map = {}  # reverse mapping
        self.engine = engine

    def extract_features(self, board):
        """Extract simple features like material balance."""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
        }

        white_material = 0
        black_material = 0

        for piece_type in piece_values:
            white_material += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
            black_material += len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]

        return [white_material - black_material]  # You can add more features later

    def fit(self, pgn_path):
        """Train the decision tree on the PGN games."""
        X = []
        y = []
        move_index = 0

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
        """Predict the best move from a given position."""
        features = self.extract_features(self.engine.board)
        move_index = self.clf.predict([features])[0]
        predicted_move = chess.Move.from_uci(self.reverse_move_map[move_index])
        if predicted_move in self.engine.board.legal_moves:
            return predicted_move
        else:
            # fallback: pick a random legal move if prediction is illegal
            return list(self.engine.board.legal_moves)[0]


# bot = TreeBot()
# bot.fit("data/1800thresh_1448.pgn")

# # Predict a move from the starting position
# board = chess.Board()
# while not board.is_game_over():
#     move = bot.predict(board)
#     print(f"Bot plays: {move}")
#     board.push(move)
#     print(board)

