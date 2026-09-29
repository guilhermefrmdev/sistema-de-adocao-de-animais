from src.domain.animal import Animal
from src.mixins.vacinavel_mixin import VacinavelMixin
from src.mixins.adestravel_mixin import AdestravelMixin

class Cachorro(Animal, VacinavelMixin, AdestravelMixin):
    """Representa um cachorro registrado no sistema.

    Estende `Animal` com atributos específicos.
    
    Attributes:
        necessidadePasseio: Se há necessidade de passeio.
    """