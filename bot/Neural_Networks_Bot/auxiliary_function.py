import chess
import chess.engine
import chess.pgn
import numpy as np
import matplotlib.pyplot as plt
import random

# --- Board encoder (14x8x8 tensor with legal moves) ---
def board_to_tensor(board):
    tensor = np.zeros((14, 8, 8), dtype=np.float32)
    piece_to_plane = {
        'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
        'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11
    }

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            plane = piece_to_plane[piece.symbol()]
            row = 7 - (square // 8)
            col = square % 8
            tensor[plane][row][col] = 1

    original_turn = board.turn

    board.turn = chess.WHITE
    for move in board.legal_moves:
        row = 7 - (move.to_square // 8)
        col = move.to_square % 8
        tensor[12][row][col] = 1

    board.turn = chess.BLACK
    for move in board.legal_moves:
        row = 7 - (move.to_square // 8)
        col = move.to_square % 8
        tensor[13][row][col] = 1

    board.turn = original_turn
    return tensor

# --- Generate Random Boards ---
def random_board(max_depth = 200):
    board = chess.Board()
    depth = random.randrange(0, max_depth)

    for _ in range(depth):
        all_moves = list(board.legal_moves)
        random_move = random.choice(all_moves)
        board.push(random_move)
        if board.is_game_over():
            break

    return board


# --- Generate Blunder positions ---
def generate_blunder_position():
    board = chess.Board()
    for _ in range(random.randint(3, 7)):
        moves = list(board.legal_moves)
        if moves:
            board.push(random.choice(moves))
        else:
            break

    if board.piece_at(chess.E4) is None:
        board.set_piece_at(chess.E4, chess.Piece(chess.QUEEN, chess.WHITE))

    if board.piece_at(chess.D5) is None:
        board.set_piece_at(chess.D5, chess.Piece(chess.PAWN, chess.BLACK))

    return board

# --- Plotting Functions ---
def plot_losses(train_losses, val_losses):
    epochs = range(1, len(train_losses) + 1)
    
    plt.figure(figsize=(8,5))
    plt.plot(epochs, train_losses, label='Train Loss')
    plt.plot(epochs, val_losses, label='Validation Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss (MSE)')
    plt.title('Training and Validation Loss')
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_predictions(y_true, y_pred):
    plt.figure(figsize=(6,6))
    plt.scatter(y_true, y_pred, alpha=0.3)
    plt.xlabel('True Evaluation (Stockfish)')
    plt.ylabel('Predicted Evaluation (ValueNet)')
    plt.title('True vs Predicted Evaluations')
    plt.grid(True)
    plt.plot([-1, 1], [-1, 1], 'r--')  # Diagonale parfaite
    plt.show()

def plot_error_distribution(y_true, y_pred):
    errors = y_pred - y_true
    plt.figure(figsize=(8,5))
    plt.hist(errors, bins=50, alpha=0.7)
    plt.xlabel('Prediction Error')
    plt.ylabel('Number of Positions')
    plt.title('Distribution of Prediction Errors')
    plt.grid(True)
    plt.show()

def plot_training_curves(train_losses, val_losses, train_accuracies=None, val_accuracies=None):
    epochs = range(1, len(train_losses) + 1)
    
    fig, ax1 = plt.subplots()

    color = 'tab:blue'
    ax1.set_xlabel('Epochs')
    ax1.set_ylabel('Loss', color=color)
    ax1.plot(epochs, train_losses, label='Train Loss', color='blue')
    ax1.plot(epochs, val_losses, label='Validation Loss', color='cyan')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.legend(loc='upper right')

    if train_accuracies is not None and val_accuracies is not None:
        ax2 = ax1.twinx()  # Deuxième axe Y
        color = 'tab:red'
        ax2.set_ylabel('Accuracy', color=color)
        ax2.plot(epochs, train_accuracies, label='Train Accuracy', color='red', linestyle='--')
        ax2.plot(epochs, val_accuracies, label='Validation Accuracy', color='orange', linestyle='--')
        ax2.tick_params(axis='y', labelcolor=color)
        ax2.legend(loc='lower right')

    plt.title('Training and Validation Loss/Accuracy over Epochs')
    plt.show()

# --- Search For mate in 1 or 2 moves ---
def find_mate_in_1_or_2(board):
    """Détecte un échec et mat immédiat ou forcé en 2 coups."""
    for move in board.legal_moves:
        board.push(move)

        if board.is_checkmate():
            board.pop()
            return move  # Mate immédiat

        opponent_moves = list(board.legal_moves)
        is_forced_mate = True

        for opp_move in opponent_moves:
            board.push(opp_move)
            if not board.is_checkmate():
                is_forced_mate = False
            board.pop()

            if not is_forced_mate:
                break

        board.pop()

        if is_forced_mate:
            return move  # Mate forcé en 2

    return None

# --- Construction of the move_to_idx and idx_to_move dictionary ---

# Generate all possible moves
squares = list(chess.SQUARES)
promotions = [None, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]

move_to_idx = {}
idx_to_move = {}
index = 0

for from_square in squares:
    for to_square in squares:
        if from_square != to_square:
            move = chess.Move(from_square, to_square)
            move_to_idx[move.uci()] = index
            idx_to_move[index] = move.uci()
            index += 1
            # White Promotion
            if chess.square_rank(from_square) == 6 and chess.square_rank(to_square) == 7:
                for promo in promotions[1:]:
                    move = chess.Move(from_square, to_square, promotion=promo)
                    move_to_idx[move.uci()] = index
                    idx_to_move[index] = move.uci()
                    index += 1
            # Black Promotion
            if chess.square_rank(from_square) == 1 and chess.square_rank(to_square) == 0:
                for promo in promotions[1:]:
                    move = chess.Move(from_square, to_square, promotion=promo)
                    move_to_idx[move.uci()] = index
                    idx_to_move[index] = move.uci()
                    index += 1

# --- Encoding/Decoding Functions ---

def move_to_index(move):
    """
    Transforms a move (chess.Move object) into an index.
    """
    return move_to_idx.get(move.uci(), None)

def index_to_move(idx):
    """
    Transforms an index into a move (chess.Move object).
    """
    if idx in idx_to_move:
        return chess.Move.from_uci(idx_to_move[idx])
    else:
        return None
