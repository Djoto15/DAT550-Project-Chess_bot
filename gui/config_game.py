from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QRadioButton,
    QPushButton, QButtonGroup, QDialogButtonBox
)
from PyQt5.QtCore import Qt


class ConfigGameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Game")
        self.setFixedSize(300, 200)

        layout = QVBoxLayout(self)

        # Bot choice
        layout.addWidget(QLabel("Play against bot?"))
        self.bot_group = QButtonGroup(self)
        bot_yes = QRadioButton("Yes")
        bot_no = QRadioButton("No")
        bot_yes.setChecked(True)

        self.bot_group.addButton(bot_yes, id=1)
        self.bot_group.addButton(bot_no, id=0)

        layout.addWidget(bot_yes)
        layout.addWidget(bot_no)

        # Color choice
        layout.addWidget(QLabel("Choose your color:"))
        self.color_group = QButtonGroup(self)
        white = QRadioButton("White")
        black = QRadioButton("Black")
        white.setChecked(True)

        self.color_group.addButton(white, id=1)
        self.color_group.addButton(black, id=0)

        layout.addWidget(white)
        layout.addWidget(black)

        # Dialog buttons (OK / Cancel)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_settings(self):
        is_bot = self.bot_group.checkedId() == 1
        player_color = "white" if self.color_group.checkedId() == 1 else "black"
        return is_bot, player_color
