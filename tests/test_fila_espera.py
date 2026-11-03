from datetime import date, datetime, timedelta

import pytest  # type: ignore

from sistema_de_adocao_de_animais.domain.adotante import Adotante
from sistema_de_adocao_de_animais.domain.cachorro import Cachorro
from sistema_de_adocao_de_animais.domain.fila_espera import EntradaFila, FilaDeEspera
from sistema_de_adocao_de_animais.domain.reserva import Reserva
from sistema_de_adocao_de_animais.enums.moradias import Moradia
from sistema_de_adocao_de_animais.enums.porte_animal import PorteAnimal
from sistema_de_adocao_de_animais.enums.status_animal import StatusAnimal
from sistema_de_adocao_de_animais.settings import load_settings
from sistema_de_adocao_de_animais.strategies.compatibilidade_strategy import (
    CompatibilidadePonderada,
)

T0 = datetime(2026, 11, 2, 12, 0)


def _adotante(id=1, nome="Ana"):
    return Adotante(
        nome=nome,
        idade=30,
        telefone="88999999999",
        moradia=Moradia.CASA,
        areaUtil=100.0,
        experiencia=True,
        criancasEmCasa=False,
        outrosAnimais=False,
        id=id,
    )


def _cachorro(id=1):
    return Cachorro(
        nome="Rex",
        idade=36,
        raca="SRD",
        sexo="M",
        porte=PorteAnimal.MEDIO,
        peso=10,
        data_entrada=date(2026, 1, 1),
        temperamento=[],
        historico=[],
        id=id,
    )


@pytest.fixture
def settings():
    return load_settings()


@pytest.fixture
def fila(settings):
    return FilaDeEspera(_cachorro(), settings)


def _ids(fila):
    return [entrada.adotante.id for entrada in fila.fila]


def test_fila_nova_esta_vazia(fila):
    assert len(fila) == 0
    assert fila.proximo(T0) is None


def test_filas_nao_compartilham_lista(settings):
    uma = FilaDeEspera(_cachorro(id=1), settings)
    outra = FilaDeEspera(_cachorro(id=2), settings)
    uma.adicionar(_adotante(), 80, T0)
    assert len(uma) == 1
    assert len(outra) == 0


def test_animal_deve_ser_instancia_de_animal(settings):
    with pytest.raises(ValueError):
        FilaDeEspera("Rex", settings)


def test_adicionar_aumenta_len_e_expoe_animal_id(fila):
    entrada = fila.adicionar(_adotante(), 80, T0)
    assert isinstance(entrada, EntradaFila)
    assert len(fila) == 1
    assert fila.animal_id == 1


def test_maior_compatibilidade_vem_primeiro(fila):
    fila.adicionar(_adotante(id=1, nome="Ana"), 60, T0)
    fila.adicionar(_adotante(id=2, nome="Bia"), 90, T0)
    fila.adicionar(_adotante(id=3, nome="Caio"), 75, T0)
    assert _ids(fila) == [2, 3, 1]


def test_tempo_de_espera_pode_superar_a_pontuacao(fila):
    # Ana: 0,7*60 + 0,3*100 = 72 | Bia: 0,7*80 = 56
    fila.adicionar(_adotante(id=1, nome="Ana"), 60, T0 - timedelta(days=30))
    fila.adicionar(_adotante(id=2, nome="Bia"), 80, T0)
    assert fila.proximo(T0).adotante.id == 1


def test_tempo_de_espera_tem_limite(fila):
    antiga = fila.adicionar(_adotante(id=1, nome="Ana"), 70, T0 - timedelta(days=300))
    recente = fila.adicionar(_adotante(id=2, nome="Bia"), 70, T0 - timedelta(days=30))
    fila.atualizar_lista(T0)
    assert antiga.prioridade == recente.prioridade


def test_empate_vence_quem_entrou_antes(fila):
    fila.adicionar(_adotante(id=1, nome="Ana"), 70, T0 - timedelta(days=300))
    fila.adicionar(_adotante(id=2, nome="Bia"), 70, T0 - timedelta(days=30))
    assert fila.proximo(T0).adotante.id == 1


def test_empate_total_vence_o_menor_id(fila):
    fila.adicionar(_adotante(id=5, nome="Ana"), 70, T0)
    fila.adicionar(_adotante(id=2, nome="Bia"), 70, T0)
    assert _ids(fila) == [2, 5]


def test_ordem_muda_com_o_passar_do_tempo(fila):
    fila.adicionar(_adotante(id=1, nome="Ana"), 60, T0)
    fila.adicionar(_adotante(id=2, nome="Bia"), 75, T0 + timedelta(days=25))
    assert fila.proximo(T0 + timedelta(days=25)).adotante.id == 1
    assert fila.proximo(T0 + timedelta(days=55)).adotante.id == 2


