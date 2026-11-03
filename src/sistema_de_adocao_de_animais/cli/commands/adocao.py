"""Comandos CLI para taxas, efetivação, contratos e devoluções de adoções."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.table import Table

from sistema_de_adocao_de_animais.cli.commands.adotante import (
    buscar_animal_objeto,
)
from sistema_de_adocao_de_animais.cli.commands.adotante import (
    conectar as conectar_adotantes,
)
from sistema_de_adocao_de_animais.cli.commands.animal import (
    conectar as conectar_animais,
)
from sistema_de_adocao_de_animais.cli.commands.reserva import (
    conectar as conectar_reservas,
)
from sistema_de_adocao_de_animais.cli.commands.reserva import salvar_evento
from sistema_de_adocao_de_animais.cli.console import console
from sistema_de_adocao_de_animais.cli.erros import confirmar, erro
from sistema_de_adocao_de_animais.enums.status_animal import StatusAnimal
from sistema_de_adocao_de_animais.settings import load_settings
from sistema_de_adocao_de_animais.strategies.taxa_adocao_strategy import (
    criar_estrategia,
)

app = typer.Typer(help="Efetivação e acompanhamento de adoções.", no_args_is_help=True)
DB_PATH = Path(__file__).resolve().parents[2] / "database" / "database.db"
ESTRATEGIAS_VALIDAS = {"padrao", "senior", "filhote", "especial"}


def conectar() -> sqlite3.Connection:
    """Abre o banco compartilhado e garante a tabela de adoções."""
    conectar_animais().close()
    conectar_adotantes().close()
    conectar_reservas().close()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""CREATE TABLE IF NOT EXISTS adocoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reserva_id INTEGER NOT NULL UNIQUE,
        animal_id INTEGER NOT NULL,
        adotante_id INTEGER NOT NULL,
        taxa REAL NOT NULL CHECK (taxa >= 0),
        estrategia TEXT NOT NULL,
        data_adocao TEXT NOT NULL,
        motivo_devolucao TEXT,
        data_devolucao TEXT,
        FOREIGN KEY (reserva_id) REFERENCES reservas(id),
        FOREIGN KEY (animal_id) REFERENCES animais(id),
        FOREIGN KEY (adotante_id) REFERENCES adotantes(pessoa_id)
    )""")
    conn.commit()
    return conn


def normalizar_estrategia(valor: Optional[str]) -> str:
    if valor is None or not valor.strip():
        valor = load_settings().taxas.get("estrategia_padrao", "padrao")
    valor = valor.strip().lower()
    if valor not in ESTRATEGIAS_VALIDAS:
        raise ValueError(
            "Estratégia inválida. Use padrao, senior, filhote ou especial."
        )
    return valor


