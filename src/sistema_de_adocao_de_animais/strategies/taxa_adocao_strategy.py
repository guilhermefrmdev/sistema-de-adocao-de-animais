from __future__ import annotations

from abc import ABC, abstractmethod

from sistema_de_adocao_de_animais.domain.animal import Animal
from sistema_de_adocao_de_animais.settings import ConfiguracaoInvalidaError, Settings


class TaxaAdocaoStrategy(ABC):
    """Estratégia do cálculo da taxa de adoção.

    Subclasses definem como a taxa é calculada; quem usa só depende de
    `calcular`, o que permite trocar a regra (configurada em
    ``settings.json``, bloco ``taxas``) sem mexer no domínio.

    Args:
        settings (Settings): Configurações já carregadas e validadas.

    Raises:
        ConfiguracaoInvalidaError: Se o bloco ``taxas`` estiver incompleto ou
            tiver valores inválidos (negativos, desconto fora de 0–1).
    """

    def __init__(self, settings: Settings) -> None:
        self._cfg = settings.taxas
        self._valor_base = self._numero(self._cfg, "valor_base", "taxas")

    @abstractmethod
    def calcular(self, animal: Animal) -> float:
        """Calcula a taxa de adoção de um animal.

        Args:
            animal (Animal): O animal que será adotado.

        Returns:
            float: Valor da taxa, em reais, com duas casas decimais e nunca
            negativo.
        """

    # Auxiliares
    @staticmethod
    def _numero(bloco: dict, chave: str, caminho: str, maximo: float | None = None):
        """Lê um número >= 0 (e <= ``maximo``, se informado) do settings."""
        try:
            valor = float(bloco[chave])
        except (KeyError, TypeError, ValueError) as erro:
            raise ConfiguracaoInvalidaError(
                f"{caminho}.{chave} ausente ou inválido."
            ) from erro
        if valor < 0 or (maximo is not None and valor > maximo):
            limite = f"entre 0 e {maximo}" if maximo is not None else ">= 0"
            raise ConfiguracaoInvalidaError(f"{caminho}.{chave} deve ser {limite}.")
        return valor

    @staticmethod
    def _arredondar(valor: float) -> float:
        return round(valor, 2)


class BaseFee(TaxaAdocaoStrategy):
    """Taxa padrão: o ``valor_base`` do settings, sem ajustes."""

    def calcular(self, animal: Animal) -> float:
        return self._arredondar(self._valor_base)


class SeniorFee(TaxaAdocaoStrategy):
    """Taxa com desconto para animais sênior.

    ``taxa = valor_base * (1 - desconto)`` quando a idade do animal (em meses)
    é maior ou igual a ``taxas.senior.idade_minima_meses``. Para os demais
    animais, cobra a taxa base.
    """

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        cfg = settings.taxas.get("senior", {})
        self._idade_minima = self._numero(cfg, "idade_minima_meses", "taxas.senior")
        self._desconto = self._numero(cfg, "desconto", "taxas.senior", maximo=1)

    def calcular(self, animal: Animal) -> float:
        if animal.idade >= self._idade_minima:
            return self._arredondar(self._valor_base * (1 - self._desconto))
        return self._arredondar(self._valor_base)


class PuppyFee(TaxaAdocaoStrategy):
    """Taxa de filhote: base + custo das vacinas.

    ``taxa = valor_base + custo_vacinas`` quando a idade do animal (em meses)
    é menor ou igual a ``taxas.filhote.idade_maxima_meses``. Para os demais
    animais, cobra a taxa base.
    """

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        cfg = settings.taxas.get("filhote", {})
        self._idade_maxima = self._numero(cfg, "idade_maxima_meses", "taxas.filhote")
        self._custo_vacinas = self._numero(cfg, "custo_vacinas", "taxas.filhote")

    def calcular(self, animal: Animal) -> float:
        if animal.idade <= self._idade_maxima:
            return self._arredondar(self._valor_base + self._custo_vacinas)
        return self._arredondar(self._valor_base)


class SpecialCareFee(TaxaAdocaoStrategy):
    """Taxa para animais que precisam de tratamento: base + custo do tratamento.

    Vale para qualquer animal; quem escolhe esta estratégia é que decide que o
    animal precisa de cuidados especiais.
    """

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        cfg = settings.taxas.get("especial", {})
        self._custo_tratamento = self._numero(cfg, "custo_tratamento", "taxas.especial")

    def calcular(self, animal: Animal) -> float:
        return self._arredondar(self._valor_base + self._custo_tratamento)


ESTRATEGIAS: dict[str, type[TaxaAdocaoStrategy]] = {
    "padrao": BaseFee,
    "senior": SeniorFee,
    "filhote": PuppyFee,
    "especial": SpecialCareFee,
}


def criar_estrategia(settings: Settings, nome: str | None = None) -> TaxaAdocaoStrategy:
    """Cria a estratégia de taxa pelo nome.

    Args:
        settings (Settings): Configurações já carregadas.
        nome (str, optional): ``padrao``, ``senior``, ``filhote`` ou
            ``especial``. Se omitido, usa ``taxas.estrategia_padrao``.

    Returns:
        TaxaAdocaoStrategy: A estratégia pronta para usar.

    Raises:
        ConfiguracaoInvalidaError: Se o nome não existir.
    """
    if nome is None:
        nome = settings.taxas.get("estrategia_padrao", "padrao")
    chave = str(nome).strip().lower()
    if chave not in ESTRATEGIAS:
        raise ConfiguracaoInvalidaError(
            f"Estratégia de taxa desconhecida: {nome!r}. Use: {', '.join(ESTRATEGIAS)}."
        )
    return ESTRATEGIAS[chave](settings)
