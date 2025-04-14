# docentes_tab.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QFileDialog, QMessageBox
from utils.data_handler import cargar_docentes, guardar_docentes

class DocentesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.table_docentes = QTableWidget()
        docentes = cargar_docentes("data/docentes.csv")
        self.configurar_tabla(docentes)
        layout.addWidget(self.table_docentes)

        self.save_button = QPushButton("Actualizar docentes")
        self.save_button.clicked.connect(self.actualizar_docentes)
        layout.addWidget(self.save_button)

    def configurar_tabla(self, docentes):
        self.table_docentes.clear()
        self.table_docentes.setRowCount(len(docentes))
        self.table_docentes.setColumnCount(6)
        self.table_docentes.setHorizontalHeaderLabels(["Nombre", "Registro", "Hora Entrada", "Hora Salida"])
        for row, docente in enumerate(docentes):
            self.table_docentes.setItem(row, 0, QTableWidgetItem(docente.nombre))
            self.table_docentes.setItem(row, 1, QTableWidgetItem(docente.registro))
            self.table_docentes.setItem(row, 2, QTableWidgetItem(docente.hora_entrada))
            self.table_docentes.setItem(row, 3, QTableWidgetItem(docente.hora_salida))

    def actualizar_docentes(self):
        # Abrir diálogo para seleccionar el archivo CSV con los nuevos cursos
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar CSV de Docentes", "", "CSV Files (*.csv);;All Files (*)")
        if file_path:
            try:
                nuevos_docentes = cargar_docentes(file_path)
                # Actualiza la tabla con los nuevos cursos, sobrescribiendo los actuales
                guardar_docentes(nuevos_docentes, "data/docentes.csv")
                self.configurar_tabla(nuevos_docentes)
                QMessageBox.information(self, "Actualizado", "Los docentes se han actualizado exitosamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al cargar los docentes: {e}")
