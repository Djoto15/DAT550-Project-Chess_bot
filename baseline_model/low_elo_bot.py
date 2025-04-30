import random
import chess

class LowEloBot():
    def __init__(self, engine):
        self.engine = engine

    def get_moves(self):
        """
        Get all legal moves for the current player.
        """
        return list(self.engine.legal_moves())

    def evaluate_board(self, board):
        """
        Evaluate the board from White's perspective based on material.
        A positive score favors White, a negative favors Black.
        """
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0  # Not used in evaluation
        }
        score = 0
        for piece_type, value in piece_values.items():
            score += len(board.pieces(piece_type, chess.WHITE)) * value
            score -= len(board.pieces(piece_type, chess.BLACK)) * value
        return score

    def fit(self):
        """ Placeholder method. """
        pass

    def predict(self):
        """
        Choose a move: 50% random, 50% greedy based on material evaluation.
        Evaluates from the perspective of the side to move.
        """
        legal_moves = self.get_moves()
        if not legal_moves:
            return None

        if random.random() < 0.5:
            return random.choice(legal_moves)

        # Evaluate from the point of view of the current player
        is_white = self.engine.board.turn
        best_score = -float('inf') if is_white else float('inf')
        best_moves = []

        for move in legal_moves:
            self.engine.board.push(move)
            score = self.evaluate_board(self.engine.board)
            self.engine.board.pop()

            if is_white:
                if score > best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)
            else:
                if score < best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)

        chosen = random.choice(best_moves) if best_moves else random.choice(legal_moves)
        # print(f"bot's move: {chosen}")
        return chosen
