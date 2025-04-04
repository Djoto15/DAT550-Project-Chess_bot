import chess
import random


def random_bot_move(board):
    """Returns a random legal move for the bot."""
    legal_moves = list(board.legal_moves)
    return random.choice(legal_moves)

def play_game():
    board = chess.Board()
    
    while not board.is_game_over():
        print(board)
        
        if board.turn:  # White's turn (True for White, False for Black)
            print("White's turn (Bot):")
            move = random_bot_move(board)
            print(f"Bot chose move: {move.uci()}")
        else:
            print("Black's turn (Human):")
            human_move = input("Enter your move (e.g., e2e4): ")
            move = chess.Move.from_uci(human_move)
            while move not in board.legal_moves:
                print("Invalid move. Try again.")
                human_move = input("Enter your move (e.g., e2e4): ")
                move = chess.Move.from_uci(human_move)
        
        board.push(move)  # Apply the move to the board

    print("Game Over!")
    print(board)

if __name__ == "__main__":
    play_game()
