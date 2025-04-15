import chess.pgn
import chess
import random
from tqdm import tqdm
from sklearn.tree import DecisionTreeClassifier

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine import Engine



class Classifier:
    def __init__(self, engine, color):
        self.clf = DecisionTreeClassifier()
        self.move_map = {}
        self.reverse_move_map = {}
        self.engine = engine  # must expose .board and .legal_moves()
        self.color = chess.WHITE if color == "white" else chess.BLACK
        self.illegal_predictions = 0
        self.trained = False
        self.transposition_table = {}

    def count_games(self, pgn_file):
        count = 0
        with open(pgn_file, 'r') as file:
            for line in file:
                if line.startswith('[Event '):
                    count += 1
        return count

    def extract_features(self, board):
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
            center_score += len(attackers) * 0.05

        return [material_balance, center_score]

    def fit(self, pgn_path):
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
        self.trained = True
        print(f"Bot training finished. Trained on {len(X)} moves from {count} games.")


    def minimax(self, board, depth, alpha, beta, maximizing_player):
        board_hash = hash(board.fen())  # Unique board position identifier
        
        # Check if the position is already in the transposition table
        if board_hash in self.transposition_table:
            return self.transposition_table[board_hash]
        
        if depth == 0 or board.is_game_over():
            score = self.evaluate_board(board)
            self.transposition_table[board_hash] = score  # Store the result in the table
            return score

        legal_moves = list(board.legal_moves)

        if maximizing_player:
            max_eval = -float("inf")
            for move in legal_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, False)
                board.pop()
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            self.transposition_table[board_hash] = max_eval  # Store the result in the table
            return max_eval
        else:
            min_eval = float("inf")
            for move in legal_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            self.transposition_table[board_hash] = min_eval  # Store the result in the table
            return min_eval
        
    def evaluate_board(self, board):
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0  # King safety handled separately
        }

        # Material evaluation
        white_material = sum(len(board.pieces(p, chess.WHITE)) * v for p, v in piece_values.items())
        black_material = sum(len(board.pieces(p, chess.BLACK)) * v for p, v in piece_values.items())
        material_score = white_material - black_material

        # Center control (D4, E4, D5, E5)
        center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
        center_control_white = sum(
            (1 if board.piece_at(sq) and board.piece_at(sq).color == chess.WHITE else 0) +
            len(board.attackers(chess.WHITE, sq)) * 0.25 for sq in center_squares
        )
        center_control_black = sum(
            (1 if board.piece_at(sq) and board.piece_at(sq).color == chess.BLACK else 0) +
            len(board.attackers(chess.BLACK, sq)) * 0.25 for sq in center_squares
        )
        center_score = center_control_white - center_control_black

        # King safety: count how many friendly pawns are around the king
        def king_safety(board, color):
            king_square = board.king(color)
            if king_square is None:
                return 0  # King is missing (shouldn't happen)
            safety_score = 0
            rank, file = divmod(king_square, 8)
            for dr in [-1, 0, 1]:
                for df in [-1, 0, 1]:
                    if dr == 0 and df == 0:
                        continue
                    r, f = rank + dr, file + df
                    if 0 <= r < 8 and 0 <= f < 8:
                        neighbor_square = chess.square(f, r)
                        piece = board.piece_at(neighbor_square)
                        if piece and piece.color == color and piece.piece_type == chess.PAWN:
                            safety_score += 1
            return safety_score

        white_king_safety = king_safety(board, chess.WHITE)
        black_king_safety = king_safety(board, chess.BLACK)
        king_safety_score = white_king_safety - black_king_safety

        # # Piece mobility (the number of legal moves for each piece)
        # def piece_mobility(board, color):
        #     mobility = 0
        #     for square in chess.SQUARES:
        #         piece = board.piece_at(square)
        #         if piece and piece.color == color:
        #             mobility += len(board.legal_moves(square))
        #     return mobility

        # white_mobility = piece_mobility(board, chess.WHITE)
        # black_mobility = piece_mobility(board, chess.BLACK)
        # mobility_score = white_mobility - black_mobility

        # Final score
        # total_score = (
        #     material_score * 1.0 +
        #     center_score * 0.5 +
        #     king_safety_score * 0.3 
            
        # )
        total_score = material_score

        # return total_score if self.color == chess.WHITE else -total_score
        return total_score





    
    def predict_top5(self):
        """Return top 5 predicted legal moves with associated probabilities."""
        if not self.trained:
            raise RuntimeError("Bot must be trained before prediction.")

        features = self.extract_features(self.engine.board)
        proba = self.clf.predict_proba([features])[0]  # shape: (n_classes,)

        legal_moves = list(self.engine.legal_moves())
        scored_moves = []

        for move in legal_moves:
            move_uci = move.uci()
            move_index = self.move_map.get(move_uci)
            if move_index is not None:
                scored_moves.append((move, proba[move_index]))

        if not scored_moves:
            print("No known legal moves. Falling back to random.")
            return [(random.choice(legal_moves), 0.0)]

        # Sort by descending probability
        scored_moves.sort(key=lambda x: x[1], reverse=True)

        # Print the top 5
        # print("Top 5 predicted legal moves:")
        # for i, (move, prob) in enumerate(scored_moves[:5], 1):
        #     print(f"{i}. {move.uci()} with probability {prob:.4f}")

        return scored_moves[:5]
    

    def predict(self, depth=3):
        top_moves = self.predict_top5()
        best_move = None
        best_eval = -float("inf")

        for move, prob in top_moves:
            self.engine.board.push(move)
            eval = self.minimax(self.engine.board, depth - 1, -float("inf"), float("inf"), maximizing_player=False)
            self.engine.board.pop()

            # print(f"Evaluated {move.uci()} -> {eval:.2f}")
            if eval > best_eval:
                best_eval = eval
                best_move = move

        return [best_move]


# if __name__ == "__main__":
#     engine = Engine()
#     bot = SimpleBot(engine, "white")
#     bot.fit("data/1800thresh_1448.pgn")
#     best_move = bot.predict()
#     print(best_move)


