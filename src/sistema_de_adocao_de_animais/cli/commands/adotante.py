"""Comandos CLI para cadastro, consulta e triagem de adotantes."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.table import Table

from sistema_de_adocao_de_animais.cli.console import console
from sistema_de_adocao_de_animais.cli.erros import confirmar, erro
from sistema_de_adocao_de_animais.domain.adotante import Adotante
from sistema_de_adocao_de_animais.domain.cachorro import Cachorro
from sistema_de_adocao_de_animais.domain.gato import Gato
from sistema_de_adocao_de_animais.enums.moradias import Moradia
from sistema_de_adocao_de_animais.enums.nivel_independencia import NivelIndependencia
from sistema_de_adocao_de_animais.enums.porte_animal import PorteAnimal
from sistema_de_adocao_de_animais.enums.status_animal import StatusAnimal
from sistema_de_adocao_de_animais.enums.tipos_pelos import TiposPelos
from sistema_de_adocao_de_animais.settings import load_settings
from sistema_de_adocao_de_animais.strategies.compatibilidade_strategy import (
    CompatibilidadePonderada,
)

app = typer.Typer(help="Cadastro e triagem de adotantes.", no_args_is_help=True)
DB_PATH = Path(__file__).resolve().parents[2] / "database" / "database.db"


def conectar() -> sqlite3.Connection:
    """Abre o banco e garante as tabelas de pessoas e adotantes."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""CREATE TABLE IF NOT EXISTS pessoas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        idade INTEGER NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS adotantes (
        pessoa_id INTEGER PRIMARY KEY,
        telefone TEXT NOT NULL,
        moradia TEXT NOT NULL,
        areaUtil REAL NOT NULL,
        experiencia INTEGER NOT NULL DEFAULT 0,
        criancasEmCasa INTEGER NOT NULL DEFAULT 0,
        outrosAnimais INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (pessoa_id) REFERENCES pessoas(id) ON DELETE CASCADE
    )""")
    conn.commit()
    return conn


def normalizar_moradia(valor: str) -> str:
    valor = valor.strip().upper().replace("-", "_")
    if valor not in {item.name for item in Moradia}:
        raise ValueError("Moradia inválida. Use CASA ou APARTAMENTO.")
    return valor


def buscar_adotante(conn: sqlite3.Connection, id_adotante: int) -> sqlite3.Row:
    row = conn.execute(
        """SELECT p.id, p.nome, p.idade, a.telefone, a.moradia,
        a.areaUtil, a.experiencia, a.criancasEmCasa, a.outrosAnimais
        FROM pessoas p JOIN adotantes a ON a.pessoa_id=p.id WHERE p.id=?""",
        (id_adotante,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Adotante com ID {id_adotante} não encontrado.")
    return row


def objeto_adotante(row: sqlite3.Row) -> Adotante:
    """Converte um registro persistido para o objeto de domínio."""
    return Adotante(
        nome=row["nome"],
        idade=row["idade"],
        telefone=row["telefone"],
        moradia=Moradia[row["moradia"]],
        areaUtil=float(row["areaUtil"]),
        experiencia=bool(row["experiencia"]),
        criancasEmCasa=bool(row["criancasEmCasa"]),
        outrosAnimais=bool(row["outrosAnimais"]),
        id=row["id"],
    )


def mostrar_adotante(row: sqlite3.Row) -> None:
    tabela = Table.grid(padding=(0, 2))
    tabela.add_column(style="bold cyan", justify="right")
    tabela.add_column()
    campos = [
        ("ID", row["id"]),
        ("Nome", row["nome"]),
        ("Idade", f"{row['idade']} anos"),
        ("Telefone", row["telefone"]),
        ("Moradia", row["moradia"]),
        ("Área útil", f"{row['areaUtil']:.1f} m²"),
        ("Experiência com animais", "Sim" if row["experiencia"] else "Não"),
        ("Crianças em casa", "Sim" if row["criancasEmCasa"] else "Não"),
        ("Outros animais", "Sim" if row["outrosAnimais"] else "Não"),
    ]
    for chave, valor in campos:
        tabela.add_row(f"{chave}:", str(valor))
    console.print(Panel(tabela, title=f"Adotante #{row['id']}", border_style="blue"))


def buscar_animal_objeto(conn: sqlite3.Connection, animal_id: int):
    """Carrega um animal da tabela compartilhada para calcular compatibilidade."""
    row = conn.execute(
        """SELECT a.*, c.necessidade_passeio, g.independencia, g.tipo_pelo,
        CASE WHEN c.animal_id IS NOT NULL THEN 'cachorro'
             WHEN g.animal_id IS NOT NULL THEN 'gato' ELSE 'animal' END especie
        FROM animais a LEFT JOIN cachorros c ON c.animal_id=a.id
        LEFT JOIN gatos g ON g.animal_id=a.id WHERE a.id=?""",
        (animal_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Animal com ID {animal_id} não encontrado.")
    import json
    from datetime import date

    temperamento = json.loads(row["temperamento"] or "[]")
    historico = json.loads(row["historico"] or "[]") if row["historico"] else []
    comuns = dict(
        nome=row["nome"],
        idade=row["idade"],
        raca=row["raca"] or "SRD",
        sexo=row["sexo"],
        temperamento=temperamento,
        porte=PorteAnimal[row["porte"]],
        peso=row["peso"],
        data_entrada=date.fromisoformat(row["data_entrada"]),
        status=StatusAnimal[row["status"]],
        castrado=bool(row["castrado"]),
        historico=historico,
        id=row["id"],
    )
    if row["especie"] == "cachorro":
        return Cachorro(**comuns, necessidadePasseio=bool(row["necessidade_passeio"]))
    if row["especie"] == "gato":
        return Gato(
            **comuns,
            independencia=NivelIndependencia[row["independencia"]],
            tipoPelo=TiposPelos[row["tipo_pelo"]],
        )
    raise ValueError(
        f"O animal #{animal_id} não possui espécie cadastrada como cachorro ou gato."
    )


@app.command("cadastrar")
def cadastrar(
    nome: str = typer.Argument(..., help="Nome completo do adotante."),
    idade: int = typer.Argument(..., min=18, help="Idade em anos."),
    telefone: str = typer.Argument(
        ..., help="Telefone com DDD e 11 dígitos, somente números."
    ),
    moradia: str = typer.Argument(..., help="CASA ou APARTAMENTO."),
    area_util: float = typer.Argument(
        ..., min=0.01, help="Área útil da moradia em m²."
    ),
    experiencia: bool = typer.Option(
        False, "--experiencia/--sem-experiencia", help="Experiência com animais."
    ),
    criancas_em_casa: bool = typer.Option(
        False, "--criancas-em-casa/--sem-criancas", help="Há crianças em casa."
    ),
    outros_animais: bool = typer.Option(
        False,
        "--outros-animais/--sem-outros-animais",
        help="Há outros animais em casa.",
    ),
) -> None:
    """Cadastra um adotante."""
    try:
        moradia = normalizar_moradia(moradia)
        candidato = Adotante(
            nome,
            idade,
            telefone,
            Moradia[moradia],
            area_util,
            experiencia,
            criancas_em_casa,
            outros_animais,
        )
        with conectar() as conn:
            cur = conn.execute(
                "INSERT INTO pessoas (nome, idade) VALUES (?, ?)",
                (candidato.nome, candidato.idade),
            )
            id_adotante = cur.lastrowid
            conn.execute(
                """INSERT INTO adotantes
                (pessoa_id, telefone, moradia, areaUtil, experiencia, criancasEmCasa, outrosAnimais)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    id_adotante,
                    candidato.telefone,
                    candidato.moradia.name,
                    candidato.areaUtil,
                    int(candidato.experiencia),
                    int(candidato.criancasEmCasa),
                    int(candidato.outrosAnimais),
                ),
            )
        confirmar(
            f"Adotante [bold]{candidato.nome}[/bold] cadastrado com sucesso. ID: [cyan]{id_adotante}[/cyan]."
        )
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("listar")
def listar() -> None:
    """Lista todos os adotantes cadastrados."""
    try:
        with conectar() as conn:
            rows = conn.execute(
                """SELECT p.id, p.nome, p.idade, a.telefone, a.moradia,
                a.areaUtil, a.experiencia, a.criancasEmCasa, a.outrosAnimais
                FROM pessoas p JOIN adotantes a ON a.pessoa_id=p.id ORDER BY p.id"""
            ).fetchall()
        if not rows:
            console.print(
                Panel(
                    "Nenhum adotante cadastrado.",
                    title="Adotantes",
                    border_style="yellow",
                )
            )
            return
        tabela = Table(title="Adotantes cadastrados", header_style="bold bright_blue")
        for nome, estilo in [
            ("ID", "cyan"),
            ("Nome", "white"),
            ("Idade", "white"),
            ("Telefone", "white"),
            ("Moradia", "white"),
            ("Área (m²)", "white"),
            ("Experiência", "white"),
            ("Crianças", "white"),
            ("Outros animais", "white"),
        ]:
            tabela.add_column(nome, style=estilo)
        for row in rows:
            tabela.add_row(
                str(row["id"]),
                row["nome"],
                str(row["idade"]),
                row["telefone"],
                row["moradia"],
                f"{row['areaUtil']:.1f}",
                "Sim" if row["experiencia"] else "Não",
                "Sim" if row["criancasEmCasa"] else "Não",
                "Sim" if row["outrosAnimais"] else "Não",
            )
        console.print(tabela)
    except sqlite3.Error as exc:
        erro(f"Falha ao listar adotantes: {exc}")


