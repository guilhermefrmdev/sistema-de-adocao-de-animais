"""Comandos CLI para cadastro e manutenção de animais."""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.table import Table

from sistema_de_adocao_de_animais.cli.console import console
from sistema_de_adocao_de_animais.cli.erros import confirmar, erro

app = typer.Typer(
    help="Cadastro, consulta e manutenção dos animais.", no_args_is_help=True
)
DB_PATH = Path(__file__).resolve().parents[2] / "database" / "database.db"


def conectar() -> sqlite3.Connection:
    """Abre o banco e garante compatibilidade com o esquema atual."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # Reutiliza o esquema do repositório existente e adiciona campos que a CLI precisa.
    conn.execute("""CREATE TABLE IF NOT EXISTS animais (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, idade INTEGER NOT NULL,
        raca TEXT, sexo TEXT NOT NULL, status TEXT NOT NULL, temperamento TEXT,
        porte TEXT NOT NULL, peso REAL NOT NULL, data_entrada TEXT NOT NULL, historico TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS cachorros (
        animal_id INTEGER PRIMARY KEY, necessidade_passeio BOOLEAN NOT NULL DEFAULT 0,
        FOREIGN KEY (animal_id) REFERENCES animais(id) ON DELETE CASCADE
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS gatos (
        animal_id INTEGER PRIMARY KEY, independencia TEXT, tipo_pelo TEXT,
        FOREIGN KEY (animal_id) REFERENCES animais(id) ON DELETE CASCADE
    )""")
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(animais)")}
    if "castrado" not in cols:
        conn.execute(
            "ALTER TABLE animais ADD COLUMN castrado INTEGER NOT NULL DEFAULT 0"
        )
    conn.commit()
    return conn


def enum_valor(
    valor: str, permitidos: list[str], rotulos: dict[str, str] | None = None
) -> str:
    """Normaliza enum e aplica atalhos documentados."""
    normalizado = valor.strip().upper().replace("-", "_")
    if rotulos:
        normalizado = rotulos.get(normalizado, normalizado)
    if normalizado not in permitidos:
        raise ValueError(f"Valor '{valor}' inválido. Opções: {', '.join(permitidos)}.")
    return normalizado


def parse_data(valor: str) -> str:
    try:
        return date.fromisoformat(valor).isoformat()
    except ValueError as exc:
        raise ValueError("Data inválida. Use o formato AAAA-MM-DD.") from exc


def buscar(conn: sqlite3.Connection, animal_id: int) -> sqlite3.Row:
    row = conn.execute(
        """SELECT a.*, CASE WHEN c.animal_id IS NOT NULL THEN 'cachorro'
        WHEN g.animal_id IS NOT NULL THEN 'gato' ELSE 'animal' END AS especie,
        c.necessidade_passeio, g.independencia, g.tipo_pelo
        FROM animais a LEFT JOIN cachorros c ON c.animal_id=a.id
        LEFT JOIN gatos g ON g.animal_id=a.id WHERE a.id=?""",
        (animal_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Animal com ID {animal_id} não encontrado.")
    return row


def temperamentos(valor: str | None) -> list[str]:
    return [item.strip() for item in (valor or "").split(",") if item.strip()]


def historico_json(valor: str | None) -> list[dict]:
    if not valor:
        return []
    try:
        dados = json.loads(valor)
        return dados if isinstance(dados, list) else []
    except json.JSONDecodeError, TypeError:
        return [{"tipo": "REGISTRO_ANTERIOR", "nome": str(valor), "data": ""}]


def salvar_evento(
    conn: sqlite3.Connection,
    animal: sqlite3.Row,
    tipo: str,
    nome: str,
    data_evento: str,
) -> None:
    eventos = historico_json(animal["historico"])
    eventos.append(
        {"tipo": tipo.strip().upper(), "nome": nome.strip(), "data": data_evento}
    )
    conn.execute(
        "UPDATE animais SET historico=? WHERE id=?",
        (json.dumps(eventos, ensure_ascii=False), animal["id"]),
    )


def mostrar_animal(row: sqlite3.Row) -> None:
    campos = [
        ("ID", row["id"]),
        ("Nome", row["nome"]),
        ("Espécie", row["especie"].capitalize()),
        ("Raça", row["raca"] or "Não informada"),
        ("Idade", f"{row['idade']} meses"),
        ("Sexo", row["sexo"]),
        ("Peso", f"{row['peso']} kg"),
        ("Porte", row["porte"]),
        ("Status", row["status"]),
        ("Castrado", "Sim" if row["castrado"] else "Não"),
        (
            "Temperamento",
            ", ".join(temperamentos(row["temperamento"])) or "Não informado",
        ),
        ("Entrada no abrigo", row["data_entrada"]),
    ]
    if row["especie"] == "cachorro":
        campos.append(
            ("Necessita passeio", "Sim" if row["necessidade_passeio"] else "Não")
        )
    if row["especie"] == "gato":
        campos.extend(
            [
                ("Independência", row["independencia"]),
                ("Tipo de pelo", row["tipo_pelo"]),
            ]
        )
    tabela = Table.grid(padding=(0, 2))
    tabela.add_column(style="bold cyan", justify="right")
    tabela.add_column()
    for chave, valor in campos:
        tabela.add_row(f"{chave}:", str(valor))
    console.print(Panel(tabela, title=f"Animal #{row['id']}", border_style="blue"))


cachorro_app = typer.Typer(help="Cadastro de cachorros.", no_args_is_help=True)
gato_app = typer.Typer(help="Cadastro de gatos.", no_args_is_help=True)


@cachorro_app.command("cadastrar")
def cadastrar_cachorro(
    nome: str = typer.Argument(..., help="Nome do cachorro."),
    idade: int = typer.Argument(..., min=1, help="Idade em meses."),
    raca: str = typer.Argument(..., help="Raça do cachorro."),
    sexo: str = typer.Argument(..., help="Sexo: M ou F."),
    peso: float = typer.Argument(..., min=0.01, help="Peso em kg."),
    porte: str = typer.Argument(
        ..., help="Porte: MINI, PEQUENO, MEDIO, GRANDE ou GIGANTE."
    ),
    necessidade_passeio: bool = typer.Option(
        False,
        "--necessidade-passeio/--sem-necessidade-passeio",
        help="Se precisa passear.",
    ),
    castrado: bool = typer.Option(
        False, "--castrado/--nao-castrado", help="Se é castrado."
    ),
    temperamento: Optional[str] = typer.Option(
        None, help="Temperamentos separados por vírgula."
    ),
    status: str = typer.Option(
        "DISPONIVEL", help="Status inicial: DISPONIVEL, INADOTAVEL ou QUARENTENA."
    ),
    data_entrada: Optional[str] = typer.Option(
        None, "--data-entrada", help="Data AAAA-MM-DD (padrão: hoje)."
    ),
) -> None:
    """Cadastra um cachorro no abrigo."""
    try:
        sexo = enum_valor(sexo, ["M", "F"])
        porte = enum_valor(
            porte,
            ["MINI", "PEQUENO", "MEDIO", "GRANDE", "GIGANTE"],
            {"P": "PEQUENO", "M": "MEDIO", "G": "GRANDE"},
        )
        status = enum_valor(status, ["DISPONIVEL", "INADOTAVEL", "QUARENTENA"])
        data_entrada = (
            parse_data(data_entrada) if data_entrada else date.today().isoformat()
        )
        if not nome.strip() or not raca.strip():
            raise ValueError("Nome e raça não podem ser vazios.")
        with conectar() as conn:
            cur = conn.execute(
                "INSERT INTO animais (nome,idade,raca,sexo,status,temperamento,porte,peso,data_entrada,historico,castrado) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    nome.strip(),
                    idade,
                    raca.strip(),
                    sexo,
                    status,
                    json.dumps(temperamentos(temperamento), ensure_ascii=False),
                    porte,
                    peso,
                    data_entrada,
                    "[]",
                    int(castrado),
                ),
            )
            animal_id = cur.lastrowid
            conn.execute(
                "INSERT INTO cachorros (animal_id,necessidade_passeio) VALUES (?,?)",
                (animal_id, int(necessidade_passeio)),
            )
            animal = buscar(conn, animal_id)
            salvar_evento(conn, animal, "ENTRADA", "Cadastro do animal", data_entrada)
        confirmar(
            f"Cachorro [bold]{nome}[/bold] cadastrado com sucesso. ID: [cyan]{animal_id}[/cyan]."
        )
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))


@gato_app.command("cadastrar")
def cadastrar_gato(
    nome: str = typer.Argument(..., help="Nome do gato."),
    idade: int = typer.Argument(..., min=1, help="Idade em meses."),
    raca: str = typer.Argument(..., help="Raça do gato."),
    sexo: str = typer.Argument(..., help="Sexo: M ou F."),
    peso: float = typer.Argument(..., min=0.01, help="Peso em kg."),
    porte: str = typer.Argument(..., help="Porte do gato."),
    independencia: str = typer.Argument(..., help="BAIXA, MEDIA ou ALTA."),
    tipo_pelo: str = typer.Argument(..., help="SEM_PELOS, CURTO, LONGO ou ONDULADO."),
    castrado: bool = typer.Option(
        False, "--castrado/--nao-castrado", help="Se é castrado."
    ),
    temperamento: Optional[str] = typer.Option(
        None, help="Temperamentos separados por vírgula."
    ),
    status: str = typer.Option(
        "DISPONIVEL", help="Status inicial: DISPONIVEL, INADOTAVEL ou QUARENTENA."
    ),
    data_entrada: Optional[str] = typer.Option(
        None, "--data-entrada", help="Data AAAA-MM-DD (padrão: hoje)."
    ),
) -> None:
    """Cadastra um gato no abrigo."""
    try:
        sexo = enum_valor(sexo, ["M", "F"])
        porte = enum_valor(
            porte,
            ["MINI", "PEQUENO", "MEDIO", "GRANDE", "GIGANTE"],
            {"P": "PEQUENO", "M": "MEDIO", "G": "GRANDE"},
        )
        independencia = enum_valor(independencia, ["BAIXA", "MEDIA", "ALTA"])
        tipo_pelo = enum_valor(tipo_pelo, ["SEM_PELOS", "CURTO", "LONGO", "ONDULADO"])
        status = enum_valor(status, ["DISPONIVEL", "INADOTAVEL", "QUARENTENA"])
        data_entrada = (
            parse_data(data_entrada) if data_entrada else date.today().isoformat()
        )
        if not nome.strip() or not raca.strip():
            raise ValueError("Nome e raça não podem ser vazios.")
        with conectar() as conn:
            cur = conn.execute(
                "INSERT INTO animais (nome,idade,raca,sexo,status,temperamento,porte,peso,data_entrada,historico,castrado) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    nome.strip(),
                    idade,
                    raca.strip(),
                    sexo,
                    status,
                    json.dumps(temperamentos(temperamento), ensure_ascii=False),
                    porte,
                    peso,
                    data_entrada,
                    "[]",
                    int(castrado),
                ),
            )
            animal_id = cur.lastrowid
            conn.execute(
                "INSERT INTO gatos (animal_id,independencia,tipo_pelo) VALUES (?,?,?)",
                (animal_id, independencia, tipo_pelo),
            )
            animal = buscar(conn, animal_id)
            salvar_evento(conn, animal, "ENTRADA", "Cadastro do animal", data_entrada)
        confirmar(
            f"Gato [bold]{nome}[/bold] cadastrado com sucesso. ID: [cyan]{animal_id}[/cyan]."
        )
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))


app.add_typer(cachorro_app, name="cachorro")
app.add_typer(gato_app, name="gato")


@app.command("listar")
def listar(
    especie: Optional[str] = typer.Option(None, help="Filtrar por cachorro ou gato."),
    porte: Optional[str] = typer.Option(None, help="Filtrar por porte."),
    status: Optional[str] = typer.Option(None, help="Filtrar por status."),
    idade_min: Optional[int] = typer.Option(None, min=0, help="Idade mínima em meses."),
    idade_max: Optional[int] = typer.Option(None, min=0, help="Idade máxima em meses."),
    temperamento: Optional[str] = typer.Option(
        None, help="Termo presente no temperamento."
    ),
) -> None:
    """Lista animais; filtros informados são combinados com AND."""
    try:
        filtros, params = [], []
        if especie:
            especie = enum_valor(especie, ["CACHORRO", "GATO"]).lower()
        if porte:
            filtros.append("UPPER(a.porte)=?")
            params.append(
                enum_valor(
                    porte,
                    ["MINI", "PEQUENO", "MEDIO", "GRANDE", "GIGANTE"],
                    {"P": "PEQUENO", "M": "MEDIO", "G": "GRANDE"},
                )
            )
        if status:
            filtros.append("UPPER(a.status)=?")
            params.append(
                enum_valor(
                    status,
                    [
                        "DISPONIVEL",
                        "RESERVADO",
                        "ADOTADO",
                        "DEVOLVIDO",
                        "QUARENTENA",
                        "INADOTAVEL",
                    ],
                )
            )
        if idade_min is not None:
            filtros.append("a.idade>=?")
            params.append(idade_min)
        if idade_max is not None:
            filtros.append("a.idade<=?")
            params.append(idade_max)
        if temperamento:
            filtros.append("LOWER(a.temperamento) LIKE ?")
            params.append(f"%{temperamento.lower()}%")
        if especie == "cachorro":
            filtros.append("c.animal_id IS NOT NULL")
        elif especie == "gato":
            filtros.append("g.animal_id IS NOT NULL")
        sql = """SELECT a.*, CASE WHEN c.animal_id IS NOT NULL THEN 'cachorro' WHEN g.animal_id IS NOT NULL THEN 'gato' ELSE 'animal' END especie
            FROM animais a LEFT JOIN cachorros c ON c.animal_id=a.id LEFT JOIN gatos g ON g.animal_id=a.id"""
        if filtros:
            sql += " WHERE " + " AND ".join(filtros)
        sql += " ORDER BY a.id"
        with conectar() as conn:
            rows = conn.execute(sql, params).fetchall()
        tabela = Table(
            title=f"Animais cadastrados ({len(rows)})", header_style="bold cyan"
        )
        for col in ["ID", "Nome", "Espécie", "Idade (meses)", "Porte", "Status"]:
            tabela.add_column(col)
        for row in rows:
            tabela.add_row(
                str(row["id"]),
                row["nome"],
                row["especie"].capitalize(),
                str(row["idade"]),
                row["porte"],
                row["status"],
            )
        console.print(
            tabela
            if rows
            else Panel(
                "Nenhum animal encontrado com os filtros informados.",
                title="Resultado",
                border_style="yellow",
            )
        )
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("ver")
def ver(id_animal: int = typer.Argument(..., min=1, help="ID do animal.")) -> None:
    """Exibe os dados completos de um animal."""
    try:
        with conectar() as conn:
            row = buscar(conn, id_animal)
        mostrar_animal(row)
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("atualizar")
def atualizar(
    id_animal: int = typer.Argument(..., min=1),
    nome: Optional[str] = typer.Option(None),
    idade: Optional[int] = typer.Option(None, min=1),
    raca: Optional[str] = typer.Option(None),
    peso: Optional[float] = typer.Option(None, min=0.01),
    porte: Optional[str] = typer.Option(None),
    castrado: Optional[bool] = typer.Option(None, "--castrado/--nao-castrado"),
    temperamento: Optional[str] = typer.Option(None),
    necessidade_passeio: Optional[bool] = typer.Option(
        None, "--necessidade-passeio/--sem-necessidade-passeio"
    ),
    independencia: Optional[str] = typer.Option(None),
    tipo_pelo: Optional[str] = typer.Option(None, "--tipo-pelo"),
) -> None:
    """Atualiza apenas os campos explicitamente informados."""
    try:
        changes: dict[str, object] = {}
        if nome is not None:
            if not nome.strip():
                raise ValueError("O nome não pode ser vazio.")
            changes["nome"] = nome.strip()
        if idade is not None:
            changes["idade"] = idade
        if raca is not None:
            if not raca.strip():
                raise ValueError("A raça não pode ser vazia.")
            changes["raca"] = raca.strip()
        if peso is not None:
            changes["peso"] = peso
        if porte is not None:
            changes["porte"] = enum_valor(
                porte,
                ["MINI", "PEQUENO", "MEDIO", "GRANDE", "GIGANTE"],
                {"P": "PEQUENO", "M": "MEDIO", "G": "GRANDE"},
            )
        if castrado is not None:
            changes["castrado"] = int(castrado)
        if temperamento is not None:
            changes["temperamento"] = json.dumps(
                temperamentos(temperamento), ensure_ascii=False
            )
        if (
            not changes
            and necessidade_passeio is None
            and independencia is None
            and tipo_pelo is None
        ):
            raise ValueError("Informe pelo menos uma opção para atualizar.")
        with conectar() as conn:
            row = buscar(conn, id_animal)
            if necessidade_passeio is not None:
                if row["especie"] != "cachorro":
                    raise ValueError(
                        "--necessidade-passeio só pode ser usado para cachorro."
                    )
                conn.execute(
                    "UPDATE cachorros SET necessidade_passeio=? WHERE animal_id=?",
                    (int(necessidade_passeio), id_animal),
                )
            if independencia is not None:
                if row["especie"] != "gato":
                    raise ValueError("--independencia só pode ser usado para gato.")
                independencia = enum_valor(independencia, ["BAIXA", "MEDIA", "ALTA"])
                conn.execute(
                    "UPDATE gatos SET independencia=? WHERE animal_id=?",
                    (independencia, id_animal),
                )
            if tipo_pelo is not None:
                if row["especie"] != "gato":
                    raise ValueError("--tipo-pelo só pode ser usado para gato.")
                tipo_pelo = enum_valor(
                    tipo_pelo, ["SEM_PELOS", "CURTO", "LONGO", "ONDULADO"]
                )
                conn.execute(
                    "UPDATE gatos SET tipo_pelo=? WHERE animal_id=?",
                    (tipo_pelo, id_animal),
                )
            if changes:
                conn.execute(
                    "UPDATE animais SET "
                    + ",".join(f"{campo}=?" for campo in changes)
                    + " WHERE id=?",
                    (*changes.values(), id_animal),
                )
        confirmar(f"Dados do animal #{id_animal} atualizados.")
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("excluir")
def excluir(
    id_animal: int = typer.Argument(..., min=1),
    sim: bool = typer.Option(False, "--sim", help="Pula a confirmação."),
) -> None:
    """Exclui um animal cadastrado."""
    try:
        with conectar() as conn:
            row = buscar(conn, id_animal)
            if not sim and not typer.confirm(
                f"Deseja excluir {row['nome']} (ID {id_animal})?"
            ):
                console.print("Operação cancelada.", style="yellow")
                raise typer.Exit()
            conn.execute("DELETE FROM animais WHERE id=?", (id_animal,))
        confirmar(f"Animal #{id_animal} excluído.")
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("historico")
def historico(id_animal: int = typer.Argument(..., min=1)) -> None:
    """Mostra os eventos registrados no histórico do animal."""
    try:
        with conectar() as conn:
            row = buscar(conn, id_animal)
        eventos = historico_json(row["historico"])
        tabela = Table(
            title=f"Histórico de {row['nome']} (#{id_animal})", header_style="bold cyan"
        )
        tabela.add_column("Data")
        tabela.add_column("Tipo")
        tabela.add_column("Descrição")
        for evento in eventos:
            data_evento = evento.get("data", "")
            if isinstance(data_evento, dict):
                data_evento = data_evento.get("isoformat", "")
            tabela.add_row(
                str(data_evento or "—"),
                str(evento.get("tipo", "—")),
                str(evento.get("nome", "—")),
            )
        console.print(
            tabela
            if eventos
            else Panel("Nenhum evento registrado.", border_style="yellow")
        )
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("adicionar-historico")
def adicionar_historico(
    id_animal: int = typer.Argument(..., min=1),
    tipo: str = typer.Argument(...),
    nome: str = typer.Argument(...),
    data: Optional[str] = typer.Option(None, help="Data AAAA-MM-DD (padrão: hoje)."),
) -> None:
    """Registra um evento no histórico do animal."""
    try:
        if not tipo.strip() or not nome.strip():
            raise ValueError("Tipo e descrição não podem ser vazios.")
        data_evento = parse_data(data) if data else date.today().isoformat()
        with conectar() as conn:
            row = buscar(conn, id_animal)
            salvar_evento(conn, row, tipo, nome, data_evento)
        confirmar(f"Evento '{tipo.upper()}' registrado para o animal #{id_animal}.")
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("vacinar")
def vacinar(
    id_animal: int = typer.Argument(..., min=1),
    nome_vacina: str = typer.Argument(...),
    data: Optional[str] = typer.Option(None, help="Data AAAA-MM-DD (padrão: hoje)."),
) -> None:
    """Registra uma vacina no histórico do animal."""
    try:
        if not nome_vacina.strip():
            raise ValueError("O nome da vacina não pode ser vazio.")
        data_evento = parse_data(data) if data else date.today().isoformat()
        with conectar() as conn:
            row = buscar(conn, id_animal)
            salvar_evento(conn, row, "VACINA", nome_vacina, data_evento)
        confirmar(
            f"Vacina [bold]{nome_vacina}[/bold] registrada para o animal #{id_animal}."
        )
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("mudar-status")
def mudar_status(
    id_animal: int = typer.Argument(..., min=1), status: str = typer.Argument(...)
) -> None:
    """Altera o status respeitando as transições permitidas."""
    transicoes = {
        "DISPONIVEL": {"RESERVADO", "INADOTAVEL"},
        "RESERVADO": {"ADOTADO"},
        "ADOTADO": {"DEVOLVIDO"},
        "DEVOLVIDO": {"QUARENTENA", "DISPONIVEL", "INADOTAVEL"},
        "QUARENTENA": {"DISPONIVEL", "INADOTAVEL"},
        "INADOTAVEL": set(),
    }
    try:
        status_novo = enum_valor(status, list(transicoes))
        with conectar() as conn:
            row = buscar(conn, id_animal)
            atual = row["status"].upper()
            if status_novo not in transicoes.get(atual, set()):
                raise ValueError(f"Transição inválida: {atual} → {status_novo}.")
            conn.execute(
                "UPDATE animais SET status=? WHERE id=?", (status_novo, id_animal)
            )
            salvar_evento(
                conn,
                row,
                "MUDANCA_STATUS",
                f"{atual} → {status_novo}",
                date.today().isoformat(),
            )
        confirmar(
            f"Status do animal #{id_animal}: [yellow]{atual}[/yellow] → [green]{status_novo}[/green]."
        )
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))


@app.command("reavaliar")
def reavaliar(
    id_animal: int = typer.Argument(..., min=1),
    status: str = typer.Argument(..., help="DISPONIVEL ou INADOTAVEL."),
    observacao: Optional[str] = typer.Option(
        None, help="Observação registrada no histórico."
    ),
) -> None:
    """Reavalia animal em quarentena ou devolvido."""
    try:
        status_novo = enum_valor(status, ["DISPONIVEL", "INADOTAVEL"])
        with conectar() as conn:
            row = buscar(conn, id_animal)
            atual = row["status"].upper()
            if atual not in {"QUARENTENA", "DEVOLVIDO"}:
                raise ValueError(
                    "A reavaliação só é permitida para animais em QUARENTENA ou DEVOLVIDO."
                )
            conn.execute(
                "UPDATE animais SET status=? WHERE id=?", (status_novo, id_animal)
            )
            descricao = f"Reavaliação: {atual} → {status_novo}"
            if observacao:
                descricao += f". Observação: {observacao.strip()}"
            salvar_evento(conn, row, "REAVALIACAO", descricao, date.today().isoformat())
        confirmar(f"Animal #{id_animal} reavaliado: {atual} → {status_novo}.")
    except (ValueError, sqlite3.Error) as exc:
        erro(str(exc))
