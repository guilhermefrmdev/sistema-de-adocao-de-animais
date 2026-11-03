"""Comandos de configuração e carga de dados de demonstração."""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import typer
from rich.panel import Panel
from rich.table import Table

from sistema_de_adocao_de_animais.cli.commands import adocao as adocao_cmd
from sistema_de_adocao_de_animais.cli.commands import adotante as adotante_cmd
from sistema_de_adocao_de_animais.cli.commands import animal as animal_cmd
from sistema_de_adocao_de_animais.cli.commands import reserva as reserva_cmd
from sistema_de_adocao_de_animais.cli.console import console
from sistema_de_adocao_de_animais.cli.erros import confirmar, erro
from sistema_de_adocao_de_animais.repositories.fila_de_espera_repository import (
    FilaDeEsperaRepository,
)
from sistema_de_adocao_de_animais.settings import (
    ConfiguracaoInvalidaError,
    load_settings,
)

config_app = typer.Typer(
    help="Exibe as políticas e configurações do sistema.", no_args_is_help=True
)
DB_PATH = Path(__file__).resolve().parents[2] / "database" / "database.db"


@config_app.command("mostrar")
def config_mostrar() -> None:
    """Exibe as políticas carregadas do settings.json."""
    try:
        cfg = load_settings()
        tabela = Table(
            title="Configurações do sistema", header_style="bold bright_blue"
        )
        tabela.add_column("Política", style="cyan")
        tabela.add_column("Valor")
        tabela.add_row("Idade mínima do adotante", f"{cfg.idade_minima_adotante} anos")
        tabela.add_row(
            "Portes com restrição de moradia", ", ".join(cfg.portes_restritos)
        )
        tabela.add_row("Moradia exigida para portes restritos", cfg.moradia_exigida)
        tabela.add_row(
            "Área mínima para portes restritos", f"{cfg.area_minima_m2:g} m²"
        )
        tabela.add_row("Duração da reserva", f"{cfg.reserva_horas} horas")
        tabela.add_row(
            "Pesos de compatibilidade",
            ", ".join(f"{nome}: {peso:g}" for nome, peso in cfg.pesos.items()),
        )
        tabela.add_row(
            "Estratégia padrão de taxa",
            str(cfg.taxas.get("estrategia_padrao", "padrao")),
        )
        tabela.add_row(
            "Valor-base da taxa", f"R$ {float(cfg.taxas.get('valor_base', 0)):.2f}"
        )
        tabela.add_row(
            "Pesos da fila",
            (
                f"compatibilidade: {cfg.fila_espera['peso_pontuacao']:g}; "
                f"tempo de espera: {cfg.fila_espera['peso_tempo_espera']:g}"
            ),
        )
        tabela.add_row(
            "Normalização do tempo de espera",
            f"{cfg.fila_espera['dias_espera_max_normalizacao']} dias",
        )
        console.print(tabela)
        console.print(
            Panel(
                "As políticas acima foram carregadas e validadas a partir do settings.json.",
                border_style="blue",
                expand=False,
            )
        )
    except (ConfiguracaoInvalidaError, KeyError, TypeError, ValueError) as exc:
        erro(str(exc))


def _preparar_esquema() -> None:
    """Inicializa as tabelas usando os conectores compartilhados da aplicação."""
    animal_cmd.conectar().close()
    adotante_cmd.conectar().close()
    reserva_cmd.conectar().close()
    adocao_cmd.conectar().close()
    repo = FilaDeEsperaRepository(DB_PATH)
    conn = repo.conectar()
    conn.close()


def _limpar_dados(conn: sqlite3.Connection) -> None:
    """Remove os dados de domínio respeitando as chaves estrangeiras."""
    # Tabelas-filhas primeiro; as tabelas são criadas antes de entrar aqui.
    for tabela in (
        "fila_espera",
        "adocoes",
        "reservas",
        "gatos",
        "cachorros",
        "adotantes",
        "pessoas",
        "animais",
    ):
        conn.execute(f"DELETE FROM {tabela}")
    conn.execute("DELETE FROM seed_control")


