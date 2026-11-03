"""Testes de integração dos comandos do grupo animal."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sistema_de_adocao_de_animais.cli.commands import animal
from sistema_de_adocao_de_animais.cli.main import app

runner = CliRunner()


@pytest.fixture
def banco_temporario(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    caminho = tmp_path / "animais.db"
    monkeypatch.setattr(animal, "DB_PATH", caminho)
    return caminho


def cadastrar_cachorro() -> object:
    return runner.invoke(
        app,
        [
            "animal",
            "cachorro",
            "cadastrar",
            "Rex",
            "24",
            "Labrador",
            "M",
            "18",
            "GRANDE",
            "--castrado",
        ],
    )


def test_cadastrar_e_listar_animal(banco_temporario: Path) -> None:
    resultado = cadastrar_cachorro()
    assert resultado.exit_code == 0
    assert "cadastrado com sucesso" in resultado.output

    resultado = runner.invoke(app, ["animal", "listar", "--especie", "cachorro"])
    assert resultado.exit_code == 0
    assert "Rex" in resultado.output


def test_transicao_invalida_nao_altera_status(banco_temporario: Path) -> None:
    assert cadastrar_cachorro().exit_code == 0
    resultado = runner.invoke(app, ["animal", "mudar-status", "1", "ADOTADO"])
    assert resultado.exit_code == 1
    assert "Transição inválida" in resultado.output
    consulta = runner.invoke(app, ["animal", "ver", "1"])
    assert "DISPONIVEL" in consulta.output


def test_vacina_aparece_no_historico(banco_temporario: Path) -> None:
    assert cadastrar_cachorro().exit_code == 0
    resultado = runner.invoke(app, ["animal", "vacinar", "1", "Antirrábica"])
    assert resultado.exit_code == 0
    historico = runner.invoke(app, ["animal", "historico", "1"])
    assert "VACINA" in historico.output
    assert "Antirrábica" in historico.output


def test_atualizar_campo_especifico(banco_temporario: Path) -> None:
    assert cadastrar_cachorro().exit_code == 0
    resultado = runner.invoke(app, ["animal", "atualizar", "1", "--nome", "Rex Junior"])
    assert resultado.exit_code == 0
    consulta = runner.invoke(app, ["animal", "ver", "1"])
    assert "Rex Junior" in consulta.output
