from enum import Enum

class TiposPelos(Enum):
    """
    Representa a enumeração dos tipos de pelos.
    """
    SEM_PELOS: int = 0
    CURTO: int = 1
    LONGO: int = 2
    ONDULADO: int = 3
    