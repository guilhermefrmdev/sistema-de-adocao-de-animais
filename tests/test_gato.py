from datetime import date

import pytest

from src.domain.gato import Gato
from src.enums.nivel_independencia import NivelIndependencia
from src.enums.porte_animal import PorteAnimal
from src.enums.status_animal import StatusAnimal
from src.enums.tipos_pelos import TiposPelos


@pytest.fixture
def gato():
    return Gato(
        nome="Mimi",
        idade=24,
        raca="Siamês",
        sexo="F",
        status=StatusAnimal.DISPONIVEL,
        temperamento=["calmo", "carinhoso"],
        castrado=True,
        porte=PorteAnimal.PEQUENO,
        peso=4,
        data_entrada=date(2026, 10, 1),
        independencia=NivelIndependencia.ALTA,
        tipoPelo=TiposPelos.CURTO,
        id=1,
    )


def test_criacao_gato(gato):
    assert gato.nome == "Mimi"
    assert gato.idade == 24
    assert gato.raca == "Siamês"
    assert gato.sexo == "F"
    assert gato.status is StatusAnimal.DISPONIVEL
    assert gato.temperamento == ["calmo", "carinhoso"]
    assert gato.castrado is True
    assert gato.porte is PorteAnimal.PEQUENO
    assert gato.peso == 4
    assert gato.data_entrada == date(2026, 10, 1)
    assert gato.independencia is NivelIndependencia.ALTA
    assert gato.tipoPelo is TiposPelos.CURTO
    assert gato.historico == []


def test_independencia_deve_ser_enum(gato):
    with pytest.raises(ValueError):
        gato.independencia = "Alta"


def test_tipo_pelo_deve_ser_enum(gato):
    with pytest.raises(ValueError):
        gato.tipoPelo = "Curto"


def test_atualizacao_das_caracteristicas(gato):
    gato.independencia = NivelIndependencia.BAIXA
    gato.tipoPelo = TiposPelos.LONGO

    assert gato.independencia is NivelIndependencia.BAIXA
    assert gato.tipoPelo is TiposPelos.LONGO


def test_status_deve_ser_enum(gato):
    with pytest.raises(ValueError):
        gato.status = "Disponível"


def test_peso_deve_ser_maior_que_zero(gato):
    with pytest.raises(ValueError):
        gato.peso = 0


def test_data_de_entrada_deve_ser_date(gato):
    with pytest.raises(ValueError):
        gato.data_entrada = "01/10/2026"


def test_mudanca_de_status(gato):
    gato.mudar_status(StatusAnimal.RESERVADO)
    gato.mudar_status(StatusAnimal.ADOTADO)

    assert gato.status is StatusAnimal.ADOTADO

def test_adicionar_historico(gato):
    gato.adicionar_historico({'tipo': "Vacinação", 'nome': "Antirrábica", 'data': date(2026, 10, 5)})

    assert len(gato.historico) == 1
    assert gato.historico[0] == {
        "tipo": "Vacinação",
        "nome": "Antirrábica",
        "data": date(2026, 10, 5),
    }

def test_equalidade_incorreta(gato):
    assert gato.__eq__("") == False
