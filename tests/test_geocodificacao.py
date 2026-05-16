"""
Testes para src/servicos/geocodificacao.py
Execute a partir da raiz: python -m tests.test_geocodificacao
Zero chamadas reais ao Nominatim — requests.get é sempre mockado.
"""
import pytest
from unittest.mock import patch, MagicMock
import requests

from src.servicos.geocodificacao import (
    montar_endereco_textual,
    geocodificar_endereco,
    calcular_distancia_km,
)


# ─── montar_endereco_textual ─────────────────────────────────────────────────

def test_montar_endereco_textual_basico():
    resultado = montar_endereco_textual("Av Paulista", "900", "Bela Vista", "São Paulo", "SP", "01310100")
    assert "Av Paulista" in resultado
    assert "900" in resultado
    assert "Bela Vista" in resultado
    assert "São Paulo" in resultado
    assert "SP" in resultado
    assert "01310100" in resultado
    print("  montar_endereco_textual_basico: OK")


def test_montar_endereco_textual_ignora_vazios():
    resultado = montar_endereco_textual("", "100", "", "Campinas", "SP", "13000000")
    assert resultado == "100, Campinas, SP, 13000000"
    print("  montar_endereco_textual_ignora_vazios: OK")


def test_montar_endereco_textual_tudo_vazio():
    resultado = montar_endereco_textual()
    assert resultado == ""
    print("  montar_endereco_textual_tudo_vazio: OK")


# ─── calcular_distancia_km ───────────────────────────────────────────────────

def test_calcular_distancia_km_zero():
    lat, lon = -23.561684, -46.655981  # Av Paulista, SP
    dist = calcular_distancia_km(lat, lon, lat, lon)
    assert dist == 0.0
    print("  calcular_distancia_km_zero: OK")


def test_calcular_distancia_km_paulista_para_itaim():
    # Av Paulista (approx) → Itaim Bibi (approx) — ~3,5 a 4,5 km em linha reta
    lat1, lon1 = -23.561684, -46.655981  # Av Paulista
    lat2, lon2 = -23.587780, -46.678280  # Itaim Bibi
    dist = calcular_distancia_km(lat1, lon1, lat2, lon2)
    assert 2.0 <= dist <= 6.0, f"Distância fora do esperado: {dist} km"
    print(f"  calcular_distancia_km_paulista_para_itaim: {dist} km — OK")


def test_calcular_distancia_km_coordenadas_invalidas_none():
    with pytest.raises(ValueError):
        calcular_distancia_km(None, -46.655981, -23.587780, -46.678280)
    print("  calcular_distancia_km_coordenadas_invalidas_none: OK")


def test_calcular_distancia_km_coordenadas_invalidas_string():
    with pytest.raises((ValueError, TypeError)):
        calcular_distancia_km("abc", -46.655981, -23.587780, -46.678280)
    print("  calcular_distancia_km_coordenadas_invalidas_string: OK")


# ─── geocodificar_endereco (mockado) ─────────────────────────────────────────

def test_geocodificar_endereco_sucesso_mock():
    payload_nominatim = [{"lat": "-23.561684", "lon": "-46.655981", "display_name": "Av Paulista, SP"}]
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = payload_nominatim

    with patch("requests.get", return_value=mock_resp):
        resultado = geocodificar_endereco("Av Paulista 900, Bela Vista, São Paulo, SP")

    assert resultado["sucesso"] is True
    assert resultado["latitude"] == -23.561684
    assert resultado["longitude"] == -46.655981
    assert resultado["motivo_falha"] is None
    print("  geocodificar_endereco_sucesso_mock: OK")


def test_geocodificar_endereco_timeout_mock():
    with patch("requests.get", side_effect=requests.Timeout):
        resultado = geocodificar_endereco("Endereço qualquer")

    assert resultado["sucesso"] is False
    assert resultado["latitude"] is None
    assert resultado["longitude"] is None
    assert "timeout" in resultado["motivo_falha"].lower()
    print("  geocodificar_endereco_timeout_mock: OK")


def test_geocodificar_endereco_lista_vazia_mock():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = []

    with patch("requests.get", return_value=mock_resp):
        resultado = geocodificar_endereco("Endereço inexistente XYZ")

    assert resultado["sucesso"] is False
    assert "não encontrado" in resultado["motivo_falha"].lower()
    print("  geocodificar_endereco_lista_vazia_mock: OK")


def test_geocodificar_endereco_http_error_mock():
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    http_error = requests.HTTPError(response=mock_resp)

    with patch("requests.get", side_effect=http_error):
        resultado = geocodificar_endereco("Av Paulista 900")

    assert resultado["sucesso"] is False
    assert resultado["motivo_falha"] is not None
    print("  geocodificar_endereco_http_error_mock: OK")


def test_geocodificar_endereco_connection_error_mock():
    with patch("requests.get", side_effect=requests.ConnectionError):
        resultado = geocodificar_endereco("Qualquer endereço")

    assert resultado["sucesso"] is False
    assert "conexão" in resultado["motivo_falha"].lower()
    print("  geocodificar_endereco_connection_error_mock: OK")


def test_geocodificar_endereco_vazio():
    resultado = geocodificar_endereco("")
    assert resultado["sucesso"] is False
    assert resultado["motivo_falha"] is not None
    print("  geocodificar_endereco_vazio: OK")


if __name__ == "__main__":
    print("=== Testes: geocodificacao ===")
    test_montar_endereco_textual_basico()
    test_montar_endereco_textual_ignora_vazios()
    test_montar_endereco_textual_tudo_vazio()
    test_calcular_distancia_km_zero()
    test_calcular_distancia_km_paulista_para_itaim()
    test_calcular_distancia_km_coordenadas_invalidas_none()
    test_calcular_distancia_km_coordenadas_invalidas_string()
    test_geocodificar_endereco_sucesso_mock()
    test_geocodificar_endereco_timeout_mock()
    test_geocodificar_endereco_lista_vazia_mock()
    test_geocodificar_endereco_http_error_mock()
    test_geocodificar_endereco_connection_error_mock()
    test_geocodificar_endereco_vazio()
    print("\nTodos os testes passaram.")
