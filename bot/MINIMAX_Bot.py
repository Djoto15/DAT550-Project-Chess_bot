import torch
import chess
import numpy as np
from StockFishCNN import ValueNet, board_to_tensor


# --- Minimax amélioré basé sur ValueNet ---
def minimax_with_value(board, model, depth, is_max=True):
    if depth == 0 or board.is_game_over():
        tensor = torch.tensor(board_to_tensor(board)).unsqueeze(0)
        with torch.no_grad():
            return model(tensor).item()

    best_value = -float('inf') if is_max else float('inf')
    for move in board.legal_moves:
        board.push(move)
        value = minimax_with_value(board, model, depth - 1, not is_max)
        board.pop()

        if is_max:
            best_value = max(best_value, value)
        else:
            best_value = min(best_value, value)

    return best_value


# --- Bot utilisant ValueNet + Minimax ---
class ValueBasedBot:
    def __init__(self, model_path="bot/value_model_stockfish.pt", depth=3):
        self.model = ValueNet()
        self.model.load_state_dict(torch.load(model_path, map_location=torch.device("cpu")))
        self.model.eval()
        self.depth = depth

    def play(self, board):
        best_score = -float('inf')
        best_move = None

        for move in board.legal_moves:
            board.push(move)
            score = minimax_with_value(board, self.model, self.depth - 1, is_max=not board.turn)
            board.pop()

            if score > best_score:
                best_score = score
                best_move = move

        # Évaluation de la position AVANT de jouer le coup
        board.push(best_move)
        eval_tensor = torch.tensor(board_to_tensor(board)).unsqueeze(0)
        with torch.no_grad():
            eval_score = self.model(eval_tensor).item()
        board.pop()

        print(f"🧠 Évaluation de la position après le coup {best_move.uci()} : {eval_score:.3f}")
        return best_move


# --- Partie en console contre le bot ---
if __name__ == "__main__":
    bot = ValueBasedBot(depth=3)
    board = chess.Board()

    while not board.is_game_over():
        print("\nPosition actuelle :\n")
        print(board)

        if board.turn == chess.WHITE:
            move_str = input("Entrez votre coup (UCI) : ")
            try:
                move = chess.Move.from_uci(move_str)
                if move in board.legal_moves:
                    board.push(move)
                else:
                    print("Coup illégal.")
            except:
                print("Format invalide.")
        else:
            print("\n🤖 Le bot réfléchit...")
            bot_move = bot.play(board)
            print(f"Le bot joue : {bot_move.uci()}")
            board.push(bot_move)

    print("\n🏁 Partie terminée :", board.result())
