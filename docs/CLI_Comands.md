# Comandos do CLI

CLI construída com **Typer** e estilizada com **Rich**.

```
python main.py <grupo> <comando> [argumentos] [opções]
python main.py --help
python main.py <grupo> --help
```

## Convenções

| Item | Formato |
|---|---|
| Data | `AAAA-MM-DD` (ex.: `2026-11-03`) |
| Porte | `MINI`, `PEQUENO`, `MEDIO`, `GRANDE`, `GIGANTE` (atalhos `P`, `M`, `G` = `PEQUENO`, `MEDIO`, `GRANDE`) |
| Sexo | `M` ou `F` |
| Moradia | `CASA` ou `APARTAMENTO` |
| Independência (gato) | `BAIXA`, `MEDIA`, `ALTA` |
| Tipo de pelo (gato) | `SEM_PELOS`, `CURTO`, `LONGO`, `ONDULADO` |
| Status do animal | `DISPONIVEL`, `RESERVADO`, `ADOTADO`, `DEVOLVIDO`, `QUARENTENA`, `INADOTAVEL` |
| Estratégia de taxa | `padrao`, `senior`, `filhote`, `especial` |
| Idade do animal | em **meses** |
| Idade do adotante | em **anos** |
| Opções | em `kebab-case` (ex.: `--necessidade-passeio`) |
| Valores com texto livre | entre aspas (ex.: `"Golden Retriever"`) |

- Valores de enum não diferenciam maiúsculas de minúsculas.
- Opções booleanas são *flags*: presentes = `True`, ausentes = `False`.
- Erros de validação e de regra de negócio aparecem em painel vermelho, sem *traceback*, e o comando termina com código de saída `1`.
- Comandos que alteram dados mostram um painel de confirmação em verde.

---

## Animal

### Cachorro
```
animal cachorro cadastrar <nome> <idade> <raca> <sexo> <peso> <porte>
> options:
    --necessidade-passeio                    (se há necessidade de passeio)   default=False
    --castrado                               (se for castrado)                default=False
    --temperamento <separado,por,virgulas>   (o temperamento do animal)       default=[]
    --status <INADOTAVEL|QUARENTENA>         (status inicial do animal)       default=DISPONIVEL
    --data-entrada <AAAA-MM-DD>              (data de entrada no abrigo)      default=hoje
```

### Gato
```
animal gato cadastrar <nome> <idade> <raca> <sexo> <peso> <porte> <independencia> <tipo-pelo>
> options:
    --castrado                               (se for castrado)                default=False
    --temperamento <separado,por,virgulas>   (o temperamento do animal)       default=[]
    --status <INADOTAVEL|QUARENTENA>         (status inicial do animal)       default=DISPONIVEL
    --data-entrada <AAAA-MM-DD>              (data de entrada no abrigo)      default=hoje
```

### Geral
```
animal listar
> options (filtros combináveis, aplicados em conjunto):
    --especie <cachorro|gato>
    --porte <PORTE>
    --status <STATUS>
    --idade-min <meses>
    --idade-max <meses>
    --temperamento <termo>
```
```
animal ver <id_animal>
```
```
animal atualizar <id_animal>
> options (somente o que for informado é alterado):
    --nome <nome>
    --idade <meses>
    --raca <raca>
    --peso <peso>
    --porte <PORTE>
    --castrado / --nao-castrado
    --temperamento <separado,por,virgulas>
    --necessidade-passeio / --sem-necessidade-passeio    (somente cachorro)
    --independencia <NIVEL>                              (somente gato)
    --tipo-pelo <TIPO>                                   (somente gato)
```
```
animal excluir <id_animal>
> options:
    --sim            (pula a confirmação)
```
```
animal historico <id_animal>
```
```
animal adicionar-historico <id_animal> <tipo> <nome>
> options:
    --data <AAAA-MM-DD>     default=hoje
```
```
animal vacinar <id_animal> <nome_vacina>
> options:
    --data <AAAA-MM-DD>     default=hoje
> registra no histórico um evento do tipo VACINA
```
```
animal mudar-status <id_animal> <status>
> aplica as transições válidas:
    DISPONIVEL -> RESERVADO -> ADOTADO
    DISPONIVEL -> INADOTAVEL
    ADOTADO    -> DEVOLVIDO -> (QUARENTENA | DISPONIVEL | INADOTAVEL)
    QUARENTENA -> (DISPONIVEL | INADOTAVEL)
> transição inválida mostra erro e não altera o animal
```
```
animal reavaliar <id_animal> <DISPONIVEL|INADOTAVEL>
> options:
    --observacao <texto>    (fica registrada no histórico)
> reavaliação de saúde/temperamento de animal em QUARENTENA ou DEVOLVIDO
```

---

## Adotante

