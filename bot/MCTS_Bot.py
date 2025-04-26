import chess
import torch
import math
import random
from StockFishCNN import ValueNet, board_to_tensor


class MCTSNode:
    def __init__(self, board, parent=None, move=None):
        self.board = board.copy()
        self.parent = parent
        self.move = move
        self.children = []
        self.visits = 0
        self.value_sum = 0.0

    def is_fully_expanded(self):
        return len(self.children) == len(list(self.board.legal_moves))

    def best_child(self, c_param=1.4):
        best_score = float('-inf')
        best_child = None
        for child in self.children:
            if child.visits == 0:
                score = float('inf')
            else:
                uct = child.value_sum / child.visits + c_param * math.sqrt(
                    math.log(self.visits) / child.visits
                )
                score = uct
            if score > best_score:
                best_score = score
                best_child = child
        return best_child

    def expand(self):
        tried_moves = [child.move for child in self.children]
        for move in self.board.legal_moves:
            if move not in tried_moves:
                new_board = self.board.copy()
                new_board.push(move)
                new_node = MCTSNode(new_board, parent=self, move=move)
                self.children.append(new_node)
                return new_node
        return None

    def backpropagate(self, value):
        self.visits += 1
        self.value_sum += value
        if self.parent:
            self.parent.backpropagate(-value if self.board.turn != self.parent.board.turn else value)


def mcts_search(root_board, model, simulations=100):
    root = MCTSNode(root_board)
    for _ in range(simulations):
        node = root

        # Selection
        while node.is_fully_expanded() and node.children:
            node = node.best_child()

        # Expansion
        if not node.board.is_game_over():
            node = node.expand()

        # Evaluation
        tensor = torch.tensor(board_to_tensor(node.board)).unsqueeze(0)
        with torch.no_grad():
            value = model(tensor).item()

        # Backpropagation
        node.backpropagate(value)

    best_move = max(root.children, key=lambda c: c.visits).move
    return best_move


# --- Exemple d'utilisation ---
if __name__ == "__main__":
    board = chess.Board()
    model = ValueNet()
    model.load_state_dict(torch.load("value_model_stockfish.pt", map_location="cpu"))
    model.eval()

    while not board.is_game_over():
        print(board)
        if board.turn == chess.WHITE:
            move_uci = input("Entrez votre coup (uci) : ")
            move = chess.Move.from_uci(move_uci)
            if move in board.legal_moves:
                board.push(move)
            else:
                print("Coup illégal.")
        else:
            print("\n MCTS réfléchit...")
            best = mcts_search(board, model, simulations=100)
            print(f"Le bot joue : {best.uci()}")
            board.push(best)

    print("\n Partie terminée.", board.result())
