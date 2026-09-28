# Diagrama de Classes Textual
```
<<abstract>>
Animal
=================================================
Atributos:
- id : int
- nome : String
- idade : int {em meses}
- raça : String
- sexo : String
- status : StatusAnimal
- temperamento : list
- castrado : bool
- historico : dict
- porte : String
-------------------------------------------------
Métodos:
+ alterarNome(nome : String) : void
+ atualizarIdade(idade : int) : void
+ atualizarPeso(peso : float) : void
+ alterarStatus(status : String) : void
+ adicionarHistórico(evento : String) : void
+ __str__() : String
+ __repr__() : String
+ __eq__() : bool
+ __hash__() : int
+ __lt__() : bool
+ __iter__() : iterator
```

```
Cachorro (Subclasse de Animal)
=================================================
Atributos:
- necessidadePasseio : bool
-------------------------------------------------
Métodos:
+ salvarCachorro() : void
```

```
Gato (Subclasse de Animal)
=================================================
Atributos:
- independencia : String
- tipoPelo : String
-------------------------------------------------
Métodos:
+ salvarGato() : void
```

```
Pessoa
=================================================
Atributos:
- id : int
- nome : String
- idade : int
-------------------------------------------------
Métodos:
+ alterarNome(nome : String) : void
+ atualizarIdade(idade : int) : void
```

```
Adotante (Subclasse de Pessoa)
=================================================
Atributos:
- telefone : String
- moradia : String
- areaUtil : float
- experiencia : bool
- criancasEmCasa : bool
- outrosAnimais : bool
-------------------------------------------------
Métodos:
+ alterarNome(nome : String) : void
+ alterarTelefone(telefone : String) : void
+ alterarMoradia(moradia : String, areaUtil : float) : void
+ alterarExperiencia(experiencia : bool) : void
+ alterarCriançasEmCasa(criancas : bool) : void
+ alterarOutrosAnimais(animais : bool) : void
```

```
Reserva
=================================================
Atributos:
- id : int
- dataReserva : datetime
- dataExpiracao : datetime
- adotante : Adotante
- animal : Animal
- compatibilidade : float
- status : String
-------------------------------------------------
Métodos:
+ alterarStatus(status : String) : void
+ gerarContrato() : String
+ __str__() : String
```

```
FilaDeEspera
=================================================
Atributos:
- animal : Animal
- fila : list
-------------------------------------------------
Métodos:
+ adicionar(adotante) : void
+ remover(adotante) : void
+ atualizarLista() : void
+ __len__() : int
+ __iter__() : iterator
```

```
<<mixin>>
VacinavelMixin
=================================================
Métodos:
+ vacinar(vacina : String) : void
```

```
<<mixin>>
AdestravelMixin
=================================================
Atributos:
- nivelDeAdestramento : int
-------------------------------------------------
Métodos:
+ treinar(comando : String) : void
```

```
<<interface>>
TaxaAdocaoStrategy
=================================================
Métodos:
+ calcularTaxa(animal : Animal) : float
```

```
BaseFee
=================================================
Métodos:
+ calcularTaxa(animal : Animal) : float
```

```
SeniorFee
=================================================
Métodos:
+ calcularTaxa(animal : Animal) : float
```

```
PuppyFee
=================================================
Métodos:
+ calcularTaxa(animal : Animal) : float
```

```
SpecialCareFee
=================================================
Métodos:
+ calcularTaxa(animal : Animal) : float
```

```
<<interface>>
CompatibilidadeStrategy
=================================================
Métodos:
+ calcularCompatibilidade(
    adotante : Adotante,
    animal : Animal
  ) : float
```

```
<<interface>>
AnimalRepository
=================================================
Métodos:
+ salvar(animal : Animal) : void
+ buscarPorId(id : int) : Animal
+ listar() : [Animal]
+ remover(id : int) : void
```

```
<<interface>>
ReservaRepository
=================================================
Métodos:
+ salvar(reserva : Reserva) : void
+ buscarPorId(id : int) : Animal
+ listar() : [Reserva]
+ remover(id : int) : void
```

```
<<interface>>
PessoaRepository
=================================================
Métodos:
+ salvar(animal : Animal) : void
+ buscarPorId(id : int) : Animal
+ listar() : [Animal]
+ remover(id : int) : void
```

```
<<interface>>
FilaDeEsperaRepository
=================================================
Métodos:
+ salvar(fila : FilaDeEspera) : void
+ buscarPorIdAnimal(idAnimal : int) : FilaDeEspera
+ atualizarLista(idAnimal : int) : void
+ limparFila(idAnimal : int) : void
```

```
<<enumeration>>
StatusAnimal
=================================================
Valores:
- DISPONIVEL
- RESERVADO
- ADOTADO
- DEVOLVIDO
- QUARENTENA
- INADOTAVEL
```