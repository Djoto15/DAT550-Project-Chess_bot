from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt

class GameOverPopup(QWidget):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.ApplicationModal)

        # Set gray background with rounded corners and blue button styling
        self.setStyleSheet("""
            QWidget#popup {
                background-color: #54575c;
                border-radius: 12px;
            }
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 18px;
                padding: 8px 16px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        self.setObjectName("popup")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)

        button = QPushButton("OK")
        button.clicked.connect(self.close)

        layout.addWidget(label)

        layout.addSpacing(20)
        layout.addWidget(button)

        self.resize(400, 200)
