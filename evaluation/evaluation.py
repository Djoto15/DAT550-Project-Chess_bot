import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot import TreeBot, RandomBot
from engine import Engine


pgn_path = "data/1800thresh_1448.pgn"

def evaluate_bot(tree_bot, random_bot, max_moves=200):
    """
    Evaluate the tree bot
    """
    board = tree_bot.engine.board
    tree_color = tree_bot.color
    total_moves = 0
    illegal_predictions = 0
    tree_moves = 0

    while not board.is_game_over() and total_moves < max_moves:
        if board.turn == tree_color:
            move, was_illegal = tree_bot.predict()
            if was_illegal:
                illegal_predictions += 1
            board.push(move)
            tree_moves += 1
        else:
            board.push(random_bot.predict()[0])

        total_moves += 1

    print("\n=== Evaluation Results ===")
    print(f"Total moves: {total_moves}")
    print(f"Illegal predictions by TreeBot: {illegal_predictions}")
    print(f"Percentage of illegal predictions: {100 * illegal_predictions / tree_moves:.2f}%")
    print(f"Game result: {board.result()}")



def evaluate():
    engine = Engine()
    tree_bot = TreeBot(engine, "white")
    random_bot = RandomBot(engine, "black")
    tree_bot.fit(pgn_path)

    evaluate_bot(tree_bot, random_bot)


if __name__ == "__main__":
    evaluate()