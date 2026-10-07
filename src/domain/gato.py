from datetime import date

from src.domain.animal import Animal
from src.enums.status_animal import StatusAnimal
from src.enums.porte_animal import PorteAnimal
from src.enums.nivel_independencia import NivelIndependencia
from src.enums.tipos_pelos import TiposPelos
from src.mixins.vacinavel_mixin import VacinavelMixin
from src.mixins.adestravel_mixin import AdestravelMixin

class Gato(Animal, VacinavelMixin, AdestravelMixin):
    """Representa um gato registrado no sistema.

    Estende `Animal` com atributos específicos.
    
    Attributes:
        independencia : Indica o nível de independencia do gato.
        tipoPelo : Indica o tipo de pelo do gato.
    """
    def __init__(self, nome: str, idade: int, raca: str, sexo: str, status: StatusAnimal, temperamento: list, castrado: bool, porte: PorteAnimal, peso: int, data_entrada: date, independencia: NivelIndependencia, tipoPelo: TiposPelos, id: int = None):
        super().__init__(nome, idade, raca, sexo, status, temperamento, castrado, porte, peso, data_entrada, id)
        self.independencia = independencia
        self.tipoPelo = tipoPelo

    # Propriedades e verificações

    # Independência
    @property
    def independencia(self):
        return self._independencia

    @independencia.setter
    def independencia(self, nivel: NivelIndependencia):
        if not isinstance(nivel, NivelIndependencia):
            raise ValueError("O nível de independência deve ser uma instância de NivelIndependencia.")
        self._independencia = nivel

    # Tipos de pelos
    @property
    def tipoPelo(self):
        return self._tipoPelo

    @tipoPelo.setter
    def tipoPelo(self, tipo: TiposPelos):
        if not isinstance(tipo, TiposPelos):
            raise ValueError("O tipo de pelo deve ser uma instância de TiposPelos.")
        self._tipoPelo = tipo

    # Métodos especiais
    def __str__(self):
        return f"""
        Id: {self.id}.
        Nome: {self.nome}
        Idade: {self.idade} meses.
        Sexo: {self.sexo}.
        Raça: {self.raca}.
        Status: {self.status.name}.
        Temperamento: {', '.join(self.temperamento)}.
        Cadastrado: {"Sim" if self.castrado else "Não"}.
        Porte: {self.porte.name}.
        Peso: {self.peso} kg.
        Independência: {self.independencia.name}.
        Tipo de pelo: {self.tipoPelo.name}.
        Histórico: {', '.join(self.historico) if self.historico != [] else "Nenhum histórico registrado."}.
        Data de entrada: {self.data_entrada.strftime("%d/%m/%Y")}.
        """

    def __repr__(self):
        return f"Gato(id={self.id}, nome={self.nome}, idade={self.idade}, raca={self.raca}, sexo={self.sexo}, status={self.status.name}, temperamento={self.temperamento}, castrado={self.castrado}, porte={self.porte.name}, peso={self.peso}, independencia={self.independencia.name}, tipoPelo={self.tipoPelo.name}, historico={self.historico}, data_entrada={self.data_entrada.strftime('%d/%m/%Y')})"