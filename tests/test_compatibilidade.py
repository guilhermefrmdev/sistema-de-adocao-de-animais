import json
from datetime import date

import pytest  # type: ignore

from sistema_de_adocao_de_animais.domain.adotante import Adotante
from sistema_de_adocao_de_animais.domain.cachorro import Cachorro
from sistema_de_adocao_de_animais.domain.gato import Gato
from sistema_de_adocao_de_animais.enums.moradias import Moradia
from sistema_de_adocao_de_animais.enums.nivel_independencia import NivelIndependencia
from sistema_de_adocao_de_animais.enums.porte_animal import PorteAnimal
from sistema_de_adocao_de_animais.enums.tipos_pelos import TiposPelos
from sistema_de_adocao_de_animais.settings import DEFAULT_PATH, load_settings
from sistema_de_adocao_de_animais.strategies.compatibilidade_strategy import (
    CompatibilidadePonderada,
    CompatibilidadeStrategy,
)


def _adotante(**kwargs):
    padrao = dict(
        nome="Maria",
        idade=30,
        telefone="88999999999",
        moradia=Moradia.CASA,
        areaUtil=100.0,
        experiencia=True,
        criancasEmCasa=False,
        outrosAnimais=False,
    )
    padrao.update(kwargs)
    return Adotante(**padrao)


def _cachorro(**kwargs):
    padrao = dict(
        nome="Rex",
        idade=36,
        raca="SRD",
        sexo="M",
        porte=PorteAnimal.MEDIO,
        peso=10,
        data_entrada=date(2026, 1, 1),
        temperamento=[],
        historico=[],
    )
    padrao.update(kwargs)
    return Cachorro(**padrao)


def _gato(**kwargs):
    padrao = dict(
        nome="Mia",
        idade=36,
        raca="SRD",
        sexo="F",
        temperamento=[],
        porte=PorteAnimal.PEQUENO,
        peso=4,
        independencia=NivelIndependencia.MEDIA,
        tipoPelo=TiposPelos.CURTO,
        data_entrada=date(2026, 1, 1),
        historico=[],
    )
    padrao.update(kwargs)
    return Gato(**padrao)


@pytest.fixture
def estrategia():
    return CompatibilidadePonderada(load_settings())


def test_cenario_ideal_da_100(estrategia):
    assert estrategia.calcular(_adotante(), _cachorro()) == 100.0


def test_score_sempre_entre_0_e_100(estrategia):
    pior = estrategia.calcular(
        _adotante(
            idade=80,
            moradia=Moradia.APARTAMENTO,
            areaUtil=5.0,
            experiencia=False,
            criancasEmCasa=True,
        ),
        _cachorro(
            idade=3,
            porte=PorteAnimal.GIGANTE,
            necessidadePasseio=True,
            temperamento=["arisco"],
        ),
    )
    assert 0 <= pior <= 100


def test_porte_grande_em_apartamento_pequeno_pontua_pouco(estrategia):
    adotante = _adotante(moradia=Moradia.APARTAMENTO, areaUtil=20.0)
    resultado = estrategia.detalhar(adotante, _cachorro(porte=PorteAnimal.GRANDE))
    assert resultado.detalhes["porte_moradia"] < 0.25


def test_area_maior_melhora_nota(estrategia):
    animal = _cachorro(porte=PorteAnimal.GRANDE)
    pequena = estrategia.calcular(_adotante(areaUtil=10.0), animal)
    grande = estrategia.calcular(_adotante(areaUtil=80.0), animal)
    assert grande > pequena


def test_filhote_com_adotante_idoso_penaliza(estrategia):
    resultado = estrategia.detalhar(_adotante(idade=70), _cachorro(idade=4))
    assert resultado.detalhes["idade_energia"] == pytest.approx(0.25)


def test_cachorro_com_necessidade_de_passeio_tem_mais_energia(estrategia):
    adotante = _adotante(idade=60)  # capacidade 3
    sem = estrategia.detalhar(adotante, _cachorro(necessidadePasseio=False))
    com = estrategia.detalhar(adotante, _cachorro(necessidadePasseio=True))
    assert sem.detalhes["idade_energia"] == 1.0
    assert com.detalhes["idade_energia"] == pytest.approx(0.75)


def test_gato_independente_exige_menos_energia(estrategia):
    adotante = _adotante(idade=70)  # capacidade 2
    alta = _gato(independencia=NivelIndependencia.ALTA)
    baixa = _gato(independencia=NivelIndependencia.BAIXA)
    assert estrategia.detalhar(adotante, alta).detalhes["idade_energia"] == 1.0
    assert estrategia.detalhar(adotante, baixa).detalhes["idade_energia"] == 0.5


def test_sem_experiencia_com_animal_arisco(estrategia):
    adotante = _adotante(experiencia=False)
    resultado = estrategia.detalhar(adotante, _cachorro(temperamento=["arisco"]))
    assert resultado.detalhes["experiencia"] == 0.3


def test_temperamento_ignora_acento_e_maiuscula(estrategia):
    adotante = _adotante(criancasEmCasa=True)
    docil = estrategia.detalhar(adotante, _cachorro(temperamento=[" DÓCIL "]))
    arisco = estrategia.detalhar(adotante, _cachorro(temperamento=["Arisco"]))
    assert docil.detalhes["criancas"] == 1.0
    assert arisco.detalhes["criancas"] == 0.2


def test_criancas_reduzem_nota_de_animal_arisco(estrategia):
    animal = _cachorro(temperamento=["arisco"])
    sem = estrategia.calcular(_adotante(criancasEmCasa=False), animal)
    com = estrategia.calcular(_adotante(criancasEmCasa=True), animal)
    assert com < sem


def test_criancas_com_animal_sem_temperamento_conhecido_e_neutro(estrategia):
    resultado = estrategia.detalhar(_adotante(criancasEmCasa=True), _cachorro())
    assert resultado.detalhes["criancas"] == 0.7


def test_calcular_e_detalhar_concordam(estrategia):
    adotante, animal = _adotante(idade=58), _gato()
    assert estrategia.calcular(adotante, animal) == (
        estrategia.detalhar(adotante, animal).score
    )


def test_pesos_do_settings_mudam_o_resultado(tmp_path):
    config = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
    config["compatibilidade"]["pesos"] = {
        "porte_moradia": 0,
        "idade_energia": 0,
        "experiencia": 0,
        "criancas": 10,
    }
    caminho = tmp_path / "settings.json"
    caminho.write_text(json.dumps(config), encoding="utf-8")

    estrategia = CompatibilidadePonderada(load_settings(caminho))
    adotante = _adotante(criancasEmCasa=True)
    # Só o critério "criancas" conta: animal arisco com crianças = 0,2 -> 20.
    assert estrategia.calcular(adotante, _cachorro(temperamento=["arisco"])) == 20.0


def test_strategy_base_e_abstrata():
    with pytest.raises(TypeError):
        CompatibilidadeStrategy()
