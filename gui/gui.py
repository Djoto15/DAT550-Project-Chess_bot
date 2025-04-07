from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QAction, QVBoxLayout, QPushButton
from PyQt5.QtGui import QPalette, QColor, QPainter, QPainterPath, QPixmap
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import math


# Define constants
PIECE_IMAGES = {
    "r": "images/black-rook.png",
    "n": "images/black-knight.png",
    "b": "images/black-bishop.png",
    "q": "images/black-queen.png",
    "k": "images/black-king.png",
    "p": "images/black-pawn.png",
    "R": "images/white-rook.png",
    "N": "images/white-knight.png",
    "B": "images/white-bishop.png",
    "Q": "images/white-queen.png",
    "K": "images/white-king.png",
    "P": "images/white-pawn.png"
}

SQUARE_SIZE = 100
WHITE = "#eeeed2"
GREEN = "#769656"
BLACK = "#000000"
YELLOW = "#e7fa6b"


class MainWindow(QMainWindow):

    def __init__(self, engine, link):
        super().__init__()
        self.setWindowTitle("Chess")
        self.setGeometry(700, 300, 1200, 1000)
        self.set_dark_mode()

        self.initUI(engine, link)
        self.initMenu()

    
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
        self.chessboard.move(20, 80)  # Position it manually


    def initMenu(self):
        self.Menu = self.menuBar()
        GameMenu = self.Menu.addMenu("Game")

        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        GameMenu.addAction(quit_action)

        
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





