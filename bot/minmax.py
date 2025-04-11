import chess
import random
import math


class TreeBot:
    def __init__(self, engine, color, depth=3):
        self.engine = engine
        self.color = chess.WHITE if color == "white" else chess.BLACK
        self.depth = depth  # Depth of search for Minimax

    def extract_features(self, board):
        """
        Basic evaluation function that considers:
        - Material balance
        - Center control
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

        return material_balance + center_score

    def minimax(self, board, depth, maximizing_player, alpha=-math.inf, beta=math.inf):
        """
        Minimax algorithm with alpha-beta pruning
        """
        # Base case: If we reached the max depth or the game is over
        if depth == 0 or board.is_game_over():
            return self.extract_features(board)

        legal_moves = list(board.legal_moves)
        best_move = None

        if maximizing_player:
            max_eval = -math.inf
            for move in legal_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, False, alpha, beta)
                board.pop()

                if eval > max_eval:
                    max_eval = eval
                    best_move = move
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break  # Beta cut-off
            return max_eval
        else:
            min_eval = math.inf
            for move in legal_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, True, alpha, beta)
                board.pop()

                if eval < min_eval:
                    min_eval = eval
                    best_move = move
                beta = min(beta, eval)
                if beta <= alpha:
                    break  # Alpha cut-off
            return min_eval

    def predict(self):
        """
        Use Minimax to predict the best move based on the current board state
        """
        best_move = None
        best_value = -math.inf if self.engine.board.turn == self.color else math.inf

        legal_moves = list(self.engine.board.legal_moves)
        for move in legal_moves:
            self.engine.board.push(move)
            move_value = self.minimax(self.engine.board, self.depth, self.engine.board.turn == self.color)
            self.engine.board.pop()

            if (self.engine.board.turn == self.color and move_value > best_value) or \
               (self.engine.board.turn != self.color and move_value < best_value):
                best_value = move_value
                best_move = move

        print(f"Best move: {best_move} with evaluation {best_value}")
        return best_move, False


# Example usage of the TreeBot with Minimax:
# engine = Engine()  # Your chess engine
# tree_bot = TreeBot(engine, "white")
# move = tree_bot.predict()
# print(f"TreeBot predicted move: {move}")
