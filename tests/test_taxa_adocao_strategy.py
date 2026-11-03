from dataclasses import replace
from datetime import date

import pytest  # type: ignore

from sistema_de_adocao_de_animais.domain.cachorro import Cachorro
from sistema_de_adocao_de_animais.enums.porte_animal import PorteAnimal
from sistema_de_adocao_de_animais.settings import (
    ConfiguracaoInvalidaError,
    load_settings,
)
from sistema_de_adocao_de_animais.strategies.taxa_adocao_strategy import (
    BaseFee,
    PuppyFee,
    SeniorFee,
    SpecialCareFee,
    TaxaAdocaoStrategy,
    criar_estrategia,
)


def _animal(idade: int) -> Cachorro:
    return Cachorro(
        nome="Rex",
        idade=idade,
        raca="SRD",
        sexo="M",
        porte=PorteAnimal.MEDIO,
        peso=10,
        data_entrada=date(2026, 1, 1),
        temperamento=[],
        historico=[],
        id=1,
    )


@pytest.fixture
def settings():
    return load_settings()


def _com_taxas(settings, **mudancas):
    """Cópia do settings com o bloco ``taxas`` alterado."""
    taxas = {**settings.taxas, **mudancas}
    return replace(settings, taxas=taxas)


def test_interface_e_abstrata(settings):
    with pytest.raises(TypeError):
        TaxaAdocaoStrategy(settings)


def test_base_cobra_valor_base(settings):
    assert BaseFee(settings).calcular(_animal(36)) == 100.0


def test_senior_aplica_desconto(settings):
    assert SeniorFee(settings).calcular(_animal(120)) == 50.0


def test_senior_no_limite_da_idade_minima(settings):
    estrategia = SeniorFee(settings)
    assert estrategia.calcular(_animal(96)) == 50.0
    assert estrategia.calcular(_animal(95)) == 100.0


def test_senior_em_animal_adulto_cobra_taxa_base(settings):
    assert SeniorFee(settings).calcular(_animal(36)) == 100.0


def test_filhote_soma_vacinas(settings):
    assert PuppyFee(settings).calcular(_animal(6)) == 180.0


def test_filhote_no_limite_da_idade_maxima(settings):
    estrategia = PuppyFee(settings)
    assert estrategia.calcular(_animal(12)) == 180.0
    assert estrategia.calcular(_animal(13)) == 100.0


def test_cuidado_especial_soma_tratamento(settings):
    assert SpecialCareFee(settings).calcular(_animal(36)) == 250.0


def test_valores_vem_do_settings(settings):
    custom = _com_taxas(settings, valor_base=200.0)
    assert BaseFee(custom).calcular(_animal(36)) == 200.0
    assert SeniorFee(custom).calcular(_animal(120)) == 100.0


def test_resultado_e_arredondado_em_duas_casas(settings):
    custom = _com_taxas(
        settings,
        valor_base=99.99,
        senior={**settings.taxas["senior"], "desconto": 0.333},
    )
    assert SeniorFee(custom).calcular(_animal(120)) == 66.69


def test_criar_estrategia_por_nome(settings):
    assert isinstance(criar_estrategia(settings, "senior"), SeniorFee)
    assert isinstance(criar_estrategia(settings, " Filhote "), PuppyFee)
    assert isinstance(criar_estrategia(settings, "especial"), SpecialCareFee)


def test_criar_estrategia_usa_a_padrao_do_settings(settings):
    assert isinstance(criar_estrategia(settings), BaseFee)
    custom = _com_taxas(settings, estrategia_padrao="senior")
    assert isinstance(criar_estrategia(custom), SeniorFee)


def test_criar_estrategia_desconhecida_levanta_erro(settings):
    with pytest.raises(ConfiguracaoInvalidaError):
        criar_estrategia(settings, "vip")


@pytest.mark.parametrize(
    "mudanca",
    [
        {"valor_base": -1},
        {"senior": {"idade_minima_meses": 96, "desconto": 1.5}},
        {"filhote": {"idade_maxima_meses": 12}},
        {"especial": {"custo_tratamento": -10}},
    ],
)
def test_configuracao_invalida_levanta_erro(settings, mudanca):
    custom = _com_taxas(settings, **mudanca)
    with pytest.raises(ConfiguracaoInvalidaError):
        for nome in ("padrao", "senior", "filhote", "especial"):
            criar_estrategia(custom, nome)