def test_nao_aceita_adotante_duplicado(fila):
    fila.adicionar(_adotante(), 80, T0)
    with pytest.raises(ValueError):
        fila.adicionar(_adotante(), 90, T0)
    assert len(fila) == 1


def test_nao_aceita_adotante_sem_id(fila):
    with pytest.raises(ValueError):
        fila.adicionar(_adotante(id=None), 80, T0)


def test_compatibilidade_fora_do_intervalo(fila):
    with pytest.raises(ValueError):
        fila.adicionar(_adotante(id=1), 101, T0)
    with pytest.raises(ValueError):
        fila.adicionar(_adotante(id=2), -1, T0)
    assert len(fila) == 0


def test_remover_tira_da_fila(fila):
    ana = _adotante(id=1, nome="Ana")
    fila.adicionar(ana, 80, T0)
    fila.remover(ana)
    assert len(fila) == 0
    assert ana not in fila


def test_remover_quem_nao_esta_na_fila(fila):
    with pytest.raises(ValueError):
        fila.remover(_adotante())


def test_posicao(fila):
    ana, bia = _adotante(id=1, nome="Ana"), _adotante(id=2, nome="Bia")
    fila.adicionar(ana, 60, T0)
    fila.adicionar(bia, 90, T0)
    assert fila.posicao(bia, T0) == 1
    assert fila.posicao(ana, T0) == 2


def test_posicao_de_quem_nao_esta_na_fila(fila):
    with pytest.raises(ValueError):
        fila.posicao(_adotante(), T0)


def test_contains_compara_por_id(fila):
    fila.adicionar(_adotante(id=1), 80, T0)
    assert _adotante(id=1) in fila
    assert _adotante(id=2, nome="Bia") not in fila
    assert "Ana" not in fila


def test_iter_percorre_em_ordem_de_prioridade(fila):
    fila.adicionar(_adotante(id=1, nome="Ana"), 60, T0)
    fila.adicionar(_adotante(id=2, nome="Bia"), 90, T0)
    assert [e.adotante.id for e in fila] == [2, 1]


def test_entradas_ordenam_por_prioridade():
    alta = EntradaFila(_adotante(id=1), 90, T0, prioridade=90)
    baixa = EntradaFila(_adotante(id=2, nome="Bia"), 50, T0, prioridade=50)
    assert alta < baixa
    assert sorted([baixa, alta]) == [alta, baixa]


def test_notificar_proximo_registra_evento_no_historico(fila):
    fila.adicionar(_adotante(id=1, nome="Ana"), 60, T0)
    fila.adicionar(_adotante(id=2, nome="Bia"), 90, T0)

    notificado = fila.notificar_proximo(T0)

    assert notificado.adotante.id == 2
    evento = fila.animal.historico[-1]
    assert evento["tipo"] == "FILA_ESPERA"
    assert "Bia" in evento["nome"]
    assert evento["data"] == T0.date()
    assert len(fila) == 2  # notificar não tira ninguém da fila


def test_notificar_fila_vazia_nao_faz_nada(fila):
    assert fila.notificar_proximo(T0) is None
    assert fila.animal.historico == []


def test_observadores_sao_avisados(fila):
    avisos = []
    fila.registrar_observador(lambda entrada, animal: avisos.append((entrada, animal)))
    fila.adicionar(_adotante(id=1, nome="Ana"), 80, T0)

    fila.notificar_proximo(T0)

    assert len(avisos) == 1
    assert avisos[0][0].adotante.id == 1
    assert avisos[0][1] is fila.animal


def test_reserva_expirada_notifica_o_proximo_da_fila(settings):
    estrategia = CompatibilidadePonderada(settings)
    animal = _cachorro()
    fila = FilaDeEspera(animal, settings)

    bia = _adotante(id=2, nome="Bia")

    # Calcula a compatibilidade utilizando a Strategy
    compatibilidade_bia = estrategia.calcular(bia, animal)

    fila.adicionar(bia, compatibilidade_bia, T0)

    ana = _adotante(id=1, nome="Ana")

    # Calcula a compatibilidade da reserva utilizando a Strategy
    compatibilidade_ana = estrategia.calcular(ana, animal)

    reserva = Reserva(
        adotante=ana,
        animal=animal,
        compatibilidade=compatibilidade_ana,
        dataReserva=T0,
        dataExpiracao=T0 + timedelta(hours=settings.reserva_horas),
    )

    # O animal está reservado para Ana
    animal.status = StatusAnimal.RESERVADO

    # Simula a passagem do prazo de expiração
    depois = T0 + timedelta(hours=settings.reserva_horas + 1)

    # Expira a reserva
    expirou = reserva.expirar_vencida(depois)

    assert expirou is True
    assert reserva.status == "EXPIRADA"
    assert animal.status == StatusAnimal.DISPONIVEL

    # Notifica o próximo adotante da fila
    notificado = fila.notificar_proximo(depois)

    assert notificado is not None
    assert notificado.adotante.id == 2
