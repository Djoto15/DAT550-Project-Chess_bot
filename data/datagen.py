# Here we process our .csv with the positions to extract useful features and create the labels for the training

import pandas as pd
import chess
import chess.engine
from tqdm import tqdm

df = pd.read_csv("data/positions.csv")
stockfish_path = "/usr/games/stockfish"

def get_material_count(board):
    piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
    return sum(len(board.pieces(pt, chess.WHITE)) * v + len(board.pieces(pt, chess.BLACK)) * v
               for pt, v in piece_values.items())

def get_piece_mobility(board):
    return len(list(board.legal_moves))

def get_king_safety(board, color):
    king_sq = board.king(color)
    return 0 if king_sq is None else len(board.attackers(not color, king_sq))

def get_center_control(board, color):
    return sum(1 for sq in [chess.D4, chess.E4, chess.D5, chess.E5] if board.is_attacked_by(color, sq))

features = []

with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
    for _, row in tqdm(df.iterrows(), total=len(df)):
        fen = row["fen"]
        board = chess.Board(fen)
        try:
            info = engine.analyse(board, chess.engine.Limit(depth=10))
            eval_cp = info["score"].white().score(mate_score=10000)
        except:
            eval_cp = None
        features.append({
            "fen": fen,
            "phase": row["phase"],
            "eco": row.get("eco", "None"),
            "material": get_material_count(board),
            "mobility": get_piece_mobility(board),
            "white_king_safety": get_king_safety(board, chess.WHITE),
            "black_king_safety": get_king_safety(board, chess.BLACK),
            "white_center_control": get_center_control(board, chess.WHITE),
            "black_center_control": get_center_control(board, chess.BLACK),
            "evaluation_cp": eval_cp
        })

pd.DataFrame(features).to_csv("data/dataset.csv", index=False)
