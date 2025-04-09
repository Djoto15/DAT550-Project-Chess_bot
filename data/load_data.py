import re

input_file = 'first_10000_games.pgn'
output_file = 'filtered_games.pgn'
min_elo = 1800

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
    return white_elo is not None and black_elo is not None and white_elo >= min_elo and black_elo >= min_elo

with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
    game = []
    for line in infile:
        game.append(line)
        if line.startswith('[Event "'):
            if has_min_elo(''.join(game), min_elo):
                outfile.write(''.join(game))
            game = []

