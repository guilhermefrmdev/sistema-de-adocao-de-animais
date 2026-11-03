# Comandos do CLI

## Animal:
### Cachorro
```
animal cachorro cadastrar <nome> <idade> <raca> <sexo> <peso> <porte>
> options: 
    --necessidadePasseio                     (se há necessidade de passeio) default=False
    --castrado                               (se for castrado) default=False
    --temperamento <separado,por,virgulas>   (o temperamento do animal) default=[]
    --status <INADOTAVEL|QUARENTENA>         (status do animal) default=DISPONIVEL
```

### Gato

```
animal gato cadastrar <nome> <idade> <raca> <sexo> <peso> <porte> <independencia> <tipoPelo>
> options: 
    --castrado                               (se for castrado) default=False
    --temperamento <separado,por,virgulas>   (o temperamento do animal) default=[]
    --status <INADOTAVEL|QUARENTENA>         (status do animal) default=DISPONIVEL
```
### Geral:
```
animal adicionar-historico <id_animal> <tipo> <nome> <data>
```
```
animal mudar-status <id_animal> <status>
```
```
animal listar
```

## Reserva:
```
reserva criar <id_adotante> <id_animal>
```
```
reserva cancelar <id_adocao>
```
```
reserva listar
```
```
reserva devolver-
```

## Adotante:
```
adotante cadastrar <nome> <idade> <telefone> <moradia> <areaUtil>
> options
    --experiencia      (se há experiência com animais)   default=False
    --criancasEmCasa   (se há crianças em casa)          default=False
    --outrosAnimais    (se há outros animais em casa)    default=False
```
```
adotante listar
```