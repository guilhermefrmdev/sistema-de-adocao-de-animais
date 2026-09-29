from src.domain.pessoa import Pessoa

class Adotante(Pessoa):
    """Representa um adotante registrado no sistema.
    
    Estende `Pessoa` com características específicas dos adotantes.

    Attributes:
        telefone : Telefone do adotante.
        moradia : Tipo de moradia do adotante.
        areaUtil : Espaço útil da moradia.
        experiencia : Experiencia com outros animais.
        criancasEmCasa : Se há crianças em casa.
        outrosAnimais : Se há outros animais em casa.
    """