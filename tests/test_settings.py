import json

import pytest  # type: ignore

from sistema_de_adocao_de_animais.settings import (
    DEFAULT_PATH,
    ConfiguracaoInvalidaError,
    load_settings,
)


def _settings_alterado(tmp_path, alterar):
    """Copia o settings.json, aplica `alterar` ao dict e devolve o novo caminho."""
    config = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
    alterar(config)
    caminho = tmp_path / "settings.json"
    caminho.write_text(json.dumps(config), encoding="utf-8")
    return caminho


def test_carrega_settings_padrao():
    settings = load_settings()
    assert settings.idade_minima_adotante == 18
    assert settings.reserva_horas == 48
    assert settings.moradia_exigida == "CASA"
    assert "GRANDE" in settings.portes_restritos
    assert sum(settings.pesos.values()) == 100


def test_arquivo_inexistente(tmp_path):
    with pytest.raises(ConfiguracaoInvalidaError):
        load_settings(tmp_path / "nao_existe.json")


def test_json_invalido(tmp_path):
    caminho = tmp_path / "settings.json"
    caminho.write_text("{ isso nao e json", encoding="utf-8")
    with pytest.raises(ConfiguracaoInvalidaError):
        load_settings(caminho)


def test_peso_ausente(tmp_path):
    caminho = _settings_alterado(
        tmp_path, lambda c: c["compatibilidade"]["pesos"].pop("criancas")
    )
    with pytest.raises(ConfiguracaoInvalidaError):
        load_settings(caminho)


def test_peso_negativo(tmp_path):
    def alterar(c):
        c["compatibilidade"]["pesos"]["criancas"] = -5

    with pytest.raises(ConfiguracaoInvalidaError):
        load_settings(_settings_alterado(tmp_path, alterar))


def test_combinacao_moradia_porte_ausente(tmp_path):
    caminho = _settings_alterado(
        tmp_path, lambda c: c["compatibilidade"]["porte_moradia"]["CASA"].pop("MINI")
    )
    with pytest.raises(ConfiguracaoInvalidaError):
        load_settings(caminho)


def test_reserva_horas_deve_ser_positiva(tmp_path):
    def alterar(c):
        c["reserva_horas"] = 0

    with pytest.raises(ConfiguracaoInvalidaError):
        load_settings(_settings_alterado(tmp_path, alterar))


def test_chave_ausente(tmp_path):
    caminho = _settings_alterado(tmp_path, lambda c: c.pop("politicas"))
    with pytest.raises(ConfiguracaoInvalidaError):
        load_settings(caminho)


def test_fila_peso_negativo(tmp_path):
    def alterar(c):
        c["fila_espera"]["peso_tempo_espera"] = -1

    with pytest.raises(ConfiguracaoInvalidaError):
        load_settings(_settings_alterado(tmp_path, alterar))


def test_fila_pesos_zerados(tmp_path):
    def alterar(c):
        c["fila_espera"]["peso_pontuacao"] = 0
        c["fila_espera"]["peso_tempo_espera"] = 0

    with pytest.raises(ConfiguracaoInvalidaError):
        load_settings(_settings_alterado(tmp_path, alterar))


def test_fila_dias_maximos_devem_ser_positivos(tmp_path):
    def alterar(c):
        c["fila_espera"]["dias_espera_max_normalizacao"] = 0

    with pytest.raises(ConfiguracaoInvalidaError):
        load_settings(_settings_alterado(tmp_path, alterar))


def test_fila_chave_ausente(tmp_path):
    caminho = _settings_alterado(
        tmp_path, lambda c: c["fila_espera"].pop("peso_pontuacao")
    )
    with pytest.raises(ConfiguracaoInvalidaError):
        load_settings(caminho)
