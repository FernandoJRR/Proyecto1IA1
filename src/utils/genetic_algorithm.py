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

    def penalizacion_continuidad_dinamica(self, generacion, total_generaciones, peso_inicial, peso_final=50):
        # Interpolación lineal: aumenta el peso de penalización por continuidad conforme avanza la evolución
        ratio = generacion / total_generaciones
        return peso_inicial + (peso_final - peso_inicial) * ratio

    # Función de costo: 
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
    # para cada curso, con cierta probabilidad se prueban varias alternativas y se escoge la que minimice la función de aptitud.
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

    def calcular_tamano_torneo(self, poblacion, generacion, total_generaciones, tamano_min=2, max_torneo_fraction=0.3):
        """
        Calcula el tamaño del torneo de forma adaptativa:
        - Al inicio se usa 'tamano_min'.
        - Al final se usa hasta 'max_torneo_fraction' * (tamaño de la población).
        Se interpola linealmente en función del progreso de la evolución.
        """
        poblacion_size = len(poblacion)
        # Tamaño máximo posible basado en la fracción de la población
        tamano_max = int(poblacion_size * max_torneo_fraction)
        
        # Interpolación lineal:
        tamano_torneo = tamano_min + int((tamano_max - tamano_min) * (generacion / total_generaciones))
        
        # Aseguramos que sea al menos 2
        return max(2, tamano_torneo)

    # Selección: Se utiliza torneo simple
    def seleccion_torneo(self, poblacion, generacion, total_generaciones):
        #tamano = self.calcular_tamano_torneo(poblacion, generacion, total_generaciones)
        tamano = 3
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

    def cruza_uniforme(self, padre1: Individuo, padre2: Individuo) -> Individuo:
        hijo = {}
        for curso in self.cursos:
            if random.random() < 0.5:
                hijo[curso] = padre1[curso]
            else:
                hijo[curso] = padre2[curso]
        return hijo

    def cruza_adaptativa(self, padre1: Individuo, padre2: Individuo, generacion: int, total_generaciones: int) -> Individuo:
        # se calcula el ratio basado en que tan avanzado va el proceso de generacion
        ratio = generacion / total_generaciones
        # mientras mas avance el proceso de generacion mas se favorecera la cruza uniforme
        if random.random() < (1 - ratio):
            return self.cruza_uniforme(padre1, padre2)
        else:
            return self.cruza(padre1, padre2)

    def tasa_mutacion_dinamica(self, tasa_inicial: float, generacion: int, total_generaciones: int, min_tasa: float = 0.05) -> float:
        """
        Calcula la tasa de mutación dinámica.
        Se usa una disminución lineal: en generación 0 se usa tasa_inicial, y en la última
        generación se usa un valor mínimo 'min_tasa'.
        """
        # Disminución lineal: 
        # tasa_actual = tasa_inicial - (tasa_inicial - min_tasa) * (generacion / total_generaciones)
        return tasa_inicial - (tasa_inicial - min_tasa) * (generacion / total_generaciones)

    def distancia(self, ind1: Individuo, ind2: Individuo) -> float:
        """
        Calcula una medida de distancia entre dos individuos.
        Se cuenta la cantidad de cursos con asignaciones diferentes y se divide
        por el total de cursos, resultando en un valor entre 0 y 1.
        """
        diferencias = 0
        total = len(self.cursos)
        for curso in self.cursos:
            # Compara la asignación de cada curso en ambos individuos
            if ind1.get(curso) != ind2.get(curso):
                diferencias += 1
        return diferencias / total  # 0: idénticos, 1: completamente distintos

    def calcular_diversidad(self, poblacion: list[Individuo]) -> float:
        """
        Calcula la diversidad de la población como la distancia promedio entre
        cada par de individuos.
        """
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

    def evaluar_poblacion(self, poblacion) -> list[tuple[float, int, Individuo, float]]:
        # Se evalua toda la poblacion con la funcion costo
        poblacion_evaluada = []
        for ind in poblacion:
            costo, conflictos, porcentaje_continuidad_solucion = self.funcion_costo(ind)
            poblacion_evaluada.append((costo, conflictos, ind, porcentaje_continuidad_solucion))
        # se ordenan de menor a mayor penalizacion
        poblacion_evaluada.sort(key=lambda tup: tup[0])
        return poblacion_evaluada
    
    def generar_hijo(self, poblacion, tasa_mutacion, generacion, total_generaciones):
        padre1 = self.seleccion_torneo(poblacion, generacion, total_generaciones)
        padre2 = self.seleccion_torneo(poblacion, generacion, total_generaciones)
        #padre1 = self.seleccion_torneo_fitness_share(poblacion)
        #padre2 = self.seleccion_torneo_fitness_share(poblacion)
        hijo = self.cruza_adaptativa(padre1, padre2, generacion, total_generaciones)
        hijo = self.mutacion_reparadora(hijo, tasa_mutacion)
        #hijo = self.mutacion(hijo, tasa_mutacion)
        return hijo

    def obtener_elites(self, poblacion_evaluada, generacion, total_generaciones, elite_fraction_min, elite_fraction_max, 
                       diversidad, umbral_diversidad):
        """
        Calcula de forma dinámica la fracción de élites a conservar según la generación actual.
        Se asume que 'poblacion_evaluada' es una lista de tuplas (costo, conflictos, individuo)
        ordenada de menor a mayor costo (es decir, el mejor primero).
        La fracción de élites aumentará de 'elite_fraction_min' al inicio a 'elite_fraction_max' al final.
        """
        # Ratio de avance: 0 en la primera generación, 1 en la última.
        ratio = generacion / total_generaciones
        elite_fraction_actual = elite_fraction_min + (elite_fraction_max - elite_fraction_min) * ratio

        if diversidad < umbral_diversidad:
            # Una opción simple: forzar la fracción a que sea el mínimo,
            # lo cual incrementa la exploración.
            #elite_fraction_actual = elite_fraction_min
            # Alternativamente, podrías usar un factor proporcional:
            factor = diversidad / umbral_diversidad  # valor entre 0 y 1
            elite_fraction_actual = elite_fraction_min + (elite_fraction_actual - elite_fraction_min) * factor

        elite_count = max(1, int(len(poblacion_evaluada) * elite_fraction_actual))
        # Extraer los 'elite_count' mejores individuos (ya ordenados)
        elites = [tup[2] for tup in poblacion_evaluada[:elite_count]]
        Logger.instance().log(f"Generación {generacion}: Se conservan {elite_count} élites (fractions: {elite_fraction_actual:.2f}).")
        return elites

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

        """
        nueva_poblacion = []
        for _ in range(poblacion_inicial):
            nueva_poblacion.append(self.generar_hijo(poblacion, tasa_mutacion, self.generacion_actual, self.total_generaciones))

        nueva_poblacion = self.reinsertar_poblacion(self.generacion_actual, intervalo_reinsercion, nueva_poblacion, 
                                                    poblacion_inicial, porcentaje_reinsercion)
        """
        """
        """
        nuevos_hijos = self.reinsertar_poblacion_adaptativo(intervalo_reinsercion, 
                                                               nueva_poblacion, (poblacion_inicial - len(elites)), porcentaje_reinsercion)
        nueva_poblacion = elites + nuevos_hijos

        return nueva_poblacion

    def ejecutar(self, poblacion_inicial, generaciones: int, tasa_mutacion, penalizacion_continuidad,
                 conflicto_esperado, evaluar_conflicto,
                 continuidad_esperada, evaluar_continuidad,
                 penalizacion_esperada, evaluar_penalizacion,
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
            diversidad = self.calcular_diversidad(poblacion)  # Define una función que mida la diversidad
            umbral_diversidad = 0.01
            tasa_actual = self.tasa_mutacion_adaptativa(tasa_mutacion, generacion, generaciones, diversidad, umbral_diversidad)

            poblacion_evaluada = self.evaluar_poblacion(poblacion)
            menor_penalizacion, conflictos, mejor_individuo, continuidad_actual = poblacion_evaluada[0]
            self.porcentaje_continuidad = continuidad_actual

            self.conflictos_por_generacion.append(conflictos)
            self.continuidad_por_generacion.append(continuidad_actual)

            porcentaje_aptitud = (1 / (1 + menor_penalizacion)) * 100
            Logger.instance().log(f"Aptitud: {porcentaje_aptitud:.5f}% Penalizacion: {menor_penalizacion:.5f} Mutacion: {tasa_actual:.5f} Continuidad: {continuidad_actual:.5f} Diversidad: {diversidad:.5f} Umbral: {umbral_diversidad:.5f}")
            
            converge = True

            if evaluar_conflicto and not (conflictos <= conflicto_esperado):
                converge = False

            if evaluar_continuidad and not (continuidad_actual >= continuidad_esperada):
                converge = False

            if evaluar_penalizacion and not (menor_penalizacion <= penalizacion_esperada):
                converge = False

            if converge:
                break
            """
            if menor_penalizacion == 0:
                convergencia = generacion
                break
            """

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
        self.memoria_consumida = process.memory_info().rss / (1024 * 1024)  # en MB

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
