from PyQt5.QtWidgets import QPlainTextEdit

class Logger(QPlainTextEdit):
    _instance = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
    
    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = Logger()
        return cls._instance
    
    def log(self, message: str):
        self.appendPlainText(message)
