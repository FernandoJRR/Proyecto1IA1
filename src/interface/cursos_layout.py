from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QFileDialog
from utils.data_handler import cargar_cursos, guardar_cursos

class CursosTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.save_button = QPushButton("Actualizar cursos")
        self.save_button.clicked.connect(self.actualizar_cursos)
        layout.addWidget(self.save_button)

        self.table_cursos = QTableWidget()
        cursos = cargar_cursos("data/cursos.csv")
        self.configurar_tabla(cursos)
        layout.addWidget(self.table_cursos)


    def configurar_tabla(self, cursos):
        self.table_cursos.clear()
        self.table_cursos.setRowCount(len(cursos))
        self.table_cursos.setColumnCount(6)
        self.table_cursos.setHorizontalHeaderLabels(["Nombre", "Código", "Carrera", "Semestre", "Sección", "Tipo"])
        for row, curso in enumerate(cursos):
            self.table_cursos.setItem(row, 0, QTableWidgetItem(curso.nombre))
            self.table_cursos.setItem(row, 1, QTableWidgetItem(curso.codigo))
            self.table_cursos.setItem(row, 2, QTableWidgetItem(curso.carrera))
            self.table_cursos.setItem(row, 3, QTableWidgetItem(str(curso.semestre)))
            self.table_cursos.setItem(row, 4, QTableWidgetItem(curso.seccion))
            self.table_cursos.setItem(row, 5, QTableWidgetItem(curso.tipo))


    def actualizar_cursos(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar CSV de Cursos", "", "CSV Files (*.csv);;All Files (*)")
        if file_path:
            try:
                nuevos_cursos = cargar_cursos(file_path)
                guardar_cursos(nuevos_cursos, "data/cursos.csv")
                self.configurar_tabla(nuevos_cursos)
                QMessageBox.information(self, "Actualizado", "Los cursos se han actualizado exitosamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al cargar los cursos: {e}")
