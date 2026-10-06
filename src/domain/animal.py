from datetime import date

from src.enums.status_animal import StatusAnimal
from src.enums.porte_animal import PorteAnimal

class Animal():
    """Representa um animal registrado no sistema.
    
    Attributes:
        id: Identificação única do animal.
        nome: Nome do animal.
        idade: Idade do animal em meses.
        raça: Raça do animal.
        sexo: Sexo do animal.
        status: Status do animal.
        temperamento: Lista com os temperamentos do animal.
        castrado: Se o animal é castrado.
        historico: Histórico do animal.
        porte: Porte do animal.
    """

    def __init__(self, nome: str, idade: int, raça: str, sexo: str, status: StatusAnimal, temperamento: list, castrado: bool, porte: PorteAnimal, peso: int, dataEntrada: date, historico: list = [], id: int = None):
        super().__init__()
        self.id = id
        self.nome = nome
        self.idade = idade
        self.raça = raça
        self.sexo = sexo
        self.status = status
        self.temperamento = temperamento
        self.castrado = castrado
        self.historico = historico
        self.porte = porte
        self.peso = peso
        self.dataEntrada = dataEntrada

    # ID
    @property
    def id(self):
        return self.__id

    @id.setter
    def id(self, novo_id: int):
        self.__id = novo_id

    # Nome
    @property
    def nome(self): 
        return self._nome

    @nome.setter
    def nome(self, novo_nome: str):
        if not novo_nome.replace(" ", "").isalpha(): # Verificação somente letras
            raise ValueError("O nome deve conter apenas letras.")
            
        if novo_nome.strip() == "": # Verificação nome vazio
            raise ValueError("O nome não pode ser vazio.")

        self._nome = novo_nome.strip()

    # Idade
    @property
    def idade(self):
        return self._idade

    @idade.setter
    def idade(self, nova_idade: int):
        if nova_idade < 1:
            raise ValueError("A idade não pode ser menor que um.") # Verificação Maioridade

        self._idade = nova_idade

    # Raça
    @property
    def raca(self):
        return self._raca
    
    @raca.setter
    def raca(self, nova_raca: str):
        nova_raca = nova_raca.strip()
        if nova_raca == "":
            raise ValueError("A raça não pode ser vazia.")

        self._raca = nova_raca

    # Sexo
    @property
    def sexo(self):
        return self._sexo

    @sexo.setter
    def sexo(self, novo_sexo: str):
        novo_sexo = novo_sexo.strip().upper()
        if novo_sexo not in ["M", "F"]:
            raise ValueError("O sexo deve ser 'M' ou 'F'.")

        self._sexo = novo_sexo

    # Status
    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, novo_status: StatusAnimal):
        if not isinstance(novo_status, StatusAnimal):
            raise ValueError("O status deve ser uma instância de StatusAnimal.")

        self._status = novo_status

    # Temperamento
    @property
    def temperamento(self):
        return self._temperamento

    @temperamento.setter
    def temperamento(self, novo_temperamento: list):
        if not isinstance(novo_temperamento, list):
            raise ValueError("O temperamento deve ser uma lista.")

        self._temperamento = novo_temperamento

    # Castrado
    @property
    def castrado(self):
        return self._castrado

    @castrado.setter
    def castrado(self, novo_castrado: bool):
        if not isinstance(novo_castrado, bool):
            raise ValueError("O castrado deve ser um valor booleano.")

        self._castrado = novo_castrado

    # Histórico
    @property
    def historico(self):
        return self._historico

    @historico.setter
    def historico(self, evento):
    # Verificações de cada atributo
        if evento['tipo'].strip() == "":
            raise ValueError("O tipo do evento não pode ser vazio.")
        if evento['nome'].strip() == "":
            raise ValueError("O nome do evento não pode ser vazio.")
        if evento['data'] is None:
            raise ValueError("A data do evento não pode ser nula.")
        if isinstance(evento['data'], date) is False:
            raise ValueError("A data deve ser uma instancia de date.")

        # Adicionar um dicionário do evento na lista
        self.historico.append({"tipo": evento['tipo'].strip(), "nome": evento['nome'].strip(), "data": evento['data']})

    # Porte
    @property
    def porte(self):
        return self._porte

    @porte.setter
    def porte(self, novo_porte: PorteAnimal):
        if not isinstance(novo_porte, PorteAnimal):
            raise ValueError("O porte deve ser uma instância de PorteAnimal.")

        self._porte = novo_porte

    # Peso
    @property
    def peso(self):
        return self._peso

    @peso.setter
    def peso(self, novo_peso: int):
        if novo_peso <= 0:
            raise ValueError("O peso deve ser maior que zero.")

        self._peso = novo_peso

    # Data de entrada
    @property
    def data_entrada(self):
        return self._data_entrada

    @data_entrada.setter
    def data_entrada(self, nova_data_entrada: date):
        if not isinstance(nova_data_entrada, date):
            raise ValueError("A data de entrada deve ser uma instância de date.")

        self._data_entrada = nova_data_entrada

    # Métodos especiais
    def __eq__(self, outro_animal):
        if not isinstance(outro_animal, Animal):
            return False
        return self.__id == outro_animal.__id

    def __hash__(self):
        return hash(self.__id)

    def __lt__(self, outro_animal):
        return self.data_entrada < outro_animal.data_entrada

    # __iter__ iterando o histórico
    def __iter__(self):
        for evento in self.historico:
            yield evento

    # Mudança de Status: Transições de estado (permitidas):
                        # DISPONIVEL → RESERVADO → ADOTADO
                        # DISPONIVEL → INADOTAVEL
                        # ADOTADO → DEVOLVIDO → (QUARENTENA|DISPONIVEL|INADOTAVEL)
                        # QUARENTENA → (DISPONIVEL|INADOTAVEL)
    def mudar_status(self, status: StatusAnimal):
        if not isinstance(status, StatusAnimal):
            raise ValueError("O status deve ser uma instância de StatusAnimal.")

        # Verificar se a transição de status é válida
        if self.status == StatusAnimal.DISPONIVEL and status in [StatusAnimal.RESERVADO, StatusAnimal.INADOTAVEL]:
            self.status = status
        elif self.status == StatusAnimal.RESERVADO and status == StatusAnimal.ADOTADO:
            self.status = status
        elif self.status == StatusAnimal.ADOTADO and status in [StatusAnimal.DEVOLVIDO]:
            self.status = status
        elif self.status == StatusAnimal.DEVOLVIDO and status in [StatusAnimal.QUARENTENA, StatusAnimal.DISPONIVEL, StatusAnimal.INADOTAVEL]:
            self.status = status
        elif self.status == StatusAnimal.QUARENTENA and status in [StatusAnimal.DISPONIVEL, StatusAnimal.INADOTAVEL]:
            self.status = status
        else:
            raise ValueError(f"Transição de status inválida: {self.status.name} → {status.name}")