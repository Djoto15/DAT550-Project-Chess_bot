import re

input_file = "lichess_db_standard_rated_2016-08.pgn"
output_file = '1800+ELO_games.pgn'
min_elo = 1800
max_games = 200_000

elo_pattern = re.compile(r'\[WhiteElo "(\d+)"\]|\[BlackElo "(\d+)"\]')

def has_min_elo(game, min_elo):
    white_elo = None
    black_elo = None
    for line in game.split('\n'):
        match = elo_pattern.match(line)
        if match:
            if match.group(1):
                white_elo = int(match.group(1))
            elif match.group(2):
                black_elo = int(match.group(2))
    return (
        white_elo is not None and 
        black_elo is not None and 
        white_elo >= min_elo and 
        black_elo >= min_elo
    )

with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
    game = []
    high_elo_count = 0
    for line in infile:
        if line.strip() == "" and game:
            # End of one game
            full_game = ''.join(game)
            if has_min_elo(full_game, min_elo):
                outfile.write(full_game + "\n")
                high_elo_count += 1
                if high_elo_count >= max_games:
                    print(f"Reached {max_games} high ELO games. Stopping.")
                    break
            game = []
        else:
            game.append(line)

print(f"Total high ELO games written: {high_elo_count}")
