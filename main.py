"""Ponto de entrada da CLI. Permite executar sem instalar o pacote."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from sistema_de_adocao_de_animais.cli.main import app

if __name__ == "__main__":
    app()
