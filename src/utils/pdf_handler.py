from datetime import datetime, timedelta
import os
from reportlab.lib.pagesizes import landscape, legal
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def break_text(text, max_chars=10):
    """
    Inserta saltos de línea (<br/>) en el texto cada vez que se supera max_chars en una línea.
    Se hace de forma sencilla tratando de no cortar palabras.
    """
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return "<br/>".join(lines)

def crear_horarios_pdf(cursos):
    """
    Genera un reporte en PDF del horario, donde las columnas representan los salones
    y las filas representan los horarios. El parámetro 'individuo' es un diccionario:
      dict[Curso, tuple[Salon, str, Docente|None]]
    Retorna el path del archivo PDF generado.
    """
    horarios = ["13:40", "14:30", "15:20", "16:10", "17:00", "17:50", "18:40", "19:30", "20:20"]

    salones_set = set()
    for asignacion in cursos.values():
        salon = asignacion[0]
        salones_set.add(salon)
    salones_list = sorted(list(salones_set), key=lambda x: x.id if hasattr(x, "id") else x.nombre)

    # Estilos para la tabla
    styles = getSampleStyleSheet()
    cell_style = styles['Normal']
    cell_style.fontSize = 6

    data = []
    header = [Paragraph("", cell_style)]
    for salon in salones_list:
        header.append(Paragraph(salon.nombre, cell_style))
    data.append(header)


    for hora in horarios:
        hora_inicial = datetime.strptime(hora, "%H:%M")
        hora_final = (hora_inicial + timedelta(minutes=50)).strftime('%H:%M')
        hora_inicial = hora_inicial.strftime('%H:%M')
        row = [Paragraph(f"{hora_inicial} - {hora_final}", cell_style)]
        for salon in salones_list:
            cell_texts = []
            for curso, asignacion in cursos.items():
                salon_asignado, hora_asignada, docente = asignacion
                if hora_asignada == hora and salon_asignado == salon:
                    cell_texts.append(f"{curso.nombre}")
                    cell_texts.append(f"{docente.nombre}")
                    cell_texts.append(f"(S:{curso.semestre})")
                    cell_texts.append(f"(C:{curso.carrera})")
            contenido = "\n".join(cell_texts) if cell_texts else ""
            paragraph = Paragraph(contenido, cell_style)
            row.append(paragraph)
        data.append(row)

    output_dir = "reports"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    pdf_path = os.path.join(output_dir, "reporte_horarios.pdf")

    doc = SimpleDocTemplate(pdf_path, pagesize=landscape(legal))
    elements = []

    title = Paragraph("Reporte de Horarios", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 6))

    col_width = 60
    num_cols = len(data[0])
    colWidths = [col_width] * num_cols

    table = Table(data, colWidths=colWidths)
    table_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])
    table.setStyle(table_style)
    elements.append(table)

    doc.build(elements)
    return pdf_path
