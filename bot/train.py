from PyQt5.QtCore import QObject, QThread, pyqtSignal

class BotTrainer(QObject):
    finished = pyqtSignal()

    def __init__(self, white_bot, black_bot):
        super().__init__()
        self.white_bot = white_bot
        self.black_bot = black_bot

    def run(self):
        """Train white then black (if they exist), sequentially."""
        training_done = 0

        if self.white_bot:
            print(f"Training started for WHITE bot: {self.white_bot}")
            self.white_bot.fit()
            print("Training finished for WHITE bot")
            training_done += 1

        if self.black_bot:
            print(f"Training started for BLACK bot: {self.black_bot}")
            self.black_bot.fit()
            print("Training finished for BLACK bot")
            training_done += 1

        print(f"Training done for {training_done} bot(s)")
        self.finished.emit()  # Tell GUI we're done



class Training:
    def __init__(self, white_player, black_player, on_complete):
        self.thread = QThread()
        self.trainer = BotTrainer(white_player, black_player)
        self.trainer.moveToThread(self.thread)

        self.trainer.finished.connect(on_complete)
        self.thread.started.connect(self.trainer.run)
        self.trainer.finished.connect(self.thread.quit)
        self.trainer.finished.connect(self.trainer.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

    def train(self):
        self.thread.start()
