import os
import random
import csv
import zstandard as zstd
import chess.pgn
import re
from tqdm import tqdm

class Processing:
    def __init__(self, input_pgn, output_pgn, csv_output, num_positions, min_elo, phase_distribution, max_games=200_000):
        self.input_pgn = input_pgn
        self.output_pgn = output_pgn
        self.csv_output = csv_output
        self.num_positions = num_positions
        self.min_elo = min_elo
        self.phase_distribution = phase_distribution
        self.max_games = max_games

    def decompress_pgn_zst(self):
        if not self.input_pgn.endswith(".zst"):
            print("No decompression needed.")
            return self.input_pgn

        decompressed_pgn = self.input_pgn.replace(".zst", "")
        print(f"Decompressing {self.input_pgn} to {decompressed_pgn}...")

        file_size = os.path.getsize(self.input_pgn)
        chunk_size = 2**20  # 1MB

        with open(self.input_pgn, 'rb') as compressed_file, open(decompressed_pgn, 'wb') as out_file:
            dctx = zstd.ZstdDecompressor()
            with dctx.stream_reader(compressed_file) as reader:
                with tqdm(total=file_size, unit='B', unit_scale=True, desc="Decompressing") as pbar:
                    while True:
                        chunk = reader.read(chunk_size)
                        if not chunk:
                            break
                        out_file.write(chunk)
                        pbar.update(len(chunk))

        print("Decompression completed.")
        self.input_pgn = decompressed_pgn

    def filter_high_elo_games_by_line(self):
        print(f"Filtering first {self.max_games} games with both players ELO >= {self.min_elo}...")

        elo_pattern = re.compile(r'\[WhiteElo "(\d+)"\]|\[BlackElo "(\d+)"\]')
        with open(self.input_pgn, 'r') as infile, open(self.output_pgn, 'w') as outfile:
            game = []
            count = 0
            for line in tqdm(infile, desc="Filtering Games"):
                if line.strip() == "" and game:
                    game_text = ''.join(game)
                    white_elo = black_elo = None
                    for g_line in game:
                        match = elo_pattern.match(g_line)
                        if match:
                            if match.group(1):
                                white_elo = int(match.group(1))
                            elif match.group(2):
                                black_elo = int(match.group(2))
                    if (
                        white_elo is not None and black_elo is not None and
                        white_elo >= self.min_elo and black_elo >= self.min_elo
                    ):
                        outfile.write(game_text + "\n")
                        count += 1
                        if count >= self.max_games:
                            break
                    game = []
                else:
                    game.append(line)
        print(f"Saved {count} high ELO games to {self.output_pgn}")

    def classify_phase(self, board):
        pieces = board.piece_map().values()
        material = sum(1 for p in pieces if p.piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT])
        if material >= 12:
            return 'opening'
        elif material >= 6:
            return 'middlegame'
        else:
            return 'endgame'

    def extract_fens(self):
        print(f"Extracting FENs with target distribution {self.phase_distribution}...")
        fens = {'opening': [], 'middlegame': [], 'endgame': []}
        total_needed = sum(self.phase_distribution.values())
        total_collected = 0

        with open(self.output_pgn) as pgn_file, tqdm(total=total_needed, desc="Extracting FENs") as pbar:
            while total_collected < total_needed:
                game = chess.pgn.read_game(pgn_file)
                if game is None:
                    break
                board = game.board()
                all_moves = list(game.mainline_moves())
                if len(all_moves) < 6:
                    continue
                for move in all_moves:
                    board.push(move)
                    phase = self.classify_phase(board)
                    if len(fens[phase]) < self.phase_distribution[phase] and random.random() < 0.02:
                        fens[phase].append((board.fen(), phase))
                        total_collected += 1
                        pbar.update(1)
                        if total_collected >= total_needed:
                            break
        print(f"Collected total: {len(fens['opening']) + len(fens['middlegame']) + len(fens['endgame'])} positions.")
        return fens['opening'] + fens['middlegame'] + fens['endgame']

    def save_csv(self, fens):
        with open(self.csv_output, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['fen', 'phase'])
            writer.writerows(fens)
        print(f"Saved {len(fens)} FENs to {self.csv_output}")

    def run(self):
        self.decompress_pgn_zst()
        self.filter_high_elo_games_by_line()  # New filtering method
        fens = self.extract_fens()
        self.save_csv(fens)





def main():
    input_pgn = "lichess_db_standard_rated_2016-08.pgn.zst"
    output_pgn_filtered = "lichess_data_filtered.pgn"
    csv_output = "sampled_fens.csv"
    num_positions = 50000
    min_elo = 1800
    phase_distribution = {
        'opening': 15000,
        'middlegame': 30000,
        'endgame': 5000
    }

    extractor = Processing(
        input_pgn=input_pgn,
        output_pgn=output_pgn_filtered,
        csv_output=csv_output,
        num_positions=num_positions,
        min_elo=min_elo,
        phase_distribution=phase_distribution
    )
    extractor.run()

if __name__ == "__main__":
    main()
