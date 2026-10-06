from datetime import date

from src.enums.status_animal import StatusAnimal
from src.enums.porte_animal import PorteAnimal
from src.domain.animal import Animal
from src.mixins.vacinavel_mixin import VacinavelMixin
from src.mixins.adestravel_mixin import AdestravelMixin

class Cachorro(Animal, VacinavelMixin, AdestravelMixin):
    """Representa um cachorro registrado no sistema.

    Estende `Animal` com atributos específicos.
    
    Attributes:
        necessidadePasseio: Se há necessidade de passeio.
    """
    def __init__(self, nome: str, idade: int, raça: str, sexo: str, status: StatusAnimal, temperamento: list, castrado: bool, porte: PorteAnimal, peso: int, dataEntrada: date, necessidadePasseio: bool, historico: list = [], id: int = None):
        super().__init__(nome, idade, raça, sexo, status, temperamento, castrado, porte, peso, dataEntrada, historico, id)
        self.necessidadePasseio = necessidadePasseio

    # Propriedades e verificações
    
    # Necessidade de passeio
    @property
    def necessidadePasseio(self):
        return self._necessidadePasseio

    @necessidadePasseio.setter
    def necessidadePasseio(self, necessidade: bool):
        if not isinstance(necessidade, bool):
            raise ValueError("A necessidade de passeio deve ser um valor booleano.")
        self._necessidadePasseio = necessidade

    # Métodos especiais
    def __str__(self):
        return f"""
        Id: {self.__id}.
        Nome: {self.nome}
        Idade: {self.idade} meses.
        Sexo: {self.sexo}.
        Raça: {self.raça}.
        Status: {self.status.name}.
        Temperamento: {', '.join(self.temperamento)}.
        Cadastrado: {"Sim" if self.castrado else "Não"}.
        Porte: {self.porte.name}.
        Peso: {self.peso} kg.
        Necessidade de passeio: {"Sim" if self.necessidadePasseio else "Não"}.
        Histórico: {', '.join(self.historico) if self.historico != [] else "Nenhum histórico registrado."}.
        Data de entrada: {self.dataEntrada.strftime("%d/%m/%Y")}.
        """

    def __repr__(self):
        return f"Cachorro(nome={self.nome}, idade={self.idade}, raça={self.raça}, sexo={self.sexo}, status={self.status.name}, temperamento={self.temperamento}, castrado={self.castrado}, porte={self.porte.name}, peso={self.peso}, necessidadePasseio={self.necessidadePasseio}, historico={self.historico}, dataEntrada={self.dataEntrada.strftime('%d/%m/%Y')})"