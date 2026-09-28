from src.repositories.pessoa_repository import PessoaRepository

class Pessoa(PessoaRepository):
    """Representa uma pessoa no sistema
    
    Attributes:
        id : Identificação única da pessoa.
        nome : Nome da pessoa.
        idade : Idade da pessoa.
    """