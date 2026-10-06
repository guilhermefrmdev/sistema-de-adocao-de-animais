import pytest

from src.domain.adotante import Adotante
from src.enums.moradias import Moradia


@pytest.fixture
def adotante():
    return Adotante(
        nome="Guilherme",
        idade=20,
        telefone="88999999999",
        moradia=Moradia.CASA,
        areaUtil=80.5,
        experiencia=True,
        criancasEmCasa=False,
        outrosAnimais=True,
        id=1,
    )


def test_criacao_adotante(adotante):
    assert adotante.nome == "Guilherme"
    assert adotante.idade == 20
    assert adotante.telefone == "88999999999"
    assert adotante.moradia == Moradia.CASA
    assert adotante.areaUtil == 80.5
    assert adotante.experiencia is True
    assert adotante.criancasEmCasa is False
    assert adotante.outrosAnimais is True


@pytest.mark.parametrize("telefone", ["8899999999", "889999999999", "8899999999a", ""])
def test_telefone_invalido(telefone):
    with pytest.raises(ValueError):
        Adotante(
            "Guilherme", 20, telefone, Moradia.CASA, 80.5, True, False, False
        )


def test_moradia_deve_ser_enum():
    with pytest.raises((ValueError, AttributeError)):
        Adotante(
            "Guilherme", 20, "88999999999", "Casa", 80.5, True, False, False
        )


def test_area_util_nao_pode_ser_zero():
    with pytest.raises(ValueError, match="área útil não pode ser zero"):
        Adotante(
            "Guilherme", 20, "88999999999", Moradia.CASA, 0.0, True, False, False
        )


def test_nome_e_idade_herdados():
    adotante = Adotante(
        "  Maria Silva  ", 25, "88999999999", Moradia.APARTAMENTO, 50.0, False, True, False
    )

    assert adotante.nome == "Maria Silva"
    assert adotante.idade == 25


def test_atualizacao_das_informacoes(adotante):
    adotante.telefone = "88988888888"
    adotante.areaUtil = 100.0
    adotante.experiencia = False
    adotante.criancasEmCasa = True
    adotante.outrosAnimais = False

    assert adotante.telefone == "88988888888"
    assert adotante.areaUtil == 100.0
    assert adotante.experiencia is False
    assert adotante.criancasEmCasa is True
    assert adotante.outrosAnimais is False


def test_igualdade_por_id():
    adotante1 = Adotante(
        "Ana", 25, "88999999999", Moradia.CASA, 70.0, True, False, False, id=10
    )
    adotante2 = Adotante(
        "Bruno", 30, "88888888888", Moradia.APARTAMENTO, 60.0, False, True, True, id=10
    )

    assert adotante1 == adotante2
