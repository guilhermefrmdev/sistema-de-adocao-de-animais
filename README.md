<h1 align="center">Sistema de Adoção de Animais</h1>

<p align="center">Aplicação de linha de comando para gerenciar animais em abrigos, triagem de adotantes, reservas, adoções, devoluções, lista de espera e relatórios.</p>

<p align="center">Projeto da disciplina de <strong>Programação Orientada a Objetos</strong> do curso de <strong>Engenharia de Software</strong> da <strong>Universidade Federal do Cariri (UFCA)</strong>.</p>

<p align="center">
  <a href="https://www.ufca.edu.br/cursos/graduacao/engenharia-de-software/">
    <img alt="Universidade Federal do Cariri" src="https://img.shields.io/badge/Universidade%20Federal%20do%20Cariri-UFCA-blue?style=for-the-badge">
  </a>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.14%2B-blue?style=for-the-badge&logo=python&logoColor=white">
  <img alt="Typer" src="https://img.shields.io/badge/CLI-Typer%20%2B%20Rich-purple?style=for-the-badge">
  <img alt="Banco de dados" src="https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white">
</p>

---

## 1. Objetivo do projeto

O sistema apoia o fluxo de adoção de animais, desde o cadastro e a avaliação de compatibilidade até a reserva, efetivação da adoção e eventual devolução. As regras de negócio são configuráveis e os dados são persistidos em SQLite.

Principais funcionalidades:

- Cadastro, consulta, atualização e exclusão de cães, gatos e adotantes.
- Histórico de eventos dos animais, incluindo vacinação e mudanças de status.
- Validação de elegibilidade do adotante e cálculo de compatibilidade entre adotante e animal.
- Reservas com prazo de expiração configurável.
- Efetivação da adoção, cálculo da taxa e geração de contrato em texto.
- Registro de devoluções e encaminhamento para quarentena quando necessário.
- Lista de espera ordenada por compatibilidade e tempo de espera.
- Relatórios gerenciais e carga de dados de demonstração.

## 2. Tecnologias e requisitos

- **Python:** `3.14.7` ou superior, conforme declarado no `pyproject.toml`.
- **Poetry:** gerenciamento de dependências e ambiente do projeto.
- **Typer:** definição dos comandos da CLI.
- **Rich:** tabelas, painéis, mensagens e apresentação dos resultados no terminal.
- **SQLite:** persistência local dos dados.
- **pytest:** execução dos testes automatizados.

## 3. Instalação e execução

### Pré-requisitos

