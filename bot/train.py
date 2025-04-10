# A file to define a training class for the bots

from PyQt5.QtCore import QObject, QThread, pyqtSignal

class BotTrainer(QObject):
    finished = pyqtSignal()

    def __init__(self, bot, pgn_path):
        super().__init__()
        self.bot = bot
        self.pgn_path = pgn_path

    def run(self):
        self.bot.fit(self.pgn_path)
        self.finished.emit()



class Training:
    def __init__(self, white_player, black_player, pgn_path, gui, on_complete):
        self.white_player = white_player
        self.black_player = black_player
        self.pgn_path = pgn_path
        self.gui = gui  # reference to the main GUI
        self.on_complete = on_complete  # function to call when training is done

        self.training_done = 0



    def train(self):

        # --- White trainer ---
        self.white_thread = QThread()
        self.white_trainer = BotTrainer(self.white_player, self.pgn_path)
        self.white_trainer.moveToThread(self.white_thread)
        self.white_thread.started.connect(self.white_trainer.run)
        self.white_trainer.finished.connect(self.white_thread.quit)
        self.white_trainer.finished.connect(self.white_trainer.deleteLater)
        self.white_thread.finished.connect(self.white_thread.deleteLater)
        self.white_thread.finished.connect(self.check_training_done)

        # --- Black trainer ---
        self.black_thread = QThread()
        self.black_trainer = BotTrainer(self.black_player, self.pgn_path)
        self.black_trainer.moveToThread(self.black_thread)
        self.black_thread.started.connect(self.black_trainer.run)
        self.black_trainer.finished.connect(self.black_thread.quit)
        self.black_trainer.finished.connect(self.black_trainer.deleteLater)
        self.black_thread.finished.connect(self.black_thread.deleteLater)
        self.black_thread.finished.connect(self.check_training_done)

        self.white_thread.start()
        self.black_thread.start()

    def check_training_done(self):
        self.training_done += 1
        if self.training_done == 2:
            self.on_complete()
