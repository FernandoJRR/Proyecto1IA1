from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QGridLayout, QGroupBox, QLabel, QLineEdit, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget

from interface.pdf_viewer import PDFViewer
from utils.genetic_algorithm import AmbienteAlgoritmo

class GALayout(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        # Layout principal de la pestaña "Generar Horario"
        layout = QVBoxLayout()

        # Grupo de parámetros
        param_group = QGroupBox("Parámetros del Algoritmo")
        param_layout = QGridLayout()

        param_layout.addWidget(QLabel("Tamaño de Población:"), 0, 0)
        self.population_edit = QLineEdit("10")
        param_layout.addWidget(self.population_edit, 0, 1)

        param_layout.addWidget(QLabel("Número de Generaciones:"), 1, 0)
        self.generations_edit = QLineEdit("100")
        param_layout.addWidget(self.generations_edit, 1, 1)

        param_layout.addWidget(QLabel("Tasa de Mutacion"), 2, 0)
        self.tasa_mutacion_edit = QLineEdit("0.1")
        param_layout.addWidget(self.tasa_mutacion_edit, 2, 1)

        self.run_button = QPushButton("Generar Horario")
        self.run_button.clicked.connect(self.start_ga)
        param_layout.addWidget(self.run_button, 3, 0, 1, 2)
        param_group.setLayout(param_layout)
        layout.addWidget(param_group)

        # Grupo para mostrar el PDF del reporte (vacío al inicio)
        self.pdf_group = QGroupBox("Horario Generado")
        self.pdf_layout = QVBoxLayout()
        self.pdf_group.setLayout(self.pdf_layout)
        self.pdf_viewer = None
        layout.addWidget(self.pdf_group)

        # Grupo para mostrar los reportes del algoritmo
        report_group = QGroupBox("Reportes del Algoritmo")
        report_layout = QVBoxLayout()
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        report_layout.addWidget(self.report_text)
        report_group.setLayout(report_layout)
        layout.addWidget(report_group)


        # Asignar el layout al widget
        self.setLayout(layout)

    def start_ga(self):
        try:
            poblacion_inicial = int(self.population_edit.text())
            generaciones = int(self.generations_edit.text())
            tasa_mutacion = float(self.tasa_mutacion_edit.text())
        except ValueError:
            QMessageBox.critical(self, "Error", "Ingrese valores numéricos válidos.")
            return

        self.run_button.setEnabled(False)
        self.worker = GAWorker(poblacion_inicial, generaciones, tasa_mutacion)
        self.worker.result_signal.connect(self.display_result)
        self.worker.start()

    def display_result(self, result_data: dict):
        # Preparar y mostrar los reportes
        tiempo = result_data.get("tiempo", "N/A")
        iteraciones = result_data.get("iteraciones", "N/A")
        conflictos = result_data.get("conflictos", [])
        final_conflicto = conflictos[-1] if conflictos else "N/A"
        continuidad = result_data.get("continuidad", "N/A")
        memoria = result_data.get("memoria", "N/A")
        report_output = (
            f"Tiempo de Ejecución: {tiempo} s\n"
            f"Iteraciones Necesarias: {iteraciones}\n"
            f"Número de Conflictos: {final_conflicto}\n"
            f"Porcentaje de Continuidad: {continuidad}%\n"
            f"Espacio en Memoria Consumido: {memoria} MB\n"
        )
        self.report_text.setPlainText(report_output)

        # Verificar si se generó el reporte PDF (se asume que ambiente.pdf_report fue asignado)
        pdf_path = result_data.get("reporte_horarios_pdf", None)
        if pdf_path:
            # Si ya existe un visor anterior, eliminarlo
            if self.pdf_viewer is not None:
                self.pdf_layout.removeWidget(self.pdf_viewer)
                self.pdf_viewer.deleteLater()
            # Instanciar PDFViewerWidget
            self.pdf_viewer = PDFViewer(pdf_path)
            self.pdf_layout.addWidget(self.pdf_viewer)

        self.run_button.setEnabled(True)

# Definición del QThread para ejecutar el algoritmo genético en segundo plano
class GAWorker(QThread):
    # Señal que envía todos los datos del algoritmo (horario y reportes)
    result_signal = pyqtSignal(dict)

    def __init__(self, poblacion_inicial: int, generaciones: int, tasa_mutacion: float, parent=None):
        super().__init__(parent)
        self.population = poblacion_inicial
        self.generations = generaciones
        self.tasa_mutacion = tasa_mutacion

    def run(self):
        ambiente = AmbienteAlgoritmo()
        ambiente.preparar_data()
        ambiente.ejecutar(self.population, self.generations, self.tasa_mutacion)

        # Se asume que AmbienteAlgoritmo ha calculado los siguientes atributos:
        # - ambiente.resultado: el horario generado (dict)
        # - ambiente.conflictos_por_generacion: lista de conflictos a lo largo de las generaciones
        # - ambiente.iteraciones_optimas: cantidad de iteraciones hasta alcanzar el óptimo
        # - ambiente.tiempo_ejecucion: tiempo total de ejecución (en segundos)
        # - ambiente.porcentaje_continuidad: porcentaje de cursos consecutivos por semestre
        # - ambiente.memoria_consumida: espacio en memoria usado por el algoritmo (en MB)
        result_data = {
            "horario": ambiente.resultado,
            "conflictos": ambiente.conflictos_por_generacion,
            "iteraciones": ambiente.iteraciones_optimas,
            "tiempo": ambiente.tiempo_ejecucion,
            "continuidad": ambiente.porcentaje_continuidad,
            "memoria": ambiente.memoria_consumida,
            "reporte_horarios_pdf": ambiente.reporte_horarios_pdf
        }
        self.result_signal.emit(result_data)
