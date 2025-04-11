from sklearn.tree import DecisionTreeClassifier
import chess.pgn
import chess
import random
from tqdm import tqdm  # Progress bar


class TreeBot:
    def __init__(self, engine, color):
        self.clf = DecisionTreeClassifier()
        self.move_map = {}  # maps move to index
        self.reverse_move_map = {}  # reverse mapping
        self.engine = engine
        self.color = chess.WHITE if color == "white" else chess.BLACK
        self.illegal_predictions = 0


    def count_games(self, pgn_file):
        game_count = 0
        with open(pgn_file, 'r') as file:
            for line in file:
                if line.startswith('[Event "'):
                    game_count += 1
        return game_count


    def extract_features(self, board):
        """
        Extract features:
        - Material balance (difference in piece material value)
        - Center control (own pieces occupying or attacking center squares)
        """
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
        }

        white_material = sum(len(board.pieces(p, chess.WHITE)) * v for p, v in piece_values.items())
        black_material = sum(len(board.pieces(p, chess.BLACK)) * v for p, v in piece_values.items())
        material_balance = white_material - black_material

        center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
        color = board.turn

        center_score = 0
        for square in center_squares:
            piece = board.piece_at(square)
            if piece and piece.color == color:
                center_score += 1
            attackers = board.attackers(color, square)
            center_score += len(attackers) * 0.5

        return [material_balance, center_score]
    

    def fit(self, pgn_path):
        """Train the decision tree on PGN games, using only moves played by the bot's color."""
        X = []
        y = []
        move_index = 0
        count = self.count_games(pgn_path)
        print("Started training...")

        with open(pgn_path) as pgn:
            for _ in tqdm(range(count), desc="Training progress", unit="game"):
                game = chess.pgn.read_game(pgn)
                if game is None:
                    break

                board = game.board()
                for move in game.mainline_moves():
                    if board.turn != self.color:
                        board.push(move)
                        continue

                    features = self.extract_features(board)
                    move_uci = move.uci()

                    if move_uci not in self.move_map:
                        self.move_map[move_uci] = move_index
                        self.reverse_move_map[move_index] = move_uci
                        move_index += 1

                    X.append(features)
                    y.append(self.move_map[move_uci])
                    board.push(move)

        if not X:
            print("No training data collected. Please check the PGN file and color filter.")
            return

        self.clf.fit(X, y)
        print(f"Bot training finished. Trained on {len(X)} moves from {count} games.")


    def predict(self):
        """Use the decision tree to predict the best move based on the current board features."""
        features = self.extract_features(self.engine.board)
        move_index = self.clf.predict([features])[0]

        move_uci = self.reverse_move_map.get(move_index)
        if move_uci is None:
            print("Predicted move not found. Picking random legal move.")
            return random.choice(list(self.engine.legal_moves())), True

        predicted_move = chess.Move.from_uci(move_uci)
        if predicted_move not in self.engine.legal_moves():
            print(f"Illegal predicted move: {predicted_move}. Picking random legal move.")
            self.illegal_predictions += 1
            return random.choice(list(self.engine.legal_moves())), True

        print(f"Legal mov predicted: {predicted_move}")
        return predicted_move, False
