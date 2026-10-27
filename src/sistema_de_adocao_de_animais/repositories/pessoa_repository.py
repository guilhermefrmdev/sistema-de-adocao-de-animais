import sqlite3
from pathlib import Path


class PessoaRepository:
    """
    Repositório responsável pela conexão e persistência de pessoas e adotantes.
    """

    def __init__(self):
        self.raiz = Path(__file__).resolve().parent.parent
        self.caminho_db = self.raiz / "database" / "database.db"

        # Cria as tabelas caso ainda não existam.
        with self.conectar() as connection:
            cursor = connection.cursor()

            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pessoas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    idade INTEGER NOT NULL
                )
                """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS adotantes (
                    pessoa_id INTEGER PRIMARY KEY,
                    telefone TEXT NOT NULL,
                    moradia TEXT NOT NULL,
                    areaUtil REAL NOT NULL,
                    experiencia INTEGER NOT NULL
                        CHECK (experiencia IN (0, 1)),
                    criancasEmCasa INTEGER NOT NULL
                        CHECK (criancasEmCasa IN (0, 1)),
                    outrosAnimais INTEGER NOT NULL
                        CHECK (outrosAnimais IN (0, 1)),
                    FOREIGN KEY (pessoa_id)
                        REFERENCES pessoas(id)
                        ON DELETE CASCADE
                )
                """)

    # Conexão com o banco de dados
    def conectar(self):
        connection = sqlite3.connect(self.caminho_db)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    # Cadastrar pessoas no banco e retorna o ID
    def cadastrarPessoa(self, nome: str, idade: int) -> int:
        with self.conectar() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO pessoas (nome, idade) VALUES (?, ?)",
                (nome, idade),
            )
            return cursor.lastrowid

    # Cadastra adotante no banco e retorna o ID
    def cadastrarAdotante(
        self,
        nome: str,
        idade: int,
        telefone: str,
        moradia: str,
        areaUtil: float,
        experiencia: bool,
        criancasEmCasa: bool,
        outrosAnimais: bool,
    ) -> int:

        pessoa_id = self.cadastrarPessoa(nome, idade)

        with self.conectar() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO adotantes (
                    id,
                    telefone,
                    moradia,
                    areaUtil,
                    experiencia,
                    criancasEmCasa,
                    outrosAnimais
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    id,
                    telefone,
                    moradia,
                    areaUtil,
                    int(experiencia),
                    int(criancasEmCasa),
                    int(outrosAnimais),
                ),
            )

            return pessoa_id

    # Exclui pessoa pelo ID
    def excluirPessoa(self, id: int):
        with self.conectar() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM pessoas WHERE id = ?", (id,))


pessoa = PessoaRepository()
