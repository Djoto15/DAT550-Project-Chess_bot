import os
os.environ.setdefault("MKL_CBWR", "AUTO")
os.environ.setdefault("MKL_VERBOSE", "0")

import os, locale
os.environ.setdefault("LANG",   "en_US.UTF-8")
os.environ.setdefault("LC_ALL", "en_US.UTF-8")

# evaluate_vs_stockfish.py
import chess, chess.pgn, chess.engine, matplotlib.pyplot as plt
from pathlib import Path
from chessbot import top_moves          # our function above

# ── config ─────────────────────────────────────────────────
#STOCKFISH_PATH = "/opt/homebrew/bin/stockfish"
STOCKFISH_PATH = "/usr/local/bin/stockfish" 
SF_TIME        = 0.4     # seconds Stockfish thinks
TOP_N          = 5       # compare against ChessBot's top-N
BOT_ITERS      = 30
BOT_DEPTH      = 4
BOT_WORKERS    = 6

# ── helpers ────────────────────────────────────────────────
engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

def coverage_for_game(game):
    board = game.board()
    hit   = []; moves = []
    for ply, move in enumerate(game.mainline_moves(), 1):
        board.push(move)
        if board.is_game_over(): break
        sf  = engine.play(board, chess.engine.Limit(time=SF_TIME)).move
        top = top_moves(board, BOT_ITERS, BOT_DEPTH, BOT_WORKERS, TOP_N)
        hit.append(int(sf in top)); moves.append(ply)
        print(f"{ply:>3}: Stockfish {sf.uci()} | hit={sf in top}")
    return moves, hit

def plot(moves, hit, title):
    fig, ax = plt.subplots(figsize=(10,4))
    ax.scatter(moves, hit); ax.set_yticks([0,1]); ax.set_yticklabels(["miss","hit"])
    ax.set_xlabel("Half-move"); ax.set_title(f"{title}  (top-{TOP_N} coverage)")
    run = [sum(hit[:i+1])/(i+1) for i in range(len(hit))]
    ax2 = ax.twinx(); ax2.plot(moves, run, ls="--"); ax2.set_ylim(0,1); ax2.set_ylabel("cumulative")
    plt.tight_layout(); plt.show()

# ── driver ────────────────────────────────────────────────
if __name__ == "__main__":
    game = chess.pgn.read_game(Path("sample_game.pgn").open())
    m, h = coverage_for_game(game)
    plot(m, h, game.headers.get("Event","PGN"))
    engine.quit()
