import os
import psutil
import random

from fitz import time
from interface.logger import Logger
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

        self.penalizacion_continuidad: float = 0

        self.generacion_actual: int = 0
        self.total_generaciones: int = 0

        self.resultado: Individuo | None = None
        self.conflictos_por_generacion: list = []
        self.continuidad_por_generacion: list = []
        self.conflictos_mejor_individuo: int = 0
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

    # Creacion de un individuo
    def crear_individuo(self) -> Individuo:
        horario_ind: Individuo = {}
        for curso in self.cursos:
            salon = random.choice(self.salones)
            hora = random.choice(self.horarios)
            docentes_permitidos = self.docentes_por_curso.get(curso.codigo, [])
            if docentes_permitidos:
                profesor = random.choice(docentes_permitidos)
            else:
                profesor = None  # En caso de que no haya docentes permitidos
            horario_ind[curso] = (salon, hora, profesor)
        return horario_ind

    # La penalizacion por la continuidad aumenta dinamicamente conforme pasan las generaciones
    def penalizacion_continuidad_dinamica(self, generacion, total_generaciones, peso_inicial, peso_final=50):
        ratio = generacion / total_generaciones
        return peso_inicial + (peso_final - peso_inicial) * ratio

    # Función de costo
    # Penaliza una solucion basado en conflictos y la continuidad de esta 
    def funcion_costo(self, individuo: Individuo) -> tuple[float, int, float]:
        penalizacion = 0
        conflictos = 0
        cursos = list(individuo.items())
        for i in range(len(cursos)):
            curso_i, asignacion_i = cursos[i]
            salon_i, hora_i, docente_i = asignacion_i

            #Conflicto si hay un docente en un curso en un horario en el que no trabaja
            if (
                docente_i is not None and
                not docente_i.esta_disponible(hora_i)
            ):
                pass
                penalizacion += 5
                conflictos += 1

            for j in range(i + 1, len(cursos)):
                curso_j, asignacion_j = cursos[j]
                salon_j, hora_j, docente_j = asignacion_j

                # Conflicto de salón y horario
                if salon_i == salon_j and hora_i == hora_j:
                    penalizacion += 5
                    conflictos += 1
                # Conflicto si hay mismo docente en el mismo horario
                if (
                    docente_i is not None and
                    docente_i == docente_j and
                    hora_i == hora_j
                ):
                    penalizacion += 1
                    conflictos += 1


                # Penalizacion si hay dos cursos del mismo semestre y carrera en el mismo horario
                if (
                    curso_i.semestre == curso_j.semestre and
                    curso_i.carrera == curso_j.carrera and
                    hora_i == hora_j
                ):
                    penalizacion += 1

        peso_continuidad = self.penalizacion_continuidad_dinamica(
            self.generacion_actual, self.total_generaciones, self.penalizacion_continuidad)

        porcentaje_continuidad_solucion = self.calcular_continuidad(individuo)
        punteo_continuidad = (porcentaje_continuidad_solucion * peso_continuidad) / 100

        # Penalizacion por falta de continuidad 
        # es inversamente proporcional al porcentaje de continuidad
        penalizacion_continuidad = peso_continuidad - punteo_continuidad
        penalizacion += penalizacion_continuidad

        return (penalizacion, conflictos, porcentaje_continuidad_solucion)

    # Mutación Reparadora 
    # para cada curso, con cierta probabilidad se prueban varias alternativas y se escoge la que minimice la función de costo.
    def mutacion_reparadora(self, individuo: Individuo, tasa_mutacion=0.1, n_alternativas=3) -> dict:
        for curso in individuo:
            if random.random() < tasa_mutacion:
                gen_original = individuo[curso]
                mejor_gen = gen_original
                menor_penalizacion,_,_ = self.funcion_costo(individuo)
                # Probar n alternativas
                for _ in range(n_alternativas):
                    nuevo_salon = random.choice(self.salones)
                    nuevo_horario = random.choice(self.horarios)
                    docentes_permitidos = self.docentes_por_curso.get(curso.codigo, [])
                    nuevo_profesor = random.choice(docentes_permitidos) if docentes_permitidos else None

                    # Asignar temporalmente la nueva opción
                    individuo[curso] = (nuevo_salon, nuevo_horario, nuevo_profesor)
                    nueva_penalizacion,_,_ = self.funcion_costo(individuo)
                    # Se elige la opción que minimiza la penalización de conflictos
                    if nueva_penalizacion < menor_penalizacion:
                        menor_penalizacion = nueva_penalizacion
                        mejor_gen = (nuevo_salon, nuevo_horario, nuevo_profesor)
                # Reasignar el mejor gen encontrado
                individuo[curso] = mejor_gen
        return individuo

    def mutacion_adaptativa(self, individuo, tasa_mutacion):
        ratio = self.generacion_actual / self.total_generaciones
        randomNum = random.random()
        if randomNum < (1 - ratio):
            return self.mutacion_reparadora(individuo, tasa_mutacion)
        else:
            return self.mutacion(individuo)

    # Selección: Se utiliza torneo simple
    def seleccion_torneo(self, poblacion, tamano=3):
        #Logger.instance().log(f"Torneo con {tamano} individuos")
        candidatos = random.sample(poblacion, tamano)
        candidatos.sort(key=lambda ind: self.funcion_costo(ind)[0])
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

    # Se usa un cruce uniforme para mezclar parejo a las asignacinoes
    def cruza_uniforme(self, padre1: Individuo, padre2: Individuo) -> Individuo:
        hijo = {}
        for curso in self.cursos:
            if random.random() < 0.5:
                hijo[curso] = padre1[curso]
            else:
                hijo[curso] = padre2[curso]
        return hijo

    # Alterna entre la cruza normal y uniforme para mejorar la diversidad
    def cruza_adaptativa(self, padre1: Individuo, padre2: Individuo, generacion: int, total_generaciones: int) -> Individuo:
        # se calcula el ratio basado en que tan avanzado va el proceso de generacion
        ratio = generacion / total_generaciones
        # mientras mas avance el proceso de generacion mas se favorecera la cruza uniforme
        if random.random() < (1 - ratio):
            return self.cruza(padre1, padre2)
        else:
            return self.cruza_uniforme(padre1, padre2)

    # La tasa de mutacion cambia, se reduce linealmente conforme pasan las generaciones
    def tasa_mutacion_dinamica(self, tasa_inicial: float, generacion: int, total_generaciones: int, min_tasa: float = 0.05) -> float:
        return tasa_inicial - (tasa_inicial - min_tasa) * (generacion / total_generaciones)

    # Se calcula la distancia entre dos individuos, esto en base a la cantidad de genes que son iguales
    def distancia(self, ind1: Individuo, ind2: Individuo) -> float:
        diferencias = 0
        total = len(self.cursos)
        for curso in self.cursos:
            # Compara la asignación de cada curso en ambos individuos
            if ind1.get(curso) != ind2.get(curso):
                diferencias += 1
        return diferencias / total  # 0 iguales, 1 distintos

    # Se calcula la diversidad de una poblacion haciendo un promedio de las distancias entre individuos
    def calcular_diversidad(self, poblacion: list[Individuo]) -> float:
        if not poblacion:
            return 0
        
        n = len(poblacion)
        suma_distancias = 0.0
        contador = 0
        for i in range(n):
            for j in range(i + 1, n):
                suma_distancias += self.distancia(poblacion[i], poblacion[j])
                contador += 1
        if contador == 0:
            return 0
        return suma_distancias / contador

    # La tasa de mutacion se reduce conforme pasan las generaciones (de forma lineal)
    # Si hay poca diversidad se aumenta
    def tasa_mutacion_adaptativa(self, tasa_inicial: float, generacion: int, total_generaciones: int,
                                diversidad: float, umbral_diversidad, min_tasa: float = 0.1,
                                potenciador_min = 1, potenciador_max = 8) -> float:
        tasa_base = tasa_inicial - (tasa_inicial - min_tasa) * (generacion / total_generaciones)
        potenciador = potenciador_min + (potenciador_max - potenciador_min) * (generacion / total_generaciones)
        # Si la diversidad es muy baja, incrementa la tasa de mutación hasta max_tasa
        #Logger.instance().log(f"Diversidad: {diversidad} Umbral: {umbral_diversidad}")
        if diversidad < umbral_diversidad:
            tasa_base = tasa_base * potenciador
        return tasa_base

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

    # Se calcula el porcentaje de continuidad que tienen los cursos de un horario
    def calcular_continuidad(self, individuo: Individuo) -> float:
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

    # Se reemplaza un porcentaje de la poblacion cada ciertas generaciones por individuos aleatorios para mantener la diversidad
    def reinsertar_poblacion(self, generacion, intervalo_reinsercion, poblacion, size_poblacion, porcentaje_reinsercion):
        if generacion > 0 and generacion % intervalo_reinsercion == 0:
            num_reinsertar = int(size_poblacion * porcentaje_reinsercion)
            #Logger.instance().log(f"Reinserción: Se reintroducen {num_reinsertar} individuos aleatorios en la generación {generacion}.")
            for _ in range(num_reinsertar):
                # Generamos un individuo aleatorio
                individuo_random = self.crear_individuo()
                # Reemplazamos el peor individuo (el último en la lista ordenada)
                poblacion[-1] = individuo_random
                # Vuelve a ordenar la población nueva para mantener la mejor solución al inicio
                poblacion.sort(key=lambda ind: self.funcion_costo(ind)[0])

        return poblacion

    # Alterna entre la reinsercion por diversidad y la reinsercion normal
    def reinsertar_poblacion_adaptativo(self, intervalo_reinsercion, poblacion, size_poblacion, 
                                        porcentaje_reinsercion, umbral_diversidad=0.001):
        diversidad_actual = self.calcular_diversidad(poblacion)
        #Logger.instance().log(f"Reinserción adaptativa: Diversidad {diversidad_actual:.5f} Umbral {umbral_diversidad}.")
        # Si la diversidad cae por debajo del umbral y se cumple el intervalo, se realiza la reinserción
        if diversidad_actual < umbral_diversidad:
            num_reinsertar = int(size_poblacion * porcentaje_reinsercion)
            #Logger.instance().log(f"Reinserción adaptativa: Diversidad {diversidad_actual:.5f} menor a {umbral_diversidad}. Se reintroducen {num_reinsertar} individuos en la generación {self.generacion_actual}.")
            for _ in range(num_reinsertar):
                nuevo_individuo = self.crear_individuo()
                # Reemplazar al peor individuo
                poblacion[-1] = nuevo_individuo
                poblacion.sort(key=lambda ind: self.funcion_costo(ind)[0])
        elif self.generacion_actual > 0 and self.generacion_actual % intervalo_reinsercion == 0:
            self.reinsertar_poblacion(self.generacion_actual, intervalo_reinsercion, poblacion, size_poblacion, porcentaje_reinsercion)

        return poblacion

    # Se evalua la poblacion en base a la funcion costo
    def evaluar_poblacion(self, poblacion) -> list[tuple[float, int, Individuo, float]]:
        poblacion_evaluada = []
        for ind in poblacion:
            costo, conflictos, porcentaje_continuidad_solucion = self.funcion_costo(ind)
            poblacion_evaluada.append((costo, conflictos, ind, porcentaje_continuidad_solucion))
        # se ordenan de menor a mayor penalizacion
        poblacion_evaluada.sort(key=lambda tup: tup[0])
        return poblacion_evaluada
    
    # Se genera un hijo 
    def generar_hijo(self, poblacion, tasa_mutacion, generacion, total_generaciones):
        padre1 = self.seleccion_torneo(poblacion)
        padre2 = self.seleccion_torneo(poblacion)
        hijo = self.cruza_adaptativa(padre1, padre2, generacion, total_generaciones)
        hijo = self.mutacion_adaptativa(hijo, tasa_mutacion)
        return hijo

    # Basado en generaciones, elites y diversidad se calcula la cantidad de individuos conservados como elites
    def obtener_elites(self, poblacion_evaluada, generacion, total_generaciones, elite_fraction_min, elite_fraction_max, 
                       diversidad, umbral_diversidad):
        ratio = generacion / total_generaciones
        elite_fraction_actual = elite_fraction_min + (elite_fraction_max - elite_fraction_min) * ratio

        # si la diversidad cae bajo el umbral se suaviza la cantidad de elites
        if diversidad < umbral_diversidad:
            factor = diversidad / umbral_diversidad
            elite_fraction_actual = elite_fraction_min + (elite_fraction_actual - elite_fraction_min) * factor

        elite_count = max(1, int(len(poblacion_evaluada) * elite_fraction_actual))
        # Extraer los 'elite_count' mejores individuos (ya ordenados)
        elites = [tup[2] for tup in poblacion_evaluada[:elite_count]]
        Logger.instance().log(f"Generación {generacion}: Se conservan {elite_count} élites (fraccion: {elite_fraction_actual:.2f}).")
        return elites

    # Se genera una poblacion
    def generar_poblacion(
            self, poblacion_inicial, poblacion, poblacion_evaluada, 
            fraccion_elite_min, fraccion_elite_max, tasa_mutacion,
            intervalo_reinsercion, porcentaje_reinsercion, diversidad, umbral_diversidad):
        elites = self.obtener_elites(
            poblacion_evaluada, self.generacion_actual, self.total_generaciones, fraccion_elite_min, fraccion_elite_max, 
            diversidad, umbral_diversidad)

        nuevos_hijos = []
        while len(nuevos_hijos) < (poblacion_inicial - len(elites)):
            nuevos_hijos.append(self.generar_hijo(poblacion, tasa_mutacion, self.generacion_actual, self.total_generaciones))
        nueva_poblacion = nuevos_hijos

        nuevos_hijos = self.reinsertar_poblacion_adaptativo(intervalo_reinsercion, 
                                                               nueva_poblacion, (poblacion_inicial - len(elites)), porcentaje_reinsercion)
        nueva_poblacion = elites + nuevos_hijos

        return nueva_poblacion

    # se ejecuta el algoritmo
    def ejecutar(self, poblacion_inicial, generaciones: int, tasa_mutacion, penalizacion_continuidad,
                 conflicto_esperado, evaluar_conflicto,
                 continuidad_esperada, evaluar_continuidad,
                 penalizacion_esperada, evaluar_penalizacion,
                 umbral_diversidad,
                 intervalo_reinsercion = 10, porcentaje_reinsercion = 0.6, fraccion_elite_min = 0.3, fraccion_elite_max = 0.7):

        start_time = time.time()
        process = psutil.Process(os.getpid())

        mejor_individuo: Individuo = dict()
        self.penalizacion_continuidad = penalizacion_continuidad
        self.generacion_actual = 0
        self.total_generaciones = generaciones
        #print(self.penalizacion_continuidad)
        #print(self.generacion_actual)
        #print(self.total_generaciones)

        # Creación de la población inicial
        poblacion = [self.crear_individuo() for _ in range(poblacion_inicial)]

        conflictos: int = 0
        self.conflictos_por_generacion = []
        self.continuidad_por_generacion = []
        convergencia = generaciones  # Si no converge, asumimos que se realizaron todas las iteraciones
        # Ciclo del algoritmo
        for generacion in range(generaciones):
            self.generacion_actual = generacion
            Logger.instance().log(f"============================Generacion {generacion}")
            #tasa_actual = self.tasa_mutacion_dinamica(tasa_mutacion, generacion, generaciones)
            diversidad = self.calcular_diversidad(poblacion)
            tasa_actual = self.tasa_mutacion_adaptativa(tasa_mutacion, generacion, generaciones, diversidad, umbral_diversidad)

            poblacion_evaluada = self.evaluar_poblacion(poblacion)
            menor_penalizacion, conflictos, mejor_individuo, continuidad_actual = poblacion_evaluada[0]
            self.porcentaje_continuidad = continuidad_actual

            self.conflictos_por_generacion.append(conflictos)
            self.continuidad_por_generacion.append(continuidad_actual)

            porcentaje_aptitud = (1 / (1 + menor_penalizacion)) * 100
            Logger.instance().log(f"Aptitud: {porcentaje_aptitud:.5f}% Penalizacion: {menor_penalizacion:.5f} Mutacion: {tasa_actual:.5f} Continuidad: {continuidad_actual:.5f} Diversidad: {diversidad:.5f}")
            
            converge = True

            if evaluar_conflicto and not (conflictos <= conflicto_esperado):
                converge = False

            if evaluar_continuidad and not (continuidad_actual >= continuidad_esperada):
                converge = False

            if evaluar_penalizacion and not (menor_penalizacion <= penalizacion_esperada):
                converge = False

            if converge:
                convergencia = generacion
                break

            nueva_poblacion = self.generar_poblacion(poblacion_inicial, poblacion, poblacion_evaluada, 
                                                     fraccion_elite_min, fraccion_elite_max, tasa_actual, 
                                                     intervalo_reinsercion, porcentaje_reinsercion, diversidad, umbral_diversidad)

            poblacion = nueva_poblacion

        end_time = time.time()

        self.resultado = mejor_individuo
        self.conflictos_mejor_individuo = conflictos
        self.tiempo_ejecucion = end_time - start_time
        self.iteraciones_optimas = convergencia
        self.porcentaje_continuidad = self.calcular_continuidad(mejor_individuo)
        self.memoria_consumida = process.memory_info().rss / (1024 * 1024)

        crear_horarios_pdf(self.resultado)
        self.reporte_horarios_pdf = os.path.join(os.getcwd(), "reports", "reporte_horarios.pdf")

    def imprimir_resultado(self):
        if self.resultado is None:
            print("No se encontro resultado")
            return
        print("Mejor horario encontrado:")
        for curso, asignacion in self.resultado.items():
            salon, hora, docente = asignacion
            print(f"Curso {curso}: Salón {salon}, Horario {hora}, Docente {docente}")
