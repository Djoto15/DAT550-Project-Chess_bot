from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QAction, QVBoxLayout, QPushButton
from PyQt5.QtGui import QPalette, QColor, QPainter, QPainterPath, QPixmap
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint, pyqtSignal

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from gui.variables import PIECE_IMAGES, WHITE, GREEN, YELLOW, SQUARE_SIZE


class PromotionWidget(QWidget):
    # Create a signal to emit the selected piece
    piece_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup)  # Make it a popup so it floats above the board
        self.setFixedSize(200, 150)
        
        # Setup the layout and buttons
        layout = QVBoxLayout(self)
        
        self.promotion_options = ["Queen", "Rook", "Bishop", "Knight"]
        self.buttons = {}

        for option in self.promotion_options:
            button = QPushButton(option, self)
            button.clicked.connect(self.on_button_clicked)
            layout.addWidget(button)
            self.buttons[button] = option

        self.setLayout(layout)

        self.color = None


    def on_button_clicked(self):
        """
        Slot that handles the selection of a promotion piece.
        """
        button = self.sender()
        selected_piece = self.buttons[button]

        # That's where we need to handle which piece will be returned
        shown_piece = None
        if selected_piece == "Queen":
            shown_piece = "q" 
        elif selected_piece == "Rook":
            shown_piece = "r" 
        elif selected_piece == "Bishop":
            shown_piece = "b" 
        elif selected_piece == "Knight":
            shown_piece = "n" 

        # Return the piece
        self.piece_selected.emit(shown_piece)  # Emit the selected piece
        self.close()  # Close the promotion widget after selection

    def show_at_position(self, position: QPoint, color):
        """
        Show the promotion widget at the specified position on the screen.
        """
        self.color = color
        self.move(position)
        self.show()