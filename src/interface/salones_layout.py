# salones_tab.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QFileDialog, QMessageBox
from utils.data_handler import cargar_salones, guardar_salones

class SalonesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.save_button = QPushButton("Actualizar salones")
        self.save_button.clicked.connect(self.actualizar_docentes)
        layout.addWidget(self.save_button)

        self.table_salones = QTableWidget()
        salones = cargar_salones("data/salones.csv")
        self.configurar_tabla(salones)
        layout.addWidget(self.table_salones)

    def configurar_tabla(self, salones):
        self.table_salones.clear()
        self.table_salones.setRowCount(len(salones))
        self.table_salones.setColumnCount(6)
        self.table_salones.setHorizontalHeaderLabels(["ID", "Nombre"])
        for row, salon in enumerate(salones):
            self.table_salones.setItem(row, 0, QTableWidgetItem(salon.id))
            self.table_salones.setItem(row, 1, QTableWidgetItem(salon.nombre))

    def actualizar_docentes(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar CSV de Salones", "", "CSV Files (*.csv);;All Files (*)")
        if file_path:
            try:
                nuevos_salones = cargar_salones(file_path)
                guardar_salones(nuevos_salones, "data/salones.csv")
                self.configurar_tabla(nuevos_salones)
                QMessageBox.information(self, "Actualizado", "Los salones se han actualizado exitosamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al salones los docentes: {e}")
