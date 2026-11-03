"""Testes de integração dos comandos do grupo reserva."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sistema_de_adocao_de_animais.cli.commands import adotante, animal, reserva
from sistema_de_adocao_de_animais.cli.main import app

runner = CliRunner()


@pytest.fixture
def banco_temporario(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    caminho = tmp_path / "reservas.db"
    monkeypatch.setattr(animal, "DB_PATH", caminho)
    monkeypatch.setattr(adotante, "DB_PATH", caminho)
    monkeypatch.setattr(reserva, "DB_PATH", caminho)
    return caminho


def preparar_dados() -> None:
    adotante_resultado = runner.invoke(
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
    animal_resultado = runner.invoke(
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
    assert adotante_resultado.exit_code == 0, adotante_resultado.output
    assert animal_resultado.exit_code == 0, animal_resultado.output


def test_criar_reserva_e_alterar_status_do_animal(banco_temporario: Path) -> None:
    preparar_dados()
    resultado = runner.invoke(app, ["reserva", "criar", "1", "1"])
    assert resultado.exit_code == 0, resultado.output
    assert "criada" in resultado.output
    assert "Compatibilidade" in resultado.output
    animal_resultado = runner.invoke(app, ["animal", "ver", "1"])
    assert "RESERVADO" in animal_resultado.output
    reservas = runner.invoke(app, ["reserva", "listar", "--status", "ATIVA"])
    assert reservas.exit_code == 0, reservas.output
    assert "Maria Silva" in reservas.output and "Rex" in reservas.output


def test_nao_permite_duas_reservas_ativas_para_o_mesmo_animal(
    banco_temporario: Path,
) -> None:
    preparar_dados()
    assert runner.invoke(app, ["reserva", "criar", "1", "1"]).exit_code == 0
    segunda = runner.invoke(app, ["reserva", "criar", "1", "1"])
    assert segunda.exit_code == 1
    assert (
        "reserva ativa" in segunda.output.lower()
        or "já está reservado" in segunda.output.lower()
    )


def test_cancelar_reserva_libera_animal(banco_temporario: Path) -> None:
    preparar_dados()
    assert runner.invoke(app, ["reserva", "criar", "1", "1"]).exit_code == 0
    resultado = runner.invoke(app, ["reserva", "cancelar", "1"])
    assert resultado.exit_code == 0, resultado.output
    assert "cancelada" in resultado.output.lower()
    animal_resultado = runner.invoke(app, ["animal", "ver", "1"])
    assert "DISPONIVEL" in animal_resultado.output
    canceladas = runner.invoke(app, ["reserva", "listar", "--status", "CANCELADA"])
    assert "Rex" in canceladas.output


def test_rodar_expiracao_libera_animal(banco_temporario: Path) -> None:
    preparar_dados()
    assert runner.invoke(app, ["reserva", "criar", "1", "1"]).exit_code == 0
    futuro = (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d %H:%M")
    resultado = runner.invoke(app, ["reserva", "rodar-expiracao", "--agora", futuro])
    assert resultado.exit_code == 0, resultado.output
    assert "Total de reservas expiradas: 1" in resultado.output
    animal_resultado = runner.invoke(app, ["animal", "ver", "1"])
    assert "DISPONIVEL" in animal_resultado.output
    expiradas = runner.invoke(app, ["reserva", "listar", "--status", "EXPIRADA"])
    assert "Rex" in expiradas.output


def test_reserva_recusa_adotante_ineligivel(banco_temporario: Path) -> None:
    runner.invoke(
        app,
        [
            "adotante",
            "cadastrar",
            "Joao Silva",
            "25",
            "88999999999",
            "APARTAMENTO",
            "40",
        ],
    )
    runner.invoke(
        app,
        [
            "animal",
            "cachorro",
            "cadastrar",
            "Thor",
            "24",
            "Pastor",
            "M",
            "30",
            "GRANDE",
        ],
    )
    resultado = runner.invoke(app, ["reserva", "criar", "1", "1"])
    assert resultado.exit_code == 1
    assert "não atende" in resultado.output.lower()


def test_data_hora_simulada_invalida(banco_temporario: Path) -> None:
    resultado = runner.invoke(
        app, ["reserva", "rodar-expiracao", "--agora", "03/11/2026"]
    )
    assert resultado.exit_code == 1
    assert "AAAA-MM-DD HH:MM" in resultado.output
