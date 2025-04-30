

class Back_Front():
    def __init__(self):
        self.square_to_pos = self.convert_square_to_pos()
        self.cases, self.cases_inv = self.define_cases()


    # -------- Processing methods --------

    def convert_square_to_pos(self):
        """
        Take square = (row, col) as input.
        Return the corresponding interger according to the python-chess representation
        """
        square_to_pos = {}
        integer = 0
        for i in range(8):
            for j in range(8):
                square_to_pos[(7 - i, j)] = integer
                integer += 1

        return square_to_pos
    

    def define_cases(self):
        """
        Link the cases of a chessboard (e2, f4 ...) to indices in a list of list.
        """
        cases = {}
        cases_inv = {}
        rows = "12345678"
        columns = "abcdefgh"
        for i in range(len(rows)):
            for j in range(len(columns)):
                cases[columns[j]+rows[i]] = (7 - i, j)
                cases_inv[(7 - i, j)] = columns[j] + rows[i]
        return cases, cases_inv
    

    
    #-------- Relation methods --------

    def get_pieces_position(self, engine):
        """
        Take a board object of the Engine class.
        Return a list of list with the position fo all the pieces that are one the board.
        """
        front_board = [[0 for _ in range(8)] for _ in range(8)]
        for square in engine.SQUARES:                               # get all square from 0 to 63
            row, col = square // 8, square % 8
            piece = engine.board.piece_at(square)         # get the piece ah the square and then its symbol
            if piece:
                front_board[row][col] = piece.symbol()

        return front_board
    

    def get_legal_moves(self, engine, square):
        """
        Take square = (row, col) as input.
        Return the legal_moves of that piece
        """
        pos = self.square_to_pos[square]
        legal_moves = engine.get_legal_moves_of(pos)    # return moves under the python-chess form
        return legal_moves
    

    def get_legal_moves_coor(self, engine, square):
        """
        Take a list of legal moves as input.
        Return the coors of the moves in a (row, col) form.
        """
        moves = self.get_legal_moves(engine, square)
        moves_coor = []                 # store the move coors
        for move in moves:
            move_uci = move.uci()[2:4]      # get the UCI string representation of the move
            
            moves_coor.append(self.cases[move_uci])

        return moves_coor
    

    def move_piece(self, engine, prev_pos, new_pos, param=None):
        """
        Move the piece in the engine from prev_pos to new_pose.
        Input: prev_pos = (row, col) and new_pos same format
        """
        start = self.cases_inv[prev_pos]
        end = self.cases_inv[new_pos]

        if param:
            move = engine.move_piece(start + end + param)
        else:
            move = engine.move_piece(start + end)


    def read_engine(self, engine):
        """
        Read the engine board and set the front board accordingly.
        Mostly to update after a castling move.
        """
        board = [[0 for _ in range(8)] for _ in range(8)]
        fen = engine.board.fen()
        ranks = fen.split(" ")[0].split("/")

        # Iterate over the ranks (8 rows of the board)
        for row_idx, rank in enumerate(ranks):
            col_idx = 0
            for char in rank:
                if char.isdigit():
                    # If the character is a number, it represents empty squares
                    col_idx += int(char)  # Skip 'n' empty squares
                else:
                    # Otherwise, it is a piece (e.g., 'r', 'N', 'P', etc.)
                    board[row_idx][col_idx] = char.lower() if char.islower() else char.upper()
                    col_idx += 1

        return board