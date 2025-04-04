from engine import Engine
from back_front import Back_Front

from gui import MainWindow

import sys
from PyQt5.QtWidgets import QApplication

# engine = Engine()
# back_front = Back_Front()
# back_front.get_pieces_position(engine)


def main():
    """
    Launch the chess engine.
    """
    app = QApplication(sys.argv)

    engine = Engine()
    link = Back_Front()

    window = MainWindow(engine, link)
    window.show()

    app.exec_()

    # This is where the code is runned after the window closed

    sys.exit()




if __name__ == "__main__":
    main()

