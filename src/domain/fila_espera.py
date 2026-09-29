from src.repositories.fila_de_espera_repository import FilaDeEsperaRepository

class FilaDeEspera(FilaDeEsperaRepository):
    """Representa a fila de espera de um determinado animal.
    
    Attributes:
        animal : O animal relacionado com essa fila de. espera
        fila : A listagem das reservas em espera.
    """