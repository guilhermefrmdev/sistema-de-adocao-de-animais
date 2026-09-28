from src.domain.animal import Animal
from src.mixins.vacinavel_mixin import VacinavelMixin
from src.mixins.adestravel_mixin import AdestravelMixin

class Gato(Animal, VacinavelMixin, AdestravelMixin):
    """Representa um gato registrado no sistema.

    Estende `Animal` com atributos específicos.
    
    Attributes:
        independencia : Indica o nível de independencia do gato.
        tipoPelo : Indica o tipo de pelo do gato.
    """