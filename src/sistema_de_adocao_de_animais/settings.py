"""Carregamento e validação do arquivo ``settings.json``."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sistema_de_adocao_de_animais.enums.moradias import Moradia
from sistema_de_adocao_de_animais.enums.porte_animal import PorteAnimal

CRITERIOS = ("porte_moradia", "idade_energia", "experiencia", "criancas")

DEFAULT_PATH = Path(__file__).resolve().parent / "settings.json"


class ConfiguracaoInvalidaError(ValueError):
    """Levantada quando o settings.json está ausente, incompleto ou inconsistente."""


@dataclass(frozen=True)
class Settings:
    """Configurações tipadas da aplicação, lidas do ``settings.json``.

    Attributes:
        idade_minima_adotante (int): Idade mínima (anos) para adotar.
        portes_restritos (tuple of str): Nomes dos `PorteAnimal` com regra
            especial de moradia (ex.: GRANDE, GIGANTE).
        moradia_exigida (str): Nome do `Moradia` exigido para esses portes.
        area_minima_m2 (float): Área mínima (m²) exigida para esses portes.
        reserva_horas (int): Duração da reserva, em horas.
        compatibilidade (dict): Bloco de compatibilidade (já validado).
        taxas (dict): Bloco de taxas de adoção.
        fila_espera (dict): Bloco de configuração da fila de espera.
    """

    idade_minima_adotante: int
    portes_restritos: tuple[str, ...]
    moradia_exigida: str
    area_minima_m2: float
    reserva_horas: int
    compatibilidade: dict[str, Any]
    taxas: dict[str, Any]
    fila_espera: dict[str, Any]

    @property
    def pesos(self) -> dict[str, float]:
        """dict: Cópia dos pesos de compatibilidade."""
        return dict(self.compatibilidade["pesos"])


def _validar_compatibilidade(bloco: dict[str, Any]) -> None:
    """Valida o bloco ``compatibilidade``.

    Args:
        bloco (dict): Conteúdo da chave ``compatibilidade``.

    Raises:
        ConfiguracaoInvalidaError: Se faltar peso/combinação ou houver valor
            fora do intervalo permitido.
    """
    pesos = bloco.get("pesos", {})
    faltando = [c for c in CRITERIOS if c not in pesos]
    if faltando:
        raise ConfiguracaoInvalidaError(f"Pesos ausentes: {faltando}")
    if any(p < 0 for p in pesos.values()) or sum(pesos.values()) <= 0:
        raise ConfiguracaoInvalidaError("Os pesos devem ser >= 0 e somar > 0.")

    for moradia in Moradia:
        for porte in PorteAnimal:
            try:
                nota = bloco["porte_moradia"][moradia.name][porte.name]
            except KeyError as erro:
                raise ConfiguracaoInvalidaError(
                    f"porte_moradia[{moradia.name}][{porte.name}] ausente."
                ) from erro
            if not 0 <= nota <= 1:
                raise ConfiguracaoInvalidaError("As notas devem estar em [0, 1].")

    for porte in PorteAnimal:
        if bloco["area_ideal_m2"].get(porte.name, 0) <= 0:
            raise ConfiguracaoInvalidaError(f"area_ideal_m2[{porte.name}] inválida.")


def _validar_fila_espera(bloco: dict[str, Any]) -> None:
    """Valida o bloco ``fila_espera``.

    Raises:
        ConfiguracaoInvalidaError: Se os pesos forem inválidos ou o limite de
            dias não for positivo.
    """
    pesos = (bloco["peso_pontuacao"], bloco["peso_tempo_espera"])
    if any(p < 0 for p in pesos) or sum(pesos) <= 0:
        raise ConfiguracaoInvalidaError("Os pesos da fila devem ser >= 0 e somar > 0.")
    if bloco["dias_espera_max_normalizacao"] <= 0:
        raise ConfiguracaoInvalidaError("dias_espera_max_normalizacao deve ser > 0.")


def load_settings(path: str | Path = DEFAULT_PATH) -> Settings:
    """Lê e valida o ``settings.json``.

    Args:
        path (str | Path): Caminho do arquivo. Por padrão, o que fica ao lado
            deste módulo.

    Returns:
        Settings: Objeto imutável com as configurações.

    Raises:
        ConfiguracaoInvalidaError: Se o arquivo não puder ser lido, não for um
            JSON válido, tiver chave ausente ou valores inconsistentes.
    """
    try:
        bruto = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erro:
        raise ConfiguracaoInvalidaError(
            f"Não foi possível ler {path}: {erro}"
        ) from erro

    try:
        politicas = bruto["politicas"]
        restrito = politicas["porte_restrito"]
        _validar_compatibilidade(bruto["compatibilidade"])
        _validar_fila_espera(bruto["fila_espera"])
        settings = Settings(
            idade_minima_adotante=int(politicas["idade_minima_adotante"]),
            portes_restritos=tuple(restrito["portes"]),
            moradia_exigida=str(restrito["moradia_exigida"]),
            area_minima_m2=float(restrito["area_minima_m2"]),
            reserva_horas=int(bruto["reserva_horas"]),
            compatibilidade=bruto["compatibilidade"],
            taxas=bruto["taxas"],
            fila_espera=bruto["fila_espera"],
        )
    except KeyError as erro:
        raise ConfiguracaoInvalidaError(f"Chave ausente no settings: {erro}") from erro

    if settings.reserva_horas <= 0:
        raise ConfiguracaoInvalidaError("reserva_horas deve ser maior que zero.")
    return settings