```
adotante cadastrar <nome> <idade> <telefone> <moradia> <area-util>
> options
    --experiencia        (se há experiência com animais)   default=False
    --criancas-em-casa   (se há crianças em casa)          default=False
    --outros-animais     (se há outros animais em casa)    default=False
```
```
adotante listar
```
```
adotante ver <id_adotante>
```
```
adotante atualizar <id_adotante>
> options (somente o que for informado é alterado):
    --nome <nome>
    --idade <anos>
    --telefone <telefone>
    --moradia <CASA|APARTAMENTO>
    --area-util <m²>
    --experiencia / --sem-experiencia
    --criancas-em-casa / --sem-criancas
    --outros-animais / --sem-outros-animais
```
```
adotante excluir <id_adotante>
> options:
    --sim            (pula a confirmação)
```
```
adotante elegivel <id_adotante> <id_animal>
> valida as políticas do settings.json (idade mínima, moradia/área para portes restritos)
> mostra cada regra com ✔ ou ✘
```
```
adotante compatibilidade <id_adotante> <id_animal>
> mostra a pontuação final (0–100) e a nota de cada critério ponderado:
    porte x moradia, idade x energia, experiência, crianças
```

---

## Reserva

```
reserva criar <id_adotante> <id_animal>
> valida elegibilidade e calcula a compatibilidade
> animal DISPONIVEL -> cria reserva ATIVA por settings.reserva_horas (padrão 48h)
                       e muda o animal para RESERVADO
> animal RESERVADO  -> informa que já há reserva ativa e sugere `fila entrar`
> apenas 1 reserva ativa por animal
```
```
reserva cancelar <id_reserva>
> status da reserva -> CANCELADA, animal volta para DISPONIVEL
> notifica o próximo da fila (se houver)
```
```
reserva listar
> options:
    --status <ATIVA|EXPIRADA|CONCLUIDA|CANCELADA>
    --animal <id_animal>
    --adotante <id_adotante>
```
```
reserva rodar-expiracao
> "job" que expira as reservas ATIVAS vencidas
> animal volta para DISPONIVEL
> notifica o próximo da fila de cada animal (registra evento no histórico)
> mostra quantas reservas foram expiradas e quem foi notificado
> options:
    --agora <AAAA-MM-DD HH:MM>     (simula a data atual, útil para demonstração e testes)
```

---

## Adoção

```
adocao taxa <id_animal>
> options:
    --estrategia <padrao|senior|filhote|especial>    default=settings.taxas.estrategia_padrao
> apenas calcula e mostra a taxa, sem alterar nada
```
```
adocao efetivar <id_reserva>
> options:
    --estrategia <padrao|senior|filhote|especial>    default=settings.taxas.estrategia_padrao
> reserva ATIVA -> CONCLUIDA, animal RESERVADO -> ADOTADO
> limpa a fila de espera do animal
> gera e exibe o contrato (resumo do animal, do adotante, taxa e termos)
```
```
adocao contrato <id_adocao>
> options:
    --salvar <arquivo.txt>    (grava o contrato em arquivo)
```
```
adocao listar
> options:
    --adotante <id_adotante>
```
```
adocao devolver <id_adocao> <motivo>
> options:
    --quarentena     (problema de saúde/comportamento: animal vai para QUARENTENA)
> sem --quarentena: animal ADOTADO -> DEVOLVIDO
> registra o motivo no histórico do animal e na adoção
```

---

## Fila de espera

```
fila entrar <id_adotante> <id_animal>
> calcula a compatibilidade e coloca o adotante na fila do animal
> prioridade = pontuação (peso 0.7) + tempo de espera (peso 0.3), pesos em settings.json
```
```
fila ver <id_animal>
> mostra a fila ordenada: posição, adotante, compatibilidade, dias de espera e prioridade
```
```
fila sair <id_adotante> <id_animal>
```

---

## Relatórios

```
relatorio top
> options:
    --limite <n>     default=5
> animais mais adotáveis (maior média de compatibilidade)
```
```
relatorio adocoes
> options:
    --por <especie|porte>    default=especie
> taxa de adoções por espécie ou porte
```
```
relatorio tempo-medio
> tempo médio, em dias, entre a entrada do animal e a adoção
```
```
relatorio devolucoes
> adoções canceladas/devoluções agrupadas por motivo
```
```
relatorio disponiveis
> animais disponíveis e adotados
```

---

## Configuração e dados

```
config mostrar
> exibe as políticas carregadas do settings.json
> (idades mínimas, regras moradia/porte, duração da reserva, pesos, estratégia de taxa)
```
```
seed
> options:
    --limpar     (apaga os dados existentes antes de popular)
> popula o banco com animais, adotantes, reservas e uma fila de exemplo
> pode ser executado mais de uma vez sem duplicar registros
```

---

## Resumo dos comandos

| Grupo | Comandos |
|---|---|
| `animal` | `cachorro cadastrar`, `gato cadastrar`, `listar`, `ver`, `atualizar`, `excluir`, `historico`, `adicionar-historico`, `vacinar`, `mudar-status`, `reavaliar` |
| `adotante` | `cadastrar`, `listar`, `ver`, `atualizar`, `excluir`, `elegivel`, `compatibilidade` |
| `reserva` | `criar`, `cancelar`, `listar`, `rodar-expiracao` |
| `adocao` | `taxa`, `efetivar`, `contrato`, `listar`, `devolver` |
| `fila` | `entrar`, `ver`, `sair` |
| `relatorio` | `top`, `adocoes`, `tempo-medio`, `devolucoes`, `disponiveis` |
| (raiz) | `config mostrar`, `seed` |

