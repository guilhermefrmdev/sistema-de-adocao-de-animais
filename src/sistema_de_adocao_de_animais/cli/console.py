"""Console Rich compartilhado pela CLI."""

from rich.console import Console
from rich.theme import Theme

THEME = Theme(
    {
        "success": "bold green",
        "error": "bold red",
        "info": "cyan",
        "muted": "dim",
        "heading": "bold bright_blue",
    }
)
console = Console(theme=THEME)
