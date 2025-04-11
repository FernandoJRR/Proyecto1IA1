import os
import psutil
import random

from fitz import time
from utils.data_handler import *
from utils.pdf_handler import crear_horarios_pdf

type Individuo = dict[Curso, tuple[Salon, str, Docente | None]]

class AmbienteAlgoritmo:
    def __init__(self):
        self.cursos: list[Curso] = []
        self.salones: list[Salon] = []
        self.docentes = []
        self.relaciones = []
        self.horarios = []
        self.docentes_por_curso: dict[str, list[Docente]] = {}

        self.resultado: Individuo | None = None
        self.conflictos_por_generacion: list = []
        self.iteraciones_optimas: int = 0
        self.tiempo_ejecucion: float = 0
        self.porcentaje_continuidad: float = 0
        self.memoria_consumida: int = 0
        self.reporte_horarios_pdf: str | None = None

    def preparar_data(self):
        self.cursos = cargar_cursos("data/cursos.csv")
        self.salones = cargar_salones("data/salones.csv")
        self.docentes = cargar_docentes("data/docentes.csv")
        self.relaciones = cargar_relaciones("data/relaciones_docente_curso.csv")
        self.horarios = ["13:40", "14:30", "15:20", "16:10", "17:00", "17:50", "18:40", "19:30", "20:20", "21:10"]

        for curso in self.cursos:
            self.docentes_por_curso[curso.codigo] = []

        for relacion in self.relaciones:
            # Se busca el docente correspondiente según su registro
            for docente in self.docentes:
                if docente.registro == relacion.registro_docente:
                    if docente not in self.docentes_por_curso[relacion.codigo_curso]:
                        self.docentes_por_curso[relacion.codigo_curso].append(docente)

    # Representación: Cada individuo es un diccionario {curso: (salón, horario)}
    def crear_individuo(self) -> Individuo:
        horario_ind: Individuo = {}
        for curso in self.cursos:
            salon = random.choice(self.salones)
            hora = random.choice(self.horarios)
            docentes_permitidos = self.docentes_por_curso.get(curso.codigo, [])
            if docentes_permitidos:
                profesor = random.choice(docentes_permitidos)
            else:
                profesor = None  # En caso de que no haya docentes permitidos; se puede ajustar según requerimiento
            horario_ind[curso] = (salon, hora, profesor)
        return horario_ind

    # Función de aptitud: 
    # Cuenta conflictos donde dos cursos tienen asignado el mismo salón y el mismo horario.
    def funcion_aptitud(self, individuo: Individuo):
        penalizacion = 0
        cursos = list(individuo.items())
        for i in range(len(cursos)):
            curso_i, asignacion_i = cursos[i]
            salon_i, hora_i, docente_i = asignacion_i
            for j in range(i + 1, len(cursos)):
                curso_j, asignacion_j = cursos[j]
                salon_j, hora_j, docente_j = asignacion_j

                # Conflicto de salón y horario
                if salon_i == salon_j and hora_i == hora_j:
                    penalizacion += 1
                # Conflicto si hay mismo docente en el mismo horario
                if (
                    docente_i is not None and
                    docente_i == docente_j and
                    hora_i == hora_j
                ):
                    penalizacion += 1

                # Penalizacion si hay dos cursos del mismo semestre y carrera en el mismo horario
                if (
                    curso_i.semestre == curso_j.semestre and
                    curso_i.carrera == curso_j.carrera and
                    hora_i == hora_j
                ):
                    penalizacion += 1

        punteo_continuidad = (self.calcular_continuidad(individuo) * 10) / 100
        # Penalizacion por falta de continuidad es inversamente proporcional al porcentaje de continuidad
        penalizacion_continuidad = 10 - punteo_continuidad
        penalizacion += penalizacion_continuidad

        return penalizacion

    # Selección: Se utiliza torneo simple
    def seleccion_torneo(self, poblacion, tamano=3):
        candidatos = random.sample(poblacion, tamano)
        candidatos.sort(key=lambda ind: self.funcion_aptitud(ind))
        return candidatos[0]

    # Cruce: Se realiza un cruce de punto medio para mezclar asignaciones
    def cruza(self, padre1, padre2):
        hijo = {}
        punto_cruce = len(self.cursos) // 2
        lista_cursos = list(self.cursos)
        for i, curso in enumerate(lista_cursos):
            if i < punto_cruce:
                hijo[curso] = padre1[curso]
            else:
                hijo[curso] = padre2[curso]
        return hijo

    # Mutación: Con una probabilidad, se cambia el salón y/o el horario de un curso
    def mutacion(self, individuo: Individuo, tasa_mutacion=0.1):
        for curso in individuo:
            if random.random() < tasa_mutacion:
                nuevo_salon = random.choice(self.salones)
                nuevo_horario = random.choice(self.horarios)
                docentes_permitidos = self.docentes_por_curso.get(curso.codigo, [])
                if docentes_permitidos:
                    nuevo_profesor = random.choice(docentes_permitidos)
                else:
                    nuevo_profesor = None
                individuo[curso] = (nuevo_salon, nuevo_horario, nuevo_profesor)
        return individuo

    def calcular_continuidad(self, individuo: Individuo) -> float:
        """
        Calcula la continuidad promedio del horario para cada grupo de cursos,
        donde cada grupo se define por (carrera, semestre). Para cada grupo que tenga
        más de un curso, se calcula el porcentaje de parejas de cursos asignados en horarios consecutivos
        (según el orden en self.horarios) y se promedia el porcentaje obtenido en todos los grupos.
        Si ningún grupo tiene más de un curso, se retorna 100.
        """
        grupos = {}

        # Agrupa los cursos según carrera y semestre.
        for curso in individuo:
            key = (curso.carrera, curso.semestre)
            grupos.setdefault(key, []).append(individuo[curso][1])

        suma_continuidad = 0.0
        grupos_validos = 0

        for horas in grupos.values():
            # Convertir cada horario en su índice según self.horarios
            indices = sorted([self.horarios.index(h) for h in horas if h in self.horarios])
            # Solo consideramos grupos con al menos dos cursos
            if len(indices) < 2:
                continue
            total_pares = len(indices) - 1
            consecutivos = 0
            for i in range(1, len(indices)):
                if indices[i] - indices[i - 1] == 1:
                    consecutivos += 1
            continuidad = (consecutivos / total_pares) * 100
            suma_continuidad += continuidad
            grupos_validos += 1

        if grupos_validos > 0:
            return suma_continuidad / grupos_validos
        else:
            return 100

    def ejecutar(self, poblacion_inicial, generaciones, tasa_mutacion):
        start_time = time.time()
        process = psutil.Process(os.getpid())

        mejor_individuo: Individuo = dict()

        # Creación de la población inicial
        poblacion = [self.crear_individuo() for _ in range(poblacion_inicial)]

        self.conflictos_por_generacion = []
        convergencia = generaciones  # Si no converge, asumimos que se realizaron todas las iteraciones
        # Bucle principal del algoritmo genético
        for generacion in range(generaciones):
            poblacion = sorted(poblacion, key=lambda ind: self.funcion_aptitud(ind))
            mejor_individuo = poblacion[0]
            aptitud = self.funcion_aptitud(mejor_individuo)
            self.conflictos_por_generacion.append(aptitud)
            print("Generación", generacion, "Aptitud:", self.funcion_aptitud(mejor_individuo))
            
            # Criterio de parada: Aptitud 0 significa sin conflictos
            if aptitud == 0:
                convergencia = generacion
                break

            nueva_poblacion = []
            for _ in range(poblacion_inicial):
                padre1 = self.seleccion_torneo(poblacion)
                padre2 = self.seleccion_torneo(poblacion)
                hijo = self.cruza(padre1, padre2)
                hijo = self.mutacion(hijo, tasa_mutacion)
                nueva_poblacion.append(hijo)
            
            poblacion = nueva_poblacion

        end_time = time.time()

        self.resultado = mejor_individuo
        self.tiempo_ejecucion = end_time - start_time
        self.iteraciones_optimas = convergencia
        self.porcentaje_continuidad = self.calcular_continuidad(mejor_individuo)
        self.memoria_consumida = process.memory_info().rss / (1024 * 1024)  # en MB

        crear_horarios_pdf(self.resultado)
        self.reporte_horarios_pdf = os.path.join(os.getcwd(), "reports", "reporte_horarios.pdf")


        print("Mejor horario encontrado:")
        for curso, asignacion in self.resultado.items():
            salon, hora, docente = asignacion
            print(f"Curso {curso}: Salón {salon}, Horario {hora}, Docente {docente}")
