import matplotlib
matplotlib.use("Qt5Agg")  # Asegura el uso del backend Qt5
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QVBoxLayout, QWidget

class ConflictPlot(QWidget):
    def __init__(self, conflicts, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.plot_conflicts(conflicts)

    def plot_conflicts(self, conflicts):
        ax = self.figure.add_subplot(111)
        ax.clear()
        generaciones = list(range(1, len(conflicts) + 1))
        ax.plot(generaciones, conflicts, marker='o', linestyle='-', color='blue')
        ax.set_xlabel("Generaciones")
        ax.set_ylabel("Conflictos")
        ax.set_title("Conflictos por Generacion")
        ax.grid(True)
        self.canvas.draw()

class ContinuidadPlot(QWidget):
    def __init__(self, continuidades, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.plot_continuidades(continuidades)

    def plot_continuidades(self, continuidades):
        ax = self.figure.add_subplot(111)
        ax.clear()
        generaciones = list(range(1, len(continuidades) + 1))
        ax.plot(generaciones, continuidades, marker='o', linestyle='-', color='blue')
        ax.set_xlabel("Generaciones")
        ax.set_ylabel("Conflictos")
        ax.set_title("Continuidad por Generacion")
        ax.grid(True)
        self.canvas.draw()
