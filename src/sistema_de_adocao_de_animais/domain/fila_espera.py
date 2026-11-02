from sistema_de_adocao_de_animais.repositories.fila_de_espera_repository import (
    FilaDeEsperaRepository,
)


class FilaDeEspera():
    """Representa a fila de espera de um determinado animal.

    Attributes:
        animal_id (str): O animal relacionado com essa fila de. espera
        fila (list): A listagem das reservas em espera.
    """
    def __init__(self, animal_id: int, fila: list = []):
        self.animal_id = animal_id
        self.fila = fila

    # Atualizar fila

    # Adicionar na fila
