"""Aplicação principal da interface de linha de comando."""

import typer
from rich.panel import Panel

from sistema_de_adocao_de_animais.cli.commands.adocao import app as adocao_app
from sistema_de_adocao_de_animais.cli.commands.adotante import app as adotante_app
from sistema_de_adocao_de_animais.cli.commands.animal import app as animal_app
from sistema_de_adocao_de_animais.cli.commands.fila import app as fila_app
from sistema_de_adocao_de_animais.cli.commands.reserva import app as reserva_app
from sistema_de_adocao_de_animais.cli.console import console

app = typer.Typer(
    name="adocao",
    help="Sistema de adoção de animais — gerenciamento via terminal.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
app.add_typer(animal_app, name="animal")
app.add_typer(adotante_app, name="adotante")
app.add_typer(reserva_app, name="reserva")
app.add_typer(adocao_app, name="adocao")
app.add_typer(fila_app, name="fila")


@app.callback(invoke_without_command=True)
def inicio(ctx: typer.Context) -> None:
    """Apresenta o sistema quando nenhum subcomando é informado."""
    if ctx.invoked_subcommand is None:
        console.print(
            Panel(
                "[bold]Sistema de Adoção de Animais[/bold]\nGerencie animais, adotantes, reservas e o processo de adoção.\n\nUse [cyan]python main.py --help[/cyan] para ver os comandos.",
                title="Bem-vindo",
                border_style="blue",
            )
        )


if __name__ == "__main__":
    app()
