from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QRectF

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from gui.variables import PIECE_IMAGES, SQUARE_SIZE



class PromotionWidget(QWidget):
    # Create a signal to emit the selected piece
    piece_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup)  # Make it a popup so it floats above the board
        self.setFixedSize(200, 200)

        # self.setStyleSheet("""
        #                     background-color: #54575c;
        #                     border-radius: 12px;
        #                 """)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            background-color: #54575c;
            border-radius: 12px;
        """)



        # Setup the layout
        layout = QGridLayout(self)
        self.promotion_options = {"White":["Q", "R", "B", "N"], "Black":["q", "r", "b", "n"]}

        self.setLayout(layout)
        self.color = None


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect())  # Convert QRect to QRectF
        radius = 12

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        painter.fillPath(path, QColor("#606266"))



    def show_at_position(self, position: QPoint, color):
        """
        Show the promotion widget at the specified position (relative to board widget),
        and draw the piece options.
        """
        self.color = color
        self.clear_layout()

        # Draw the promotion piece images
        for row in range(2):
            for col in range(2):
                piece_code = self.promotion_options[self.color][row * 2 + col]
                piece_img_path = PIECE_IMAGES[piece_code]
                piece_label = QLabel(self)
                pixmap = QPixmap(piece_img_path).scaled(SQUARE_SIZE, SQUARE_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                piece_label.setPixmap(pixmap)
                piece_label.setAlignment(Qt.AlignCenter)
                self.layout().addWidget(piece_label, row, col)

        # Convert the clicked position (relative to chessboard widget) to screen coordinates
        global_pos = self.parent().mapToGlobal(position)
        self.move(global_pos.x() - 50, global_pos.y() - 50)
        self.show()




    def mousePressEvent(self, event):
        click_position = event.pos()
        square_pos = self.which_square(click_position)
        self.on_click(square_pos)



    def on_click(self, choice):
        """
        Return the selected piece.
        """
        # That's where we need to handle which piece will be returned
        shown_piece = None
        if choice == (0, 0):
            shown_piece = "q" # Queen
        elif choice == (0, 1):
            shown_piece = "r" # Rook
        elif choice == (1, 0):
            shown_piece = "b" # Bishop
        elif choice == (1, 1):
            shown_piece = "n" # Knight

        # Return the piece
        self.piece_selected.emit(shown_piece)  # Emit the selected piece
        self.close()  # Close the promotion widget after selection

        


    # -------- Specific square methods --------

    def which_square(self, pos):
        """
        Take a pair of coordinates in the widget and return the corresponded square in the chessboard.
        """
        square_pos = (pos.y() // SQUARE_SIZE, pos.x() // SQUARE_SIZE)
        return square_pos
    

    def clear_layout(self):
        while self.layout().count():
            child = self.layout().takeAt(0)
            if child.widget():
                child.widget().deleteLater()
