"""Tratamento padronizado de erros para comandos CLI."""

import typer
from rich.panel import Panel

from sistema_de_adocao_de_animais.cli.console import console


def erro(mensagem: str) -> None:
    """Exibe um erro amigável e encerra o comando com código 1."""
    console.print(Panel(mensagem, title="Erro", border_style="red", expand=False))
    raise typer.Exit(code=1)


def confirmar(mensagem: str) -> None:
    """Exibe confirmação de uma operação concluída."""
    console.print(
        Panel(mensagem, title="Concluído", border_style="green", expand=False)
    )
