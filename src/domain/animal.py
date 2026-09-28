from src.repositories.animal_repository import AnimalRepository

class Animal(AnimalRepository):
    """Representa um animal registrado no sistema.
    
    Attributes:
        id: Identificação única do animal.
        nome: Nome do animal.
        idade: Idade do animal em meses.
        raça: Raça do animal.
        sexo: Sexo do animal.
        status: Status do animal.
        temperamento: Lista com os temperamentos do animal.
        castrado: Se o animal é castrado.
        historico: Histórico do animal.
        porte: Porte do animal.
    """