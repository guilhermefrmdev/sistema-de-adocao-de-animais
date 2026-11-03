"""Relatórios gerenciais sobre compatibilidade, adoções e situação dos animais."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path

import typer
from rich.panel import Panel
from rich.table import Table

from sistema_de_adocao_de_animais.cli.commands.adocao import (
    conectar as conectar_adocoes,
)
from sistema_de_adocao_de_animais.cli.commands.adotante import (
    buscar_animal_objeto,
)
from sistema_de_adocao_de_animais.cli.commands.adotante import (
    conectar as conectar_adotantes,
)
from sistema_de_adocao_de_animais.cli.commands.adotante import objeto_adotante
from sistema_de_adocao_de_animais.cli.commands.animal import (
    conectar as conectar_animais,
)
from sistema_de_adocao_de_animais.cli.console import console
from sistema_de_adocao_de_animais.cli.erros import erro
from sistema_de_adocao_de_animais.enums.status_animal import StatusAnimal
from sistema_de_adocao_de_animais.settings import load_settings
from sistema_de_adocao_de_animais.strategies.compatibilidade_strategy import (
    CompatibilidadePonderada,
)

app = typer.Typer(
    help="Relatórios gerenciais do sistema de adoção.", no_args_is_help=True
)
DB_PATH = Path(__file__).resolve().parents[2] / "database" / "database.db"


def conectar() -> sqlite3.Connection:
    """Inicializa os esquemas compartilhados e abre o banco de relatórios."""
    conectar_animais().close()
    conectar_adotantes().close()
    conectar_adocoes().close()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _especie_sql() -> str:
    return "CASE WHEN c.animal_id IS NOT NULL THEN 'cachorro' WHEN g.animal_id IS NOT NULL THEN 'gato' ELSE 'animal' END"


@app.command("top")
def top(
    limite: int = typer.Option(
        5, "--limite", min=1, help="Quantidade de animais no ranking."
    )
) -> None:
    """Lista os animais com maior média de compatibilidade entre os adotantes."""
    try:
        with conectar() as conn:
            animais_rows = conn.execute(
                "SELECT id, nome FROM animais WHERE id IN (SELECT animal_id FROM cachorros UNION SELECT animal_id FROM gatos)"
                " ORDER BY id"
            ).fetchall()
            adotantes_rows = conn.execute(
                "SELECT p.id, p.nome, p.idade, a.telefone, a.moradia, a.areaUtil, a.experiencia,"
                " a.criancasEmCasa, a.outrosAnimais FROM pessoas p JOIN adotantes a ON a.pessoa_id=p.id ORDER BY p.id"
            ).fetchall()
            if not animais_rows:
                console.print(
                    Panel(
                        "Nenhum animal cadastrado para calcular o ranking.",
                        title="Top animais",
                        border_style="yellow",
                    )
                )
                return
            if not adotantes_rows:
                console.print(
                    Panel(
                        "Nenhum adotante cadastrado para calcular as médias de compatibilidade.",
                        title="Top animais",
                        border_style="yellow",
                    )
                )
                return
            estrategia = CompatibilidadePonderada(load_settings())
            ranking: list[tuple[int, str, float]] = []
            adotantes = [objeto_adotante(row) for row in adotantes_rows]
            for animal_row in animais_rows:
                animal = buscar_animal_objeto(conn, animal_row["id"])
                notas = [
                    estrategia.calcular(adotante, animal) for adotante in adotantes
                ]
                ranking.append(
                    (animal_row["id"], animal_row["nome"], sum(notas) / len(notas))
                )
        ranking.sort(key=lambda item: (-item[2], item[0]))
        tabela = Table(
            title=f"Top {min(limite, len(ranking))} animais por compatibilidade média",
            header_style="bold bright_blue",
        )
        tabela.add_column("Pos.", justify="right")
        tabela.add_column("ID", justify="right")
        tabela.add_column("Animal")
        tabela.add_column("Compatibilidade média", justify="right")
        for posicao, (id_animal, nome, media) in enumerate(ranking[:limite], start=1):
            tabela.add_row(str(posicao), str(id_animal), nome, f"{media:.1f}/100")
        console.print(tabela)
    except (ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("adocoes")
def adocoes(
    por: str = typer.Option("especie", "--por", help="Agrupar por especie ou porte.")
) -> None:
    """Mostra taxa de adoção por espécie ou porte (adotados / total)."""
    try:
        agrupamento = por.strip().lower()
        if agrupamento not in {"especie", "porte"}:
            raise ValueError("Agrupamento inválido. Use --por especie ou --por porte.")
        with conectar() as conn:
            campo = _especie_sql() if agrupamento == "especie" else "a.porte"
            rows = conn.execute(
                f"SELECT {campo} AS grupo, COUNT(*) AS total, "
                "SUM(CASE WHEN a.status='ADOTADO' THEN 1 ELSE 0 END) AS adotados "
                "FROM animais a LEFT JOIN cachorros c ON c.animal_id=a.id "
                "LEFT JOIN gatos g ON g.animal_id=a.id GROUP BY grupo ORDER BY grupo"
            ).fetchall()
        if not rows:
            console.print(
                Panel(
                    "Nenhum animal cadastrado.",
                    title="Taxa de adoções",
                    border_style="yellow",
                )
            )
            return
        tabela = Table(
            title=f"Taxa de adoções por {agrupamento}", header_style="bold bright_blue"
        )
        tabela.add_column(agrupamento.capitalize())
        tabela.add_column("Total de animais", justify="right")
        tabela.add_column("Adotados", justify="right")
        tabela.add_column("Taxa de adoção", justify="right")
        for row in rows:
            total = int(row["total"])
            adotados = int(row["adotados"] or 0)
            taxa = (adotados / total * 100) if total else 0.0
            tabela.add_row(
                str(row["grupo"]).capitalize(),
                str(total),
                str(adotados),
                f"{taxa:.1f}%",
            )
        console.print(tabela)
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("tempo-medio")
def tempo_medio() -> None:
    """Calcula a média de dias entre entrada no abrigo e adoção."""
    try:
        with conectar() as conn:
            rows = conn.execute(
                "SELECT a.nome, a.data_entrada, d.data_adocao FROM adocoes d "
                "JOIN animais a ON a.id=d.animal_id ORDER BY d.id"
            ).fetchall()
        if not rows:
            console.print(
                Panel(
                    "Ainda não há adoções registradas para calcular o tempo médio.",
                    title="Tempo médio até adoção",
                    border_style="yellow",
                )
            )
            return
        duracoes: list[int] = []
        for row in rows:
            entrada = date.fromisoformat(row["data_entrada"][:10])
            adocao = datetime.fromisoformat(row["data_adocao"]).date()
            duracoes.append(max(0, (adocao - entrada).days))
        media = sum(duracoes) / len(duracoes)
        console.print(
            Panel(
                f"Adoções consideradas: {len(duracoes)}\nTempo médio entre entrada e adoção: {media:.1f} dias",
                title="Tempo médio até adoção",
                border_style="blue",
            )
        )
    except (ValueError, TypeError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("devolucoes")
def devolucoes() -> None:
    """Agrupa devoluções registradas pelo motivo informado."""
    try:
        with conectar() as conn:
            rows = conn.execute(
                "SELECT TRIM(motivo_devolucao) AS motivo, COUNT(*) AS quantidade "
                "FROM adocoes WHERE motivo_devolucao IS NOT NULL AND TRIM(motivo_devolucao)<>'' "
                "GROUP BY TRIM(motivo_devolucao) ORDER BY quantidade DESC, motivo COLLATE NOCASE"
            ).fetchall()
        if not rows:
            console.print(
                Panel(
                    "Nenhuma devolução registrada.",
                    title="Devoluções por motivo",
                    border_style="yellow",
                )
            )
            return
        tabela = Table(
            title="Devoluções agrupadas por motivo", header_style="bold bright_blue"
        )
        tabela.add_column("Motivo")
        tabela.add_column("Quantidade", justify="right")
        for row in rows:
            tabela.add_row(row["motivo"], str(row["quantidade"]))
        console.print(tabela)
    except sqlite3.Error as exc:
        erro(str(exc))


@app.command("disponiveis")
def disponiveis() -> None:
    """Lista animais disponíveis e adotados, separados por status."""
    try:
        with conectar() as conn:
            grupos = {}
            for status in (StatusAnimal.DISPONIVEL.name, StatusAnimal.ADOTADO.name):
                grupos[status] = conn.execute(
                    "SELECT id, nome, raca, porte FROM animais WHERE status=? ORDER BY nome COLLATE NOCASE, id",
                    (status,),
                ).fetchall()
        for status, titulo in (
            (StatusAnimal.DISPONIVEL.name, "DISPONÍVEIS"),
            (StatusAnimal.ADOTADO.name, "ADOTADOS"),
        ):
            rows = grupos[status]
            tabela = Table(
                title=f"{titulo} ({len(rows)})", header_style="bold bright_blue"
            )
            tabela.add_column("ID", justify="right")
            tabela.add_column("Nome")
            tabela.add_column("Raça")
            tabela.add_column("Porte")
            for row in rows:
                tabela.add_row(
                    str(row["id"]), row["nome"], row["raca"] or "SRD", row["porte"]
                )
            if not rows:
                console.print(
                    Panel(
                        f"Nenhum animal com status {status}.",
                        title=titulo,
                        border_style="yellow",
                    )
                )
            else:
                console.print(tabela)
    except sqlite3.Error as exc:
        erro(str(exc))
