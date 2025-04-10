from PyQt5.QtWidgets import QScrollArea, QVBoxLayout, QWidget
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
        
        # Crear un scroll area para poder ver todas las páginas
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        
        # Widget contenedor para las páginas
        container = QWidget()
        container_layout = QVBoxLayout(container)
        
        # Abrir el PDF usando PyMuPDF (fitz)
        try:
            doc = fitz.open(self.pdf_path)
        except Exception as e:
            label_error = QLabel(f"Error al abrir el PDF: {e}", self)
            container_layout.addWidget(label_error)
            self.setLayout(layout)
            return

        # Renderizar cada página y agregarlas como QLabel con QPixmap
        for page_number in range(len(doc)):
            page = doc.load_page(page_number)
            # Ajusta el DPI (p.ej., 100) para un buen balance entre resolución y tamaño
            pix = page.get_pixmap(dpi=100) #type: ignore
            # Crear QImage a partir de los pixeles; fitz por defecto genera RGB
            image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            label = QLabel(self)
            label.setPixmap(pixmap)
            container_layout.addWidget(label)
        
        container.setLayout(container_layout)
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)
        self.setLayout(layout)