class ChessBoard(QWidget):
    def __init__(self, engine, link, parent=None):
        super().__init__(parent)
        
        self.setFixedSize(800, 800)

        self.engine = engine
        self.back_front = link

        self.front_board = link.get_pieces_position(self.engine)[::-1]  # invert due to the structure of the chessboard

        self.highlighted_square = []     # to keep track of the square for highlighting
        self.legal_moves = []            # keep track of the possible moves for selected pieces
        self.selected_squares = []       # keep track of all selected squares

        self.promotion_widget = PromotionWidget(self)


    # -------- Board drawing methods --------

    def paintEvent(self, event):
        """
        Handle the painting of all components.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)

        self.draw_board(painter)                        # Draws the chessboard squares (needs to be first)

        if len(self.highlighted_square) > 0:
            self.highlight_square(painter, self.highlighted_square[-1])

        if len(self.selected_squares) > 0:
            self.draw_possible_moves(painter, self.selected_squares[-1])


        self.draw_pieces(painter, self.front_board)     # Draws the pieces (needs to be second to last)
        self.draw_labels(painter)                       # Draws the indexes for the cells (needs to be last)


    def draw_board(self, painter):
        """
        Draw the chessboard.
        """
        border_radius = 8  
        path = QPainterPath()
        path.addRoundedRect(0, 0, 8 * SQUARE_SIZE, 8 * SQUARE_SIZE, border_radius, border_radius)
        painter.setClipPath(path)

        # Draw the board squares
        for row in range(8):
            for col in range(8):
                color = QColor(WHITE if (row + col) % 2 == 0 else GREEN) 
                painter.setBrush(color)
                painter.drawRect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)


    def draw_labels(self, painter):
        """
        Draws the column (a-h) and row (1-8) labels around the chessboard.
        """
        # set up the font for the labels
        font = painter.font()
        font.setPointSize(15)
        font.setWeight(63)
        painter.setFont(font)
        

        # draw the labels
        letters , numbers= "abcdefgh", "87654321"

        for i in range(len(numbers)):
            color = QColor(GREEN if i % 2 == 0 else WHITE)
            op_color = QColor(WHITE if i % 2 == 0 else GREEN)
            painter.setPen(color)
            painter.drawText(6, 23 + i * SQUARE_SIZE, numbers[i])
            painter.setPen(op_color)
            painter.drawText(82 + i * SQUARE_SIZE, 792 , letters[i])


    def draw_pieces(self, painter, front_board):
        """
        Draws the pieces on the board at their original position
        """
        for row in range(8):
            for col in range(8):
                piece = front_board[row][col]  # Get piece at (row, col)
                self.draw_piece(painter, piece, row, col)  # Draw the piece

    def draw_piece(self, painter, piece, row, col):
        """
        Draws a single chess piece on the board.
        """
        if piece != 0:  # Ensure it's not an empty square

            piece_image = QPixmap(PIECE_IMAGES[piece])  # Load image
            piece_size = SQUARE_SIZE * 0.95  # Scale down slightly for spacing

            # Use the scaled method to smoothly scale the image
            scaled_image = piece_image.scaled(int(piece_size), int(piece_size), Qt.KeepAspectRatio, Qt.SmoothTransformation)

            # Compute centered coordinates
            x = col * SQUARE_SIZE + (SQUARE_SIZE - piece_size) / 2
            y = row * SQUARE_SIZE + (SQUARE_SIZE - piece_size) / 2

            # Enable anti-aliasing for smoother rendering
            painter.setRenderHint(QPainter.Antialiasing, True)

            # Draw the scaled piece with anti-aliasing
            painter.drawPixmap(int(x), int(y), scaled_image)


    def highlight_square(self, painter, square_pos):
        """
        Highlights the selected square with a different color (for example, yellow).
        """

        # Set the color for highlighting (e.g., a light yellow)
        highlight_color = QColor(YELLOW)
        painter.setBrush(highlight_color)
        painter.setPen(Qt.NoPen)

        # Draw the highlight on the square
        row, col = square_pos
        painter.drawRect(int(col * SQUARE_SIZE), int(row * SQUARE_SIZE), SQUARE_SIZE, SQUARE_SIZE)


    def draw_possible_moves(self, painter, square):
            """
            Draws black circles on the given list of move positions.
            """
            painter.setBrush(QColor(0, 0, 0, 120))  # Set color to black and alpha = 120 for transparancy
            painter.setPen(Qt.NoPen)  # No border

            self.legal_moves = self.back_front.get_legal_moves_coor(self.engine, square)

            for row, col in self.legal_moves:
                # Calculate the center of the square
                center_x = col * SQUARE_SIZE + SQUARE_SIZE / 2
                center_y = row * SQUARE_SIZE + SQUARE_SIZE / 2
                radius = SQUARE_SIZE * 0.18  # Radius of the circle

                # Draw the circle
                painter.drawEllipse(int(center_x - radius), int(center_y - radius), int(radius * 2), int(radius * 2))




    # -------- Mouse event methods --------

    def mousePressEvent(self, event):
        click_position = event.pos()
        square_pos = self.which_square(click_position)
        row, col = square_pos

        front_piece = self.front_board[row][col]

        # Check if the piece is a pawn on the promotion rank (8th rank for white or 1st rank for black)
        if front_piece != 0:
            if front_piece.lower() == 'p' and (row == 0 or row == 7):
                # Trigger pawn promotion
                self.pawn_promotion(square_pos)
                return

        # If clicking on an empty square and a piece is selected, move it
        if front_piece == 0 and len(self.selected_squares) > 0:
            prev_square = self.selected_squares[-1]
            p_row, p_col = prev_square[0], prev_square[1]
            prev_front_piece = self.front_board[p_row][p_col]

            if prev_front_piece != 0:
                self.legal_moves = self.back_front.get_legal_moves_coor(self.engine, prev_square)

                if square_pos in self.legal_moves:
                    self.front_board[p_row][p_col] = 0
                    self.move_piece(prev_front_piece, prev_square, square_pos)   # move the piece in the front_board

                    # Deselect everything after moving
                    self.selected_squares = []
                    self.highlighted_square = []
                    self.moves = []
                    self.update()
                    return  # Stop further processing

        # If clicking on an opponent's piece that can be captured        
        elif front_piece != 0 and len(self.selected_squares) > 0:
            prev_square = self.selected_squares[-1]
            p_row, p_col = prev_square[0], prev_square[1]
            prev_front_piece = self.front_board[p_row][p_col]

            if prev_front_piece != 0 and ((front_piece.isupper() and prev_front_piece.islower()) or front_piece.islower() and prev_front_piece.isupper()):
                self.legal_moves = self.back_front.get_legal_moves_coor(self.engine, prev_square)

                if square_pos in self.legal_moves:
                    self.front_board[square_pos[0]][square_pos[1]] = 0
                    self.front_board[prev_square[0]][prev_square[1]] = 0

                    self.move_piece(prev_front_piece, prev_square, square_pos)

                    # **Deselect everything after capturing**
                    self.selected_squares = []
                    self.highlighted_square = []
                    self.moves = []
                    self.update()
                    return
        
        if front_piece != 0:
            self.highlighted_square.append(square_pos)
            self.selected_squares.append(square_pos)


        # Square processing
        if front_piece != 0:
            self.highlighted_square = [square_pos]
            self.selected_squares = [square_pos]

        
        self.update()   # call the paintEvent method to redraw the board



    # -------- Specific square methods --------

    def which_square(self, pos):
        """
        Take a pair of coordinates in the widget and return the corresponded square in the chessboard.
        """
        square_pos = (pos.y() // SQUARE_SIZE, pos.x() // SQUARE_SIZE)
        return square_pos
    

    # -------- Piece movement methods --------

    def move_piece(self, piece, prev_pos, new_pos):
        """
        Move piece to the new_pos.
        """
        self.move_animate_piece(piece, prev_pos, new_pos)

        # Move the piece in the engine (back-front)
        self.back_front.move_piece(self.engine, prev_pos, new_pos)


    def move_animate_piece(self, piece, prev_pos, new_pos):
        """
        Animate the piece movement on the GUI and update the engine.
        """
        # Create the label for the piece to animate
        self.piece_label = QLabel(self)
        self.piece_pixmap = QPixmap(PIECE_IMAGES[piece])
        piece_size = int(SQUARE_SIZE * 0.95)
        self.piece_label.setPixmap(self.piece_pixmap.scaled(piece_size, piece_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        # Initial position of the piece
        x_pos = prev_pos[1] * SQUARE_SIZE
        y_pos = prev_pos[0] * SQUARE_SIZE
        self.piece_label.setGeometry(int(x_pos), int(y_pos), piece_size, piece_size)

        # Add the label to the chessboard widget for animation
        self.piece_label.show()

        # Target position of the piece
        new_pos_x = new_pos[1] * SQUARE_SIZE
        new_pos_y = new_pos[0] * SQUARE_SIZE

        # Calculate the distance between the current and new position (Euclidean distance)
        distance = math.sqrt((new_pos_x - x_pos) ** 2 + (new_pos_y - y_pos) ** 2)

        # Duration of the animation depends on the distance
        duration = int(distance * 0.8)

        # Set up the animation for smooth piece movement
        self.animation = QPropertyAnimation(self.piece_label, b"pos")
        self.animation.setDuration(duration)
        self.animation.setStartValue(self.piece_label.pos())
        self.animation.setEndValue(QPoint(new_pos_x, new_pos_y))

        # Start the animation        
        self.animation.start()
        
        # Once the animation is finished, update the board and the chess engine
        self.animation.finished.connect(lambda: self.on_animation_finished(piece, new_pos))
        

    def on_animation_finished(self, piece, new_pos):
        """
        Callback for when the piece movement animation finishes.
        """
        # Clear the label and update the board
        self.front_board[new_pos[0]][new_pos[1]] = piece
        self.piece_label.deleteLater()
        self.read_board()
        self.update()


    # -------- Reading methods --------

    def read_board(self):
        """
        Read the engine board and set the front board accordingly.
        Mostly to update after a castling move.
        """
        new_board = self.back_front.read_engine(self.engine)
        self.front_board = new_board


    # -------- Promotion methods --------

    def pawn_promotion(self, square_pos):
        # Get the position of the square to display the promotion widget above it
        x_pos = square_pos[1] * SQUARE_SIZE
        y_pos = square_pos[0] * SQUARE_SIZE

        # Show the promotion widget above the square
        self.promotion_widget.show_at_position(QPoint(x_pos, y_pos))






class PromotionWidget(QWidget):
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

        self.selected_piece = None
        self.setLayout(layout)

    def on_button_clicked(self):
        """
        Slot that handles the selection of a promotion piece.
        """
        button = self.sender()
        self.selected_piece = self.buttons[button]
        self.close()  # Close the promotion widget after selection
        print(f"Selected piece for promotion: {self.selected_piece}")

    def get_selected_piece(self):
        """
        Return the selected piece.
        """
        return self.selected_piece

    def show_at_position(self, position: QPoint):
        """
        Show the promotion widget at the specified position on the screen.
        """
        self.move(position)
        self.show()


     

        
