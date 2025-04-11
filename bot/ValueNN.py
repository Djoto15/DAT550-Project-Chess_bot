import chess.pgn
import torch
import torch.nn as nn
import numpy as np
from bot.ValueNN_bot import ValueNet, board_to_tensor


def result_to_score(result_str):
    if result_str == "1-0":
        return 1.0  # blancs gagnent
    elif result_str == "0-1":
        return -1.0  # noirs gagnent
    else:
        return 0.0  # match nul


def extract_value_data(pgn_path, max_games=1000):
    X, y = [], []
    with open(pgn_path, "r") as f:
        game_count = 0
        while game_count < max_games:
            game = chess.pgn.read_game(f)
            if game is None:
                break
            result = game.headers.get("Result")
            score = result_to_score(result)
            board = game.board()
            for move in game.mainline_moves():
                X.append(board_to_tensor(board))
                y.append(score)
                board.push(move)
            game_count += 1
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


def train_value_net(X, y, epochs=10, lr=0.001):
    X_tensor = torch.tensor(X)
    y_tensor = torch.tensor(y).unsqueeze(1)

    model = ValueNet()
    loss_fn = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        preds = model(X_tensor)
        loss = loss_fn(preds, y_tensor)
        loss.backward()
        optimizer.step()
        print(f"Epoch {epoch+1}/{epochs} - Loss: {loss.item():.4f}")

    return model


if __name__ == "__main__":
    print("\n📥 Lecture des parties...")
    X, y = extract_value_data("data/1800thresh_1448.pgn", max_games=1000)

    print("\n🧠 Entraînement du réseau ValueNet...")
    model = train_value_net(X, y, epochs=10)

    print("\n💾 Sauvegarde du modèle...")
    torch.save(model.state_dict(), "mon_value_model.pt")
    print("\n✅ Modèle enregistré sous 'mon_value_model.pt'")
