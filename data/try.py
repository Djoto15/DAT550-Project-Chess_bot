import chess

board = chess.Board()
fen = "rnbqkbnr/ppp1pppp/3p4/8/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2"
board.set_fen(fen)


def get_material_count(board):
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
    }
    count = 0
    for piece_type in piece_values:
        count += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
        count += len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]
    return count


print(get_material_count(board))
print(board)
