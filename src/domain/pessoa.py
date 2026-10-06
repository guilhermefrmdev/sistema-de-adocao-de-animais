from src.repositories.pessoa_repository import PessoaRepository

class Pessoa(PessoaRepository):
    """Representa uma pessoa no sistema
    
    Attributes:
        id : Identificação única da pessoa.
        nome : Nome da pessoa.
        idade : Idade da pessoa.
    """

    def __init__(self, nome: str, idade: int, id: int = None):
            self.id = id
            self.nome = nome
            self.idade = idade

    # Propriedades e verificações

    # ID
    @property
    def id(self):
        return self.__id

    @id.setter
    def id(self, novo_id: int):
        self.__id = novo_id

    # Nome
    @property
    def nome(self): 
        return self._nome

    @nome.setter
    def nome(self, novo_nome: str):
        if not novo_nome.replace(" ", "").isalpha(): # Verificação somente letras
            raise ValueError("O nome deve conter apenas letras.")
         
        if novo_nome.strip() == "": # Verificação nome vazio
            raise ValueError("O nome não pode ser vazio.")

        self._nome = novo_nome.strip()

    # Idade
    @property
    def idade(self):
        return self._idade

    @idade.setter
    def idade(self, nova_idade: int):
        if nova_idade < 18:
            raise ValueError("Não pode ser menor de idade.") # Verificação Maioridade

        self._idade = nova_idade