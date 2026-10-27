from datetime import datetime, timedelta

from sistema_de_adocao_de_animais.domain.adotante import Adotante
from sistema_de_adocao_de_animais.domain.animal import Animal
from sistema_de_adocao_de_animais.repositories.reserva_repository import (
    ReservaRepository,
)


class Reserva(ReservaRepository):
    """Representa uma reserva no sistema.

    Faz a relação entre um `Adotante` e um `Animal`: o adotante reserva o animal.

    Attributes:
        id : Identificação única da reserva.
        dataReserva : Data da reserva.
        dataExpiracao : Data de expiração da reserva.
        adotante : O adotante relacionado.
        animal : O animal relacionado.
        compatibilidade : A pontuação de compatibilidade
        status : Status da reserva.
    """

    STATUS_VALIDOS = ["ATIVA", "EXPIRADA", "CONCLUIDA", "CANCELADA"]

    def __init__(
        self,
        adotante: Adotante,
        animal: Animal,
        compatibilidade: float = 0.0,
        dataReserva: datetime = None,
        dataExpiracao: datetime = None,
        status: str = "ATIVA",
        id: int = None,
    ):
        self.id = id
        self.adotante = adotante
        self.animal = animal
        self.compatibilidade = compatibilidade
        self.dataReserva = dataReserva if dataReserva is not None else datetime.now()
        # Se não for informada, a reserva expira em 48h (valor padrão)
        self.dataExpiracao = (
            dataExpiracao
            if dataExpiracao is not None
            else self.dataReserva + timedelta(hours=48)
        )
        self.status = status

    # Propriedades e verificações

    # ID
    @property
    def id(self):
        return self.__id

    @id.setter
    def id(self, novo_id: int):
        self.__id = novo_id

    # Adotante
    @property
    def adotante(self):
        return self._adotante

    @adotante.setter
    def adotante(self, novo_adotante: Adotante):
        if not isinstance(novo_adotante, Adotante):
            raise ValueError("O adotante deve ser uma instância de Adotante.")
        self._adotante = novo_adotante

    # Animal
    @property
    def animal(self):
        return self._animal

    @animal.setter
    def animal(self, novo_animal: Animal):
        if not isinstance(novo_animal, Animal):
            raise ValueError("O animal deve ser uma instância de Animal.")
        self._animal = novo_animal

    # Compatibilidade
    @property
    def compatibilidade(self):
        return self._compatibilidade

    @compatibilidade.setter
    def compatibilidade(self, nova_compatibilidade: float):
        if not 0 <= nova_compatibilidade <= 100:
            raise ValueError("A compatibilidade deve estar entre 0 e 100.")
        self._compatibilidade = nova_compatibilidade

    # Data da reserva
    @property
    def dataReserva(self):
        return self._dataReserva

    @dataReserva.setter
    def dataReserva(self, nova_dataReserva: datetime):
        if not isinstance(nova_dataReserva, datetime):
            raise ValueError("A data da reserva deve ser uma instância de datetime.")
        self._dataReserva = nova_dataReserva

    # Data de expiração
    @property
    def dataExpiracao(self):
        return self._dataExpiracao

    @dataExpiracao.setter
    def dataExpiracao(self, nova_dataExpiracao: datetime):
        if not isinstance(nova_dataExpiracao, datetime):
            raise ValueError("A data de expiração deve ser uma instância de datetime.")
        if nova_dataExpiracao <= self.dataReserva:
            raise ValueError("A data de expiração deve ser depois da data da reserva.")
        self._dataExpiracao = nova_dataExpiracao

    # Status
    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, novo_status: str):
        novo_status = novo_status.strip().upper()
        if novo_status not in self.STATUS_VALIDOS:
            raise ValueError(
                f"O status deve ser um destes: {', '.join(self.STATUS_VALIDOS)}."
            )
        self._status = novo_status

    # Métodos
    def alterarStatus(self, novo_status: str):
        self.status = novo_status

    # Métodos Especiais
    def __str__(self) -> str:
        return f"""
ID: {self.id}.
Adotante: {self.adotante.nome}.
Animal: {self.animal.nome}.
Compatibilidade: {self.compatibilidade}%.
Data da reserva: {self.dataReserva.strftime("%d/%m/%Y %H:%M")}.
Data de expiração: {self.dataExpiracao.strftime("%d/%m/%Y %H:%M")}.
Status: {self.status}.
"""

    def __repr__(self):
        return f"Reserva(id={self.id}, adotante={self.adotante.nome}, animal={self.animal.nome}, compatibilidade={self.compatibilidade}, dataReserva={self.dataReserva.strftime('%d/%m/%Y %H:%M')}, dataExpiracao={self.dataExpiracao.strftime('%d/%m/%Y %H:%M')}, status={self.status})"

    def __eq__(self, outra_reserva):
        if not isinstance(outra_reserva, Reserva):
            return False
        return self.id == outra_reserva.id

    def __hash__(self):
        return hash(self.id)
