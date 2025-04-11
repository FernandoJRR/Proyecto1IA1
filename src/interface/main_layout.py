from PyQt5.QtWidgets import (
    QLayout, QMainWindow, QScrollArea, QWidget, QTabWidget, QLabel, QLineEdit, QPushButton,
    QTextEdit, QVBoxLayout, QGridLayout, QMessageBox, QGroupBox,
    QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import QThread, pyqtSignal
from interface.relacion_layout import RelacionesTab
from utils.genetic_algorithm import *
from interface.genetic_algorithm_layout import GALayout
from interface.cursos_layout import CursosTab
from interface.docentes_layout import DocentesTab
from interface.salones_layout import SalonesTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generador de Horarios - Algoritmo Genético")
        self.setGeometry(100, 100, 800, 600)
        self.initUI()

    def initUI(self):
        self.tabs = QTabWidget()

        # Crear las pestañas
        self.tab_ga = GALayout()
        self.tab_cursos = CursosTab()
        self.tab_docentes = DocentesTab()
        self.tab_salones = SalonesTab()
        self.tab_relaciones = RelacionesTab()

        self.tabs.addTab(self.tab_ga, "Generar Horario")
        self.tabs.addTab(self.tab_cursos, "Cursos")
        self.tabs.addTab(self.tab_docentes, "Docentes")
        self.tabs.addTab(self.tab_salones, "Salones")
        self.tabs.addTab(self.tab_relaciones, "Relaciones")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(self.tabs)
        
        container = QWidget()
        container.setLayout(main_layout)
        #self.setCentralWidget(container)

        # Aquí se envuelve el widget contenedor en un QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidget(container)
        scroll_area.setWidgetResizable(True)

        self.setCentralWidget(scroll_area)
