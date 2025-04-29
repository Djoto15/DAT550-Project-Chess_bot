import chess
import chess.engine
import random
import torch
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
from complex_model.ValueNet import ValueNet
from complex_model.PolicyNet import PolicyNet
from complex_model.auxiliary_function import *

# --- Configuration ---
nb_positions = 50000  # Number of positions for testing
stockfish_path = "C:/Users/harry/Bureau/Data Mining/Final Project/DAT550-Project-Chess_bot/stockfish/stockfish-windows-x86-64-avx2.exe"  # <<< Mets ici ton chemin
depth = 12  # Depth of StockFish analyse

# --- Load PolicyNet and ValueNet ---
policy_net = PolicyNet()
policy_net.load_state_dict(torch.load("C:/Users/harry/Bureau/Data Mining/Final Project/DAT550-Project-Chess_bot/modeles/policy_net_model2.pt", map_location=torch.device('cpu')))
policy_net.eval()

value_net = ValueNet()
value_net.load_state_dict(torch.load("C:/Users/harry/Bureau/Data Mining/Final Project/DAT550-Project-Chess_bot/modeles/value_net_model2.pt", map_location=torch.device('cpu')))
value_net.eval()

# --- Start Stockfish ---
engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)

# --- Generate random positions ---
positions = []
for _ in range(nb_positions):
    board = chess.Board()
    for _ in range(random.randint(5, 50)):  # Joue quelques coups aléatoires
        if board.is_game_over():
            break
        move = random.choice(list(board.legal_moves))
        board.push(move)
    if not board.is_game_over():
        positions.append(board.copy())

# --- Select Move ---
def select_policy_move(board):
    tensor = torch.tensor(board_to_tensor(board)).unsqueeze(0)
    with torch.no_grad():
        logits = policy_net(tensor)
        move_idx = torch.argmax(logits).item()
        move = index_to_move(move_idx)
        if move in board.legal_moves:
            return move
    return random.choice(list(board.legal_moves))

def select_policy_value_move(board, top_k=5):
    tensor = torch.tensor(board_to_tensor(board)).unsqueeze(0)
    with torch.no_grad():
        logits = policy_net(tensor).squeeze()
    
    legal_moves = list(board.legal_moves)
    move_scores = []
    for move in legal_moves:
        move_id = move_to_index(move)
        if move_id is not None:
            move_scores.append((move, logits[move_id].item()))
    move_scores.sort(key=lambda x: x[1], reverse=True)
    top_moves = [m for m, _ in move_scores[:top_k]]

    best_move = None
    best_value = -float('inf')
    for move in top_moves:
        board.push(move)
        tensor_after = torch.tensor(board_to_tensor(board)).unsqueeze(0)
        with torch.no_grad():
            value = value_net(tensor_after).item()
        board.pop()
        if value > best_value:
            best_value = value
            best_move = move
    if best_move:
        return best_move
    else:
        return random.choice(list(board.legal_moves))

# --- Errors Evaluation ---
policy_errors = []
policy_value_errors = []

print("\n Compute errors evaluation...")

for board in tqdm(positions):
    # --- Find best StocFish move
    best_move_info = engine.analyse(board, chess.engine.Limit(depth=depth))
    best_move = best_move_info["pv"][0]  
    board.push(best_move)
    perfect_score = engine.analyse(board, chess.engine.Limit(depth=depth))["score"].white().score(mate_score=10000)
    perfect_score = max(-1000, min(1000, perfect_score)) / 1000
    board.pop()

    if perfect_score is None:
        continue 

    # --- Policy only
    move_policy = select_policy_move(board)
    board.push(move_policy)
    eval_policy = engine.analyse(board, chess.engine.Limit(depth=depth))["score"].white().score(mate_score=10000)
    eval_policy = max(-1000, min(1000, eval_policy)) / 1000
    board.pop()

    if eval_policy is not None:
        error_policy = (perfect_score - eval_policy)
        policy_errors.append(error_policy)

    # --- Policy + Value
    move_policy_value = select_policy_value_move(board)
    board.push(move_policy_value)
    eval_policy_value = engine.analyse(board, chess.engine.Limit(depth=depth))["score"].white().score(mate_score=10000)
    eval_policy_value = max(-1000, min(1000, eval_policy_value)) / 1000
    board.pop()

    if eval_policy_value is not None:
        error_policy_value = (perfect_score - eval_policy_value)
        policy_value_errors.append(error_policy_value)

engine.quit()

# --- Plot Results ---
plt.figure(figsize=(10,6))
plt.hist(policy_errors, bins=50, alpha=0.6, label="Policy Only")
plt.hist(policy_value_errors, bins=50, alpha=0.6, label="Policy + Value")
plt.title("Distribution des erreurs d'évaluation par rapport au meilleur coup")
plt.xlabel("Erreur absolue (centipawns)")
plt.ylabel("Nombre de positions")
plt.legend()
plt.grid()
plt.show()

# --- Numeric Summary ---
print(f"Erreur moyenne Policy Only : {np.mean(policy_errors):.2f}")
print(f"Erreur moyenne Policy+Value : {np.mean(policy_value_errors):.2f}")
