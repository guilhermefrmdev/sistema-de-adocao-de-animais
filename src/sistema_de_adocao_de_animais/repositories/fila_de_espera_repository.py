from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, NamedTuple

from sistema_de_adocao_de_animais.exceptions.repositorio_error import (
    RepositorioError,
)


class RegistroFila(NamedTuple):
    """Uma linha da fila de espera como está gravada no banco.

    Attributes:
        adotante_id (int): Id do adotante que espera.
        compatibilidade (float): Pontuação adotante-animal (0–100).
        data_entrada (datetime): Quando entrou na fila.
        prioridade (float): Última prioridade calculada (0–100).
        posicao (int): Posição na fila (1 = próximo).
    """

    adotante_id: int
    compatibilidade: float
    data_entrada: datetime
    prioridade: float
    posicao: int


class FilaDeEsperaRepository:
    """Faz a conexão e salva no banco os dados da fila de espera.

    Cada linha da tabela ``fila_espera`` é um adotante esperando por um animal.
    As operações usam *duck typing*: ``salvar`` e ``atualizarLista`` aceitam
    qualquer objeto com ``animal_id`` e ``fila`` (lista de entradas com
    ``adotante.id``, ``compatibilidade``, ``data_entrada`` e ``prioridade``),
    como a ``FilaDeEspera`` do domínio. Assim, o repositório não importa o
    domínio (evita import circular, já que ``FilaDeEspera`` herda daqui).

    A tabela é criada sob demanda em ``conectar``, então a classe funciona
    mesmo quando uma subclasse não chama ``super().__init__()``.

    Attributes:
        caminho_db (Path): Arquivo SQLite usado (o mesmo dos outros repositórios).
    """

    caminho_db: Path = (
        Path(__file__).resolve().parent.parent / "database" / "database.db"
    )

    def __init__(self, caminho_db: Path | str | None = None):
        if caminho_db is not None:
            self.caminho_db = Path(caminho_db)

    # Conexão com o banco de dados
    def conectar(self) -> sqlite3.Connection:
        """Abre uma conexão e garante que a tabela ``fila_espera`` exista.

        Returns:
            sqlite3.Connection: Conexão com chaves estrangeiras ativadas.
        """
        connection = sqlite3.connect(self.caminho_db)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("""CREATE TABLE IF NOT EXISTS fila_espera (
                animal_id INTEGER NOT NULL,
                adotante_id INTEGER NOT NULL,
                compatibilidade REAL NOT NULL
                    CHECK (compatibilidade BETWEEN 0 AND 100),
                data_entrada TEXT NOT NULL,
                prioridade REAL NOT NULL DEFAULT 0,
                posicao INTEGER NOT NULL,
                PRIMARY KEY (animal_id, adotante_id),
                FOREIGN KEY (animal_id)
                    REFERENCES animais(id) ON DELETE CASCADE,
                FOREIGN KEY (adotante_id)
                    REFERENCES adotantes(pessoa_id) ON DELETE CASCADE
            )""")
        return connection

    @contextmanager
    def _transacao(self) -> Iterator[sqlite3.Connection]:
        """Abre uma transação: faz commit no sucesso e rollback em erro.

        Raises:
            RepositorioError: Se o banco devolver qualquer ``sqlite3.Error``.
        """
        connection = self.conectar()
        try:
            with connection:  # commit ao sair; rollback se houver exceção
                yield connection
        except sqlite3.Error as erro:
            raise RepositorioError(
                f"Falha ao acessar a fila de espera: {erro}"
            ) from erro
        finally:
            connection.close()

    @staticmethod
    def _linhas(fila: Any) -> list[tuple[int, int, float, str, float, int]]:
        """Converte a fila em tuplas prontas para gravar, na ordem atual."""
        animal_id = fila.animal_id
        if animal_id is None:
            raise RepositorioError(
                "O animal da fila precisa estar cadastrado (sem id)."
            )
        return [
            (
                animal_id,
                entrada.adotante.id,
                float(entrada.compatibilidade),
                entrada.data_entrada.isoformat(),
                float(entrada.prioridade),
                posicao,
            )
            for posicao, entrada in enumerate(fila.fila, start=1)
        ]

    # Salvar
    def salvar(self, fila: Any = None) -> None:
        """Grava a fila inteira do animal, substituindo o que havia.

        Apaga e reinsere as linhas na mesma transação, então ou tudo é gravado
        ou nada muda.

        Args:
            fila: Fila a gravar (``FilaDeEspera``). Se omitida, usa ``self``,
                o que permite chamar ``fila.salvar()`` quando a classe herda
                deste repositório.

        Raises:
            RepositorioError: Se o animal não tiver id, ou se o banco falhar
                (ex.: adotante ou animal inexistente).
        """
        fila = fila if fila is not None else self
        linhas = self._linhas(fila)
        with self._transacao() as connection:
            connection.execute(
                "DELETE FROM fila_espera WHERE animal_id = ?", (fila.animal_id,)
            )
            connection.executemany(
                """INSERT INTO fila_espera
                (animal_id, adotante_id, compatibilidade, data_entrada, prioridade, posicao)
                VALUES (?,?,?,?,?,?)""",
                linhas,
            )

    # Buscar
    def buscarPorIdAnimal(self, id_animal: int) -> list[RegistroFila]:
        """Lê a fila de um animal, do mais ao menos prioritário.

        Devolve registros simples, e não uma ``FilaDeEspera``, porque remontar
        a fila exige buscar ``Animal`` e ``Adotante`` por id, e os repositórios
        correspondentes ainda não têm leitura.

        Args:
            id_animal (int): Id do animal.

        Returns:
            list of RegistroFila: Vazia se ninguém espera por esse animal.
        """
        with self._transacao() as connection:
            cursor = connection.execute(
                """SELECT adotante_id, compatibilidade, data_entrada, prioridade, posicao
                FROM fila_espera WHERE animal_id = ? ORDER BY posicao""",
                (id_animal,),
            )
            return [
                RegistroFila(
                    adotante_id, compat, datetime.fromisoformat(data), prio, pos
                )
                for adotante_id, compat, data, prio, pos in cursor.fetchall()
            ]

    # Atualizar
    def atualizarLista(self, fila: Any = None) -> None:
        """Atualiza prioridade e posição das linhas já gravadas.

        Use depois de ``FilaDeEspera.atualizar_lista()``, que recalcula as
        prioridades. Não insere nem apaga nada: só altera quem já está salvo.

        Args:
            fila: Fila já reordenada. Se omitida, usa ``self``.

        Raises:
            RepositorioError: Se algum adotante da fila não estiver gravado
                (nesse caso nada é alterado; use ``salvar``).
        """
        fila = fila if fila is not None else self
        linhas = self._linhas(fila)
        with self._transacao() as connection:
            for animal_id, adotante_id, _, _, prioridade, posicao in linhas:
                cursor = connection.execute(
                    """UPDATE fila_espera SET prioridade = ?, posicao = ?
                    WHERE animal_id = ? AND adotante_id = ?""",
                    (prioridade, posicao, animal_id, adotante_id),
                )
                if cursor.rowcount == 0:
                    raise RepositorioError(
                        f"Adotante {adotante_id} não está salvo na fila do animal {animal_id}."
                    )

    # Remover
    def removerEntrada(self, id_animal: int, id_adotante: int) -> None:
        """Tira um adotante da fila (ex.: quando ele reserva o animal).

        As posições dos que ficaram são refeitas (1, 2, 3...).

        Raises:
            RepositorioError: Se o adotante não estiver na fila do animal.
        """
        with self._transacao() as connection:
            cursor = connection.execute(
                "DELETE FROM fila_espera WHERE animal_id = ? AND adotante_id = ?",
                (id_animal, id_adotante),
            )
            if cursor.rowcount == 0:
                raise RepositorioError(
                    f"Adotante {id_adotante} não está na fila do animal {id_animal}."
                )
            restantes = connection.execute(
                "SELECT adotante_id FROM fila_espera WHERE animal_id = ? ORDER BY posicao",
                (id_animal,),
            ).fetchall()
            connection.executemany(
                "UPDATE fila_espera SET posicao = ? WHERE animal_id = ? AND adotante_id = ?",
                [
                    (pos, id_animal, linha[0])
                    for pos, linha in enumerate(restantes, start=1)
                ],
            )

    def limparFila(self, id_animal: int) -> None:
        """Apaga toda a fila de um animal (ex.: quando ele é adotado)."""
        with self._transacao() as connection:
            connection.execute(
                "DELETE FROM fila_espera WHERE animal_id = ?", (id_animal,)
            )
