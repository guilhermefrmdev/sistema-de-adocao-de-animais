"""Testes de integração para configuração e carga de dados de demonstração."""

import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sistema_de_adocao_de_animais.cli.commands import (
    adocao,
    adotante,
    animal,
    fila,
    reserva,
    sistema,
)
from sistema_de_adocao_de_animais.cli.main import app

runner = CliRunner()


@pytest.fixture
def banco_temporario(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    caminho = tmp_path / "sistema.db"
    for modulo in (adocao, animal, adotante, fila, reserva, sistema):
        monkeypatch.setattr(modulo, "DB_PATH", caminho)
    return caminho


def test_config_mostrar_exibe_politicas() -> None:
    resultado = runner.invoke(app, ["config", "mostrar"])
    assert resultado.exit_code == 0, resultado.output
    assert "Idade mínima do adotante" in resultado.output
    assert "Duração da reserva" in resultado.output
    assert "Estratégia padrão de taxa" in resultado.output
    assert "Pesos da fila" in resultado.output


def test_seed_popula_animais_adotantes_reserva_e_fila(banco_temporario: Path) -> None:
    resultado = runner.invoke(app, ["seed"])
    assert resultado.exit_code == 0, resultado.output
    assert "Animais: 3" in resultado.output
    assert "Adotantes: 3" in resultado.output
    with sqlite3.connect(banco_temporario) as conn:
        assert conn.execute("SELECT COUNT(*) FROM animais").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM pessoas").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM reservas").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM fila_espera").fetchone()[0] == 2


def test_seed_repetido_nao_duplica_registros(banco_temporario: Path) -> None:
    assert runner.invoke(app, ["seed"]).exit_code == 0
    resultado = runner.invoke(app, ["seed"])
    assert resultado.exit_code == 0, resultado.output
    assert "já existem" in resultado.output
    with sqlite3.connect(banco_temporario) as conn:
        assert conn.execute("SELECT COUNT(*) FROM animais").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM pessoas").fetchone()[0] == 3


def test_seed_limpar_recria_dados_sem_duplicar(banco_temporario: Path) -> None:
    assert runner.invoke(app, ["seed"]).exit_code == 0
    resultado = runner.invoke(app, ["seed", "--limpar"])
    assert resultado.exit_code == 0, resultado.output
    assert "carregados com sucesso" in resultado.output
    with sqlite3.connect(banco_temporario) as conn:
        assert conn.execute("SELECT COUNT(*) FROM animais").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM pessoas").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM reservas").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM fila_espera").fetchone()[0] == 2
