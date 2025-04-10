class Curso:
    def __init__(self, nombre, codigo, carrera, semestre, seccion, tipo):
        self.nombre = nombre
        self.codigo = codigo
        self.carrera = carrera
        self.semestre = semestre
        self.seccion = seccion
        self.tipo = tipo

    def __str__(self) -> str:
        return f"Curso({self.nombre},{self.codigo},{self.carrera},{self.semestre},{self.seccion},{self.tipo})"
