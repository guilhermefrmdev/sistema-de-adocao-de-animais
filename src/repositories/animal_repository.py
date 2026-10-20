import sqlite3
from pathlib import Path

from src.enums.status_animal import StatusAnimal

class AnimalRepository:
    """
        Interface que faz a conecção e salva dados no banco de dados de animais.
    """
    def __init__(self):
        self.raiz = Path(__file__).resolve().parent.parent.parent
        self.caminho_db = self.raiz / "database" / "database.db"

        with self.conectar() as connection:
            cursor = connection.cursor()

            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("""CREATE TABLE IF NOT EXISTS animais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                idade INTEGER NOT NULL,
                raca TEXT,
                sexo TEXT NOT NULL,
                status TEXT NOT NULL,
                temperamento TEXT,
                porte TEXT NOT NULL,
                peso REAL NOT NULL,
                data_entrada TEXT NOT NULL,
                historico TEXT
            )""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS cachorros (
                animal_id INTEGER PRIMARY KEY,
                necessidade_passeio BOOLEAN NOT NULL CHECK (necessidade_passeio IN (0, 1)),
                FOREIGN KEY (animal_id) REFERENCES animais(id) ON DELETE CASCADE
            )""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS gatos (
                animal_id INTEGER PRIMARY KEY,
                independencia TEXT,
                tipo_pelo TEXT,
                FOREIGN KEY (animal_id) REFERENCES animais(id) ON DELETE CASCADE
            )""")

    def conectar(self):
        connection = sqlite3.connect(self.caminho_db)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def cadastrarAnimal(self, nome: str, idade: int, raca: str, sexo: str, status: str, temperamento: str, porte: str, peso: float, data_entrada: str, historico: str):
        with self.conectar() as connection:
            cursor = connection.cursor()

            cursor.execute("""INSERT INTO animais (nome, idade, raca, sexo, status, temperamento, porte, peso, data_entrada, historico)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (nome, idade, raca, sexo, status, temperamento, porte, peso, data_entrada, historico))

            return cursor.lastrowid
        
    def cadastrarCachorro(self, nome: str, idade: int, raca: str, sexo: str, status: str, temperamento: str, porte: str, peso: float, data_entrada: str, historico: str, necessidadePasseio: bool):
        animal_id = self.cadastrarAnimal(nome, idade, raca, sexo, status, temperamento, porte, peso, data_entrada, historico)
        with self.conectar() as connection:
            cursor = connection.cursor()

            cursor.execute("""INSERT INTO cachorros (animal_id, necessidade_passeio)
                VALUES (?,?)
            """,
            (animal_id, int(necessidadePasseio)))

    def cadastrarGato(self, nome: str, idade: int, raca: str, sexo: str, status: str, temperamento: str, porte: str, peso: float, data_entrada: str, historico: str, independencia: str, tipoPelo: str):
        animal_id = self.cadastrarAnimal(nome, idade, raca, sexo, status, temperamento, porte, peso, data_entrada, historico)
        with self.conectar() as connection:
            cursor = connection.cursor()

            cursor.execute("""INSERT INTO gatos (animal_id, independencia, tipo_pelo)
                VALUES (?,?,?)
            """,
            (animal_id, independencia, tipoPelo))

    def excluirAnimal(self, id: int):
        with self.conectar() as connection:
            cursor = connection.cursor()

            cursor.execute("DELETE FROM animais WHERE id = ?", (id,))

        # Gera um relatório simples com os animais disponíveis e adotados.
        def relatorioDisponiveisAdotados(self) -> str:
            grupos = [("DISPONÍVEIS", StatusAnimal.DISPONIVEL.name), ("ADOTADOS", StatusAnimal.ADOTADO.name)]
            linhas = ["===== RELATÓRIO DE ANIMAIS ====="]

            with self.conectar() as connection:
                cursor = connection.cursor()

                for titulo, status in grupos:
                    cursor.execute("SELECT id, nome, raca, porte FROM animais WHERE status = ? ORDER BY nome", (status,))
                    animais = cursor.fetchall()

                    linhas.append(f"\n--- {titulo} ({len(animais)}) ---")
                    if not animais:
                        linhas.append("Nenhum animal.")
                    for id, nome, raca, porte in animais:
                        linhas.append(f"#{id} - {nome} | Raça: {raca} | Porte: {porte}")

            return "\n".join(linhas)