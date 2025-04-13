import chess
import chess.engine

class Stockfish:
    def __init__(self, engine, elo, stockfish_path="/usr/games/stockfish"):
        self.bot = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        self.engine = engine
        self.elo = elo
        self.config()  # Set the skill level based on the ELO

    def config(self):
        """
        Configure the Stockfish engine by setting its skill level based on the given ELO.
        Skill level ranges from 0 to 20, with higher numbers being stronger.
        """
        skill_level = self.elo_to_skill_level()
        self.bot.configure({"Skill Level": skill_level})

    def elo_to_skill_level(self):
        """
        Map the given ELO rating to Stockfish skill level.
        Stockfish skill levels range from 0 (weakest) to 20 (strongest).
        """
        if self.elo < 1000:
            return 0  # Skill level for below 1000 ELO
        elif self.elo < 1500:
            return 5  # Skill level for 1000-1500 ELO
        elif self.elo < 1800:
            return 10  # Skill level for 1500-1800 ELO
        elif self.elo < 2100:
            return 15  # Skill level for 1800-2100 ELO
        else:
            return 20  # Skill level for above 2100 ELO

    def predict(self):
        """
        Returns the best move chosen by Stockfish for the current position.
        """
        result = self.bot.play(self.engine.board, chess.engine.Limit(time=0.1))  # Set the time for Stockfish's move
        return [result.move]

    def close(self):
        """
        Close the Stockfish engine when finished.
        """
        self.engine.quit()

    def fit(self, pgn_path):
        """Just do nothing but debbug."""
        pass
