"""Testes de integração dos comandos do grupo adotante."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sistema_de_adocao_de_animais.cli.commands import adotante, animal
from sistema_de_adocao_de_animais.cli.main import app

runner = CliRunner()


@pytest.fixture
def banco_temporario(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    caminho = tmp_path / "adocao.db"
    monkeypatch.setattr(adotante, "DB_PATH", caminho)
    monkeypatch.setattr(animal, "DB_PATH", caminho)
    return caminho


def cadastrar_adotante() -> object:
    return runner.invoke(
        app,
        [
            "adotante",
            "cadastrar",
            "Maria Silva",
            "30",
            "88999999999",
            "CASA",
            "80",
            "--experiencia",
            "--criancas-em-casa",
        ],
    )


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
            "--temperamento",
            "docil",
        ],
    )


def test_cadastrar_listar_e_ver_adotante(banco_temporario: Path) -> None:
    resultado = cadastrar_adotante()
    assert resultado.exit_code == 0, resultado.output
    assert "cadastrado com sucesso" in resultado.output
    assert "Maria" in runner.invoke(app, ["adotante", "listar"]).output
    consulta = runner.invoke(app, ["adotante", "ver", "1"])
    assert consulta.exit_code == 0
    assert "88999999999" in consulta.output


def test_atualizar_apenas_campos_informados(banco_temporario: Path) -> None:
    assert cadastrar_adotante().exit_code == 0
    resultado = runner.invoke(
        app, ["adotante", "atualizar", "1", "--area-util", "100", "--sem-criancas"]
    )
    assert resultado.exit_code == 0, resultado.output
    consulta = runner.invoke(app, ["adotante", "ver", "1"])
    assert "100.0 m²" in consulta.output
    assert "Crianças em casa" in consulta.output and "Não" in consulta.output
    assert "Experiência com animais" in consulta.output and "Sim" in consulta.output


def test_validacao_de_telefone(banco_temporario: Path) -> None:
    resultado = runner.invoke(
        app, ["adotante", "cadastrar", "Maria Silva", "30", "123", "CASA", "80"]
    )
    assert resultado.exit_code == 1
    assert "telefone" in resultado.output.lower()


def test_elegibilidade_e_compatibilidade(banco_temporario: Path) -> None:
    assert cadastrar_adotante().exit_code == 0
    assert cadastrar_cachorro().exit_code == 0
    elegibilidade = runner.invoke(app, ["adotante", "elegivel", "1", "1"])
    assert elegibilidade.exit_code == 0, elegibilidade.output
    assert "Idade mínima" in elegibilidade.output
    assert "Moradia exigida" in elegibilidade.output
    compatibilidade = runner.invoke(app, ["adotante", "compatibilidade", "1", "1"])
    assert compatibilidade.exit_code == 0, compatibilidade.output
    assert "Pontuação final" in compatibilidade.output
    assert "Porte × moradia" in compatibilidade.output


def test_excluir_com_flag_sim(banco_temporario: Path) -> None:
    assert cadastrar_adotante().exit_code == 0
    resultado = runner.invoke(app, ["adotante", "excluir", "1", "--sim"])
    assert resultado.exit_code == 0, resultado.output
    consulta = runner.invoke(app, ["adotante", "ver", "1"])
    assert consulta.exit_code == 1
    assert "não encontrado" in consulta.output
