import chess
import chess.engine

class Stockfish:
    def __init__(self, engine, elo=200, stockfish_path="/usr/games/stockfish"):
        self.engine = engine
        self.elo = elo
        self.stockfish_path = stockfish_path
        self.bot = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)

    def __enter__(self):
        self.bot = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
        self._configure_engine()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.bot:
            self.bot.quit()

    def _configure_engine(self):
        """Configure Stockfish's skill level based on the desired ELO."""
        skill_level = self._elo_to_skill_level()
        try:
            self.bot.configure({"Skill Level": skill_level})
        except Exception as e:
            print(f"[Stockfish Config] Failed to set skill level: {e}")

    def _elo_to_skill_level(self):
        """Maps approximate ELO to Stockfish's skill level (0–20)."""
        if self.elo < 1000:
            return 0
        elif self.elo < 1500:
            return 5
        elif self.elo < 1800:
            return 10
        elif self.elo < 2100:
            return 15
        else:
            return 20

    def predict(self):
        """Returns Stockfish's best move from the current board."""
        board = self.engine.board
        try:
            result = self.bot.play(board, chess.engine.Limit(time=0.1))
            return result.move
        except Exception as e:
            print(f"[Stockfish Predict] Error: {e}")
            return None


    def evaluate(self, board):
        """Returns the centipawn evaluation from White's perspective."""
        try:
            info = self.bot.analyse(board, chess.engine.Limit(time=0.1))
            return info["score"].white().score(mate_score=10000) / 100
        except Exception as e:
            print(f"[Stockfish Evaluate] Error: {e}")
            return 0.0

    def fit(self, pgn_path):
        # Not used for Stockfish, but included for interface consistency
        pass

    def close(self):
        self.bot.quit()
