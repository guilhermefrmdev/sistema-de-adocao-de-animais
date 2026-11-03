"""Testes de integração do grupo adocao."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sistema_de_adocao_de_animais.cli.commands import adocao, adotante, animal, reserva
from sistema_de_adocao_de_animais.cli.main import app

runner = CliRunner()


@pytest.fixture
def banco_temporario(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    caminho = tmp_path / "adocoes.db"
    for modulo in (adocao, animal, adotante, reserva):
        monkeypatch.setattr(modulo, "DB_PATH", caminho)
    return caminho


def preparar_reserva() -> None:
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
    reserva_resultado = runner.invoke(app, ["reserva", "criar", "1", "1"])
    assert reserva_resultado.exit_code == 0, reserva_resultado.output


def test_taxa_calcula_sem_alterar_status(banco_temporario: Path) -> None:
    runner.invoke(
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
        ],
    )
    resultado = runner.invoke(app, ["adocao", "taxa", "1"])
    assert resultado.exit_code == 0, resultado.output
    assert "R$ 100.00" in resultado.output
    assert "DISPONIVEL" in runner.invoke(app, ["animal", "ver", "1"]).output


def test_efetivar_reserva_gera_contrato_e_conclui(banco_temporario: Path) -> None:
    preparar_reserva()
    resultado = runner.invoke(app, ["adocao", "efetivar", "1"])
    assert resultado.exit_code == 0, resultado.output
    assert "Adoção #1 efetivada" in resultado.output
    assert "CONTRATO DE ADOÇÃO RESPONSÁVEL" in resultado.output
    assert "R$ 100.00" in resultado.output
    assert "ADOTADO" in runner.invoke(app, ["animal", "ver", "1"]).output
    assert "CONCLUIDA" in runner.invoke(app, ["reserva", "listar"]).output
    assert "Rex" in runner.invoke(app, ["adocao", "listar"]).output


def test_devolver_registra_motivo_e_quarentena(banco_temporario: Path) -> None:
    preparar_reserva()
    assert runner.invoke(app, ["adocao", "efetivar", "1"]).exit_code == 0
    resultado = runner.invoke(
        app, ["adocao", "devolver", "1", "Alergia na família", "--quarentena"]
    )
    assert resultado.exit_code == 0, resultado.output
    assert "QUARENTENA" in resultado.output
    assert (
        "Alergia na família" in runner.invoke(app, ["animal", "historico", "1"]).output
    )
    assert "Alergia na família" in runner.invoke(app, ["adocao", "listar"]).output


def test_nao_efetiva_reserva_inativa(banco_temporario: Path) -> None:
    preparar_reserva()
    assert runner.invoke(app, ["reserva", "cancelar", "1"]).exit_code == 0
    resultado = runner.invoke(app, ["adocao", "efetivar", "1"])
    assert resultado.exit_code == 1
    assert "precisa estar ATIVA" in resultado.output
