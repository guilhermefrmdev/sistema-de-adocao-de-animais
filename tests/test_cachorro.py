from datetime import date

import pytest

from src.domain.cachorro import Cachorro
from src.enums.porte_animal import PorteAnimal
from src.enums.status_animal import StatusAnimal


@pytest.fixture
def cachorro():
    return Cachorro(
        nome="Rex",
        idade=36,
        raca="Labrador",
        sexo="M",
        status=StatusAnimal.DISPONIVEL,
        temperamento=["brincalhão", "dócil"],
        castrado=True,
        porte=PorteAnimal.GRANDE,
        peso=28,
        data_entrada=date(2026, 10, 1),
        necessidadePasseio=True,
        id=1,
    )


def test_criacao_cachorro(cachorro):
    assert cachorro.nome == "Rex"
    assert cachorro.idade == 36
    assert cachorro.raca == "Labrador"
    assert cachorro.sexo == "M"
    assert cachorro.status is StatusAnimal.DISPONIVEL
    assert cachorro.temperamento == ["brincalhão", "dócil"]
    assert cachorro.castrado is True
    assert cachorro.porte is PorteAnimal.GRANDE
    assert cachorro.peso == 28
    assert cachorro.data_entrada == date(2026, 10, 1)
    assert cachorro.necessidadePasseio is True
    assert cachorro.historico == []


def test_necessidade_de_passeio_deve_ser_booleana(cachorro):
    cachorro.necessidadePasseio = False
    assert cachorro.necessidadePasseio is False

    with pytest.raises(ValueError):
        cachorro.necessidadePasseio = "Sim"


def test_nome_invalido(cachorro):
    with pytest.raises(ValueError):
        cachorro.nome = "Rex123"


def test_idade_invalida(cachorro):
    with pytest.raises(ValueError):
        cachorro.idade = 0


def test_castrado_deve_ser_booleano(cachorro):
    with pytest.raises(ValueError):
        cachorro.castrado = "Sim"


def test_porte_deve_ser_enum(cachorro):
    with pytest.raises(ValueError):
        cachorro.porte = "Grande"


def test_adicionar_historico(cachorro):
    cachorro.adicionar_historico({'tipo': "Vacinação", 'nome': "Antirrábica", 'data': date(2026, 10, 5)})

    assert len(cachorro.historico) == 1
    assert cachorro.historico[0] == {
        "tipo": "Vacinação",
        "nome": "Antirrábica",
        "data": date(2026, 10, 5),
    }


def test_transicao_de_status(cachorro):
    cachorro.mudar_status(StatusAnimal.RESERVADO)
    cachorro.mudar_status(StatusAnimal.ADOTADO)
    cachorro.mudar_status(StatusAnimal.DEVOLVIDO)
    cachorro.mudar_status(StatusAnimal.QUARENTENA)
    cachorro.mudar_status(StatusAnimal.DISPONIVEL)

    assert cachorro.status is StatusAnimal.DISPONIVEL

def test_nome_vazio(cachorro):
    with pytest.raises(ValueError):
        cachorro.nome = " "

def test_mudar_raca(cachorro):
    with pytest.raises(ValueError):
        cachorro.raca = " "

def test_sexo_invalido(cachorro):
    with pytest.raises(ValueError):
        cachorro.sexo = " "

def test_temperamento_invalido(cachorro):
    with pytest.raises(ValueError):
        cachorro.temperamento = ""