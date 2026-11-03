"""Comandos CLI para gerenciamento da lista de espera por animal."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

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
from sistema_de_adocao_de_animais.domain.fila_espera import EntradaFila, FilaDeEspera
from sistema_de_adocao_de_animais.exceptions.repositorio_error import RepositorioError
from sistema_de_adocao_de_animais.repositories.fila_de_espera_repository import (
    FilaDeEsperaRepository,
)
from sistema_de_adocao_de_animais.settings import load_settings
from sistema_de_adocao_de_animais.strategies.compatibilidade_strategy import (
    CompatibilidadePonderada,
)

app = typer.Typer(
    help="Gerenciamento da lista de espera por animal.", no_args_is_help=True
)
DB_PATH = Path(__file__).resolve().parents[2] / "database" / "database.db"


def _abrir_contexto():
    """Garante os esquemas compartilhados e retorna conexão e repositório."""
    conectar_animais().close()
    conn = conectar_adotantes()
    return conn, FilaDeEsperaRepository(DB_PATH)


def _carregar_fila(
    conn: sqlite3.Connection, repo: FilaDeEsperaRepository, id_animal: int
) -> FilaDeEspera:
    """Reconstrói a fila persistida como objetos de domínio."""
    animal = buscar_animal_objeto(conn, id_animal)
    entradas: list[EntradaFila] = []
    for registro in repo.buscarPorIdAnimal(id_animal):
        adotante = objeto_adotante(buscar_adotante(conn, registro.adotante_id))
        entradas.append(
            EntradaFila(
                adotante=adotante,
                compatibilidade=registro.compatibilidade,
                data_entrada=registro.data_entrada,
                prioridade=registro.prioridade,
            )
        )
    return FilaDeEspera(animal, load_settings(), entradas)


@app.command("entrar")
def entrar(
    id_adotante: int = typer.Argument(..., min=1, help="ID do adotante."),
    id_animal: int = typer.Argument(..., min=1, help="ID do animal desejado."),
) -> None:
    """Calcula a compatibilidade e insere o adotante na fila do animal."""
    conn = None
    try:
        conn, repo = _abrir_contexto()
        adotante = objeto_adotante(buscar_adotante(conn, id_adotante))
        animal = buscar_animal_objeto(conn, id_animal)
        fila = _carregar_fila(conn, repo, id_animal)
        compatibilidade = CompatibilidadePonderada(load_settings()).calcular(
            adotante, animal
        )
        entrada = fila.adicionar(adotante, compatibilidade)
        repo.salvar(fila)
        confirmar(
            f"{adotante.nome} entrou na lista de espera de {animal.nome}.\n"
            f"Compatibilidade: {compatibilidade:.1f}/100 | "
            f"Posição atual: {fila.posicao(adotante)} | Prioridade: {entrada.prioridade:.1f}"
        )
    except (ValueError, KeyError, TypeError, sqlite3.Error, RepositorioError) as exc:
        erro(str(exc))
    finally:
        if conn is not None:
            conn.close()


@app.command("ver")
def ver(id_animal: int = typer.Argument(..., min=1, help="ID do animal.")) -> None:
    """Mostra a lista de espera do animal ordenada por prioridade atual."""
    conn = None
    try:
        conn, repo = _abrir_contexto()
        animal = buscar_animal_objeto(conn, id_animal)
        fila = _carregar_fila(conn, repo, id_animal)
        fila.atualizar_lista()
        if len(fila) == 0:
            console.print(
                Panel(
                    f"Ninguém está aguardando por {animal.nome} (#{id_animal}).",
                    title="Lista de espera",
                    border_style="yellow",
                )
            )
            return

        # Persiste as prioridades e posições recalculadas com o tempo decorrido.
        repo.atualizarLista(fila)
        tabela = Table(
            title=f"Lista de espera — {animal.nome} (#{id_animal})",
            header_style="bold bright_blue",
        )
        for coluna in (
            "Pos.",
            "ID",
            "Adotante",
            "Compatibilidade",
            "Dias",
            "Prioridade",
        ):
            tabela.add_column(
                coluna, justify="right" if coluna != "Adotante" else "left"
            )
        agora = datetime.now()
        for posicao, entrada in enumerate(fila.fila, start=1):
            dias = max(0, (agora - entrada.data_entrada).days)
            tabela.add_row(
                str(posicao),
                str(entrada.adotante.id),
                entrada.adotante.nome,
                f"{entrada.compatibilidade:.1f}/100",
                str(dias),
                f"{entrada.prioridade:.1f}/100",
            )
        console.print(tabela)
    except (ValueError, KeyError, TypeError, sqlite3.Error, RepositorioError) as exc:
        erro(str(exc))
    finally:
        if conn is not None:
            conn.close()


@app.command("sair")
def sair(
    id_adotante: int = typer.Argument(..., min=1, help="ID do adotante."),
    id_animal: int = typer.Argument(..., min=1, help="ID do animal."),
) -> None:
    """Remove o adotante da lista de espera do animal."""
    conn = None
    try:
        conn, repo = _abrir_contexto()
        # Valida os dois IDs para apresentar erros amigáveis antes da remoção.
        buscar_adotante(conn, id_adotante)
        buscar_animal_objeto(conn, id_animal)
        repo.removerEntrada(id_animal, id_adotante)
        confirmar(
            f"Adotante #{id_adotante} removido da lista de espera do animal #{id_animal}."
        )
    except (ValueError, KeyError, TypeError, sqlite3.Error, RepositorioError) as exc:
        erro(str(exc))
    finally:
        if conn is not None:
            conn.close()
