from PyQt5.QtWidgets import QFileDialog, QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget
import fitz
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt5.QtGui import QPixmap, QImage

class PDFViewer(QWidget):
    def __init__(self, pdf_path, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        
        container = QWidget()
        container_layout = QVBoxLayout(container)

        self.download_button = QPushButton("Descargar horarios")
        self.download_button.clicked.connect(self.descargar_horarios)
        container_layout.addWidget(self.download_button)
        
        try:
            doc = fitz.open(self.pdf_path)
        except Exception as e:
            label_error = QLabel(f"Error al abrir el PDF: {e}", self)
            container_layout.addWidget(label_error)
            self.setLayout(layout)
            return

        for page_number in range(len(doc)):
            page = doc.load_page(page_number)
            pix = page.get_pixmap(dpi=100) #type: ignore
            image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            label = QLabel(self)
            label.setPixmap(pixmap)
            container_layout.addWidget(label)
        
        container.setLayout(container_layout)
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)
        self.setLayout(layout)

    def descargar_horarios(self):
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar PDF",
            "",
            "PDF Files (*.pdf)"
        )
        if save_path:
            try:
                with open(self.pdf_path, "rb") as file_in:
                    data = file_in.read()

                with open(save_path, "wb") as file_out:
                    file_out.write(data)
                QMessageBox.information(self, "Éxito", "El PDF se ha guardado exitosamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar el PDF: {e}")
