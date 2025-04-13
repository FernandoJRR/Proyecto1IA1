from datetime import datetime, timedelta


class Docente:
    def __init__(self, nombre, registro, hora_entrada, hora_salida):
        self.nombre = nombre
        self.registro = registro
        self.hora_entrada = hora_entrada
        self.hora_salida = hora_salida

    def __str__(self) -> str:
        return f"Docente({self.nombre},{self.registro},{self.hora_entrada},{self.hora_salida})"

    def esta_disponible(self, hora_inicio_cmp) -> bool:
        formato = "%H:%M"
        try:
            hora_inicio_cmp = datetime.strptime(hora_inicio_cmp, formato)
            hora_final = hora_inicio_cmp + timedelta(minutes=50)
            hora_ent = datetime.strptime(self.hora_entrada, formato)
            hora_sal = datetime.strptime(self.hora_salida, formato)
            
            return hora_ent <= hora_inicio_cmp and hora_final <= hora_sal
        except ValueError:
            return False

