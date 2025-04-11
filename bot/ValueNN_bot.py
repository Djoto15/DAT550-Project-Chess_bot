import chess
import torch
import torch.nn as nn
import numpy as np

# --- Value Network ---
class ValueNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(773, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, 1),
            nn.Tanh()  # Score entre -1 (noirs gagnent) et +1 (blancs gagnent)
        )

    def forward(self, x):
        return self.net(x)


# --- Encodeur de plateau ---
def board_to_tensor(board):
    tensor = np.zeros(773, dtype=np.float32)
    piece_map = board.piece_map()
    piece_to_index = {
        'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
        'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11
    }
    for square, piece in piece_map.items():
        idx = piece_to_index[piece.symbol()]
        tensor[square * 12 + idx] = 1
    tensor[768] = int(board.turn)
    tensor[769] = int(board.has_kingside_castling_rights(chess.WHITE))
    tensor[770] = int(board.has_queenside_castling_rights(chess.WHITE))
    tensor[771] = int(board.has_kingside_castling_rights(chess.BLACK))
    tensor[772] = int(board.has_queenside_castling_rights(chess.BLACK))
    return tensor


# --- Minimax avec ValueNet ---
def minimax_with_nn(board, model, depth, alpha=-float('inf'), beta=float('inf'), is_maximizing=True):
    if depth == 0 or board.is_game_over():
        input_tensor = torch.tensor(board_to_tensor(board)).unsqueeze(0)
        with torch.no_grad():
            value = model(input_tensor).item()
        return value

    legal_moves = list(board.legal_moves)
    if is_maximizing:
        max_eval = -float('inf')
        for move in legal_moves:
            board.push(move)
            eval = minimax_with_nn(board, model, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            board.push(move)
            eval = minimax_with_nn(board, model, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval


# --- Bot intelligent ---
class SmartNNBot:
    def __init__(self, model, depth=2):
        self.model = model
        self.depth = depth

    def play(self, board): 
        best_score = -float('inf')
        best_move = None

        for move in board.legal_moves:
            board.push(move)
            score = minimax_with_nn(board, self.model, self.depth, is_maximizing=False)
            board.pop()
            if score > best_score:
                best_score = score
                best_move = move

        return best_move
