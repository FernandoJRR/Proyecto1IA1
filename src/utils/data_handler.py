import pandas as pd
from models import Curso, Docente, Salon, DocenteCurso

def cargar_cursos(archivo_csv) -> list[Curso]:
    """
    Lee un archivo CSV de cursos y devuelve una lista de objetos Curso.
    
    Se asume que el CSV tiene las columnas: 
    'nombre', 'codigo', 'carrera', 'semestre', 'seccion', 'tipo'
    """
    df = pd.read_csv(archivo_csv)
    cursos = []
    for _, row in df.iterrows():
        curso = Curso(
            nombre=row['nombre'],
            codigo=row['codigo'],
            carrera=row['carrera'],
            semestre=row['semestre'],
            seccion=row['seccion'],
            tipo=row['tipo']
        )
        cursos.append(curso)
    return cursos

def guardar_cursos(cursos: list[Curso], archivo_csv):
    """
    Guarda un archivo CSV de cursos
    
    Se asume que el CSV tiene las columnas: 
    'nombre', 'codigo', 'carrera', 'semestre', 'seccion', 'tipo'
    """
    # Convertir la lista de objetos a una lista de diccionarios
    data = [{
        'nombre': curso.nombre,
        'codigo': curso.codigo,
        'carrera': curso.carrera,
        'semestre': curso.semestre,
        'seccion': curso.seccion,
        'tipo': curso.tipo
    } for curso in cursos]

    # Crear un DataFrame a partir de la lista de diccionarios
    df = pd.DataFrame(data)

    # Escribir el DataFrame en el archivo CSV (esto sobreescribe el archivo existente)
    df.to_csv(archivo_csv, index=False)

def cargar_docentes(archivo_csv) -> list[Docente]:
    """
    Lee un archivo CSV de docentes y devuelve una lista de objetos Docente.
    
    Se asume que el CSV tiene las columnas: 
    'nombre', 'registro', 'hora_entrada', 'hora_salida'
    """
    df = pd.read_csv(archivo_csv)
    docentes = []
    for _, row in df.iterrows():
        docente = Docente(
            nombre=row['nombre'],
            registro=row['registro'],
            hora_entrada=row['hora_entrada'],
            hora_salida=row['hora_salida']
        )
        docentes.append(docente)
    return docentes

def guardar_docentes(docentes: list[Docente], archivo_csv):
    """
    Guarda un archivo CSV de docentes
    
    Se asume que el CSV tiene las columnas: 
    'nombre', 'registro', 'hora_entrada', 'hora_salida'
    """
    # Convertir la lista de objetos a una lista de diccionarios
    data = [{
        'nombre': docente.nombre,
        'registro': docente.registro,
        'hora_entrada': docente.hora_entrada,
        'hora_salida': docente.hora_salida,
    } for docente in docentes]

    # Crear un DataFrame a partir de la lista de diccionarios
    df = pd.DataFrame(data)

    # Escribir el DataFrame en el archivo CSV (esto sobreescribe el archivo existente)
    df.to_csv(archivo_csv, index=False)

def cargar_relaciones(archivo_csv) -> list[DocenteCurso]:
    """
    Lee un archivo CSV con la relación entre docentes y cursos
    y devuelve una lista de objetos RelacionDocenteCurso.
    
    Se asume que el CSV tiene las columnas: 
    'registro' (de docente) y 'codigo' (del curso)
    """
    df = pd.read_csv(archivo_csv)
    relaciones = []
    for _, row in df.iterrows():
        relacion = DocenteCurso(
            registro_docente=row['registro'],
            codigo_curso=row['codigo']
        )
        relaciones.append(relacion)
    return relaciones

def guardar_relaciones(relaciones: list[DocenteCurso], archivo_csv):
    """
    Guarda un archivo CSV de relaciones
    
    Se asume que el CSV tiene las columnas: 
    'registro', 'codigo'
    """
    # Convertir la lista de objetos a una lista de diccionarios
    data = [{
        'registro': relacion.registro_docente,
        'codigo': relacion.codigo_curso,
    } for relacion in relaciones]

    # Crear un DataFrame a partir de la lista de diccionarios
    df = pd.DataFrame(data)

    # Escribir el DataFrame en el archivo CSV (esto sobreescribe el archivo existente)
    df.to_csv(archivo_csv, index=False)

def cargar_salones(archivo_csv) -> list[Salon]:
    """
    Lee un archivo CSV con la información de los salones y devuelve una lista de objetos Salon.
    
    Se asume que el CSV tiene las columnas: 'id' y 'nombre'
    """
    df = pd.read_csv(archivo_csv)
    salones = []
    for _, row in df.iterrows():
        salon = Salon(
            id=row['id'],
            nombre=row['nombre']
        )
        salones.append(salon)
    return salones

def guardar_salones(salones: list[Salon], archivo_csv):
    """
    Guarda un archivo CSV de salones
    
    Se asume que el CSV tiene las columnas: 
    'nombre', 'id'
    """
    # Convertir la lista de objetos a una lista de diccionarios
    data = [{
        'nombre': salon.nombre,
        'id': salon.id,
    } for salon in salones]

    # Crear un DataFrame a partir de la lista de diccionarios
    df = pd.DataFrame(data)

    # Escribir el DataFrame en el archivo CSV (esto sobreescribe el archivo existente)
    df.to_csv(archivo_csv, index=False)