Instale Python compatível com a versão indicada acima e [Poetry](https://python-poetry.org/docs/).

### Instalar as dependências

Na raiz do repositório, execute:

```bash
poetry install
```

### Executar a aplicação

A aplicação pode ser executada diretamente pelo arquivo `main.py`:

```bash
poetry run python main.py --help
```

Para ver a ajuda de um grupo ou comando específico:

```bash
poetry run python main.py animal --help
poetry run python main.py animal cachorro cadastrar --help
poetry run python main.py adotante --help
```

Também é possível executar `python main.py ...` quando as dependências já estiverem disponíveis no ambiente Python ativo.

### Preparar dados de demonstração

O comando `seed` cria registros de exemplo de animais, adotantes, reserva e lista de espera:

```bash
poetry run python main.py seed
```

A carga é idempotente: executar novamente não duplica a carga de demonstração. Para limpar os dados de domínio antes de carregar os exemplos novamente:

```bash
poetry run python main.py seed --limpar
```

> **Atenção:** `seed --limpar` apaga os registros existentes nas tabelas de domínio do banco utilizado pela aplicação. Use apenas se quiser reinicializar esses dados.

## 4. Comandos da CLI

A forma geral de uso é:

```text
python main.py <grupo> <comando> [argumentos] [opções]
```

Consulte `--help` para conhecer os argumentos e opções disponíveis. A tabela abaixo resume os grupos implementados.

| Grupo | Comandos | Finalidade |
|---|---|---|
| `animal` | `cachorro cadastrar`, `gato cadastrar`, `listar`, `ver`, `atualizar`, `excluir`, `historico`, `adicionar-historico`, `vacinar`, `mudar-status`, `reavaliar` | Cadastro, manutenção, status e histórico dos animais. |
| `adotante` | `cadastrar`, `listar`, `ver`, `atualizar`, `excluir`, `elegivel`, `compatibilidade` | Cadastro e triagem de adotantes. |
| `reserva` | `criar`, `cancelar`, `listar`, `rodar-expiracao` | Gerenciamento e expiração de reservas. |
| `adocao` | `taxa`, `efetivar`, `contrato`, `listar`, `devolver` | Taxas, contratos, adoções e devoluções. |
| `fila` | `entrar`, `ver`, `sair` | Lista de espera por animal. |
| `relatorio` | `top`, `adocoes`, `tempo-medio`, `devolucoes`, `disponiveis` | Indicadores do abrigo e do processo de adoção. |
| `config` | `mostrar` | Exibe as políticas carregadas de `settings.json`. |
| raiz | `seed` | Cria dados de demonstração. |

### Exemplos de uso

Os exemplos a seguir pressupõem que os dados necessários já existam no banco. Os IDs são ilustrativos e dependem dos registros cadastrados.

#### Animais

```bash
# Cadastrar um cachorro: nome, idade em meses, raça, sexo, peso e porte
poetry run python main.py animal cachorro cadastrar "Rex" 24 "Labrador" M 18 GRANDE --castrado --temperamento "calmo,brincalhao"

# Cadastrar um gato: nome, idade em meses, raça, sexo, peso, porte, independência e tipo de pelo
poetry run python main.py animal gato cadastrar "Mimi" 12 "SRD" F 4 PEQUENO MEDIA CURTO

# Listar animais disponíveis com idade máxima de 36 meses
poetry run python main.py animal listar --status DISPONIVEL --idade-max 36
poetry run python main.py animal ver 1
poetry run python main.py animal vacinar 1 "Antirrábica"
poetry run python main.py animal historico 1
```

#### Adotantes e compatibilidade

```bash
poetry run python main.py adotante cadastrar "Maria Silva" 30 88999999999 CASA 80 --experiencia --criancas-em-casa
poetry run python main.py adotante listar
poetry run python main.py adotante ver 1
poetry run python main.py adotante elegivel 1 1
poetry run python main.py adotante compatibilidade 1 1
```

#### Reservas e adoções

```bash
poetry run python main.py reserva criar 1 1
poetry run python main.py reserva listar --status ATIVA
poetry run python main.py reserva rodar-expiracao

poetry run python main.py adocao taxa 1
poetry run python main.py adocao efetivar 1
poetry run python main.py adocao listar
poetry run python main.py adocao contrato 1 --salvar contrato.txt
poetry run python main.py adocao devolver 1 "Motivo da devolução"
```

Para simular a data/hora de expiração durante demonstrações ou testes:

```bash
poetry run python main.py reserva rodar-expiracao --agora "2026-11-06 14:30"
```

#### Lista de espera

```bash
# Argumentos de entrar/sair: ID do adotante e ID do animal
poetry run python main.py fila entrar 1 1
poetry run python main.py fila ver 1
poetry run python main.py fila sair 1 1
```

A prioridade combina a pontuação de compatibilidade e o tempo de espera. Os pesos são configurados em `settings.json`.

#### Relatórios, configuração e dados

```bash
poetry run python main.py relatorio top
poetry run python main.py relatorio top --limite 10
poetry run python main.py relatorio adocoes
poetry run python main.py relatorio adocoes --por porte
poetry run python main.py relatorio tempo-medio
poetry run python main.py relatorio devolucoes
poetry run python main.py relatorio disponiveis

poetry run python main.py config mostrar
poetry run python main.py seed
```

## 5. Regras de negócio e configuração

As políticas ficam no arquivo `src/sistema_de_adocao_de_animais/settings.json` e são carregadas e validadas pelo módulo `settings.py`. O comando abaixo mostra os principais valores lidos pelo sistema:

```bash
poetry run python main.py config mostrar
```

Valores definidos atualmente no arquivo de configuração:

| Configuração | Valor padrão |
|---|---:|
| Idade mínima do adotante | 18 anos |
| Moradia exigida para portes restritos | `CASA` |
| Área mínima para portes restritos | 50 m² |
| Duração da reserva | 48 horas |
| Pesos de compatibilidade | moradia/porte: 30; idade/energia: 25; experiência: 25; crianças: 20 |
| Estratégia padrão da taxa | `padrao` |
| Valor-base da taxa | R$ 100,00 |
| Pesos da fila | compatibilidade: 0,7; tempo de espera: 0,3 |
| Normalização do tempo de espera | 30 dias |

As regras para portes restritos, faixas de energia, experiência, presença de crianças, estratégias de taxa e prioridade da fila também são definidas no JSON. Para alterar o comportamento, edite a configuração preservando sua estrutura e os tipos de dados esperados.

### Status dos animais

Os status usados pelo sistema são `DISPONIVEL`, `RESERVADO`, `ADOTADO`, `DEVOLVIDO`, `QUARENTENA` e `INADOTAVEL`. As transições são validadas para evitar mudanças incompatíveis com o fluxo de adoção. Uma reserva ativa impede que o mesmo animal receba outra reserva ativa; ao cancelar ou expirar, o animal pode voltar a ficar disponível e o próximo interessado da fila pode ser notificado.

### Convenções de entrada

- Datas: `AAAA-MM-DD`; para simular a expiração, use `AAAA-MM-DD HH:MM`.
- Idade do animal: meses.
- Idade do adotante: anos.
- Sexo: `M` ou `F`.
- Moradia: `CASA` ou `APARTAMENTO`.
- Porte: `MINI`, `PEQUENO`, `MEDIO`, `GRANDE` ou `GIGANTE` (a CLI também documenta atalhos `P`, `M` e `G`).
- Independência do gato: `BAIXA`, `MEDIA` ou `ALTA`.
- Tipo de pelo: `SEM_PELOS`, `CURTO`, `LONGO` ou `ONDULADO`.
- Estratégia de taxa: `padrao`, `senior`, `filhote` ou `especial`.
- Opções booleanas são flags; por exemplo, `--castrado` ativa a opção.
- Textos com espaços devem ser colocados entre aspas.

## 6. Estrutura de classes e decisões de POO

A organização das classes de domínio foi mantida. O diagrama UML e sua versão textual documentam os atributos, métodos e relacionamentos principais.

### Diagrama de classes UML

![Diagrama de Classes UML](docs/assets/DiagramaDeClasses.png)

- [Diagrama de classes textual](docs/DiagramaDeClassesTextual.md)
- [Documentação do CLI](docs/CLI_Comands.md)

### Hierarquia e responsabilidades

```text
Animal (classe-base)
├── Cachorro
└── Gato

Pessoa
└── Adotante

Cachorro ── usa ── VacinavelMixin
         └─ usa ── AdestravelMixin
Gato     ── usa ── VacinavelMixin
         └─ usa ── AdestravelMixin

TaxaAdocaoStrategy (abstração)
├── BaseFee
├── SeniorFee
├── PuppyFee
└── SpecialCareFee

CompatibilidadeStrategy (abstração)
└── CompatibilidadePonderada

Repositories
├── AnimalRepository
├── PessoaRepository
├── ReservaRepository
└── FilaDeEsperaRepository
```

### Principais classes e padrões

| Elemento | Responsabilidade |
|---|---|
| `Animal` | Dados e comportamentos comuns dos animais, incluindo status e histórico. |
| `Cachorro` e `Gato` | Especializam `Animal` com atributos próprios de cada espécie. |
| `Pessoa` e `Adotante` | Representam os dados comuns de pessoa e os dados necessários para a triagem de adoção. |
| `Reserva` | Representa a reserva de um animal por um adotante e seu ciclo de vida. |
| `FilaDeEspera` e `EntradaFila` | Mantêm interessados e informações usadas para ordenar a prioridade. |
| `VacinavelMixin` | Acrescenta comportamento relacionado à vacinação. |
| `AdestravelMixin` | Acrescenta comportamento relacionado ao treinamento. |
| `TaxaAdocaoStrategy` e implementações | Permitem variar o cálculo da taxa sem concentrar todas as regras em um único algoritmo. |
| `CompatibilidadeStrategy` e `CompatibilidadePonderada` | Calculam a compatibilidade adotante–animal a partir de critérios ponderados. |
| Repositórios | Isolam operações de persistência e consulta dos dados. |
| `StatusAnimal` | Enumera os estados possíveis do animal. |

O projeto aplica principalmente **herança**, **herança múltipla com mixins**, **encapsulamento e validação**, **Repository**, **Strategy** e enumerações para representar estados. Métodos especiais implementados nas classes de domínio permitem representações textuais, comparação, hash e iteração quando aplicável.

### Estrutura de diretórios

```text
.
├── main.py
├── pyproject.toml
├── poetry.lock
├── mkdocs.yml
├── README.md
├── docs/
│   ├── CLI_Comands.md
│   ├── DiagramaDeClasses.drawio
│   ├── DiagramaDeClassesTextual.md
│   ├── assets/
│   │   └── DiagramaDeClasses.png
│   └── Domain Classes/
├── src/
│   └── sistema_de_adocao_de_animais/
│       ├── cli/
│       │   ├── main.py
│       │   ├── console.py
│       │   ├── erros.py
│       │   └── commands/
│       │       ├── animal.py
│       │       ├── adotante.py
│       │       ├── reserva.py
│       │       ├── adocao.py
│       │       ├── fila.py
│       │       ├── relatorio.py
│       │       └── sistema.py
│       ├── database/
│       │   └── database.db
│       ├── domain/
│       │   ├── animal.py
│       │   ├── cachorro.py
│       │   ├── gato.py
│       │   ├── pessoa.py
│       │   ├── adotante.py
│       │   ├── reserva.py
│       │   └── fila_espera.py
│       ├── enums/
│       ├── exceptions/
│       ├── mixins/
│       ├── repositories/
│       ├── strategies/
│       ├── settings.json
│       └── settings.py
└── tests/
```

## 7. Banco de dados

A persistência é feita com SQLite. O arquivo padrão está em `src/sistema_de_adocao_de_animais/database/database.db`. As tabelas são inicializadas pelos comandos que precisam delas; para criar e popular os dados de demonstração, use `seed`.

O banco de desenvolvimento está incluído no projeto. Se quiser começar com dados de demonstração limpos, faça isso conscientemente com `seed --limpar`, lembrando que o comando apaga os registros de domínio do banco configurado.

## 8. Testes e qualidade

Execute toda a suíte de testes com:

```bash
poetry run pytest -q
```

Para executar os testes com detalhes e cobertura, use a tarefa definida no `pyproject.toml`:

```bash
poetry run task test
```

A tarefa `test` executa o pytest com cobertura do pacote e gera um relatório HTML de cobertura. Para verificar a formatação e a organização dos imports:

```bash
poetry run task lint
```

Os testes cobrem fluxos de CLI, persistência, políticas de elegibilidade, compatibilidade, estratégias de taxa, reservas, expiração, fila de espera e relatórios.
