from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterator

from sistema_de_adocao_de_animais.domain.adotante import Adotante
from sistema_de_adocao_de_animais.domain.animal import Animal
from sistema_de_adocao_de_animais.repositories.fila_de_espera_repository import (
    FilaDeEsperaRepository,
)
from sistema_de_adocao_de_animais.settings import Settings

Observador = Callable[["EntradaFila", Animal], None]


@dataclass(eq=False)
class EntradaFila:
    """Um adotante esperando por um animal.

    A ordenação (`__lt__`) segue a prioridade: "menor" significa "mais
    prioritário", então `sorted(entradas)` já devolve a ordem da fila.

    Attributes:
        adotante (Adotante): Quem está esperando.
        compatibilidade (float): Pontuação adotante-animal (0–100) no momento
            em que entrou na fila.
        data_entrada (datetime): Quando entrou na fila.
        prioridade (float): Prioridade (0–100) calculada pela última chamada de
            `FilaDeEspera.atualizar_lista`.
    """

    adotante: Adotante
    compatibilidade: float
    data_entrada: datetime
    prioridade: float = 0.0

    # Métodos especiais
    def __eq__(self, outra: object) -> bool:
        if not isinstance(outra, EntradaFila):
            return False
        return self.adotante.id == outra.adotante.id

    def __hash__(self) -> int:
        return hash(self.adotante.id)

    def __lt__(self, outra: object) -> bool:
        if not isinstance(outra, EntradaFila):
            return NotImplemented
        # Maior prioridade primeiro; empate: quem entrou antes; depois, menor id.
        return (-self.prioridade, self.data_entrada, self.adotante.id) < (
            -outra.prioridade,
            outra.data_entrada,
            outra.adotante.id,
        )


