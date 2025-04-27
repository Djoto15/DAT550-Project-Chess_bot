from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QAction, QVBoxLayout, QDialog, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPalette, QColor, QPainter, QPainterPath, QPixmap
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint, pyqtSignal, QTimer

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import math

from gui.variables import PIECE_IMAGES, WHITE, GREEN, YELLOW, SQUARE_SIZE, RED
from gui.promotion import PromotionWidget
from gui.game_over import GameOverPopup

# Bot import
from bot import LowEloBot, Training, Stockfish, BaseBot, BaseBot2, BaseBot3



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
        self.king_position = None

        self.promotion_widget = PromotionWidget(self)
        self.promotion = None            # keep track of the prev_pos and new_pose for the promotion

        self.evals = []

        # Connect the piece_selected signal to a method in this class
        self.promotion_widget.piece_selected.connect(self.handle_promotion)

        # Game configuration
        self.initConfig()
        self.initTraining()




    def initConfig(self):
        """
        Initialize the game.
        """
        self.current_turn = "white"
        self.player_color = "white"
        self.is_player = None

        self.white_player = None
        self.black_player = None
        self.isBot = False

        # Temp attributes
        self.bot_color = None



    def initTraining(self):
        """
        Initialize the training of the bots with a custom widget displaying the training status.
        """
        # Create a widget for the training message
        self.training_widget = QWidget(self)
        self.training_widget.setStyleSheet(
            """
            background-color: #54575c;
            border-radius: 10px;
            padding: 10px;
            """
        )

        # Create the label for the message
        self.training_label = QLabel("Training bots...", self)
        self.training_label.setAlignment(Qt.AlignCenter)
        self.training_label.setStyleSheet("font-size: 24px; color: white;")
        
        # Create a layout for the training widget (center the label)
        self.layout = QVBoxLayout(self.training_widget)
        self.layout.addWidget(self.training_label)
        
        # Create a layout for the ChessBoard to center the training widget
        main_layout = QVBoxLayout(self)  # Assuming self is a QWidget (ChessBoard)
        main_layout.setAlignment(Qt.AlignCenter)  # Align child widgets to center
        main_layout.addWidget(self.training_widget)
        
        # Hide the widget initially
        self.training_widget.hide()



        


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

        if self.is_check():
            self.highlight_check(painter)


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


    def highlight_check(self, painter):
        """
        Highlight the kings position if there's a check
        """
        

        # Set the color for highlighting (e.g., a light yellow)
        highlight_color = QColor(RED)
        painter.setBrush(highlight_color)
        painter.setPen(Qt.NoPen)

        # Draw the highlight on the square
        row, col = self.king_position
        painter.drawRect(int(col * SQUARE_SIZE), int(row * SQUARE_SIZE), SQUARE_SIZE, SQUARE_SIZE)




    # -------- Help methods --------

    def switch_turn(self):
        self.current_turn = "black" if self.current_turn == "white" else "white"

    def refresh(self):
        QTimer.singleShot(100, lambda: self.update())

    def start_game(self):
        if self.bot_color == "white" and self.isBot:
            QTimer.singleShot(100, lambda: self.play_bot(self.bot))



    # -------- Mouse event methods --------

    def mousePressEvent(self, event):
        click_position = event.pos()
        square_pos = self.which_square(click_position)
        row, col = square_pos

        front_piece = self.front_board[row][col]

        # Check if it's two player playing or if there's a bot too
        if self.is_player and (self.player_color == self.current_turn or not self.isBot):    # if there is no Bot, two players game

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

                        
                        self.switch_turn()    # Change player's turn

                        if self.isBot and self.current_turn == self.bot_color:
                            QTimer.singleShot(500, lambda: self.play_bot(self.bot))

                        # Deselect everything after capturing
                        self.selected_squares = []
                        self.highlighted_square = []
                        self.moves = []

                        self.refresh()

                        # Check if the game is over
                        self.is_game_over()


                        return

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

                        
                        self.switch_turn()    # Change player's turn

                        if self.isBot and self.current_turn == self.bot_color:
                            QTimer.singleShot(500, lambda: self.play_bot(self.bot))
                        
                        # Deselect everything after capturing
                        self.selected_squares = []
                        self.highlighted_square = []
                        self.moves = []
                        
                        self.refresh()

                        # Check if the game is over
                        self.is_game_over()

                        return


            # Square processing
            if front_piece != 0:
                self.highlighted_square = [square_pos]
                self.selected_squares = [square_pos]

            self.refresh()   # call the paintEvent method to redraw the board

            

        else:
            pass
            # if the bot plays white, need to configure that further

        
        

        # Check if the game is over
        self.is_game_over()
        


    # -------- Bot methods --------
    def play_bot(self, bot):
        """
        Make the bot move.
        """
        chess_move = bot.predict() # return the move to do using the python-chess format
        if chess_move:
            # print("there's a move")
            move_uci = chess_move.uci() # string format like "e2e4" or "e7e8q"

            # Transform the move format for the gui
            prev_pos = self.back_front.cases[move_uci[:2]]
            new_pos = self.back_front.cases[move_uci[2:4]]
            piece = self.front_board[prev_pos[0]][prev_pos[1]]
            self.front_board[prev_pos[0]][prev_pos[1]] = 0
            self.refresh()

            if len(move_uci) < 5:   # if not a pawn promotion
                self.move_piece(piece, prev_pos, new_pos)
            else:
                self.engine.move_piece(move_uci)
                self.read_board()

            self.switch_turn()    # Change player's turn

            # Append the evaluation of the board to self.evals
            self.evals.append(self.evaluate())

        else:
            pass


    def bots_game(self):
        """
        Handle a full game with two bots playing, alternating between them with a delay.
        """
        # We want to control when to call play_bot using a QTimer
        def play_next_turn():
            # print("next turn")
            if self.current_turn == "white":
                # print(f"White's turn: {self.current_turn}")
                self.play_bot(self.white_player)  # Make White's move
                self.refresh()
                # print(f"Turn after White: {self.current_turn}")
            
            elif self.current_turn == "black":
                # print(f"Black's turn: {self.current_turn}")
                self.play_bot(self.black_player)  # Make Black's move
                self.refresh()
                # print(f"Turn after Black: {self.current_turn}")
            
            # Set up the next turn after a delay (500ms) 
            if not self.engine.is_game_over():  # Check if the game is over
                QTimer.singleShot(500, play_next_turn)  # Delay before the next move
            else:
                self.is_game_over()

        # Start the first move with a delay
        QTimer.singleShot(500, play_next_turn)


    def start_training(self, White, Black):
        """ Method to start the training phase """
        def on_training_complete():
            """ Callback method when training is complete """
            
            # Hide the training widget once done
            self.training_widget.hide()

            # Any other logic to handle after training completion
            print("Training completed!")

        # Show the training widget
        self.training_widget.show()

        # Initialize and start training
        self.training = Training(White, Black, on_training_complete)
        self.training.train()



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
            self.promotion_pending = True
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
        duration = int(distance * 0.6)  # 0.6 is the sweet spot

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
        self.refresh()


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
        self.refresh()

        if self.isBot:
            QTimer.singleShot(500, lambda: self.play_bot(self.bot))
            # self.play_bot()
        


    # -------- Action methods --------
    def reset_game(self):
        """
        Reset the game.
        """
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.engine.set_fen(fen)
        self.read_board()
        self.refresh()

        self.selected_squares = []
        self.highlighted_square = []
        self.legal_moves = []

        self.current_turn = "white"

        self.engine.checkmate = False
        self.engine.stalemate = False
        self.engine.insufficient_material = False
        self.engine.game_over = False
        
        self.start_game()

    
    def set_game(self):
        """
        Set the board to a specific position for debbuging.
        """
        # custom_fen = "8/1P6/8/8/8/8/8/8 w - - 0 1"                                # pawn promotion
        # custom_fen = "1r3Q1r/p3p3/k3p3/2Q1p3/8/2N5/PPPP2P1/R1B2K2 b - - 0 23"
        # custom_fen = "8/6K1/Q7/8/8/8/2p2k2/8"
        custom_fen = "1nbb2n1/2pk1p2/8/pp6/P6r/1PP4R/4P1K1/RN4N1 w - - 1 26"
        self.engine.set_fen(custom_fen)
        self.read_board()
        self.refresh()
        self.selected_squares = []
        self.highlighted_square = []
        self.legal_moves = []
        self.current_turn = "white"


    def config_game(self, white_player, black_player):
        """
        Configure the game such as:
            - choose is there is a bot or no
            - choose the player's color
        """
        # print(f"White's player: {white_player}")
        # print(f"Black's player: {black_player}")

        # Check if there's two humans, two bots or a human a a bot

        if white_player == "Human" or black_player == "Human":
            self.is_player = True

            if white_player != "Human" or black_player != "Human":
                self.isBot = True
            else:
                self.isBot = False

        else:
            self.is_player = False
            self.isBot = True

        


        # Manage if this is two bot playing one against the other
        if not self.is_player:

            if white_player == "Low elo bot":
                self.white_player = LowEloBot(self.engine)
            elif white_player == "Base bot":
                self.white_player = BaseBot(self.engine)
            elif white_player == "Minimax":
                self.white_player = BaseBot2(self.engine)
            elif white_player == "Random forest":
                self.white_player = BaseBot3(self.engine)
            
            elif white_player == "Stockfish":
                self.white_player = Stockfish(self.engine, elo=200)
                self.is_stockfish = self.white_player
            else:
                self.white_player = None


            if black_player == "Low elo bot":
                self.black_player = LowEloBot(self.engine)
            elif black_player == "Base bot":
                self.black_player = BaseBot(self.engine)
            elif black_player == "Minimax":
                self.black_player = BaseBot2(self.engine)
            elif black_player == "Random forest":
                self.black_player = BaseBot3(self.engine)
            
            elif black_player == "Stockfish":
                self.black_player = Stockfish(self.engine, elo=200)
                self.is_stockfish = self.black_player
            else:
                self.black_player = None

            # Start the training phase
            if white_player == "Base bot" or black_player != "Base bot" or white_player == "Minimax" or black_player != "Minimax":
                if white_player == "Low elo bot":
                    self.start_training(None, self.black_player)
                elif black_player == "Low elo bot":
                    self.start_training(self.white_player, None)
                else:
                    self.start_training(self.white_player, self.black_player)
            else:
                self.bots_game()
            
            

        elif self.isBot:
            bot_color = "white" if white_player != "Human" else "black"
            self.bot_color = bot_color

            if white_player == "Low elo bot" or black_player == "Low elo bot":
                self.bot = LowEloBot(self.engine)

            elif white_player == "Base bot" or black_player == "Base bot":
                self.bot = BaseBot(self.engine)
                # self.bot.fit(PGN_PATH)
                self.start_training(self.bot, None)

            elif white_player == "Random forest" or black_player == "Random forest":
                self.bot = BaseBot3(self.engine)
                # self.bot.fit(PGN_PATH)
                self.start_training(self.bot, None)

            elif white_player == "Minimax" or black_player == "Minimax":
                self.bot = BaseBot2(self.engine)
                # self.bot.fit(PGN_PATH)
                self.start_training(self.bot, None)

            elif white_player == "Stockfish" or black_player == "Stockfish":
                self.bot = Stockfish(self.engine, elo=200)
                self.is_stockfish = self.bot

            self.player_color = "white" if white_player == "Human" else "black"

            if bot_color == "white":
                self.start_game()





    def get_fen(self):
        """
        Get the fen representation of the board.
        """
        fen = self.engine.get_fen()
        print(fen)


    def launch_game(self):
        """
        Launch the game if this is two bots playing against each other.
        """
        if not self.is_player:
            self.bots_game()
        else:
            QTimer.singleShot(500, lambda: self.start_game())

    def evaluate(self):
        """
        Evaluate the chessboard using the StockFish method
        """
        with Stockfish(self.engine, elo=200) as stockfish:
            score = stockfish.evaluate(self.engine.board)
            # print(score)
            return score


    # -------- Game state methods --------

    def is_check(self):
        """
        Check if the board is in check state.
        """
        look_king = "k" if self.current_turn == "black" else "K"

        for i in range(8):
            for j in range(8):
                if self.front_board[i][j] == look_king:
                    self.king_position = (i, j)

        return self.engine.is_check()

    def is_game_over(self):
        """
        Check if the game is over.
        Pops a QMessage Box to indicate what win and who win.
        """
        if self.engine.game_over:
            if self.engine.checkmate:
                status = "checkmate"
            elif self.engine.stalemate:
                status = "stalemate"
            elif self.engine.insufficient_material:
                status = "insufficient material"
            else:
                status = None

            winner = "White" if self.current_turn == "black" else "Black"
            
            self.show_game_over_message(status, winner, self)


    def show_game_over_message(self, status, winner=None, parent=None):
        if status == "checkmate":
            message = f"Checkmate! {winner} wins."
        elif status == "stalemate":
            message = "Stalemate. It's a draw."
        elif status == "insufficient_material":
            message = "Draw due to insufficient material."
        else:
            message = "Game over."

        popup = GameOverPopup(message, parent)

        popup.show()