@app.command("ver")
def ver(id_adotante: int = typer.Argument(..., min=1)) -> None:
    """Exibe os dados completos de um adotante."""
    try:
        with conectar() as conn:
            row = buscar_adotante(conn, id_adotante)
        mostrar_adotante(row)
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("atualizar")
def atualizar(
    id_adotante: int = typer.Argument(..., min=1),
    nome: Optional[str] = typer.Option(None, help="Novo nome."),
    idade: Optional[int] = typer.Option(None, min=18, help="Nova idade em anos."),
    telefone: Optional[str] = typer.Option(None, help="Novo telefone com 11 dígitos."),
    moradia: Optional[str] = typer.Option(None, help="CASA ou APARTAMENTO."),
    area_util: Optional[float] = typer.Option(
        None, "--area-util", min=0.01, help="Nova área útil em m²."
    ),
    experiencia: Optional[bool] = typer.Option(None, "--experiencia/--sem-experiencia"),
    criancas_em_casa: Optional[bool] = typer.Option(
        None, "--criancas-em-casa/--sem-criancas"
    ),
    outros_animais: Optional[bool] = typer.Option(
        None, "--outros-animais/--sem-outros-animais"
    ),
) -> None:
    """Atualiza somente os campos informados."""
    try:
        with conectar() as conn:
            atual = buscar_adotante(conn, id_adotante)
            dados = {chave: atual[chave] for chave in atual.keys()}
            alteracoes = {
                "nome": nome,
                "idade": idade,
                "telefone": telefone,
                "moradia": normalizar_moradia(moradia) if moradia is not None else None,
                "areaUtil": area_util,
                "experiencia": experiencia,
                "criancasEmCasa": criancas_em_casa,
                "outrosAnimais": outros_animais,
            }
            nomes_sql = {
                "nome": "nome",
                "idade": "idade",
                "telefone": "telefone",
                "moradia": "moradia",
                "areaUtil": "areaUtil",
                "experiencia": "experiencia",
                "criancasEmCasa": "criancasEmCasa",
                "outrosAnimais": "outrosAnimais",
            }
            dados.update({k: v for k, v in alteracoes.items() if v is not None})
            # Reutiliza as validações da entidade de domínio antes de persistir.
            candidato = Adotante(
                dados["nome"],
                int(dados["idade"]),
                dados["telefone"],
                Moradia[dados["moradia"]],
                float(dados["areaUtil"]),
                bool(dados["experiencia"]),
                bool(dados["criancasEmCasa"]),
                bool(dados["outrosAnimais"]),
                id=id_adotante,
            )
            campos = {
                nomes_sql[k]: getattr(candidato, attr)
                for k, attr in {
                    "nome": "nome",
                    "idade": "idade",
                    "telefone": "telefone",
                    "moradia": "moradia",
                    "areaUtil": "areaUtil",
                    "experiencia": "experiencia",
                    "criancasEmCasa": "criancasEmCasa",
                    "outrosAnimais": "outrosAnimais",
                }.items()
                if alteracoes[k] is not None
            }
            # Enum moradia e bools precisam ser convertidos para valores SQLite.
            campos = {
                k: (
                    v.name
                    if isinstance(v, Moradia)
                    else int(v) if isinstance(v, bool) else v
                )
                for k, v in campos.items()
            }
            if not campos:
                raise ValueError("Informe ao menos uma opção para atualizar.")
            campos_pessoa = {k: v for k, v in campos.items() if k in {"nome", "idade"}}
            campos_adotante = {
                k: v for k, v in campos.items() if k not in {"nome", "idade"}
            }
            if campos_pessoa:
                conn.execute(
                    "UPDATE pessoas SET "
                    + ", ".join(f"{k}=?" for k in campos_pessoa)
                    + " WHERE id=?",
                    (*campos_pessoa.values(), id_adotante),
                )
            if campos_adotante:
                conn.execute(
                    "UPDATE adotantes SET "
                    + ", ".join(f"{k}=?" for k in campos_adotante)
                    + " WHERE pessoa_id=?",
                    (*campos_adotante.values(), id_adotante),
                )
        confirmar(f"Dados do adotante #{id_adotante} atualizados com sucesso.")
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("excluir")
def excluir(
    id_adotante: int = typer.Argument(..., min=1),
    sim: bool = typer.Option(False, "--sim", help="Pula a confirmação."),
) -> None:
    """Exclui um adotante após confirmação."""
    try:
        with conectar() as conn:
            row = buscar_adotante(conn, id_adotante)
            if not sim and not typer.confirm(
                f"Deseja realmente excluir {row['nome']} (ID {id_adotante})?"
            ):
                console.print("[yellow]Operação cancelada.[/yellow]")
                raise typer.Exit()
            conn.execute("DELETE FROM pessoas WHERE id=?", (id_adotante,))
        confirmar(f"Adotante [bold]{row['nome']}[/bold] excluído com sucesso.")
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("elegivel")
def elegivel(
    id_adotante: int = typer.Argument(..., min=1),
    id_animal: int = typer.Argument(..., min=1),
) -> None:
    """Avalia as políticas de elegibilidade configuradas no settings.json."""
    try:
        cfg = load_settings()
        with conectar() as conn:
            adotante = objeto_adotante(buscar_adotante(conn, id_adotante))
            animal = buscar_animal_objeto(conn, id_animal)
        regras = [
            (
                f"Idade mínima ({cfg.idade_minima_adotante} anos)",
                adotante.idade >= cfg.idade_minima_adotante,
                f"Idade informada: {adotante.idade}",
            ),
        ]
        porte_restrito = animal.porte.name in cfg.portes_restritos
        if porte_restrito:
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
        tabela = Table(
            title=f"Elegibilidade — {adotante.nome} × {animal.nome}",
            header_style="bold bright_blue",
        )
        tabela.add_column("Regra")
        tabela.add_column("Resultado", justify="center")
        tabela.add_column("Detalhe")
        for nome_regra, passou, detalhe in regras:
            tabela.add_row(
                nome_regra,
                "[green]✔ Atendida[/green]" if passou else "[red]✘ Não atendida[/red]",
                detalhe,
            )
        console.print(tabela)
        if all(regra[1] for regra in regras):
            console.print(
                Panel(
                    "Adotante elegível conforme as políticas configuradas.",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel("Adotante não atende a todas as políticas.", border_style="red")
            )
    except (ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("compatibilidade")
def compatibilidade(
    id_adotante: int = typer.Argument(..., min=1),
    id_animal: int = typer.Argument(..., min=1),
) -> None:
    """Calcula a compatibilidade (0–100) e detalha os critérios ponderados."""
    try:
        with conectar() as conn:
            adotante = objeto_adotante(buscar_adotante(conn, id_adotante))
            animal = buscar_animal_objeto(conn, id_animal)
        resultado = CompatibilidadePonderada(load_settings()).detalhar(adotante, animal)
        rotulos = {
            "porte_moradia": "Porte × moradia",
            "idade_energia": "Idade × energia",
            "experiencia": "Experiência",
            "criancas": "Crianças em casa",
        }
        pesos = load_settings().pesos
        tabela = Table(
            title=f"Compatibilidade — {adotante.nome} × {animal.nome}",
            header_style="bold bright_blue",
        )
        tabela.add_column("Critério")
        tabela.add_column("Nota", justify="right")
        tabela.add_column("Peso", justify="right")
        for criterio, nota in resultado.detalhes.items():
            tabela.add_row(
                rotulos[criterio], f"{nota * 100:.1f}/100", f"{pesos[criterio]:g}"
            )
        console.print(tabela)
        cor = (
            "green"
            if resultado.score >= 75
            else "yellow" if resultado.score >= 50 else "red"
        )
        console.print(
            Panel(
                f"[bold]Pontuação final: [{cor}]{resultado.score:.1f}/100[/{cor}][/bold]",
                title="Resultado",
                border_style=cor,
            )
        )
    except (ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        erro(str(exc))
