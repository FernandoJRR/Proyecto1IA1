from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QCheckBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget

from interface.logger import Logger
from interface.pdf_viewer import PDFViewer
from interface.plot_viewer import ConflictPlot, ContinuidadPlot
from utils.genetic_algorithm import AmbienteAlgoritmo

class GALayout(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        # Layout principal de la pestaña "Generar Horario"
        layout = QVBoxLayout()

        header_hlayout = QHBoxLayout()
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
        self.tasa_mutacion_edit = QLineEdit("0.3")
        param_layout.addWidget(self.tasa_mutacion_edit, 2, 1)

        param_layout.addWidget(QLabel("Penalizacion por Continuidad"), 3, 0)
        self.penalizacion_continuidad_edit = QLineEdit("10")
        param_layout.addWidget(self.penalizacion_continuidad_edit, 3, 1)

        param_layout.addWidget(QLabel("Generaciones por Reinsercion"),4, 0)
        self.generaciones_reinsercion_edit = QLineEdit("5")
        param_layout.addWidget(self.generaciones_reinsercion_edit, 4, 1)

        param_layout.addWidget(QLabel("Porcentaje de Reinsercion"), 5, 0)
        self.porcentaje_reinsercion_edit = QLineEdit("0.3")
        param_layout.addWidget(self.porcentaje_reinsercion_edit, 5, 1)

        self.run_button = QPushButton("Generar Horario")
        self.run_button.clicked.connect(self.start_ga)
        param_layout.addWidget(self.run_button, 6, 0, 1, 2)
        param_group.setLayout(param_layout)
        header_hlayout.addWidget(param_group)

        # Creamos una pestaña o un grupo adicional para la consola
        console_group = QGroupBox("Consola")
        console_layout = QVBoxLayout()
        # Obtenemos la instancia del Logger
        self.console = Logger.instance()
        # Opcionalmente, se pueden ajustar propiedades adicionales:
        self.console.setSizePolicy(self.console.sizePolicy().Expanding, 
                                   self.console.sizePolicy().Expanding)
        self.console.textChanged.connect(
            lambda: self.console.verticalScrollBar().setValue(self.console.verticalScrollBar().maximum()) #type: ignore
        )
        self.console.moveCursor(QTextCursor.End)
        console_layout.addWidget(self.console)
        console_group.setLayout(console_layout)
        header_hlayout.addWidget(console_group)

        layout.addLayout(header_hlayout)


        # Grupo para parametros de evaluacion
        eval_group = QGroupBox("Parámetros de Evaluacion")
        eval_layout = QGridLayout()

        self.evaluar_penalizacion_check = QCheckBox("Evaluar Penalizacion")
        self.evaluar_penalizacion_check.setChecked(True)
        eval_layout.addWidget(self.evaluar_penalizacion_check, 2, 0)
        eval_layout.addWidget(QLabel("Penalización Esperada:"), 2, 1)
        self.penalizacion_esperada_edit = QLineEdit("0")
        eval_layout.addWidget(self.penalizacion_esperada_edit, 2, 2)

        self.evaluar_conflictos_check = QCheckBox("Evaluar Conflictos")
        eval_layout.addWidget(self.evaluar_conflictos_check, 0, 0)
        eval_layout.addWidget(QLabel("Conflictos Esperados:"), 0, 1)
        self.conflictos_esperados_edit = QLineEdit("0")
        eval_layout.addWidget(self.conflictos_esperados_edit, 0, 2)

        self.evaluar_continuidad_check = QCheckBox("Evaluar Continuidad")
        eval_layout.addWidget(self.evaluar_continuidad_check, 1, 0)
        eval_layout.addWidget(QLabel("Continuidad Esperada:"), 1, 1)
        self.continuidad_esperada_edit = QLineEdit("0")
        eval_layout.addWidget(self.continuidad_esperada_edit, 1, 2)

        eval_group.setLayout(eval_layout)
        layout.addWidget(eval_group)

        # Grupo para mostrar el PDF del reporte (vacío al inicio)
        self.pdf_group = QGroupBox("Horario Generado")
        self.pdf_group.setMinimumHeight(400)
        self.pdf_layout = QVBoxLayout()
        self.pdf_group.setLayout(self.pdf_layout)
        self.pdf_viewer = None
        layout.addWidget(self.pdf_group)

        reports_hlayout = QHBoxLayout()

        report_group = QGroupBox("Individuo Seleccionado")
        report_layout = QVBoxLayout()
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        report_layout.addWidget(self.report_text)
        report_group.setLayout(report_layout)
        reports_hlayout.addWidget(report_group)

        # Grupo para mostrar los reportes del algoritmo
        history_group = QGroupBox("Reportes del Algoritmo")
        history_layout = QVBoxLayout()
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        history_layout.addWidget(self.history_text)
        history_group.setLayout(history_layout)
        reports_hlayout.addWidget(history_group)

        layout.addLayout(reports_hlayout)

        self.plot_group = QGroupBox("")
        self.plot_group.setMinimumHeight(400)
        self.plot_layout = QVBoxLayout()
        self.plot_group.setLayout(self.plot_layout)
        layout.addWidget(self.plot_group)

        self.plot_continuidad_group = QGroupBox("")
        self.plot_continuidad_group.setMinimumHeight(400)
        self.plot_continuidad_layout = QVBoxLayout()
        self.plot_continuidad_group.setLayout(self.plot_continuidad_layout)
        layout.addWidget(self.plot_continuidad_group)

        # Asignar el layout al widget
        self.setLayout(layout)

    def start_ga(self):
        try:
            Logger.instance().clear()
            poblacion_inicial = int(self.population_edit.text())
            generaciones = int(self.generations_edit.text())
            tasa_mutacion = float(self.tasa_mutacion_edit.text())
            penalizacion_continuidad = float(self.penalizacion_continuidad_edit.text())
            generaciones_reinsercion = int(self.generaciones_reinsercion_edit.text())
            porcentaje_reinsercion = float(self.porcentaje_reinsercion_edit.text())

            evaluar_conflictos = self.evaluar_conflictos_check.isChecked()
            conflictos_esperados = int(self.conflictos_esperados_edit.text())
            
            evaluar_continuidad = self.evaluar_continuidad_check.isChecked()
            continuidad_esperada = int(self.continuidad_esperada_edit.text())
            
            evaluar_penalizacion = self.evaluar_penalizacion_check.isChecked()
            penalizacion_esperada = int(self.penalizacion_esperada_edit.text())
        except ValueError:
            QMessageBox.critical(self, "Error", "Ingrese valores numéricos válidos.")
            return

        self.run_button.setEnabled(False)
        self.worker = GAWorker(poblacion_inicial, generaciones, tasa_mutacion, penalizacion_continuidad, 
                               generaciones_reinsercion, porcentaje_reinsercion, 
                               evaluar_conflictos, conflictos_esperados, 
                               evaluar_continuidad, continuidad_esperada, 
                               evaluar_penalizacion, penalizacion_esperada)
        self.worker.result_signal.connect(self.display_result)
        self.worker.start()

    def display_result(self, result_data: dict):
        # Preparar y mostrar los reportes
        tiempo = result_data.get("tiempo", "N/A")
        iteraciones = result_data.get("iteraciones", "N/A")
        conflictos = result_data.get("conflictos", [])
        continuidades = result_data.get("continuidades", [])
        final_conflicto = (sum(conflictos) / len(conflictos)) if conflictos else "N/A"
        conflictos_mejor_individuo = result_data.get("conflictos_mejor_individuo", "N/A")
        continuidad = result_data.get("continuidad", "N/A")
        memoria = result_data.get("memoria", "N/A")

        report_output = (
            f"Conflictos: {conflictos_mejor_individuo}\n"
            f"Porcentaje de Continuidad: {continuidad}%\n"
        )
        self.report_text.setPlainText(report_output)

        history_output = (
            f"Tiempo de Ejecución: {tiempo} s\n"
            f"Iteraciones Necesarias: {iteraciones}\n"
            f"Conflictos Promedio: {final_conflicto}\n"
            f"Espacio en Memoria Consumido: {memoria} MB\n"
        )
        self.history_text.setPlainText(history_output)

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

        # Mostrar gráfica de conflictos a lo largo de las generaciones.
        if conflictos:
            # Si ya existe una gráfica en el layout se elimina
            if hasattr(self, "conflict_plot"):
                self.plot_layout.removeWidget(self.conflict_plot)
                self.conflict_plot.deleteLater()
            self.conflict_plot = ConflictPlot(conflictos, self)
            # Agregar la grafica al final del layout principal.
            self.plot_layout.addWidget(self.conflict_plot)

        # Mostrar gráfica de conflictos a lo largo de las generaciones.
        if continuidades:
            # Si ya existe una gráfica en el layout se elimina
            if hasattr(self, "continuidad_plot"):
                self.plot_continuidad_layout.removeWidget(self.continuidad_plot)
                self.continuidad_plot.deleteLater()
            self.continuidad_plot = ContinuidadPlot(continuidades, self)
            # Agregar la grafica al final del layout principal.
            self.plot_continuidad_layout.addWidget(self.continuidad_plot)

        self.run_button.setEnabled(True)

# QThread para poder ejecutar el algoritmo dentro de la interfaz
class GAWorker(QThread):
    # Señal que envía todos los datos del algoritmo (horario y reportes)
    result_signal = pyqtSignal(dict)

    def __init__(self, poblacion_inicial: int, generaciones: int, tasa_mutacion: float, penalizacion_continuidad: float, 
                 generaciones_reinsercion, porcentaje_reinsercion,
                 evaluar_conflictos, conflictos_esperados,
                 evaluar_continuidad, continuidad_esperada,
                 evaluar_penalizacion, penalizacion_esperada,
                 parent=None):
        super().__init__(parent)
        self.population = poblacion_inicial
        self.generations = generaciones
        self.tasa_mutacion = tasa_mutacion
        self.penalizacion_continuidad = penalizacion_continuidad
        self.generaciones_reinsercion = generaciones_reinsercion
        self.porcentaje_reinsercion = porcentaje_reinsercion

        self.evaluar_conflictos = evaluar_conflictos
        self.conflictos_esperados = conflictos_esperados

        self.evaluar_continuidad = evaluar_continuidad
        self.continuidad_esperada = continuidad_esperada

        self.evaluar_penalizacion = evaluar_penalizacion
        self.penalizacion_esperada = penalizacion_esperada

    def run(self):
        ambiente = AmbienteAlgoritmo()
        ambiente.preparar_data()
        ambiente.ejecutar(self.population, self.generations, self.tasa_mutacion, 
                          self.penalizacion_continuidad, 
                          self.conflictos_esperados, self.evaluar_conflictos,
                          self.continuidad_esperada, self.evaluar_continuidad,
                          self.penalizacion_esperada, self.evaluar_penalizacion,
                          self.generaciones_reinsercion, self.porcentaje_reinsercion)

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
            "continuidades": ambiente.continuidad_por_generacion,
            "conflictos_mejor_individuo": ambiente.conflictos_mejor_individuo,
            "iteraciones": ambiente.iteraciones_optimas,
            "tiempo": ambiente.tiempo_ejecucion,
            "continuidad": ambiente.porcentaje_continuidad,
            "memoria": ambiente.memoria_consumida,
            "reporte_horarios_pdf": ambiente.reporte_horarios_pdf
        }
        self.result_signal.emit(result_data)
