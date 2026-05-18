import math
import requests

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# User-Agent identificável é obrigatório pela política de uso público do Nominatim.
# Usar o padrão de bibliotecas HTTP (python-requests/x.y) viola os termos e pode gerar bloqueio.
_USER_AGENT = "ProjetoNoraFIAP/1.0 (academico-fiap@projeto-nora.local)"
_TIMEOUT = 5        # segundos; evita que falha do Nominatim trave o endpoint de sugestão
_RAIO_TERRA_KM = 6371.0


def montar_endereco_textual(logradouro="", numero="", bairro="", cidade="", uf="", cep="") -> str:
    partes = [str(p).strip() for p in [logradouro, numero, bairro, cidade, uf, cep] if str(p).strip()]
    endereco = ", ".join(partes)
    # remove vírgulas órfãs e espaços duplicados
    while ",," in endereco:
        endereco = endereco.replace(",,", ",")
    return " ".join(endereco.split())


def geocodificar_endereco(endereco_str: str) -> dict:
    """Geocodifica via Nominatim/OSM. Sempre retorna dict com sucesso, latitude, longitude, motivo_falha."""
    _falha = lambda motivo: {"sucesso": False, "latitude": None, "longitude": None, "motivo_falha": motivo}

    if not endereco_str or not endereco_str.strip():
        return _falha("endereço vazio")

    params = {"q": endereco_str, "format": "json", "limit": 1, "countrycodes": "br"}
    headers = {"User-Agent": _USER_AGENT}

    try:
        resposta = requests.get(_NOMINATIM_URL, params=params, headers=headers, timeout=_TIMEOUT)
        resposta.raise_for_status()
        resultados = resposta.json()
    except requests.Timeout:
        return _falha("timeout na requisição ao Nominatim")
    except requests.ConnectionError:
        return _falha("sem conexão com o Nominatim")
    except requests.HTTPError as exc:
        return _falha(f"erro HTTP do Nominatim: {exc.response.status_code}")
    except ValueError:
        return _falha("resposta JSON inválida do Nominatim")
    except requests.RequestException as exc:
        return _falha(f"erro de requisição: {exc}")

    if not resultados:
        return _falha("endereço não encontrado pelo Nominatim")

    primeiro = resultados[0]
    try:
        lat = float(primeiro["lat"])
        lon = float(primeiro["lon"])
    except (KeyError, TypeError, ValueError):
        return _falha("lat/lon ausentes ou inválidos na resposta do Nominatim")

    if not (math.isfinite(lat) and math.isfinite(lon)):
        return _falha("lat/lon não são números finitos")

    return {"sucesso": True, "latitude": lat, "longitude": lon, "motivo_falha": None}


def calcular_distancia_km(lat1, lon1, lat2, lon2) -> float:
    """Distância aproximada em linha reta (fórmula de Haversine). Não representa rota viária,
    trânsito ou tempo de deslocamento — apenas a menor distância geodésica entre dois pontos."""
    for val in (lat1, lon1, lat2, lon2):
        if val is None or not isinstance(val, (int, float)) or not math.isfinite(val):
            raise ValueError("Coordenadas inválidas")

    lat1_r, lon1_r, lat2_r, lon2_r = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    return round(_RAIO_TERRA_KM * c, 2)
