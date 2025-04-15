import torch
import pickle
import chess

from bot.ValueNN_bot import ValueNet, SmartNNBot

# --- Charger le modèle ---
model = ValueNet()
model.load_state_dict(torch.load("bot/mon_value_model.pt"))  # Ton modèle entraîné
model.eval()

# --- Créer le bot ---
bot = SmartNNBot(model, depth=3)  # Tu peux mettre depth=3 pour + strat

# --- Créer l’échiquier ---
board = chess.Board()

print("\n🎯 Tu joues les BLANCS.")
print("Entre tes coups au format UCI (ex: e2e4).")

# --- Boucle de jeu ---
while not board.is_game_over():
    print("\n🔷 État de l’échiquier :\n")
    print(board)

    # Tour du joueur
    move_str = input("\n👉 Ton coup : ").strip()
    try:
        move = chess.Move.from_uci(move_str)
        if move not in board.legal_moves:
            raise ValueError("Coup illégal.")
        board.push(move)
    except:
        print("❌ Coup invalide. Réessaie.")
        continue

    if board.is_game_over():
        break

    # Tour du bot
    print("\n🤖 Le bot réfléchit...")
    bot_move = bot.play(board)

    if bot_move is None:
        print("❌ Le bot ne trouve pas de coup.")
        break

    print(f"🤖 Le bot joue : {bot_move.uci()}")
    board.push(bot_move)

# --- Résultat ---
print("\n🏁 Partie terminée !")
print(board)
print("Résultat :", board.result())
