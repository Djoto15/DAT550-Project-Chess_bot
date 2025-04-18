from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox, QHBoxLayout, QWidget
)
from PyQt5.QtCore import Qt


class ConfigGameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Game")
        self.setFixedSize(350, 150)

        main_layout = QVBoxLayout(self)

        # Horizontal layout for White and Black selectors
        player_layout = QHBoxLayout()

        # White side group
        white_widget = QWidget()
        white_layout = QVBoxLayout(white_widget)
        white_label = QLabel("White:")
        white_label.setAlignment(Qt.AlignCenter)
        self.white_player_combo = QComboBox()
        self.white_player_combo.addItems(["Human", "Random bot", "Base bot", "Stockfish"])
        white_layout.addWidget(white_label)
        white_layout.addWidget(self.white_player_combo)

        # Black side group
        black_widget = QWidget()
        black_layout = QVBoxLayout(black_widget)
        black_label = QLabel("Black:")
        black_label.setAlignment(Qt.AlignCenter)
        self.black_player_combo = QComboBox()
        self.black_player_combo.addItems(["Human", "Random bot", "Base bot", "Stockfish"])
        black_layout.addWidget(black_label)
        black_layout.addWidget(self.black_player_combo)

        # Add both widgets side by side
        player_layout.addWidget(white_widget)
        player_layout.addWidget(black_widget)

        # Add to main layout
        main_layout.addLayout(player_layout)

        # OK / Cancel buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        main_layout.addWidget(self.buttons)

    def get_settings(self):
        white_player = self.white_player_combo.currentText()
        black_player = self.black_player_combo.currentText()
        return white_player, black_player
