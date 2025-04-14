# docentes_tab.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QFileDialog, QMessageBox
from utils.data_handler import cargar_relaciones, guardar_relaciones

class RelacionesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.save_button = QPushButton("Actualizar relaciones")
        self.save_button.clicked.connect(self.actualizar_relaciones)
        layout.addWidget(self.save_button)

        self.table_relaciones = QTableWidget()
        relaciones = cargar_relaciones("data/relaciones_docente_curso.csv")
        self.configurar_tabla(relaciones)
        layout.addWidget(self.table_relaciones)

    def configurar_tabla(self, relaciones):
        self.table_relaciones.clear()
        self.table_relaciones.setRowCount(len(relaciones))
        self.table_relaciones.setColumnCount(6)
        self.table_relaciones.setHorizontalHeaderLabels(["Registro Docente", "Codigo Curso"])
        for row, salon in enumerate(relaciones):
            self.table_relaciones.setItem(row, 0, QTableWidgetItem(salon.registro_docente))
            self.table_relaciones.setItem(row, 1, QTableWidgetItem(salon.codigo_curso))

    def actualizar_relaciones(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar CSV de Relaciones Docente-Curso", "", "CSV Files (*.csv);;All Files (*)")
        if file_path:
            try:
                nuevas_relaciones = cargar_relaciones(file_path)
                guardar_relaciones(nuevas_relaciones, "data/relaciones_docente_curso.csv")
                self.configurar_tabla(nuevas_relaciones)
                QMessageBox.information(self, "Actualizado", "Las relaciones se han actualizado exitosamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al cargar los relaciones: {e}")
