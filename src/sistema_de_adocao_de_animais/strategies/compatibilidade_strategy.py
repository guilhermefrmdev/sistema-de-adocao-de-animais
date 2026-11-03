from __future__ import annotations

import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable

from sistema_de_adocao_de_animais.domain.adotante import Adotante
from sistema_de_adocao_de_animais.domain.animal import Animal
from sistema_de_adocao_de_animais.settings import Settings


@dataclass(frozen=True)
class ResultadoCompatibilidade:
    """Resultado detalhado do cálculo de compatibilidade.

    Attributes:
        score (float): Nota final, entre 0 e 100.
        detalhes (dict): Nota de cada critério, entre 0 e 1.
    """

    score: float
    detalhes: dict[str, float] = field(default_factory=dict)


class CompatibilidadeStrategy(ABC):
    """Estratégia do cálculo da compatibilidade Animal x Adotante.

    Subclasses definem como a nota é calculada; quem usa só depende de
    `calcular`, o que permite trocar o algoritmo sem mexer no domínio.
    """

    @abstractmethod
    def calcular(self, adotante: Adotante, animal: Animal) -> float:
        """Calcula a compatibilidade entre um adotante e um animal.

        Args:
            adotante (Adotante): O adotante avaliado.
            animal (Animal): O animal avaliado.

        Returns:
            float: Nota entre 0 e 100.
        """


class CompatibilidadePonderada(CompatibilidadeStrategy):
    """Soma ponderada de quatro critérios, com pesos vindos do settings.json.

    ``score = 100 * soma(peso_i * nota_i) / soma(pesos)``

    Dividir pela soma dos pesos mantém o resultado entre 0 e 100 mesmo que os
    pesos do arquivo não somem exatamente 100.

    Critérios (cada um vale de 0 a 1):
        - porte_moradia: tipo de moradia x porte, atenuado pela área útil.
        - idade_energia: energia do animal x capacidade do adotante pela idade.
        - experiencia: experiência com animais x temperamento exigente.
        - criancas: crianças em casa x temperamento arriscado/amigável.

    Args:
        settings (Settings): Configurações já carregadas e validadas.
    """

    def __init__(self, settings: Settings) -> None:
        self._cfg = settings.compatibilidade
        self._pesos = settings.pesos
        self._arriscados = self._normalizar_todos(self._cfg["temperamentos_arriscados"])
        self._exigentes = self._normalizar_todos(self._cfg["temperamentos_exigentes"])
        self._amigaveis = self._normalizar_todos(self._cfg["temperamentos_amigaveis"])

    # Interface pública
    def calcular(self, adotante: Adotante, animal: Animal) -> float:
        """Calcula a nota final (0–100). Veja `detalhar` para a explicação."""
        return self.detalhar(adotante, animal).score

    def detalhar(self, adotante: Adotante, animal: Animal) -> ResultadoCompatibilidade:
        """Calcula a nota final e a nota de cada critério.

        Args:
            adotante (Adotante): O adotante avaliado.
            animal (Animal): O animal avaliado.

        Returns:
            ResultadoCompatibilidade: Nota final (0–100) e notas por critério (0–1).
        """
        notas = {
            "porte_moradia": self._porte_moradia(adotante, animal),
            "idade_energia": self._idade_energia(adotante, animal),
            "experiencia": self._experiencia(adotante, animal),
            "criancas": self._criancas(adotante, animal),
        }
        total = sum(self._pesos.values())
        bruto = sum(self._pesos[criterio] * nota for criterio, nota in notas.items())
        score = max(0.0, min(100.0, 100.0 * bruto / total))
        return ResultadoCompatibilidade(round(score, 1), notas)

    # Critérios
    def _porte_moradia(self, adotante: Adotante, animal: Animal) -> float:
        """Tabela moradia x porte, reduzida quando a área é menor que a ideal."""
        base = self._cfg["porte_moradia"][adotante.moradia.name][animal.porte.name]
        ideal = self._cfg["area_ideal_m2"][animal.porte.name]
        fator_area = min(1.0, max(0.0, adotante.areaUtil) / ideal)
        return base * (0.5 + 0.5 * fator_area)

    def _idade_energia(self, adotante: Adotante, animal: Animal) -> float:
        """Penaliza quando a energia do animal passa da capacidade do adotante."""
        excesso = max(
            0, self._energia_animal(animal) - self._capacidade_adotante(adotante.idade)
        )
        return 1.0 - excesso / 4.0  # diferença máxima possível: 5 contra 1

    def _experiencia(self, adotante: Adotante, animal: Animal) -> float:
        exigente = self._tem_algum(animal, self._exigentes)
        bloco = self._cfg["experiencia"][
            "animal_exigente" if exigente else "animal_comum"
        ]
        return bloco["com_experiencia" if adotante.experiencia else "sem_experiencia"]

    def _criancas(self, adotante: Adotante, animal: Animal) -> float:
        notas = self._cfg["criancas"]
        if not adotante.criancasEmCasa:
            return notas["sem_criancas"]
        if self._tem_algum(animal, self._arriscados):
            return notas["com_criancas_arriscado"]
        if self._tem_algum(animal, self._amigaveis):
            return notas["com_criancas_amigavel"]
        return notas["com_criancas_neutro"]

    # Auxiliares
    def _energia_animal(self, animal: Animal) -> int:
        """Nível de energia (1–5) a partir da idade e das características."""
        cfg = self._cfg["energia"]
        if animal.idade < cfg["idade_filhote_meses"]:
            fase = "filhote"
        elif animal.idade >= cfg["idade_senior_meses"]:
            fase = "senior"
        else:
            fase = "adulto"
        nivel = int(cfg["padrao_por_fase"][fase])

        # Atributos específicos: Cachorro.necessidadePasseio e Gato.independencia
        if getattr(animal, "necessidadePasseio", False):
            nivel += int(cfg["ajuste_necessidade_passeio"])
        independencia = getattr(animal, "independencia", None)
        if independencia is not None:
            nivel += int(cfg["ajuste_independencia"][independencia.name])
        return max(1, min(5, nivel))

    def _capacidade_adotante(self, idade: int) -> int:
        faixas = self._cfg["energia"]["capacidade_adotante_por_idade"]
        for faixa in faixas:
            if idade <= faixa["idade_ate"]:
                return int(faixa["nivel"])
        return int(faixas[-1]["nivel"])

    def _tem_algum(self, animal: Animal, termos: frozenset[str]) -> bool:
        return any(self._normalizar(t) in termos for t in animal.temperamento)

    @staticmethod
    def _normalizar(texto: object) -> str:
        """Remove acentos, espaços nas pontas e maiúsculas ("Dócil " -> "docil")."""
        sem_acento = (
            unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
        )
        return sem_acento.strip().lower()

    @classmethod
    def _normalizar_todos(cls, textos: Iterable[object]) -> frozenset[str]:
        return frozenset(cls._normalizar(t) for t in textos)
