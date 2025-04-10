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
        """
        Extract rich features from the current board position.

        - Material Balance: as before.
        - King Safety: count how many pieces (including pawns) are near the king (3x3 grid).
        - Center Control: count how many pieces control or occupy central squares (d4, e4, d5, e5).
        - Mobility: number of legal moves (helps estimate initiative).
        - Pawn Structure: number of isolated pawns.
        - Piece Development: how many minor pieces (knights/bishops) are off their initial squares.
        
        """
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
        }

        # 1. Material balance
        white_material = 0
        black_material = 0
        for piece_type in piece_values:
            white_material += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
            black_material += len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]
        material_balance = white_material - black_material

        # 2. King safety (pieces around the king in 3x3 grid)
        def king_safety(board, color):
            king_square = board.king(color)
            if king_square is None:
                return 0  # checkmate / invalid board
            safety_score = 0
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    neighbor = king_square + dx + 8 * dy
                    if chess.SQUARES[0] <= neighbor <= chess.SQUARES[-1]:
                        piece = board.piece_at(neighbor)
                        if piece and piece.color == color:
                            safety_score += 1
            return safety_score

        white_king_safety = king_safety(board, chess.WHITE)
        black_king_safety = king_safety(board, chess.BLACK)

        # 3. Center control (d4, e4, d5, e5)
        center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
        white_center = 0
        black_center = 0
        for square in center_squares:
            attackers_white = board.attackers(chess.WHITE, square)
            attackers_black = board.attackers(chess.BLACK, square)
            white_center += len(attackers_white)
            black_center += len(attackers_black)

        # 4. Mobility (number of legal moves)
        board_turn = board.turn
        board_legal_moves = len(list(board.legal_moves))

        # 5. Isolated pawns
        def count_isolated_pawns(board, color):
            pawns = board.pieces(chess.PAWN, color)
            files_with_pawns = [chess.square_file(sq) for sq in pawns]
            isolated = 0
            for sq in pawns:
                file = chess.square_file(sq)
                if (file - 1 not in files_with_pawns) and (file + 1 not in files_with_pawns):
                    isolated += 1
            return isolated

        white_isolated = count_isolated_pawns(board, chess.WHITE)
        black_isolated = count_isolated_pawns(board, chess.BLACK)

        # 6. Development (minor pieces off their starting squares)
        def minor_development(board, color):
            developed = 0
            starting_squares = {
                chess.WHITE: [chess.B1, chess.G1, chess.C1, chess.F1],
                chess.BLACK: [chess.B8, chess.G8, chess.C8, chess.F8],
            }
            for sq in starting_squares[color]:
                piece = board.piece_at(sq)
                if not piece or piece.piece_type not in (chess.KNIGHT, chess.BISHOP):
                    developed += 1
            return developed

        white_dev = minor_development(board, chess.WHITE)
        black_dev = minor_development(board, chess.BLACK)

        # Combine features into a single vector
        features = [
            material_balance,
            white_king_safety - black_king_safety,
            white_center - black_center,
            board_legal_moves if board_turn == chess.WHITE else -board_legal_moves,
            white_isolated - black_isolated,
            white_dev - black_dev,
        ]

        return features


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

