import sys
from PyQt5.QtWidgets import QApplication
from utils.algoritmo import *
from interface.main_layout import *

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