def _popular(conn: sqlite3.Connection) -> tuple[int, int, int, int]:
    """Insere exemplos de animais, adotantes, reserva e lista de espera."""
    hoje = date.today()
    agora = datetime.now()
    animais = [
        (
            "Mel",
            24,
            "Labrador",
            "F",
            "DISPONIVEL",
            json.dumps(["docil", "sociavel"]),
            "GRANDE",
            25.0,
            (hoje - timedelta(days=35)).isoformat(),
            "[]",
            1,
        ),
        (
            "Thor",
            48,
            "SRD",
            "M",
            "DISPONIVEL",
            json.dumps(["brincalhao", "agitado"]),
            "MEDIO",
            18.0,
            (hoje - timedelta(days=20)).isoformat(),
            "[]",
            1,
        ),
        (
            "Lua",
            8,
            "SRD",
            "F",
            "DISPONIVEL",
            json.dumps(["docil", "brincalhao"]),
            "PEQUENO",
            3.2,
            (hoje - timedelta(days=12)).isoformat(),
            "[]",
            1,
        ),
    ]
    animal_ids: list[int] = []
    for (
        nome,
        idade,
        raca,
        sexo,
        status,
        temperamento,
        porte,
        peso,
        entrada,
        historico,
        castrado,
    ) in animais:
        cur = conn.execute(
            "INSERT INTO animais (nome, idade, raca, sexo, status, temperamento, porte, peso, data_entrada, historico, castrado) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                nome,
                idade,
                raca,
                sexo,
                status,
                temperamento,
                porte,
                peso,
                entrada,
                historico,
                castrado,
            ),
        )
        animal_ids.append(int(cur.lastrowid))

    conn.execute(
        "INSERT INTO cachorros (animal_id, necessidade_passeio) VALUES (?,?)",
        (animal_ids[0], 1),
    )
    conn.execute(
        "INSERT INTO cachorros (animal_id, necessidade_passeio) VALUES (?,?)",
        (animal_ids[1], 1),
    )
    conn.execute(
        "INSERT INTO gatos (animal_id, independencia, tipo_pelo) VALUES (?,?,?)",
        (animal_ids[2], "MEDIA", "CURTO"),
    )

    adotantes = [
        ("Ana Souza", 32, "85999990001", "CASA", 80.0, 1, 0, 0),
        ("Bruno Lima", 27, "85999990002", "APARTAMENTO", 45.0, 1, 1, 1),
        ("Carla Alves", 41, "85999990003", "CASA", 100.0, 1, 1, 0),
    ]
    adotante_ids: list[int] = []
    for (
        nome,
        idade,
        telefone,
        moradia,
        area,
        experiencia,
        criancas,
        outros,
    ) in adotantes:
        cur = conn.execute(
            "INSERT INTO pessoas (nome, idade) VALUES (?,?)", (nome, idade)
        )
        adotante_id = int(cur.lastrowid)
        adotante_ids.append(adotante_id)
        conn.execute(
            "INSERT INTO adotantes (pessoa_id, telefone, moradia, areaUtil, experiencia, criancasEmCasa, outrosAnimais) VALUES (?,?,?,?,?,?,?)",
            (adotante_id, telefone, moradia, area, experiencia, criancas, outros),
        )

    cfg = load_settings()
    data_reserva = agora
    data_expiracao = agora + timedelta(hours=cfg.reserva_horas)
    conn.execute(
        "INSERT INTO reservas (adotante_id, animal_id, compatibilidade, data_reserva, data_expiracao, status) VALUES (?,?,?,?,?,?)",
        (
            adotante_ids[0],
            animal_ids[0],
            92.0,
            data_reserva.isoformat(timespec="seconds"),
            data_expiracao.isoformat(timespec="seconds"),
            "ATIVA",
        ),
    )
    conn.execute("UPDATE animais SET status='RESERVADO' WHERE id=?", (animal_ids[0],))

    conn.execute(
        "INSERT INTO fila_espera (animal_id, adotante_id, compatibilidade, data_entrada, prioridade, posicao) VALUES (?,?,?,?,?,?)",
        (
            animal_ids[2],
            adotante_ids[1],
            87.0,
            (agora - timedelta(days=4)).isoformat(timespec="seconds"),
            90.9,
            1,
        ),
    )
    conn.execute(
        "INSERT INTO fila_espera (animal_id, adotante_id, compatibilidade, data_entrada, prioridade, posicao) VALUES (?,?,?,?,?,?)",
        (
            animal_ids[2],
            adotante_ids[2],
            82.0,
            (agora - timedelta(days=8)).isoformat(timespec="seconds"),
            87.4,
            2,
        ),
    )
    conn.execute("INSERT INTO seed_control (seed_key) VALUES ('dados_demo_v1')")
    return len(animais), len(adotantes), 1, 2


def seed(
    limpar: bool = typer.Option(
        False, "--limpar", help="Apaga os dados existentes antes de popular."
    )
) -> None:
    """Popula o banco com animais, adotantes, uma reserva e uma fila de exemplo.

    A execução é idempotente: se os dados de demonstração já foram inseridos,
    uma nova execução não duplica os registros. Use --limpar para recriá-los.
    """
    conn: sqlite3.Connection | None = None
    try:
        load_settings()  # Valida a configuração antes de alterar os dados.
        _preparar_esquema()
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        conn.execute(
            "CREATE TABLE IF NOT EXISTS seed_control (seed_key TEXT PRIMARY KEY)"
        )
        if limpar:
            with conn:
                _limpar_dados(conn)
        ja_executado = conn.execute(
            "SELECT 1 FROM seed_control WHERE seed_key='dados_demo_v1'"
        ).fetchone()
        if ja_executado:
            console.print(
                Panel(
                    "Os dados de demonstração já existem. Nenhum registro foi duplicado.",
                    title="Seed",
                    border_style="yellow",
                    expand=False,
                )
            )
            return
        with conn:
            animais, adotantes, reservas, entradas_fila = _popular(conn)
        confirmar(
            "Dados de demonstração carregados com sucesso.\n"
            f"Animais: {animais} | Adotantes: {adotantes} | "
            f"Reservas: {reservas} | Entradas na fila: {entradas_fila}"
        )
    except (
        ConfiguracaoInvalidaError,
        ValueError,
        KeyError,
        TypeError,
        sqlite3.Error,
    ) as exc:
        erro(str(exc))
    finally:
        if conn is not None:
            conn.close()
