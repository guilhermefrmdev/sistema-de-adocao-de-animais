class RepositorioError(Exception):
    """Levantada quando uma operação de persistência falha.

    Encapsula os erros do banco (ex.: ``sqlite3.Error``) para que o domínio
    não precise conhecer o mecanismo de persistência usado.
    """
