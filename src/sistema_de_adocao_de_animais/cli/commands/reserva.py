"""Comandos CLI para criação, consulta, cancelamento e expiração de reservas."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.table import Table

from sistema_de_adocao_de_animais.cli.commands.adotante import (
    buscar_adotante,
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
from sistema_de_adocao_de_animais.cli.erros import confirmar, erro
from sistema_de_adocao_de_animais.enums.status_animal import StatusAnimal
from sistema_de_adocao_de_animais.settings import load_settings
from sistema_de_adocao_de_animais.strategies.compatibilidade_strategy import (
    CompatibilidadePonderada,
)

app = typer.Typer(help="Gerenciamento de reservas de adoção.", no_args_is_help=True)
DB_PATH = Path(__file__).resolve().parents[2] / "database" / "database.db"


def conectar() -> sqlite3.Connection:
    """Abre o banco compartilhado e garante a tabela de reservas."""
    # Garante que os esquemas usados para carregar animal e adotante estejam criados.
    conectar_animais().close()
    conectar_adotantes().close()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        adotante_id INTEGER NOT NULL,
        animal_id INTEGER NOT NULL,
        compatibilidade REAL NOT NULL CHECK (compatibilidade BETWEEN 0 AND 100),
        data_reserva TEXT NOT NULL,
        data_expiracao TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('ATIVA','EXPIRADA','CONCLUIDA','CANCELADA')),
        FOREIGN KEY (adotante_id) REFERENCES adotantes(pessoa_id),
        FOREIGN KEY (animal_id) REFERENCES animais(id)
    )""")
    conn.execute("""CREATE UNIQUE INDEX IF NOT EXISTS uq_reserva_ativa_por_animal
        ON reservas(animal_id) WHERE status = 'ATIVA'""")
    conn.commit()
    return conn


def parse_agora(valor: Optional[str]) -> datetime:
    """Converte o formato opcional AAAA-MM-DD HH:MM para datetime."""
    if valor is None:
        return datetime.now()
    try:
        return datetime.strptime(valor, "%Y-%m-%d %H:%M")
    except ValueError as exc:
        raise ValueError(
            "Data/hora inválida. Use AAAA-MM-DD HH:MM, por exemplo '2026-11-03 14:30'."
        ) from exc


def verificar_elegibilidade(adotante, animal, cfg) -> list[tuple[str, bool, str]]:
    """Avalia as políticas obrigatórias antes de criar uma reserva."""
    regras = [
        (
            f"Idade mínima ({cfg.idade_minima_adotante} anos)",
            adotante.idade >= cfg.idade_minima_adotante,
            f"Idade informada: {adotante.idade}",
        )
    ]
    if animal.porte.name in cfg.portes_restritos:
        regras.append(
            (
                f"Moradia exigida ({cfg.moradia_exigida})",
                adotante.moradia.name == cfg.moradia_exigida,
                f"Moradia informada: {adotante.moradia.name}",
            )
        )
        regras.append(
            (
                f"Área mínima ({cfg.area_minima_m2:g} m²)",
                adotante.areaUtil >= cfg.area_minima_m2,
                f"Área informada: {adotante.areaUtil:g} m²",
            )
        )
    return regras


def salvar_evento(
    conn: sqlite3.Connection, animal_id: int, tipo: str, nome: str, data: datetime
) -> None:
    """Acrescenta um evento ao histórico JSON do animal."""
    row = conn.execute(
        "SELECT historico FROM animais WHERE id=?", (animal_id,)
    ).fetchone()
    if row is None:
        return
    try:
        eventos = json.loads(row["historico"] or "[]")
        if not isinstance(eventos, list):
            eventos = []
    except json.JSONDecodeError, TypeError:
        eventos = []
    eventos.append({"tipo": tipo, "nome": nome, "data": data.date().isoformat()})
    conn.execute(
        "UPDATE animais SET historico=? WHERE id=?",
        (json.dumps(eventos, ensure_ascii=False), animal_id),
    )


def proximo_da_fila(conn: sqlite3.Connection, animal_id: int) -> Optional[sqlite3.Row]:
    """Retorna o próximo adotante da fila, caso a tabela já exista."""
    existe = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='fila_espera'"
    ).fetchone()
    if not existe:
        return None
    return conn.execute(
        """SELECT f.adotante_id, f.compatibilidade, f.posicao, p.nome
        FROM fila_espera f JOIN pessoas p ON p.id=f.adotante_id
        WHERE f.animal_id=? ORDER BY f.posicao ASC, f.prioridade DESC, f.data_entrada ASC LIMIT 1""",
        (animal_id,),
    ).fetchone()


def mostrar_fila_notificada(row: Optional[sqlite3.Row], animal_id: int) -> None:
    if row:
        console.print(
            Panel(
                f"Próximo da fila para o animal #{animal_id}: [bold]{row['nome']}[/bold] "
                f"(adotante #{row['adotante_id']}, compatibilidade {row['compatibilidade']:.1f}%).",
                title="Próximo da fila",
                border_style="cyan",
            )
        )


