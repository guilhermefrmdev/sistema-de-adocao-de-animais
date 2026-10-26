from pathlib import Path

# Cria o arquivo 'database/database.db' se ele não existir
raiz = Path(__file__).resolve().parent.parent
caminho_db = raiz / "database" / "database.db"
with open(caminho_db, "a", encoding="utf-8") as arquivo:
    ...
