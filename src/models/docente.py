class Docente:
    def __init__(self, nombre, registro, hora_entrada, hora_salida):
        self.nombre = nombre
        self.registro = registro
        self.hora_entrada = hora_entrada
        self.hora_salida = hora_salida

    def __str__(self) -> str:
        return f"Docente({self.nombre},{self.registro},{self.hora_entrada},{self.hora_salida})"
