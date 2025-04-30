import chess
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

# Add parent directory to path to import engine and bots
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine import Engine
from baseline_model import Stockfish, RegressionTreeBot

if __name__ == "__main__":
    engine = Engine()
    bot = RegressionTreeBot(engine)
    stockfish = Stockfish(engine)

    bot.fit()
    print("Training done.")

    stockfish.predict()