from engine import Engine
from back_front import Back_Front
from gui import MainWindow

import sys
from PyQt5.QtWidgets import QApplication


def main():
    """
    Launch the chess engine.
    """
    app = QApplication(sys.argv)

    engine = Engine()
    link = Back_Front()

    window = MainWindow(engine, link)
    window.show()
    window.config_game()

    app.exec_()

    # This is where the code is runned after the window close

    sys.exit()




if __name__ == "__main__":
    main()

