import chess

class MinimaxBot:
    def __init__(self, engine, depth=3):
        self.depth = depth
        self.engine = engine
    
    import chess

class MinimaxBot:
    def __init__(self, engine, depth=3):
        self.depth = depth
        self.engine = engine
    
    def evaluate(self, board):
        """Evaluate the board based on material, piece activity, pawn structure, and king safety."""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
        }
        
        # Material evaluation
        score = 0
        for piece_type in piece_values:
            score += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
            score -= len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]
        
        # King safety evaluation (simple version)
        score += self.king_safety(board, chess.WHITE) - self.king_safety(board, chess.BLACK)
        
        # Center control evaluation
        score += self.center_control(board, chess.WHITE) - self.center_control(board, chess.BLACK)

        # Piece activity evaluation (how well the pieces are positioned)
        score += self.piece_activity(board, chess.WHITE) - self.piece_activity(board, chess.BLACK)

        # Pawn structure evaluation
        score += self.pawn_structure(board, chess.WHITE) - self.pawn_structure(board, chess.BLACK)

        return score

    def king_safety(self, board, color):
        """Evaluate king safety (simplified)."""
        king_square = board.king(color)
        attack_squares = board.attackers(not color, king_square)
        
        # Simple safety check: number of attackers on the king
        return -len(attack_squares) * 0.5

    def center_control(self, board, color):
        """Evaluate control of the center."""
        center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
        score = 0
        for square in center_squares:
            if board.piece_at(square) and board.piece_at(square).color == color:
                score += 0.5  # Piece in the center is worth more
        return score

    def piece_activity(self, board, color):
        """Evaluate piece activity (simplified)."""
        score = 0
        for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            for square in board.pieces(piece_type, color):
                piece = board.piece_at(square)
                if piece:
                    # Knights and bishops on the central squares are more active
                    if piece.piece_type == chess.KNIGHT or piece.piece_type == chess.BISHOP:
                        if square in [chess.D4, chess.E4, chess.D5, chess.E5]:
                            score += 0.5
                    # Rooks and queens on the 7th/8th rank (for White) or 2nd/1st (for Black) are more active
                    if piece.piece_type == chess.ROOK or piece.piece_type == chess.QUEEN:
                        if (color == chess.WHITE and square // 8 == 6) or (color == chess.BLACK and square // 8 == 1):
                            score += 0.5
        return score

    def pawn_structure(self, board, color):
        """Evaluate pawn structure (isolated, doubled pawns)."""
        score = 0
        for square in board.pieces(chess.PAWN, color):
            # Isolated pawn check (no adjacent pawns)
            if not board.is_attacked_by(not color, square):
                score += 0.3  # Isolated pawns are a bit weaker
        return score


    def minimax(self, board, depth, alpha, beta, maximizing_player):
        """The Minimax algorithm with Alpha-Beta pruning."""
        if depth == 0 or board.is_game_over():
            return self.evaluate(board)

        legal_moves = list(board.legal_moves)
        if maximizing_player:
            max_eval = float('-inf')
            for move in legal_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                board.pop()
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                board.pop()
                if beta <= alpha:
                    break
            return min_eval
    
    def predict(self):
        """Find the best move using Minimax."""
        board = self.engine.board
        legal_moves = list(board.legal_moves)
        best_move = None
        best_value = float('-inf') if board.turn == chess.WHITE else float('inf')

        for move in legal_moves:
            board.push(move)
            board_value = self.minimax(board, self.depth - 1, float('-inf'), float('inf'), board.turn == chess.BLACK)
            if (board.turn == chess.WHITE and board_value > best_value) or (board.turn == chess.BLACK and board_value < best_value):
                best_value = board_value
                best_move = move
            board.pop()
        
        return best_move


