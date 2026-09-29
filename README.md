<h1 align="center">Sistema de Adoção de Animais</h1>
<p align="center">Projeto voltado a criação de um sistema de adoção de animais para gerenciar o cadastro de animais, triagem de adotantes, reservas, adoções, devoluções, quarentena e relatórios.</p>
<p align="center">Esse é um projeto da disciplina de <strong>Programação Orientada a Objetos</strong> do curso de <strong>Engenharia de Software</strong> na <strong>Universidade Federal do Cariri (UFCA)</strong></p>

<div align="center">
    <a href="https://www.ufca.edu.br/cursos/graduacao/engenharia-de-software/">
    <img alt="Static Badge" src="https://img.shields.io/badge/Universidade%20Federal%20do%20Cariri-blue?style=for-the-badge&link=https%3A%2F%2Fwww.ufca.edu.br%2Fcursos%2Fgraduacao%2Fengenharia-de-software%2F">
    </a>
</div>

---
<br>

## Diagrama de Classes UML
![Diagrama de Classes](docs/DiagramaDeClasses.png)

---
<br>

## [Diagrama de Classes textual](docs/DiagramaDeClassesTextual.md)

## Estrutura de arquivos atual:
```
│   .gitignore
│   main.py
│   README.md
│
├───database
├───docs
│       DiagramaDeClasses.drawio
│       DiagramaDeClasses.png
│       DiagramaDeClassesTextual.md
│
├───src
│   ├───domain
│   │       adotante.py
│   │       animal.py
│   │       cachorro.py
│   │       fila_espera.py
│   │       gato.py
│   │       pessoa.py
│   │       reserva.py
│   │       __init__.py
│   │
│   ├───enums
│   │       status_animal.py
│   │
│   ├───exceptions
│   ├───mixins
│   │       adestravel_mixin.py
│   │       vacinavel_mixin.py
│   │
│   ├───repositories
│   │       animal_repository.py
│   │       fila_de_espera_repository.py
│   │       pessoa_repository.py
│   │       reserva_repository.py
│   │
│   └───strategies
│           compatibilidade_strategy.py
│           taxa_adocao_strategy.py
│
└───tests
```
