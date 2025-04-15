from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QAction, QVBoxLayout, QPushButton, QDialog
from PyQt5.QtGui import QPalette, QColor, QPainter, QPainterPath, QPixmap
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint, pyqtSignal

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from gui.variables import PIECE_IMAGES, WHITE, GREEN, YELLOW, SQUARE_SIZE

from gui.chessboard import ChessBoard
from gui.config_game import ConfigGameDialog



class MainWindow(QMainWindow):

    def __init__(self, engine, link):
        super().__init__()
        self.setWindowTitle("Chess")
        # self.setGeometry(700, 300, 1200, 1000)
        self.setGeometry(700, 300, 840, 880)
        self.set_dark_mode()


        self.initUI(engine, link)

        self.engine = engine

        self.initMenu()

        self.chessboard.start_game()
        


    
    # -------- Initialzing methods --------

    def initUI(self, engine, link):
        """
        Initialize the main UI.
        """
        # Create main container
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Create the chessboard widget and set its parent to central_widget
        self.chessboard = ChessBoard(engine, link, self.central_widget)
        # self.chessboard.move(20, 80)  # Position it manually
        self.chessboard.move(20, 20)


    def initMenu(self):
        self.Menu = self.menuBar()
        GameMenu = self.Menu.addMenu("Game")
        ToolMenu = self.Menu.addMenu("Tools")

        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        GameMenu.addAction(quit_action)

        new_game = QAction("New game", self)
        new_game.setShortcut("Ctrl+N")
        new_game.triggered.connect(self.new_game)
        GameMenu.addAction(new_game)

        config = QAction("Config game", self)
        config.setShortcut("Ctrl+C")
        config.triggered.connect(self.config_game)
        GameMenu.addAction(config)

        launch = QAction("Launch game", self)
        launch.setShortcut("Ctrl+L")
        launch.triggered.connect(self.launch_game)
        GameMenu.addAction(launch)


        set_game = QAction("Debbug game", self)
        set_game.setShortcut("Ctrl+D")
        set_game.triggered.connect(self.set_game)
        ToolMenu.addAction(set_game)

        get_fen = QAction("Get fen", self)
        get_fen.setShortcut("Ctrl+G")
        get_fen.triggered.connect(self.get_fen)
        ToolMenu.addAction(get_fen)

        eval = QAction("Evaluate board", self)
        eval.setShortcut("Ctrl+E")
        eval.triggered.connect(self.eval)
        ToolMenu.addAction(eval)


    # -------- Action methods --------

    def new_game(self):
        """
        Launch a new game.
        """
        self.chessboard.reset_game()

    def set_game(self):
        self.chessboard.set_game()

    def config_game(self):
        dialog = ConfigGameDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            white_player, black_player = dialog.get_settings()
            self.chessboard.config_game(white_player, black_player)

    def get_fen(self):
        self.chessboard.get_fen()

    def launch_game(self):
        self.chessboard.launch_game()

    def eval(self):
        self.chessboard.evaluate()
        

        
    # -------- Style Sheet methods --------

    def set_dark_mode(self):
        palette = QPalette()

        # Set dark background and lighter foreground
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))

        # Set button and highlight colors
        palette.setColor(QPalette.Base, QColor(42, 42, 42))
        palette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(64, 64, 64))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(72, 72, 72))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

        # Apply the dark mode palette
        QApplication.setPalette(palette)

        # Add dark styling for menu bar and menus
        self.setStyleSheet("""
        QMenuBar {
            background-color: #2c2c2c;
            color: white;
            padding: 4px;
            border-radius: 8px;
        }

        QMenuBar::item {
            background-color: transparent;
            color: white;
            padding: 6px 12px;
            border-radius: 6px;
        }

        QMenuBar::item:selected {
            background-color: #3c3c3c;
        }

        QMenu {
            background-color: #2c2c2c;
            color: white;
            border: 1px solid #555;
            border-radius: 8px;
            padding: 6px;
        }

        QMenu::item {
            background-color: transparent;
            padding: 6px 16px;
            border-radius: 4px;
        }

        QMenu::item:selected {
            background-color: #444;
        }
    """)