@app.command("criar")
def criar(
    id_adotante: int = typer.Argument(..., min=1),
    id_animal: int = typer.Argument(..., min=1),
) -> None:
    """Cria uma reserva ativa após validar elegibilidade e compatibilidade."""
    try:
        cfg = load_settings()
        agora = datetime.now()
        with conectar() as conn:
            adotante = objeto_adotante(buscar_adotante(conn, id_adotante))
            animal = buscar_animal_objeto(conn, id_animal)
            if animal.status != StatusAnimal.DISPONIVEL:
                ativa = conn.execute(
                    "SELECT id, adotante_id FROM reservas WHERE animal_id=? AND status='ATIVA'",
                    (id_animal,),
                ).fetchone()
                if animal.status == StatusAnimal.RESERVADO or ativa:
                    detalhe = (
                        f"Já existe uma reserva ativa (ID {ativa['id']}, adotante {ativa['adotante_id']})."
                        if ativa
                        else "O animal já está reservado."
                    )
                    raise ValueError(
                        f"{detalhe} Considere usar o comando 'fila entrar'."
                    )
                raise ValueError(
                    f"O animal precisa estar DISPONIVEL; status atual: {animal.status.name}."
                )
            regras = verificar_elegibilidade(adotante, animal, cfg)
            tabela = Table(
                title="Verificação de elegibilidade", header_style="bold bright_blue"
            )
            tabela.add_column("Regra")
            tabela.add_column("Resultado", justify="center")
            tabela.add_column("Detalhe")
            for nome, passou, detalhe in regras:
                tabela.add_row(
                    nome,
                    (
                        "[green]✔ Atendida[/green]"
                        if passou
                        else "[red]✘ Não atendida[/red]"
                    ),
                    detalhe,
                )
            console.print(tabela)
            if not all(regra[1] for regra in regras):
                raise ValueError(
                    "Reserva não criada: o adotante não atende a todas as políticas de elegibilidade."
                )
            score = CompatibilidadePonderada(cfg).calcular(adotante, animal)
            expiracao = agora + timedelta(hours=cfg.reserva_horas)
            cur = conn.execute(
                """INSERT INTO reservas
                (adotante_id, animal_id, compatibilidade, data_reserva, data_expiracao, status)
                VALUES (?, ?, ?, ?, ?, 'ATIVA')""",
                (
                    id_adotante,
                    id_animal,
                    score,
                    agora.isoformat(timespec="seconds"),
                    expiracao.isoformat(timespec="seconds"),
                ),
            )
            reserva_id = cur.lastrowid
            conn.execute(
                "UPDATE animais SET status=? WHERE id=?",
                (StatusAnimal.RESERVADO.name, id_animal),
            )
            salvar_evento(
                conn,
                id_animal,
                "RESERVA",
                f"Reserva #{reserva_id} criada para {adotante.nome}",
                agora,
            )
        confirmar(
            f"Reserva [bold]#{reserva_id}[/bold] criada para [bold]{animal.nome}[/bold].\n"
            f"Compatibilidade: [cyan]{score:.1f}/100[/cyan]\n"
            f"Expira em: [cyan]{expiracao:%d/%m/%Y %H:%M}[/cyan] ({cfg.reserva_horas} horas)."
        )
    except (ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("cancelar")
def cancelar(id_reserva: int = typer.Argument(..., min=1)) -> None:
    """Cancela uma reserva ativa e libera o animal."""
    try:
        agora = datetime.now()
        with conectar() as conn:
            reserva = conn.execute(
                "SELECT * FROM reservas WHERE id=?", (id_reserva,)
            ).fetchone()
            if reserva is None:
                raise ValueError(f"Reserva com ID {id_reserva} não encontrada.")
            if reserva["status"] != "ATIVA":
                raise ValueError(
                    f"A reserva #{id_reserva} não está ativa (status: {reserva['status']})."
                )
            conn.execute(
                "UPDATE reservas SET status='CANCELADA' WHERE id=?", (id_reserva,)
            )
            conn.execute(
                "UPDATE animais SET status=? WHERE id=? AND status=?",
                (
                    StatusAnimal.DISPONIVEL.name,
                    reserva["animal_id"],
                    StatusAnimal.RESERVADO.name,
                ),
            )
            salvar_evento(
                conn,
                reserva["animal_id"],
                "RESERVA_CANCELADA",
                f"Reserva #{id_reserva} cancelada",
                agora,
            )
            proximo = proximo_da_fila(conn, reserva["animal_id"])
        confirmar(
            f"Reserva [bold]#{id_reserva}[/bold] cancelada. O animal foi liberado para novas reservas."
        )
        mostrar_fila_notificada(proximo, reserva["animal_id"])
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("listar")
def listar(
    status: Optional[str] = typer.Option(
        None, "--status", help="ATIVA, EXPIRADA, CONCLUIDA ou CANCELADA."
    ),
    animal: Optional[int] = typer.Option(
        None, "--animal", min=1, help="Filtra por ID do animal."
    ),
    adotante: Optional[int] = typer.Option(
        None, "--adotante", min=1, help="Filtra por ID do adotante."
    ),
) -> None:
    """Lista reservas, com filtros opcionais combináveis."""
    try:
        filtros, parametros = [], []
        if status:
            status = status.strip().upper()
            if status not in {"ATIVA", "EXPIRADA", "CONCLUIDA", "CANCELADA"}:
                raise ValueError(
                    "Status inválido. Use ATIVA, EXPIRADA, CONCLUIDA ou CANCELADA."
                )
            filtros.append("r.status=?")
            parametros.append(status)
        if animal is not None:
            filtros.append("r.animal_id=?")
            parametros.append(animal)
        if adotante is not None:
            filtros.append("r.adotante_id=?")
            parametros.append(adotante)
        sql = """SELECT r.*, p.nome AS nome_adotante, a.nome AS nome_animal
            FROM reservas r JOIN pessoas p ON p.id=r.adotante_id
            JOIN animais a ON a.id=r.animal_id"""
        if filtros:
            sql += " WHERE " + " AND ".join(filtros)
        sql += " ORDER BY r.id DESC"
        with conectar() as conn:
            rows = conn.execute(sql, parametros).fetchall()
        if not rows:
            console.print(
                Panel(
                    "Nenhuma reserva encontrada com os filtros informados.",
                    title="Reservas",
                    border_style="yellow",
                )
            )
            return
        tabela = Table(title="Reservas", header_style="bold bright_blue")
        for coluna in (
            "ID",
            "Adotante",
            "Animal",
            "Compatibilidade",
            "Criada em",
            "Expira em",
            "Status",
        ):
            tabela.add_column(coluna)
        for row in rows:
            criada = datetime.fromisoformat(row["data_reserva"]).strftime(
                "%d/%m/%Y %H:%M"
            )
            expira = datetime.fromisoformat(row["data_expiracao"]).strftime(
                "%d/%m/%Y %H:%M"
            )
            estilo = "green" if row["status"] == "ATIVA" else "dim"
            tabela.add_row(
                str(row["id"]),
                f"{row['nome_adotante']} (#{row['adotante_id']})",
                f"{row['nome_animal']} (#{row['animal_id']})",
                f"{row['compatibilidade']:.1f}%",
                criada,
                expira,
                f"[{estilo}]{row['status']}[/{estilo}]",
            )
        console.print(tabela)
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("rodar-expiracao")
def rodar_expiracao(
    agora: Optional[str] = typer.Option(
        None, "--agora", help="Simula agora no formato AAAA-MM-DD HH:MM."
    ),
) -> None:
    """Expira reservas ativas vencidas e informa o próximo da fila."""
    try:
        instante = parse_agora(agora)
        expiradas: list[tuple[int, int, str]] = []
        with conectar() as conn:
            rows = conn.execute(
                """SELECT r.id, r.animal_id, a.nome AS nome_animal
                FROM reservas r JOIN animais a ON a.id=r.animal_id
                WHERE r.status='ATIVA' AND r.data_expiracao<=? ORDER BY r.data_expiracao""",
                (instante.isoformat(timespec="seconds"),),
            ).fetchall()
            for row in rows:
                conn.execute(
                    "UPDATE reservas SET status='EXPIRADA' WHERE id=? AND status='ATIVA'",
                    (row["id"],),
                )
                conn.execute(
                    "UPDATE animais SET status=? WHERE id=? AND status=?",
                    (
                        StatusAnimal.DISPONIVEL.name,
                        row["animal_id"],
                        StatusAnimal.RESERVADO.name,
                    ),
                )
                salvar_evento(
                    conn,
                    row["animal_id"],
                    "RESERVA_EXPIRADA",
                    f"Reserva #{row['id']} expirou",
                    instante,
                )
                expiradas.append((row["id"], row["animal_id"], row["nome_animal"]))
            notificacoes = [
                (animal_id, proximo_da_fila(conn, animal_id))
                for _, animal_id, _ in expiradas
            ]
        if not expiradas:
            console.print(
                Panel(
                    "Nenhuma reserva ativa vencida encontrada.",
                    title="Expiração de reservas",
                    border_style="yellow",
                )
            )
            return
        tabela = Table(title="Reservas expiradas", header_style="bold bright_blue")
        tabela.add_column("Reserva", justify="right")
        tabela.add_column("Animal")
        tabela.add_column("Resultado")
        for reserva_id, animal_id, nome_animal in expiradas:
            tabela.add_row(
                f"#{reserva_id}", f"{nome_animal} (#{animal_id})", "Animal liberado"
            )
        console.print(tabela)
        console.print(
            Panel(
                f"Total de reservas expiradas: {len(expiradas)}", border_style="green"
            )
        )
        for animal_id, proximo in notificacoes:
            mostrar_fila_notificada(proximo, animal_id)
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))
