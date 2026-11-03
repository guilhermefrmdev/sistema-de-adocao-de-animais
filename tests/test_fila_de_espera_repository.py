import sqlite3
from datetime import date, datetime, timedelta

import pytest  # type: ignore

from sistema_de_adocao_de_animais.domain.adotante import Adotante
from sistema_de_adocao_de_animais.domain.cachorro import Cachorro
from sistema_de_adocao_de_animais.domain.fila_espera import FilaDeEspera
from sistema_de_adocao_de_animais.enums.moradias import Moradia
from sistema_de_adocao_de_animais.enums.porte_animal import PorteAnimal
from sistema_de_adocao_de_animais.exceptions.repositorio_error import (
    RepositorioError,
)
from sistema_de_adocao_de_animais.repositories.fila_de_espera_repository import (
    FilaDeEsperaRepository,
)
from sistema_de_adocao_de_animais.settings import load_settings

T0 = datetime(2026, 11, 2, 12, 0)


def _adotante(id: int) -> Adotante:
    return Adotante(
        nome="Ana",
        idade=30,
        telefone="88999999999",
        moradia=Moradia.CASA,
        areaUtil=100.0,
        id=id,
    )


def _cachorro(id: int = 1) -> Cachorro:
    return Cachorro(
        nome="Rex",
        idade=36,
        raca="SRD",
        sexo="M",
        porte=PorteAnimal.MEDIO,
        peso=10,
        data_entrada=date(2026, 1, 1),
        temperamento=[],
        historico=[],
        id=id,
    )


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Banco temporário com as tabelas-pai (animais e adotantes) já populadas."""
    caminho = tmp_path / "teste.db"
    with sqlite3.connect(caminho) as con:
        con.execute("CREATE TABLE animais (id INTEGER PRIMARY KEY)")
        con.execute("CREATE TABLE adotantes (pessoa_id INTEGER PRIMARY KEY)")
        con.executemany("INSERT INTO animais VALUES (?)", [(1,), (2,)])
        con.executemany("INSERT INTO adotantes VALUES (?)", [(i,) for i in range(1, 5)])
    con.close()
    # FilaDeEspera herda o repositório sem chamar super().__init__(),
    # então redirecionamos o caminho na própria classe.
    monkeypatch.setattr(FilaDeEsperaRepository, "caminho_db", caminho)
    return caminho


@pytest.fixture
def fila():
    return FilaDeEspera(_cachorro(), load_settings())


def _preencher(fila):
    fila.adicionar(_adotante(1), 60, T0)
    fila.adicionar(_adotante(2), 90, T0)
    fila.adicionar(_adotante(3), 75, T0)


def test_cria_tabela_sob_demanda(banco):
    FilaDeEsperaRepository().buscarPorIdAnimal(1)
    with sqlite3.connect(banco) as con:
        tabelas = {r[0] for r in con.execute("SELECT name FROM sqlite_master")}
    con.close()
    assert "fila_espera" in tabelas


def test_buscar_fila_inexistente_devolve_lista_vazia(banco):
    assert FilaDeEsperaRepository().buscarPorIdAnimal(1) == []


def test_salvar_e_buscar_preserva_ordem_e_dados(banco, fila):
    _preencher(fila)
    repo = FilaDeEsperaRepository()
    repo.salvar(fila)

    registros = repo.buscarPorIdAnimal(1)

    assert [r.adotante_id for r in registros] == [2, 3, 1]
    assert [r.posicao for r in registros] == [1, 2, 3]
    assert registros[0].compatibilidade == 90
    assert registros[0].data_entrada == T0
    assert registros[0].prioridade == fila.fila[0].prioridade


def test_fila_herda_repositorio_e_salva_a_si_mesma(banco, fila):
    _preencher(fila)
    fila.salvar()
    assert len(fila.buscarPorIdAnimal(1)) == 3


def test_salvar_substitui_o_que_havia(banco, fila):
    repo = FilaDeEsperaRepository()
    _preencher(fila)
    repo.salvar(fila)
    fila.remover(_adotante(2))
    repo.salvar(fila)

    assert [r.adotante_id for r in repo.buscarPorIdAnimal(1)] == [3, 1]


def test_salvar_nao_mexe_na_fila_de_outro_animal(banco, fila):
    repo = FilaDeEsperaRepository()
    outra = FilaDeEspera(_cachorro(id=2), load_settings())
    outra.adicionar(_adotante(4), 50, T0)
    repo.salvar(outra)
    _preencher(fila)
    repo.salvar(fila)
    repo.limparFila(1)

    assert repo.buscarPorIdAnimal(1) == []
    assert [r.adotante_id for r in repo.buscarPorIdAnimal(2)] == [4]


def test_salvar_e_atomico_em_caso_de_erro(banco, fila):
    repo = FilaDeEsperaRepository()
    fila.adicionar(_adotante(1), 60, T0)
    repo.salvar(fila)

    fila.adicionar(_adotante(99), 80, T0)  # adotante inexistente no banco
    with pytest.raises(RepositorioError):
        repo.salvar(fila)

    assert [r.adotante_id for r in repo.buscarPorIdAnimal(1)] == [1]


def test_salvar_animal_sem_id_levanta_erro(banco):
    fila = FilaDeEspera(_cachorro(id=None), load_settings())
    with pytest.raises(RepositorioError):
        fila.salvar()


def test_atualizar_lista_regrava_prioridade_e_posicao(banco, fila):
    repo = FilaDeEsperaRepository()
    _preencher(fila)
    repo.salvar(fila)

    # 30 dias depois o tempo de espera pesa e a prioridade muda.
    fila.atualizar_lista(T0 + timedelta(days=30))
    repo.atualizarLista(fila)

    registros = repo.buscarPorIdAnimal(1)
    assert [r.prioridade for r in registros] == [e.prioridade for e in fila.fila]
    assert all(r.prioridade > r.compatibilidade * 0.7 for r in registros)


def test_atualizar_lista_com_adotante_nao_salvo_levanta_erro(banco, fila):
    fila.adicionar(_adotante(1), 60, T0)
    with pytest.raises(RepositorioError):
        FilaDeEsperaRepository().atualizarLista(fila)


def test_remover_entrada_refaz_posicoes(banco, fila):
    repo = FilaDeEsperaRepository()
    _preencher(fila)
    repo.salvar(fila)

    repo.removerEntrada(1, 2)  # o primeiro da fila

    registros = repo.buscarPorIdAnimal(1)
    assert [r.adotante_id for r in registros] == [3, 1]
    assert [r.posicao for r in registros] == [1, 2]


def test_remover_entrada_inexistente_levanta_erro(banco):
    with pytest.raises(RepositorioError):
        FilaDeEsperaRepository().removerEntrada(1, 1)


def test_excluir_animal_apaga_a_fila_em_cascata(banco, fila):
    repo = FilaDeEsperaRepository()
    _preencher(fila)
    repo.salvar(fila)

    with repo.conectar() as con:
        con.execute("DELETE FROM animais WHERE id = 1")
    con.close()

    assert repo.buscarPorIdAnimal(1) == []
