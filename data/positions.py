import chess.pgn
import pandas as pd
import random
from tqdm import tqdm
from collections import defaultdict

# === Config ===
INPUT_PGN = "filtered_1800_pgn.pgn"
OUTPUT_CSV = "positions.csv"
NUM_POSITIONS = 50000

TARGET = {
    "opening": int(0.3 * NUM_POSITIONS),
    "middlegame": int(0.6 * NUM_POSITIONS),
    "endgame": int(0.1 * NUM_POSITIONS),
}

MAX_PLIES_OPENING = 10
MIN_PLIES_OPENING = 2
OPENING_PLY_STEPS = list(range(MIN_PLIES_OPENING, MAX_PLIES_OPENING + 1, 2))  # [2, 4, 6, 8, 10]
MAX_PER_ECO = 300
MIDDLEGAME_MIN_MATERIAL = 15
ENDGAME_MAX_MATERIAL = 13

MAX_OPENING_PER_GAME = 2
MAX_MIDDLEGAME_PER_GAME = 3
MAX_ENDGAME_PER_GAME = 2

# === Helper Functions ===
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

def is_minor_piece_developed(board, color):
    home_knights = [chess.B1, chess.G1] if color == chess.WHITE else [chess.B8, chess.G8]
    home_bishops = [chess.C1, chess.F1] if color == chess.WHITE else [chess.C8, chess.F8]
    for sq in home_knights + home_bishops:
        piece = board.piece_at(sq)
        if piece is None or piece.color != color or piece.piece_type not in (chess.KNIGHT, chess.BISHOP):
            return True
    return False

def has_material_imbalance(board):
    piece_counts = lambda color: sum(len(board.pieces(pt, color)) for pt in range(1, 6))
    return abs(piece_counts(chess.WHITE) - piece_counts(chess.BLACK)) >= 3

# === Storage ===
eco_openings = defaultdict(list)
middlegame_fens = []
endgame_fens = []
seen_positions = set()

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
        opening_added = 0
        middlegame_added = 0
        endgame_added = 0
        collected_opening_plies = set()

        for move in game.mainline_moves():
            board.push(move)
            plies += 1
            fen = board.fen()
            material = get_material_count(board)

            if fen in seen_positions:
                continue

            # Opening position variety by ply
            if (eco and
                plies in OPENING_PLY_STEPS and
                plies not in collected_opening_plies and
                len(eco_openings[eco]) < MAX_PER_ECO and
                opening_added < MAX_OPENING_PER_GAME and
                sum(len(fens) for fens in eco_openings.values()) < TARGET["opening"]):

                eco_openings[eco].append((fen, eco))
                collected_opening_plies.add(plies)
                seen_positions.add(fen)
                opening_added += 1
                total_collected += 1
                pbar.update(1)
                continue

            # Endgame position
            if (material <= ENDGAME_MAX_MATERIAL and
                len(endgame_fens) < TARGET["endgame"] and
                endgame_added < MAX_ENDGAME_PER_GAME):

                endgame_fens.append(fen)
                seen_positions.add(fen)
                endgame_added += 1
                total_collected += 1
                pbar.update(1)
                continue

            # Middlegame position
            if (material > ENDGAME_MAX_MATERIAL and
                len(middlegame_fens) < TARGET["middlegame"] and
                middlegame_added < MAX_MIDDLEGAME_PER_GAME and
                is_minor_piece_developed(board, chess.WHITE) and
                is_minor_piece_developed(board, chess.BLACK) and
                has_material_imbalance(board)):

                middlegame_fens.append(fen)
                seen_positions.add(fen)
                middlegame_added += 1
                total_collected += 1
                pbar.update(1)
                continue

            if (sum(len(fens) for fens in eco_openings.values()) >= TARGET["opening"] and
                len(middlegame_fens) >= TARGET["middlegame"] and
                len(endgame_fens) >= TARGET["endgame"]):
                break

# === Build final dataset ===
opening_fens = [(fen, "opening", eco) for eco_fens in eco_openings.values() for (fen, eco) in eco_fens]
middlegame_fens = [(fen, "middlegame", None) for fen in middlegame_fens]
endgame_fens = [(fen, "endgame", None) for fen in endgame_fens]

all_fens = opening_fens + middlegame_fens + endgame_fens
random.shuffle(all_fens)

df = pd.DataFrame(all_fens, columns=["fen", "phase", "eco"])
df.to_csv(OUTPUT_CSV, index=False)

print(f"\n✅ Saved {len(df)} positions to {OUTPUT_CSV}")
