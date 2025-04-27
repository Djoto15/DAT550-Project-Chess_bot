import chess.pgn
from tqdm import tqdm

# Set paths
input_pgn_file = "lichess_db_standard_rated_2014-09.pgn"  # has 1,000,056 games
output_pgn_file = "filtered_400to600.pgn"

# Function to check if both players have an ELO >= 1800
def is_valid_game(headers):
    try:
        white_elo = int(headers.get("WhiteElo", 0))
        black_elo = int(headers.get("BlackElo", 0))
        return white_elo >= 1800 and black_elo >= 1800
    except:
        return False
    




# Open input PGN file and output PGN file
MAX_GAMES = 1000

with open(input_pgn_file, encoding='utf-8') as input_pgn, open(output_pgn_file, "w", encoding='utf-8') as output_pgn:
    game_count = 0
    valid_count = 0

    pbar = tqdm(total=MAX_GAMES, desc="Filtered 1800+ games")

    while True:
        game = chess.pgn.read_game(input_pgn)
        if game is None:
            break

        game_count += 1

        if is_valid_game(game.headers):
            output_pgn.write(str(game) + "\n\n")
            valid_count += 1
            pbar.update(1)

        if valid_count >= MAX_GAMES:
            break


    pbar.close()
    print(f"\n✅ Done! Processed {game_count} total games.")
    print(f"✅ Filtered {valid_count} valid games with 1800+ ELO players.")