class FilaDeEspera(FilaDeEsperaRepository):
    """Representa a fila de espera de um determinado animal.

    A prioridade de cada adotante combina a compatibilidade e o tempo de espera,
    com pesos lidos do ``settings.json`` (bloco ``fila_espera``)::

        prioridade = (peso_pontuacao * compatibilidade
                      + peso_tempo_espera * tempo) / (peso_pontuacao + peso_tempo_espera)

    onde ``tempo`` vai de 0 a 100 e chega a 100 após
    ``dias_espera_max_normalizacao`` dias de espera. Passado esse limite, esperar
    mais não aumenta a prioridade.

    Attributes:
        animal (Animal): O animal relacionado com essa fila de espera.
        fila (list of EntradaFila): Os adotantes em espera, do mais prioritário
            para o menos prioritário (a partir da última atualização).
    """

    def __init__(
        self,
        animal: Animal,
        settings: Settings,
        fila: list[EntradaFila] | None = None,
    ):
        if not isinstance(animal, Animal):
            raise ValueError("O animal deve ser uma instância de Animal.")
        config = settings.fila_espera
        self._animal = animal
        self._peso_pontuacao = float(config["peso_pontuacao"])
        self._peso_tempo = float(config["peso_tempo_espera"])
        self._dias_maximos = float(config["dias_espera_max_normalizacao"])
        self._observadores: list[Observador] = []
        self.fila: list[EntradaFila] = fila if fila is not None else []

    # Propriedades
    @property
    def animal(self) -> Animal:
        return self._animal

    @property
    def animal_id(self) -> int:
        return self._animal.id

    # Atualizar fila
    def atualizar_lista(self, agora: datetime | None = None) -> None:
        """Recalcula a prioridade de cada entrada e reordena a fila.

        Como o tempo de espera muda com o passar dos dias, a ordem pode mudar
        mesmo sem ninguém entrar ou sair.

        Args:
            agora (datetime, optional): Momento de referência (útil em testes).
        """
        agora = agora if agora is not None else datetime.now()
        for entrada in self.fila:
            entrada.prioridade = self._calcular_prioridade(entrada, agora)
        self.fila.sort()

    def _calcular_prioridade(self, entrada: EntradaFila, agora: datetime) -> float:
        dias = max(0.0, (agora - entrada.data_entrada).total_seconds() / 86400)
        tempo = min(1.0, dias / self._dias_maximos) * 100
        bruto = (
            self._peso_pontuacao * entrada.compatibilidade + self._peso_tempo * tempo
        )
        return round(bruto / (self._peso_pontuacao + self._peso_tempo), 6)

    # Adicionar e remover da fila
    def adicionar(
        self,
        adotante: Adotante,
        compatibilidade: float,
        agora: datetime | None = None,
    ) -> EntradaFila:
        """Coloca um adotante na fila.

        Args:
            adotante (Adotante): Quem vai esperar (precisa ter `id`).
            compatibilidade (float): Pontuação adotante-animal, de 0 a 100.
            agora (datetime, optional): Momento da entrada (útil em testes).

        Returns:
            EntradaFila: A entrada criada.

        Raises:
            ValueError: Se o adotante não tiver id, se já estiver na fila ou se a
                compatibilidade estiver fora de 0–100.
        """
        if adotante.id is None:
            raise ValueError("O adotante precisa estar cadastrado (sem id).")
        if not 0 <= compatibilidade <= 100:
            raise ValueError("A compatibilidade deve estar entre 0 e 100.")
        if adotante in self:
            raise ValueError("O adotante já está na fila deste animal.")

        agora = agora if agora is not None else datetime.now()
        entrada = EntradaFila(adotante, float(compatibilidade), agora)
        self.fila.append(entrada)
        self.atualizar_lista(agora)
        return entrada

    def remover(self, adotante: Adotante) -> EntradaFila:
        """Tira um adotante da fila (ex.: quando ele reserva o animal).

        Raises:
            ValueError: Se o adotante não estiver na fila.
        """
        for posicao, entrada in enumerate(self.fila):
            if entrada.adotante.id == adotante.id:
                return self.fila.pop(posicao)
        raise ValueError("O adotante não está na fila deste animal.")

    # Consultas
    def proximo(self, agora: datetime | None = None) -> EntradaFila | None:
        """Devolve (sem remover) o adotante mais prioritário, ou `None`."""
        self.atualizar_lista(agora)
        return self.fila[0] if self.fila else None

    def posicao(self, adotante: Adotante, agora: datetime | None = None) -> int:
        """Posição do adotante na fila (1 = próximo).

        Raises:
            ValueError: Se o adotante não estiver na fila.
        """
        self.atualizar_lista(agora)
        for posicao, entrada in enumerate(self.fila, start=1):
            if entrada.adotante.id == adotante.id:
                return posicao
        raise ValueError("O adotante não está na fila deste animal.")

    # Notificação (Observer)
    def registrar_observador(self, observador: Observador) -> None:
        """Registra uma função chamada sempre que o próximo da fila é notificado.

        Args:
            observador (Callable): Recebe `(entrada, animal)`.
        """
        self._observadores.append(observador)

    def notificar_proximo(self, agora: datetime | None = None) -> EntradaFila | None:
        """Notifica o próximo da fila (chame quando uma reserva expirar).

        Registra um evento no histórico do animal e avisa os observadores
        registrados. Não retira o adotante da fila: isso acontece em `remover`,
        quando ele de fato reservar o animal.

        Args:
            agora (datetime, optional): Momento da notificação (útil em testes).

        Returns:
            EntradaFila | None: O adotante notificado, ou `None` se a fila estiver
            vazia.
        """
        agora = agora if agora is not None else datetime.now()
        entrada = self.proximo(agora)
        if entrada is None:
            return None

        self._animal.adicionar_historico(
            {
                "tipo": "FILA_ESPERA",
                "nome": f"Vaga liberada: {entrada.adotante.nome} é o próximo da fila",
                "data": agora.date(),
            }
        )
        for observador in self._observadores:
            observador(entrada, self._animal)
        return entrada

    # Métodos especiais
    def __len__(self) -> int:
        return len(self.fila)

    def __iter__(self) -> Iterator[EntradaFila]:
        self.atualizar_lista()
        yield from list(self.fila)

    def __contains__(self, adotante: object) -> bool:
        if not isinstance(adotante, Adotante):
            return False
        return any(entrada.adotante.id == adotante.id for entrada in self.fila)

    def __repr__(self) -> str:
        return f"FilaDeEspera(animal_id={self.animal_id}, tamanho={len(self)})"
