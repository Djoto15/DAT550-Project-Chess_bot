import torch
import chess
from complex_model.PolicyNet import PolicyNet
from complex_model.ValueNet import ValueNet  
from random import random
from complex_model.auxiliary_function import *



class SmartChessBot:
    def __init__(self, engine, policy_path, value_path, top_k=5):
        self.policy_net = PolicyNet()
        self.policy_net.load_state_dict(torch.load(policy_path, map_location=torch.device('cpu')))
        self.policy_net.eval()

        self.value_net = ValueNet()
        self.value_net.load_state_dict(torch.load(value_path, map_location=torch.device('cpu')))
        self.value_net.eval()

        self.top_k = top_k
        self.engine = engine

    def predict(self):
        board = self.engine.board
        # --- Step 1 : Is there mate ?
        mate_move = find_mate_in_1_or_2(board)
        if mate_move:
            print(f" Mate detected ! Bot plays {mate_move.uci()}")
            return mate_move

        # --- Étape 2: Policy + Value
        tensor = torch.tensor(board_to_tensor(board)).unsqueeze(0)
        with torch.no_grad():
            policy_output = self.policy_net(tensor).squeeze()

        legal_moves = list(board.legal_moves)
        move_scores = []

        for move in legal_moves:
            move_id = move_to_index(move)
            if move_id is not None:
                score = policy_output[move_id].item()
                move_scores.append((move, score))

        move_scores.sort(key=lambda x: x[1], reverse=True)
        top_moves = [move for move, _ in move_scores[:self.top_k]]

        best_move = None
        best_value = -float('inf') if board.turn == chess.WHITE else float('inf')

        for move in top_moves:
            board.push(move)
            tensor_after = torch.tensor(board_to_tensor(board)).unsqueeze(0)
            with torch.no_grad():
                value = self.value_net(tensor_after).item()
            board.pop()

            if (board.turn == chess.WHITE and value > best_value) or (board.turn == chess.BLACK and value < best_value):
                best_value = value
                best_move = move

        return best_move if best_move else random.choice(legal_moves)
    
    def fit(self):
        pass
    
