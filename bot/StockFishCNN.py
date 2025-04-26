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


# --- Encodeur de plateau (14x8x8 tensor avec coups légaux) ---
def board_to_tensor(board):
    tensor = np.zeros((14, 8, 8), dtype=np.float32)
    piece_to_plane = {
        'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
        'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11
    }

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            plane = piece_to_plane[piece.symbol()]
            row = 7 - (square // 8)
            col = square % 8
            tensor[plane][row][col] = 1

    original_turn = board.turn

    board.turn = chess.WHITE
    for move in board.legal_moves:
        row = 7 - (move.to_square // 8)
        col = move.to_square % 8
        tensor[12][row][col] = 1

    board.turn = chess.BLACK
    for move in board.legal_moves:
        row = 7 - (move.to_square // 8)
        col = move.to_square % 8
        tensor[13][row][col] = 1

    board.turn = original_turn
    return tensor

# --- Génération de positions absurdes ---
def generate_blunder_position():
    board = chess.Board()
    for _ in range(random.randint(3, 7)):
        moves = list(board.legal_moves)
        if moves:
            board.push(random.choice(moves))
        else:
            break

    # Ajoute une dame blanche mal placée
    if board.piece_at(chess.E4) is None:
        board.set_piece_at(chess.E4, chess.Piece(chess.QUEEN, chess.WHITE))
    # Ajoute un pion noir qui attaque
    if board.piece_at(chess.D5) is None:
        board.set_piece_at(chess.D5, chess.Piece(chess.PAWN, chess.BLACK))

    return board


# --- Réseau CNN ValueNet amélioré ---
class ValueNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(14, 64, kernel_size=3, padding=1),
            #nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            #nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            #nn.BatchNorm2d(128),
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


# --- Extraction et évaluation ---
def extract_data_with_stockfish(pgn_path, stockfish_path, max_positions=1000, cache_file="data/dataset_value_net.npz", proportion_blunder=0.2):
    if Path(cache_file).exists():
        print("\n🔁 Chargement des données depuis le cache...")
        data = np.load(cache_file)
        return data['X'], data['y']

    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    X, y = [], []

    f = open(pgn_path, "r")
    game = chess.pgn.read_game(f)

    with tqdm(total=max_positions, desc="🔄 Extraction", unit="pos") as pbar:
        while len(X) < max_positions:
            # Décide si on génère une blunder
            if random.random() < proportion_blunder:
                board = generate_blunder_position()
            else:
                if game is None:
                    break
                board = game.board()
                for move in game.mainline_moves():
                    break
                game = chess.pgn.read_game(f)

            try:
                tensor = board_to_tensor(board)
                info = engine.analyse(board, chess.engine.Limit(depth=10))
                score = info["score"].white().score(mate_score=10000)
                if score is not None:
                    norm_score = max(-1000, min(1000, score)) / 1000
                    X.append(tensor)
                    y.append(norm_score)
                    pbar.update(1)
            except Exception as e:
                print("Stockfish error:", e)

    engine.quit()
    f.close()
    X, y = np.array(X), np.array(y)
    np.savez(cache_file, X=X, y=y)
    print("Données sauvegardées dans", cache_file)
    return X, y


# --- Entraînement avec split validation + batchs ---
def train_value_net(X, y, epochs=10, lr=0.0001, batch_size=128):
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    train_dataset = TensorDataset(torch.tensor(X_train, dtype=torch.float32), torch.tensor(y_train, dtype=torch.float32).unsqueeze(1))
    val_dataset = TensorDataset(torch.tensor(X_val, dtype=torch.float32), torch.tensor(y_val, dtype=torch.float32).unsqueeze(1))

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)

    model = ValueNet()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    train_losses = []
    val_losses = []

    for epoch in range(epochs):
        model.train()
        epoch_train_loss = 0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            output = model(batch_X)
            loss = loss_fn(output, batch_y)
            loss.backward()
            optimizer.step()
            epoch_train_loss += loss.item() * batch_X.size(0)
        epoch_train_loss /= len(train_loader.dataset)

        model.eval()
        epoch_val_loss = 0
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                val_output = model(batch_X)
                val_loss = loss_fn(val_output, batch_y)
                epoch_val_loss += val_loss.item() * batch_X.size(0)
        epoch_val_loss /= len(val_loader.dataset)

        train_losses.append(epoch_train_loss)
        val_losses.append(epoch_val_loss)

        print(f"Epoch {epoch+1}/{epochs} - Train Loss: {epoch_train_loss:.4f} - Val Loss: {epoch_val_loss:.4f}")

    plt.plot(range(1, epochs + 1), train_losses, label='Train Loss')
    plt.plot(range(1, epochs + 1), val_losses, label='Val Loss')
    plt.xlabel("Epoch")
    plt.ylabel("Loss (MSE)")
    plt.title("Courbe de perte train/validation")
    plt.legend()
    plt.grid(True)
    plt.show()

    return model


if __name__ == "__main__":
    
    pgn_path = "data\lichess_elite_2025-02.pgn"  # Remplace par ton fichier PGN
    stockfish_path = "stockfish\stockfish-windows-x86-64-avx2.exe"  

    print("\n Extraction des données avec Stockfish...")
    X, y = extract_data_with_stockfish(pgn_path, stockfish_path, max_positions=50000)

    
    '''print("Dataset charge.")
    print(f"X shape: {X.shape}")       # (N, 14, 8, 8)
    print(f"y shape: {y.shape}")       # (N,)
    print(f"y min: {y.min():.3f}, max: {y.max():.3f}, mean: {y.mean():.3f}")

    plt.hist(y, bins=50, color='skyblue')
    plt.title("Distribution des evaluations Stockfish (y)")
    plt.xlabel("evaluation normalisee (-1 = noir gagne, +1 = blanc gagne)")
    plt.ylabel("Nombre de positions")
    plt.grid(True)
    plt.show()'''


    
    print("\n🧠 Entraînement du ValueNet CNN...")
    model = train_value_net(X, y, epochs=15, batch_size=128)

    print("\n💾 Sauvegarde du modèle...")
    torch.save(model.state_dict(), "value_model_stockfish.pt")
    print("\n✅ Modèle sauvegardé sous 'value_model_stockfish.pt'")
