<h1 align="center">Sistema de Adoção de Animais</h1>
<p align="center">Projeto voltado a criação de um sistema de adoção de animais para gerenciar o cadastro de animais, triagem de adotantes, reservas, adoções, devoluções, quarentena e relatórios.</p>
<p align="center">Esse é um projeto da disciplina de <strong>Programação Orientada a Objetos</strong> do curso de <strong>Engenharia de Software</strong> na <strong>Universidade Federal do Cariri (UFCA)</strong></p>

---
<br>

## Diagrama de Classes UML
![Diagrama de Classes](docs/DiagramaDeClasses.png)

---
<br>

## Diagrama de Classes textual
```
<<abstract>>
Animal
=================================================
Atributos:
- id : int
- nome : String
- idade : int
- raça : String
- sexo : String
- peso : float
- status : String
- temperamento : list
- castrado : bool
- historico : list
- porte: String
-------------------------------------------------
Métodos:
+ alterarNome(nome : String) : void
+ atualizarIdade(idade : int) : void
+ atualizarPeso(peso : float) : void
+ alterarStatus(status : String) : void
```

---

```
Cachorro (Subclasse de Animal)
=================================================
Atributos:
- necessidadePasseio: bool
- adestrado: bool
```

---

```
Gato (Subclasse de Animal)
=================================================
Atributos:
- independencia : String
- tipoPelo : String
```

---

```
Reserva
=================================================
Atributos:
- id : int
- dataReserva : String
- adotante : String
- animal : String
- compatibilidade : int
- status : String
-------------------------------------------------
Métodos:
+ alterarStatus(status : String) : void
+ gerarContrato() : String
```

---

```
Adotante
=================================================
Atributos:
- id : int
- nome : String
- idade : int
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
+ alterarExperiencia(experiencia : bool): void
+ alterarCriançasEmCasa(criancas : bool) : void
+ alterarOutrosAnimais(animais : bool) : void
```