import random
import chess

class RandomBot():
    def __init__(self, engine, color):
        self.moves = None
        self.engine = engine
        self.color = color

    def get_moves(self):
        """
        Get the legal moves that the bot can do, if it's its turn.
        """
        # if (self.engine.board.turn == chess.WHITE and color == "white") or \
        # (self.engine.board.turn == chess.BLACK and color == "black"):
        #     legal_moves = list(self.engine.board.legal_moves)
        #     # print(f"Legal moves for {color}: {legal_moves}")  # Debugging output
        #     print(color)
        #     return legal_moves
        # return []
        moves = self.engine.legal_moves()
        chess_color = chess.WHITE if self.color == "white" else chess.BLACK
        legal_moves = [move for move in moves if self.engine.board.color_at(move.from_square) == chess_color]
        return legal_moves
    
    def fit(self):
        """Just do nothing but debbug."""
        pass


    def predict(self):
        """
        Make the move
        """
        legal_moves = self.get_moves()
        if legal_moves: # if there is not checkmate
            move = random.choice(legal_moves)
            return move
        else:
            return None

