import chess.pgn
import pandas as pd
import random
from tqdm import tqdm
from collections import defaultdict

"""
TODO: increase the number of games in the filtered-1800 file (40,000 seems fine)
      change this file to have various positions (oppening with one move up to ten move, correct middlegame and endgame)
      Well change the entire file to have a good dataset of 50,000 positions
"""

# === Config ===
INPUT_PGN = "filtered_1800_pgn.pgn"
OUTPUT_CSV = "positions.csv"

TARGET = {
    "opening": 15000,
    "middlegame": 30000,
    "endgame": 5000,
}

MAX_PLIES_OPENING = 10  # First 10 moves
MAX_PER_ECO = 300
MIDDLEGAME_MIN_MATERIAL = 15  # Excludes kings
ENDGAME_MAX_MATERIAL = 14

# === Material counter (excluding kings) ===
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

# === Mobility counter (number of legal moves) ===
def get_mobility(board):
    white_mobility = len(list(board.legal_moves))  # White's mobility
    board.push(chess.Move.null())  # Add a dummy move to check the opponent's mobility
    black_mobility = len(list(board.legal_moves))
    board.pop()
    return white_mobility, black_mobility


# === King Safety (simplified pawn structure around the king) ===
def get_king_safety(board):
    white_king_pos = board.king(chess.WHITE)
    black_king_pos = board.king(chess.BLACK)
    white_safety = count_protecting_pawns(board, white_king_pos, chess.WHITE)
    black_safety = count_protecting_pawns(board, black_king_pos, chess.BLACK)
    return white_safety, black_safety

def count_protecting_pawns(board, king_pos, color):
    # Check how many pawns are protecting the king (from 1 square distance)
    protecting_pawns = 0
    for square in chess.SQUARES:
        if board.piece_at(square) == chess.PAWN and board.color_at(square) == color:
            if abs(chess.square_rank(square) - chess.square_rank(king_pos)) <= 1 and abs(chess.square_file(square) - chess.square_file(king_pos)) <= 1:
                protecting_pawns += 1
    return protecting_pawns

# === Pawn structure (passed pawns) ===
def get_passed_pawns(board, color):
    passed_pawns = 0
    for pawn in board.pieces(chess.PAWN, color):
        if (color == chess.WHITE and chess.square_rank(pawn) == 6) or (color == chess.BLACK and chess.square_rank(pawn) == 1):
            passed_pawns += 1
    return passed_pawns

# === Storage ===
eco_openings = defaultdict(list)  # ECO -> list of (fen, eco)
middlegame_fens = []  # (fen,)
endgame_fens = []     # (fen,)

with open(INPUT_PGN, encoding='utf-8') as pgn:
    pbar = tqdm(total=sum(TARGET.values()))
    total_collected = 0

    while total_collected < sum(TARGET.values()):
        game = chess.pgn.read_game(pgn)
        if game is None:
            break

        eco = game.headers.get("ECO")
        board = game.board()
        plies = 0
        phase_assigned = {"opening": False, "middlegame": False, "endgame": False}

        for move in game.mainline_moves():
            board.push(move)
            plies += 1
            fen = board.fen()
            material = get_material_count(board)
            white_mobility, black_mobility = get_mobility(board)
            white_safety, black_safety = get_king_safety(board)
            white_passed = get_passed_pawns(board, chess.WHITE)
            black_passed = get_passed_pawns(board, chess.BLACK)

            # --- Opening ---
            if eco and plies <= MAX_PLIES_OPENING and len(eco_openings[eco]) < MAX_PER_ECO and not phase_assigned["opening"]:
                eco_openings[eco].append((fen, eco))
                phase_assigned["opening"] = True
                total_collected += 1
                pbar.update(1)

            # --- Endgame ---
            elif material <= ENDGAME_MAX_MATERIAL and len(endgame_fens) < TARGET["endgame"] and not phase_assigned["endgame"]:
                endgame_fens.append(fen)
                phase_assigned["endgame"] = True
                total_collected += 1
                pbar.update(1)

            # --- Middlegame ---
            elif material > ENDGAME_MAX_MATERIAL and len(middlegame_fens) < TARGET["middlegame"] and not phase_assigned["middlegame"]:
                # Detect phase based on the balance of mobility, safety, and passed pawns
                if (white_mobility > 10 and black_mobility > 10 and
                    abs(white_safety - black_safety) < 2 and
                    (white_passed + black_passed < 2)):
                    middlegame_fens.append(fen)
                    phase_assigned["middlegame"] = True
                    total_collected += 1
                    pbar.update(1)

            if all([
                sum(len(fens) for fens in eco_openings.values()) >= TARGET["opening"],
                len(middlegame_fens) >= TARGET["middlegame"],
                len(endgame_fens) >= TARGET["endgame"]
            ]):
                break

# === Build the dataset ===
opening_fens = [(fen, "opening", eco) for eco_fens in eco_openings.values() for (fen, eco) in eco_fens]
middlegame_fens = [(fen, "middlegame", None) for fen in middlegame_fens]
endgame_fens = [(fen, "endgame", None) for fen in endgame_fens]

all_fens = opening_fens + middlegame_fens + endgame_fens
random.shuffle(all_fens)

# === Save to CSV ===
df = pd.DataFrame(all_fens, columns=["fen", "phase", "eco"])
df.to_csv(OUTPUT_CSV, index=False)

print(f"\n✅ Saved {len(df)} positions to {OUTPUT_CSV}")
