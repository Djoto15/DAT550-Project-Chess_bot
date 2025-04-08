import random
import chess

class RandomBot():
    def __init__(self, engine):
        self.moves = None
        self.engine = engine

    def get_moves(self):
        """
        Get the legal moves that the bot can do.
        """
        legal_moves = self.engine.board.legal_moves
        black_moves = [move for move in legal_moves if self.engine.board.turn == chess.BLACK]   # change for it to be general
        return black_moves
        

    def play(self):
        """
        Make the move
        """
        legal_moves = self.get_moves()
        if legal_moves: # if there is not checkmate
            move = random.choice(legal_moves)
            return move
        else:
            return None

