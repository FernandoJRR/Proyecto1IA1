class Salon:
    def __init__(self, nombre, id):
        self.nombre = nombre
        self.id = id

    def __str__(self) -> str:
        return f"Salon({self.nombre},{self.id})"
