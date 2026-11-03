"""Testes de integração dos relatórios da CLI."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sistema_de_adocao_de_animais.cli.commands import (
    adocao,
    adotante,
    animal,
    fila,
    relatorio,
    reserva,
)
from sistema_de_adocao_de_animais.cli.main import app

runner = CliRunner()


@pytest.fixture
def banco_temporario(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    caminho = tmp_path / "relatorio.db"
    for modulo in (adocao, adotante, animal, fila, relatorio, reserva):
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
            "animal",
            "cachorro",
            "cadastrar",
            "Rex",
            "24",
            "SRD",
            "M",
            "18",
            "MEDIO",
            "--data-entrada",
            "2026-01-01",
            "--temperamento",
            "docil",
        ],
    )
    assert resultado.exit_code == 0, resultado.output
    resultado = runner.invoke(
        app,
        [
            "animal",
            "gato",
            "cadastrar",
            "Mimi",
            "12",
            "SRD",
            "F",
            "4",
            "PEQUENO",
            "ALTA",
            "CURTO",
            "--data-entrada",
            "2026-01-01",
        ],
    )
    assert resultado.exit_code == 0, resultado.output


def efetivar_adocao() -> None:
    resultado = runner.invoke(app, ["reserva", "criar", "1", "1"])
    assert resultado.exit_code == 0, resultado.output
    resultado = runner.invoke(app, ["adocao", "efetivar", "1"])
    assert resultado.exit_code == 0, resultado.output


def test_top_exibe_ranking_por_media_de_compatibilidade(banco_temporario: Path) -> None:
    preparar_dados()
    resultado = runner.invoke(app, ["relatorio", "top"])
    assert resultado.exit_code == 0, resultado.output
    assert "compatibilidade média" in resultado.output.lower()
    assert "Rex" in resultado.output
    assert "Mimi" in resultado.output


def test_top_limite_precisa_ser_positivo(banco_temporario: Path) -> None:
    preparar_dados()
    resultado = runner.invoke(app, ["relatorio", "top", "--limite", "0"])
    assert resultado.exit_code != 0


def test_relatorio_adocoes_por_especie_e_porte(banco_temporario: Path) -> None:
    preparar_dados()
    efetivar_adocao()
    especie = runner.invoke(app, ["relatorio", "adocoes"])
    assert especie.exit_code == 0, especie.output
    assert "Cachorro" in especie.output
    assert "100.0%" in especie.output
    porte = runner.invoke(app, ["relatorio", "adocoes", "--por", "porte"])
    assert porte.exit_code == 0, porte.output
    assert "Medio" in porte.output


def test_relatorio_adocoes_rejeita_agrupamento_invalido(banco_temporario: Path) -> None:
    resultado = runner.invoke(app, ["relatorio", "adocoes", "--por", "idade"])
    assert resultado.exit_code == 1
    assert "Use --por especie ou --por porte" in resultado.output


def test_tempo_medio_sem_adocoes_mostra_aviso(banco_temporario: Path) -> None:
    preparar_dados()
    resultado = runner.invoke(app, ["relatorio", "tempo-medio"])
    assert resultado.exit_code == 0, resultado.output
    assert "Ainda não há adoções" in resultado.output


def test_tempo_medio_calcula_dias_ate_adocao(banco_temporario: Path) -> None:
    preparar_dados()
    efetivar_adocao()
    resultado = runner.invoke(app, ["relatorio", "tempo-medio"])
    assert resultado.exit_code == 0, resultado.output
    assert "Tempo médio entre entrada e adoção" in resultado.output
    assert "dias" in resultado.output


def test_devolucoes_agrupa_motivos(banco_temporario: Path) -> None:
    preparar_dados()
    efetivar_adocao()
    resultado = runner.invoke(app, ["adocao", "devolver", "1", "Mudança de residência"])
    assert resultado.exit_code == 0, resultado.output
    rel = runner.invoke(app, ["relatorio", "devolucoes"])
    assert rel.exit_code == 0, rel.output
    assert "Mudança de residência" in rel.output
    assert "Quantidade" in rel.output


def test_devolucoes_sem_registros_mostra_aviso(banco_temporario: Path) -> None:
    resultado = runner.invoke(app, ["relatorio", "devolucoes"])
    assert resultado.exit_code == 0, resultado.output
    assert "Nenhuma devolução registrada" in resultado.output


def test_disponiveis_lista_disponiveis_e_adotados(banco_temporario: Path) -> None:
    preparar_dados()
    efetivar_adocao()
    resultado = runner.invoke(app, ["relatorio", "disponiveis"])
    assert resultado.exit_code == 0, resultado.output
    assert "DISPONÍVEIS (1)" in resultado.output
    assert "ADOTADOS (1)" in resultado.output
    assert "Rex" in resultado.output
    assert "Mimi" in resultado.output
