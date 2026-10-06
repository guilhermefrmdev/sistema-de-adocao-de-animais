from src.domain.pessoa import Pessoa
from src.enums.moradias import Moradia

class Adotante(Pessoa):
    """Representa um adotante registrado no sistema.
    
    Estende `Pessoa` com características específicas dos adotantes.

    Attributes:
        telefone : Telefone do adotante.
        moradia : Tipo de moradia do adotante.
        areaUtil : Espaço útil da moradia.
        experiencia : Experiencia com outros animais.
        criancasEmCasa : Se há crianças em casa.
        outrosAnimais : Se há outros animais em casa.
    """

    def __init__(self, nome: str, idade: int, telefone: str, moradia: Moradia, areaUtil: float, experiencia: bool, criancasEmCasa: bool, outrosAnimais: bool, id = None):
        super().__init__(nome, idade, id)
        self.telefone = telefone
        self.moradia = moradia
        self.areaUtil = areaUtil
        self.experiencia = experiencia
        self.criancasEmCasa = criancasEmCasa
        self.outrosAnimais = outrosAnimais

    # Propriedades e verificações

    # Telefone
    @property 
    def telefone(self):
        return self._telefone

    @telefone.setter
    def telefone(self, novo_telefone: str):
        novo_telefone = novo_telefone.strip()

        if not novo_telefone.isdecimal():
            raise ValueError("O telefone deve ter somente números")
        if len(novo_telefone) != 11:
            raise ValueError("O telefone deve ter 11 números")

        self._telefone = novo_telefone 

    # Moradia
    @property
    def moradia(self):
        return self._moradia

    @moradia.setter
    def moradia(self, nova_moradia: Moradia):
        self._moradia = nova_moradia 

    # Área útil
    @property
    def areaUtil(self):
        return self._areaUtil

    @areaUtil.setter
    def areaUtil(self, nova_areaUtil: float):
        if nova_areaUtil == 0.00:
            raise ValueError("A área útil não pode ser zero.")

        self._areaUtil = nova_areaUtil 

    # Experiência
    @property
    def experiencia(self):
        return self._experiencia

    @experiencia.setter
    def experiencia(self, experiencia_atualizado: bool):
        self._experiencia = experiencia_atualizado

    # Crianças em casa
    @property
    def criancasEmCasa(self):
        return self._criancasEmCasa

    @criancasEmCasa.setter
    def criancasEmCasa(self, criancasEmCasa_atualizado: bool):
        self._criancasEmCasa = criancasEmCasa_atualizado

    # Outros animais
    @property
    def outrosAnimais(self):
        return self._outrosAnimais

    @outrosAnimais.setter
    def outrosAnimais(self, outrosAnimais_atualizado: bool):
        self._outrosAnimais = outrosAnimais_atualizado

    # Métodos Especiais
    def __str__(self) -> str:
        return f"""
ID: {self.__id}.
Nome: {self.nome}.
Idade: {self.idade} anos.
Telefone: ({self.telefone[:2]}) 9 {self.telefone[3:7]}-{self.telefone[7:]}.
Tipo de moradia: {self.moradia.name.lower()}.
Área útil: {str(self.areaUtil).replace('.', ',')} metros.
Tem experiência com animais? {"Sim" if self.experiencia else "Não"}.
Tem crianças em casa? {"Sim" if self.criancasEmCasa else "Não"}.
Tem outros animais? {"Sim" if self.outrosAnimais else "Não"}.
"""

    def __repr__(self):
        return f"{self.__id=}; {self.nome=}; {self.idade=}; {self.telefone=}; {self.moradia=}; {self.areaUtil=}; {self.experiencia=}; {self.criancasEmCasa=}; {self.outrosAnimais=}"

    def __eq__(self, outroAdotante):
        return self.id == outroAdotante.id