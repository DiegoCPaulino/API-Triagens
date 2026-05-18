import requests
from src.apoio.utils import gerar_resposta
from src.apoio.validators import validar_cep


def consultar_cep(cep: str) -> dict:
    # ViaCEP é usado para complementar endereço (logradouro, bairro, cidade, UF) e apoiar
    # o fallback de sugestão de dentista. Não calcula distância — apenas enriquece o dado.
    resultado_val = validar_cep(cep)
    if not resultado_val["status"]:
        return resultado_val

    cep_limpo = resultado_val["data"]
    url = f"https://viacep.com.br/ws/{cep_limpo}/json/"

    try:
        resposta = requests.get(url, timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
    except requests.exceptions.ConnectionError:
        return gerar_resposta(False, 503, "Sem conexão com a internet. Verifique sua rede.")
    except requests.exceptions.Timeout:
        return gerar_resposta(False, 504, "A consulta ao ViaCEP demorou demais. Tente novamente.")
    except requests.exceptions.RequestException as exc:
        return gerar_resposta(False, 503, f"Erro ao consultar o ViaCEP: {exc}")
    except ValueError:
        return gerar_resposta(False, 502, "Resposta inválida do ViaCEP.")

    if dados.get("erro"):
        return gerar_resposta(False, 404, "CEP não encontrado. Verifique o número informado.")

    endereco = {
        "cep": cep_limpo,
        "logradouro": dados.get("logradouro", ""),
        "bairro": dados.get("bairro", ""),
        "cidade": dados.get("localidade", ""),
        "uf": dados.get("uf", ""),
        "complemento": dados.get("complemento", ""),
    }
    return gerar_resposta(True, 200, "CEP localizado com sucesso.", endereco)
