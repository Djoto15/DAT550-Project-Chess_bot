import chess
import chess.engine
import chess.pgn
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from pathlib import Path
from tqdm import tqdm
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import random
from auxiliary_function import *


# --- ValueNet ---
class ValueNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(14, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(128 * 8 * 8, 512),
            nn.ReLU(),
            nn.Dropout(p=0.3),
            nn.Linear(512, 1),
            nn.Tanh()
        )

    def forward(self, x):
        return self.net(x)


# --- Extraction and evaluation with StockFish ---
def extract_data_with_stockfish(pgn_path, stockfish_path, max_positions=1000, cache_file="data/VALUE_DATASET.npz", proportion_blunder=0.3):
    if Path(cache_file).exists():
        print("\n Loading Data from cache ")
        data = np.load(cache_file)
        return data['X'], data['y']

    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    X, y = [], []

    with open(pgn_path, "r") as f:
        with tqdm(total=max_positions, desc=" Extraction", unit="pos") as pbar:
            while len(X) < max_positions:

                game = chess.pgn.read_game(f)              

                # Decides whether to generate a blunder
                if random.random() < proportion_blunder:
                    board = random_board()
                else:

                    if game is None:
                        break
                    board = game.board()

                    for move in game.mainline_moves():

                        tensor = board_to_tensor(board)
                        try:
                            
                            info = engine.analyse(board, chess.engine.Limit(depth=3))
                            score = info["score"].white().score(mate_score=10000)
                            if score is not None:
                                norm_score = max(-1000, min(1000, score)) / 1000
                                X.append(tensor)
                                y.append(norm_score)
                                pbar.update(1)
                        except Exception as e:
                            print("Stockfish error:", e)
                        board.push(move)

    engine.quit()
    X, y = np.array(X), np.array(y)
    np.savez(cache_file, X=X, y=y)
    print("Data saved in", cache_file)
    return X, y




if __name__ == "__main__":
    
    pgn_path = "data\lichess_elite_2025-02.pgn" # PGN data file
    stockfish_path = "stockfish\stockfish-windows-x86-64-avx2.exe"  #Stockfish

    print("\n Extracting data with Stockfish...")
    X, y = extract_data_with_stockfish(pgn_path, stockfish_path, max_positions=200000)

    
    print("Dataset charge.")
    print(f"X shape: {X.shape}")       # (N, 14, 8, 8)
    print(f"y shape: {y.shape}")       # (N,)
    print(f"y min: {y.min():.3f}, max: {y.max():.3f}, mean: {y.mean():.3f}")

    plt.hist(y, bins=50, color='skyblue')
    plt.title("Distribution des evaluations Stockfish (y)")
    plt.xlabel("evaluation normalisee (-1 = noir gagne, +1 = blanc gagne)")
    plt.ylabel("Nombre de positions")
    plt.grid(True)
    plt.show()


    # --- Split train/val ---
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    train_dataset = TensorDataset(torch.tensor(X_train, dtype=torch.float32), torch.tensor(y_train, dtype=torch.float32).unsqueeze(1))
    val_dataset = TensorDataset(torch.tensor(X_val, dtype=torch.float32), torch.tensor(y_val, dtype=torch.float32).unsqueeze(1))

    train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=128)

    # --- Model training ---
    model = ValueNet()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.0001)
    loss_fn = nn.MSELoss()

    train_losses = []
    val_losses = []

    epochs = 15

    for epoch in range(epochs):
        model.train()
        train_loss = 0
        for batch_X, batch_y in train_loader:
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
                val_output = model(batch_X)
                loss = loss_fn(val_output, batch_y)
                val_loss += loss.item() * batch_X.size(0)
        val_loss /= len(val_loader.dataset)
        
        train_losses.append(train_loss)
        val_losses.append(val_loss)
        
        print(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f} - Val Loss: {val_loss:.4f}")
        
        
    # --- Plot Graph ---
    plot_losses(train_losses, val_losses)

    # --- Test on validation set ---
    model.eval()
    y_val_tensor = torch.tensor(X_val, dtype=torch.float32)
    y_pred = model(y_val_tensor).detach().numpy().flatten()

    # ---  scatter plot + histogram  ---
    plot_predictions(y_val, y_pred)
    plot_error_distribution(y_val, y_pred)

    
    print("\n💾 Saving the model...")
    torch.save(model.state_dict(), "modeles/value_model_stockfish.pt")
    print("\n Model saved as 'value_model_stockfish.pt'")
