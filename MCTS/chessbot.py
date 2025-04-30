import os
os.environ.setdefault("MKL_CBWR", "AUTO")

# chessbot
import chess, math, random, multiprocessing
from typing import List, Dict
from typing import List, Dict, Optional
import multiprocessing

# ────────────────────────────────────────────────────────────
#  ░  Simple material evaluator
# ────────────────────────────────────────────────────────────
PIECE_VALUE = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
               chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}

def evaluate_material(board: chess.Board) -> float:
    """
    Evaluate material difference from White's POV.
    args:
        board: chess.Board object
    returns:
        float: material difference (positive for White, negative for Black)
    """
    diff = sum(
        PIECE_VALUE[p.piece_type] * (1 if p.color == chess.WHITE else -1)
        for p in board.piece_map().values()
    )
    return diff

# ────────────────────────────────────────────────────────────
#  ░  Core game & MCTS
# ────────────────────────────────────────────────────────────
class GameState:
    """
    Represents a game state in chess.
    Contains the current board position and methods to interact with it.
    """
    def __init__(self, board: Optional[chess.Board] = None):
    #def __init__(self, board: chess.Board | None = None):
        self.board = board.copy() if board else chess.Board()

    # lightweight helpers -----------------------------------------------------
    def moves(self) -> List[chess.Move]:
        """
        Returns a list of legal moves from the current position.
        """
        return list(self.board.legal_moves)

    def next(self, move: chess.Move) -> "GameState":
        """
        Returns a new GameState after making the given move.
        args:
            move: chess.Move object
        returns:
            GameState: new game state after the move
        """
        if move not in self.board.legal_moves:
            raise ValueError(f"Illegal: {move}")
        nxt = self.board.copy(); nxt.push(move)
        return GameState(nxt)

    def terminal(self) -> bool:         return self.board.is_game_over()
    def reward(self)   -> float:        return evaluate_material(self.board)

# ---------------------------------------------------------------------------    
class Node:
    """
    Represents a node in the MCTS tree.
    Contains the game state, parent node, and child nodes.
    """

    def __init__(self, state: GameState, parent=None):
        self.state, self.parent   = state, parent
        self.children: List[Node] = []
        self.visits = self.wins   = 0

    # UCT selection -----------------------------------------------------------
    def best_child(self, c=1.4):
        """
        Selects the best child node using Upper Confidence Bound for Trees (UCT).
        args:
            c: exploration parameter (default: 1.4)
        returns:
            Node: best child node
        """
        uct = [(ch.wins/(ch.visits+1e-9) +
                c*math.sqrt(math.log(self.visits+1)/(ch.visits+1e-9)))
               for ch in self.children]
        return self.children[uct.index(max(uct))]

    def expand(self):
        """
        Expands the node by adding a new child node for an unexplored move.
        returns:
            Node: newly created child node
        """
        if self.state.terminal(): return None
        tried = {ch.state.board.peek() for ch in self.children}
        move  = random.choice([m for m in self.state.moves() if m not in tried])
        child = Node(self.state.next(move), self)
        self.children.append(child);  return child

# ---------------------------------------------------------------------------    
class MCTS:
    """
    Monte Carlo Tree Search (MCTS) algorithm for game playing.
    """
    def __init__(self, iters=100): self.iters = iters

    def search(self, state: GameState) -> GameState:
        """
        Performs MCTS to find the best move from the given state.
        args:
            state: GameState object representing the current position
        returns:
            GameState: best move found by MCTS
        """
        root = Node(state)
        for _ in range(self.iters):
            node = self._select(root)
            reward = self._simulate(node.state)
            self._backprop(node, reward)
        return root.best_child(c=0).state           # exploit

    # — helpers —
    def _select(self, node: Node):
        """
        Selects a node to expand using UCT.
        args:
            node: Node object to select from
        returns:
            Node: selected node
        """
        while not node.state.terminal():
            if len(node.children) < len(node.state.moves()):
                return node.expand()
            node = node.best_child()
        return node

    def _simulate(self, state: GameState):
        """
        Simulates a random game from the given state to a terminal state.
        args:
            state: GameState object to simulate from
        returns:
            float: reward from the terminal state
        """
        while not state.terminal():
            state = state.next(random.choice(state.moves()))
        return state.reward()

    def _backprop(self, node: Node, reward):
        """
        Backpropagates the reward from the terminal state to the root node.
        args:
            node: Node object to backpropagate from
            reward: reward from the terminal state
        """
        while node:
            node.visits += 1;  node.wins += reward;  node = node.parent

# ---------------------------------------------------------------------------    
def simulate_single(args) -> Dict:
    """
    Simulates a single move and returns the result.
    args:
        args: tuple containing (move, GameState, iters, depth)
    returns:
        dict: result of the simulation
    """
    move, gs, iters, depth = args
    seq = [move.uci()]
    curr = gs.next(move)
    mcts = MCTS(iters)
    for _ in range(depth-1):
        if curr.terminal(): break
        curr = mcts.search(curr);  seq.append(curr.board.peek().uci())
    return dict(move=move.uci(), sequence=seq,
                reward=curr.reward(), terminal=curr.terminal())

def _init_worker():
    """
    Initializes the worker process for multiprocessing.
    This is called before any import in the worker process.
    """
    os.environ.setdefault("MKL_CBWR", "AUTO")
    os.environ.setdefault("MKL_VERBOSE", "0")


def _run_pool(args, workers):
    """
    Runs a pool of worker processes to simulate multiple moves in parallel.
    args:
        args: list of arguments for each simulation
        workers: number of worker processes to use
    returns:
        list: results of the simulations
    """
    # start_method 'spawn' guarantees the initializer runs *before* any import
    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(processes=workers, initializer=_init_worker) as p:
        return p.map(simulate_single, args)


def top_moves(board: chess.Board, iters=30, depth=4, workers=6, n=5) -> List[chess.Move]:
    """
    Returns the top n moves for the given board position using MCTS.
    args:
        board: chess.Board object representing the current position
        iters: number of iterations for MCTS (default: 30)
        depth: depth of the search (default: 4)
        workers: number of worker processes to use (default: 6)
        n: number of top moves to return (default: 5)
    returns:
        list: list of top n chess.Move objects
    """
    gs   = GameState(board)
    args = [(m, gs, iters, depth) for m in gs.moves()]
    with multiprocessing.Pool(processes=min(workers, multiprocessing.cpu_count())) as p:
        res = p.map(simulate_single, args)
    res.sort(key=lambda r: r["reward"], reverse=True)
    return [chess.Move.from_uci(r["move"]) for r in res[:n]]
