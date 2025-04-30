import chess, chess.pgn, random
from chessbot import GameState, MCTS

MAX_PLIES      = 60     # 30 full moves, change as you like
MCTS_ITERS_PER = 30
DEPTH          = 4

board = chess.Board()
root  = chess.pgn.Game()
node  = root
bot    = MCTS(iters=MCTS_ITERS_PER)

for ply in range(MAX_PLIES):
    if board.is_game_over(): break
    move = random.choice(list(board.legal_moves)) if ply % 2 == 0 else \
           bot.search(GameState(board)).board.peek()
    board.push(move)
    node = node.add_variation(move)

root.headers["Event"] = "ChessBot self-play"
with open("sample_game.pgn", "w") as fh:
    print(root, file=fh, end="\n\n")
print("Wrote sample_game.pgn")