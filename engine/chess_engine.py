import chess


# Define a class for the chess engine

class Engine():
    def __init__(self):
        self.board = chess.Board()
        self.SQUARES = chess.SQUARES

        self.checkmate = False
        self.stalemate = False
        self.insufficient_material = False
        self.game_over = False

    # Example of delegating a method to the chess.Board instance
    def push(self, move):
        """Push a move to the board."""
        self.board.push(move)

    def pop(self):
        """Pop the last move."""
        self.board.pop()

    def get_board(self):
        """Get the current board representation."""
        return str(self.board)

    def is_check(self):
        """Check if the current position is check."""
        return self.board.is_check()

    def is_checkmate(self):
        """Check if the current position is checkmate."""
        return self.board.is_checkmate()

    def is_stalemate(self):
        """Check if the current position is stalemate."""
        return self.board.is_stalemate()
    
    def is_insufficient_material(self):
        """Check is there is insufficient material."""
        return self.board.is_insufficient_material()
    
    def is_game_over(self):
        """Check if the game is over"""
        return self.board.is_game_over()

    def legal_moves(self):
        """Get all legal moves."""
        return list(self.board.legal_moves)

    def piece_at(self, square):
        """Get the piece at a given square."""
        return self.board.piece_at(square)
    
    def get_legal_moves_of(self, square):
        """Get the legal moves of the piece on the input square."""
        moves = []
        for move in self.board.legal_moves:
            if move.from_square == square:
                moves.append(move)

        return moves
    
    
    def move_piece(self, move):
        """Do the move."""
        valid_move = chess.Move.from_uci(move)
        self.board.push(valid_move)

        if self.is_checkmate():
            self.checkmate = True
            self.game_over = True
            print("Checkmate!")

        elif self.is_stalemate():
            self.stalemate = True
            self.game_over = True
            print("Stalemate !")

        elif self.is_insufficient_material():
            self.insufficient_material = True
            self.game_over = True
            print("Insufficient material !")




    def square_name(self, square):
        """Get the name of a square (e.g., 'e2')."""
        return chess.square_name(square)

    def print_board(self):
        """Print the board in a human-readable format."""
        print(self.board)

    def set_fen(self, fen):
        """Set the board to a specific FEN string."""
        self.board.set_fen(fen)

    def get_fen(self):
        """Get the FEN string for the current board state."""
        return self.board.fen()


