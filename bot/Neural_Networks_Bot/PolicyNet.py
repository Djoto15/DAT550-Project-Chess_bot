import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import chess
import chess.pgn
from tqdm import tqdm
import random
from pathlib import Path

from auxiliary_function import *

# ---  PolicyNet Model ---
class PolicyNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(14, 64, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(128 * 8 * 8, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 4672)  # 4672 possible moves in total
        )

    def forward(self, x):
        return self.net(x)

# --- Data Extraction for PolicyNet ---
def extract_policy_data(pgn_path, max_positions=1000, cache_file="data/POLICY_DATASET.npz"):
    if Path(cache_file).exists():
        print("\n Loading PolicyNet data from cache...")
        data = np.load(cache_file)
        return data['X'], data['y']

    X, y = [], []

    with open(pgn_path, "r") as f:
        with tqdm(total=max_positions, desc=" Extraction", unit="pos") as pbar:
            while len(X) < max_positions:

                game = chess.pgn.read_game(f)
                if game is None:
                    break

                board = game.board()
                for move in game.mainline_moves():

                    board.push(move)

                    tensor = board_to_tensor(board)

                    # Encode move into index
                    move_idx = move_to_index(move)
                    if move_idx is not None:
                        X.append(tensor)
                        y.append(move_idx)
                        pbar.update(1)

                    if len(X) >= max_positions:
                        break


    X, y = np.array(X), np.array(y)
    np.savez(cache_file, X=X, y=y)
    print(" PolicyNet Data saved in ", cache_file)
    return X, y

def move_to_index(move):
    return move_to_idx.get(move.uci(), None)

def index_to_move(idx):
    return chess.Move.from_uci(idx_to_move.get(idx, "e2e4"))
    

if __name__ == "__main__":

    pgn_path = "data\lichess_elite_2025-02.pgn"  

    print("\n Data extraction...")
    X, y = extract_policy_data(pgn_path, max_positions=2000000)


    # --- Split en train/val ---
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    train_dataset = TensorDataset(torch.tensor(X_train, dtype=torch.float32), torch.tensor(y_train, dtype=torch.long))
    val_dataset = TensorDataset(torch.tensor(X_val, dtype=torch.float32), torch.tensor(y_val, dtype=torch.long))

    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64)

    # --- Model training ---
    model = PolicyNet()
    optimizer = optim.Adam(model.parameters(), lr=0.0001)
    loss_fn = nn.CrossEntropyLoss()

    train_losses = []
    val_losses = []

    epochs = 40

    for epoch in range(epochs):
        model.train()
        train_loss = 0
        for batch_X, batch_y in tqdm(train_loader):
            optimizer.zero_grad()
            output = model(batch_X)
            loss = loss_fn(output, batch_y)
            loss.backward()

            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

            optimizer.step()
            train_loss += loss.item() * batch_X.size(0)
        train_loss /= len(train_loader.dataset)

        model.eval()
        val_loss = 0
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                output = model(batch_X)
                loss = loss_fn(output, batch_y)
                val_loss += loss.item() * batch_X.size(0)
        val_loss /= len(val_loader.dataset)

        train_losses.append(train_loss)
        val_losses.append(val_loss)

        print(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f} - Val Loss: {val_loss:.4f}")

    # --- Tracer loss ---
    plot_training_curves(train_losses, val_losses)

    # --- Sauvegarder modèle ---
    torch.save(model.state_dict(), "policy_net_model.pt")

