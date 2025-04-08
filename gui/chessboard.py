from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QAction, QVBoxLayout, QPushButton
from PyQt5.QtGui import QPalette, QColor, QPainter, QPainterPath, QPixmap
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint, pyqtSignal

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import math

from gui.variables import PIECE_IMAGES, WHITE, GREEN, YELLOW, SQUARE_SIZE
from gui.promotion import PromotionWidget
from bot import RandomBot


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
        self.promotion = None            # keep track of the prev_pos and new_pose for the promotion

        # Connect the piece_selected signal to a method in this class
        self.promotion_widget.piece_selected.connect(self.handle_promotion)

        # Bot integration
        self.initBot()


    def initBot(self):
        """
        Initialize the bot integration.
        """
        self.bot = RandomBot(self.engine)

        self.current_turn = "white"
        self.bot_color = "black"
        self.player_color = "white"
        self.isBot = False
        


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
            self.legal_moves = self.back_front.get_legal_moves_coor(self.engine, square)
            seen = set()
            self.legal_moves = [x for x in self.legal_moves if not (x in seen or seen.add(x))]  # removes duplicates

            painter.setBrush(QColor(0, 0, 0, 120))  # Set color to black and alpha = 120 for transparancy
            painter.setPen(Qt.NoPen)  # No border

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

        # Check if it's two player playing or if there's a bot too
        if self.player_color == self.current_turn or not self.isBot:    # if there is no Bot, two players game

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
                        self.current_turn = "black" if self.current_turn == "white" else "white"    # Change player's turn
                        self.play_bot()
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

                        # Deselect everything after capturing
                        self.selected_squares = []
                        self.highlighted_square = []
                        self.moves = []
                        self.update()
                        self.current_turn = "black" if self.current_turn == "white" else "white"    # Change player's turn
                        self.play_bot()
                        self.update()
                        return
            
            if front_piece != 0:
                self.highlighted_square.append(square_pos)
                self.selected_squares.append(square_pos)


            # Square processing
            if front_piece != 0:
                self.highlighted_square = [square_pos]
                self.selected_squares = [square_pos]

            

        else:
            pass

        
        self.update()   # call the paintEvent method to redraw the board
        


    # -------- Bot methods --------
    def play_bot(self):
        """
        Make the bot move.
        """
        self.bot.play()
        self.current_turn = "black" if self.current_turn == "white" else "white"    # Change player's turn
        



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
        if piece == 'p' and new_pos[0] == 7 or piece == 'P' and new_pos[0] == 0:    # when there's a promotion
            self.promotion = [prev_pos, new_pos]
            self.pawn_promotion(new_pos)

        else:
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

        color = "White" if square_pos[0] == 0 else "Black"

        # Show the promotion widget above the square
        self.promotion_widget.show_at_position(QPoint(x_pos, y_pos), color)
        
    

    def handle_promotion(self, selected_piece):
        """
        Handle the piece promotion by updating the board and game state.
        selected_piece = "Q" or "r".
        """
        # print(selected_piece)
        prev_pos, new_pos = self.promotion
        self.back_front.move_piece(self.engine, prev_pos, new_pos, param = selected_piece)
        self.read_board()
        self.update()
        


    # -------- Action methods --------
    def reset_game(self):
        """
        Reset the game.
        """
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.engine.set_fen(fen)
        self.read_board()
        self.update()
        self.selected_squares = []
        self.highlighted_square = []
        self.legal_moves = []

    
    def set_game(self):
        """
        Set the board to a specific position for debbuging.
        """
        custom_fen = "8/1P6/8/8/8/8/8/8 w - - 0 1"
        self.engine.set_fen(custom_fen)
        self.read_board()
        self.update()
        self.selected_squares = []
        self.highlighted_square = []
        self.legal_moves = []