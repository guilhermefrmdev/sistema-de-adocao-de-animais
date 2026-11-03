"""Testes de integração dos comandos da lista de espera."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sistema_de_adocao_de_animais.cli.commands import (
    adocao,
    adotante,
    animal,
    fila,
    reserva,
)
from sistema_de_adocao_de_animais.cli.main import app

runner = CliRunner()


@pytest.fixture
def banco_temporario(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    caminho = tmp_path / "fila.db"
    for modulo in (adocao, animal, adotante, fila, reserva):
        monkeypatch.setattr(modulo, "DB_PATH", caminho)
    return caminho


def preparar_dados() -> None:
    resultado = runner.invoke(
        app,
        [
            "adotante",
            "cadastrar",
            "Maria Silva",
            "30",
            "88999999999",
            "CASA",
            "100",
            "--experiencia",
        ],
    )
    assert resultado.exit_code == 0, resultado.output
    resultado = runner.invoke(
        app,
        [
            "adotante",
            "cadastrar",
            "João Souza",
            "35",
            "88988887777",
            "CASA",
            "80",
        ],
    )
    assert resultado.exit_code == 0, resultado.output
    resultado = runner.invoke(
        app,
        [
            "animal",
            "cachorro",
            "cadastrar",
            "Rex",
            "24",
            "SRD",
            "M",
            "18",
            "MEDIO",
            "--temperamento",
            "docil",
        ],
    )
    assert resultado.exit_code == 0, resultado.output


def test_entrar_calcula_compatibilidade_e_persiste(banco_temporario: Path) -> None:
    preparar_dados()
    resultado = runner.invoke(app, ["fila", "entrar", "1", "1"])
    assert resultado.exit_code == 0, resultado.output
    assert "Maria Silva entrou" in resultado.output
    assert "Compatibilidade:" in resultado.output
    lista = runner.invoke(app, ["fila", "ver", "1"])
    assert lista.exit_code == 0, lista.output
    assert "Maria Silva" in lista.output
    assert "Compatibilidade" in lista.output
    assert "Prioridade" in lista.output


def test_nao_permite_adotante_duplicado_na_fila(banco_temporario: Path) -> None:
    preparar_dados()
    assert runner.invoke(app, ["fila", "entrar", "1", "1"]).exit_code == 0
    resultado = runner.invoke(app, ["fila", "entrar", "1", "1"])
    assert resultado.exit_code == 1
    assert "já está na fila" in resultado.output


def test_sair_remove_adotante_e_refaz_posicoes(banco_temporario: Path) -> None:
    preparar_dados()
    assert runner.invoke(app, ["fila", "entrar", "1", "1"]).exit_code == 0
    assert runner.invoke(app, ["fila", "entrar", "2", "1"]).exit_code == 0
    resultado = runner.invoke(app, ["fila", "sair", "1", "1"])
    assert resultado.exit_code == 0, resultado.output
    assert "removido da lista de espera" in resultado.output
    lista = runner.invoke(app, ["fila", "ver", "1"])
    assert "João Souza" in lista.output
    assert "Maria Silva" not in lista.output
    assert "1" in lista.output


def test_ver_fila_vazia(banco_temporario: Path) -> None:
    preparar_dados()
    resultado = runner.invoke(app, ["fila", "ver", "1"])
    assert resultado.exit_code == 0, resultado.output
    assert "Ninguém está aguardando" in resultado.output


def test_sair_de_adotante_que_nao_esta_na_fila_falha(banco_temporario: Path) -> None:
    preparar_dados()
    resultado = runner.invoke(app, ["fila", "sair", "1", "1"])
    assert resultado.exit_code == 1
    assert "não está na fila" in resultado.output
