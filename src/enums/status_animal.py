from enum import Enum

class StatusAnimal(Enum):
    """
    Representa a enumeração dos status dos animais.
    """
    DISPONIVEL: int = 0
    RESERVADO: int = 1
    ADOTADO: int = 2
    DEVOLVIDO: int = 3
    INADOTAVEL: int = 4
    QUARENTENA: int = 5