def buscar_adocao(conn: sqlite3.Connection, id_adocao: int) -> sqlite3.Row:
    row = conn.execute(
        """SELECT d.*, a.nome AS nome_animal, a.idade, a.raca, a.sexo,
        a.porte, a.status AS status_animal,
        CASE WHEN c.animal_id IS NOT NULL THEN 'Cachorro'
             WHEN g.animal_id IS NOT NULL THEN 'Gato' ELSE 'Animal' END AS especie,
        p.nome AS nome_adotante, p.idade AS idade_adotante, ad.telefone
        FROM adocoes d JOIN animais a ON a.id=d.animal_id
        LEFT JOIN cachorros c ON c.animal_id=a.id LEFT JOIN gatos g ON g.animal_id=a.id
        JOIN pessoas p ON p.id=d.adotante_id JOIN adotantes ad ON ad.pessoa_id=d.adotante_id
        WHERE d.id=?""",
        (id_adocao,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Adoção com ID {id_adocao} não encontrada.")
    return row


def formatar_contrato(row: sqlite3.Row) -> str:
    """Gera um resumo do animal, adotante, taxa e termos de adoção."""
    data = datetime.fromisoformat(row["data_adocao"]).strftime("%d/%m/%Y %H:%M")
    return (
        "CONTRATO DE ADOÇÃO RESPONSÁVEL\n" + "=" * 34 + "\n\n"
        f"Adoção: #{row['id']}\nData: {data}\n\n"
        "DADOS DO ANIMAL\n"
        f"Nome: {row['nome_animal']}\nEspécie: {row['especie']}\n"
        f"Raça: {row['raca'] or 'SRD'}\nIdade: {row['idade']} meses\n"
        f"Sexo: {row['sexo']}\nPorte: {row['porte']}\n\n"
        "DADOS DO ADOTANTE\n"
        f"Nome: {row['nome_adotante']}\nIdade: {row['idade_adotante']} anos\n"
        f"Telefone: {row['telefone']}\n\nTAXA DE ADOÇÃO\n"
        f"Estratégia: {row['estrategia']}\nValor: R$ {row['taxa']:.2f}\n\n"
        "TERMOS E RESPONSABILIDADES\n"
        "1. O adotante assume a responsabilidade pelo bem-estar do animal.\n"
        "2. O adotante compromete-se a fornecer alimentação, abrigo, cuidados veterinários e ambiente seguro.\n"
        "3. O animal não deverá ser abandonado ou maltratado.\n"
        "4. Em caso de impossibilidade de manter a adoção, o adotante deverá contatar a instituição responsável.\n\n"
        "Assinatura do adotante: ______________________________\n"
        "Representante do abrigo: _____________________________\n"
    )


@app.command("taxa")
def taxa(
    id_animal: int = typer.Argument(..., min=1),
    estrategia: Optional[str] = typer.Option(
        None, "--estrategia", help="padrao, senior, filhote ou especial."
    ),
) -> None:
    """Calcula a taxa sem alterar dados."""
    try:
        cfg = load_settings()
        nome_estrategia = normalizar_estrategia(estrategia)
        with conectar() as conn:
            animal = buscar_animal_objeto(conn, id_animal)
            valor = criar_estrategia(cfg, nome_estrategia).calcular(animal)
        console.print(
            Panel(
                f"Animal: [bold]{animal.nome}[/bold] (#{id_animal})\n"
                f"Estratégia: {nome_estrategia}\nTaxa de adoção: R$ {valor:.2f}",
                title="Taxa de adoção",
                border_style="blue",
            )
        )
    except (ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("efetivar")
def efetivar(
    id_reserva: int = typer.Argument(..., min=1),
    estrategia: Optional[str] = typer.Option(
        None, "--estrategia", help="padrao, senior, filhote ou especial."
    ),
) -> None:
    """Conclui uma reserva ativa, registra a adoção e exibe o contrato."""
    try:
        cfg = load_settings()
        nome_estrategia = normalizar_estrategia(estrategia)
        agora = datetime.now()
        with conectar() as conn:
            reserva = conn.execute(
                "SELECT * FROM reservas WHERE id=?", (id_reserva,)
            ).fetchone()
            if reserva is None:
                raise ValueError(f"Reserva com ID {id_reserva} não encontrada.")
            if reserva["status"] != "ATIVA":
                raise ValueError(
                    f"A reserva #{id_reserva} precisa estar ATIVA; status atual: {reserva['status']}."
                )
            animal = buscar_animal_objeto(conn, reserva["animal_id"])
            if animal.status != StatusAnimal.RESERVADO:
                raise ValueError(
                    f"O animal precisa estar RESERVADO; status atual: {animal.status.name}."
                )
            valor = criar_estrategia(cfg, nome_estrategia).calcular(animal)
            cur = conn.execute(
                """INSERT INTO adocoes
                (reserva_id, animal_id, adotante_id, taxa, estrategia, data_adocao)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    id_reserva,
                    reserva["animal_id"],
                    reserva["adotante_id"],
                    valor,
                    nome_estrategia,
                    agora.isoformat(timespec="seconds"),
                ),
            )
            id_adocao = cur.lastrowid
            conn.execute(
                "UPDATE reservas SET status='CONCLUIDA' WHERE id=?", (id_reserva,)
            )
            conn.execute(
                "UPDATE animais SET status=? WHERE id=?",
                (StatusAnimal.ADOTADO.name, reserva["animal_id"]),
            )
            salvar_evento(
                conn,
                reserva["animal_id"],
                "ADOCAO",
                f"Adoção #{id_adocao} efetivada",
                agora,
            )
            existe_fila = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='fila_espera'"
            ).fetchone()
            if existe_fila:
                conn.execute(
                    "DELETE FROM fila_espera WHERE animal_id=?", (reserva["animal_id"],)
                )
            contrato_texto = formatar_contrato(buscar_adocao(conn, id_adocao))
        confirmar(
            f"Adoção #{id_adocao} efetivada. Reserva #{id_reserva} concluída e animal marcado como ADOTADO.\nTaxa: R$ {valor:.2f}"
        )
        console.print(
            Panel(
                contrato_texto,
                title=f"Contrato de adoção #{id_adocao}",
                border_style="cyan",
            )
        )
    except (ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("contrato")
def contrato(
    id_adocao: int = typer.Argument(..., min=1),
    salvar: Optional[Path] = typer.Option(
        None, "--salvar", help="Caminho do arquivo .txt para salvar o contrato."
    ),
) -> None:
    """Exibe o contrato e opcionalmente grava em arquivo."""
    try:
        with conectar() as conn:
            texto = formatar_contrato(buscar_adocao(conn, id_adocao))
        console.print(
            Panel(texto, title=f"Contrato de adoção #{id_adocao}", border_style="cyan")
        )
        if salvar is not None:
            destino = salvar.expanduser()
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(texto, encoding="utf-8")
            confirmar(f"Contrato salvo em: {destino.resolve()}")
    except (ValueError, OSError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("listar")
def listar(
    adotante: Optional[int] = typer.Option(
        None, "--adotante", min=1, help="Filtra pelo ID do adotante."
    )
) -> None:
    """Lista adoções efetivadas, com filtro opcional por adotante."""
    try:
        sql = """SELECT d.*, a.nome AS nome_animal, p.nome AS nome_adotante
            FROM adocoes d JOIN animais a ON a.id=d.animal_id JOIN pessoas p ON p.id=d.adotante_id"""
        parametros: tuple[int, ...] = ()
        if adotante is not None:
            sql += " WHERE d.adotante_id=?"
            parametros = (adotante,)
        sql += " ORDER BY d.id DESC"
        with conectar() as conn:
            if (
                adotante is not None
                and conn.execute(
                    "SELECT 1 FROM adotantes WHERE pessoa_id=?", (adotante,)
                ).fetchone()
                is None
            ):
                raise ValueError(f"Adotante com ID {adotante} não encontrado.")
            rows = conn.execute(sql, parametros).fetchall()
        if not rows:
            console.print(
                Panel(
                    "Nenhuma adoção encontrada.", title="Adoções", border_style="yellow"
                )
            )
            return
        tabela = Table(title="Adoções", header_style="bold bright_blue")
        for coluna in (
            "ID",
            "Animal",
            "Adotante",
            "Data",
            "Taxa",
            "Estratégia",
            "Devolução",
        ):
            tabela.add_column(coluna)
        for row in rows:
            data = datetime.fromisoformat(row["data_adocao"]).strftime("%d/%m/%Y %H:%M")
            tabela.add_row(
                str(row["id"]),
                f"{row['nome_animal']} (#{row['animal_id']})",
                f"{row['nome_adotante']} (#{row['adotante_id']})",
                data,
                f"R$ {row['taxa']:.2f}",
                row["estrategia"],
                row["motivo_devolucao"] or "—",
            )
        console.print(tabela)
        for row in rows:
            if row["motivo_devolucao"]:
                console.print(
                    Panel(
                        f"Adoção #{row['id']} — motivo da devolução: {row['motivo_devolucao']}",
                        border_style="yellow",
                    )
                )
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("devolver")
def devolver(
    id_adocao: int = typer.Argument(..., min=1),
    motivo: str = typer.Argument(..., help="Motivo da devolução."),
    quarentena: bool = typer.Option(
        False, "--quarentena", help="Encaminha o animal para QUARENTENA."
    ),
) -> None:
    """Registra devolução, motivo e novo status do animal."""
    try:
        agora = datetime.now()
        motivo = motivo.strip()
        if len(motivo) < 3:
            raise ValueError(
                "Informe um motivo de devolução com pelo menos 3 caracteres."
            )
        novo_status = StatusAnimal.QUARENTENA if quarentena else StatusAnimal.DEVOLVIDO
        with conectar() as conn:
            adocao = buscar_adocao(conn, id_adocao)
            if adocao["motivo_devolucao"]:
                raise ValueError(
                    f"A adoção #{id_adocao} já possui uma devolução registrada."
                )
            if adocao["status_animal"] != StatusAnimal.ADOTADO.name:
                raise ValueError(
                    f"O animal precisa estar ADOTADO para ser devolvido; status atual: {adocao['status_animal']}."
                )
            conn.execute(
                "UPDATE animais SET status=? WHERE id=?",
                (novo_status.name, adocao["animal_id"]),
            )
            conn.execute(
                "UPDATE adocoes SET motivo_devolucao=?, data_devolucao=? WHERE id=?",
                (motivo, agora.isoformat(timespec="seconds"), id_adocao),
            )
            salvar_evento(conn, adocao["animal_id"], "DEVOLUCAO", motivo, agora)
        confirmar(
            f"Devolução da adoção #{id_adocao} registrada.\nAnimal: {adocao['nome_animal']}\nNovo status: {novo_status.name}\nMotivo: {motivo}"
        )
    except (ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        erro(str(exc))
