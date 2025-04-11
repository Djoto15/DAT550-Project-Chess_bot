def count_games(pgn_file):
    game_count = 0
    with open(pgn_file, 'r') as file:
        for line in file:
            if line.startswith('[Event "'):
                game_count += 1
    return game_count

pgn_file = '1800thresh_6938.pgn'
# pgn_file = "1800thresh_1448.pgn"
number_of_games = count_games(pgn_file)
print(f'Number of games in {pgn_file}: {number_of_games}')
