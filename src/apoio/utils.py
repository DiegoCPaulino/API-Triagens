from datetime import datetime


def gerar_data_atual() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calcular_idade_por_data_nascimento(data_str: str) -> int:
    hoje = datetime.now()
    nascimento = datetime.strptime(data_str, "%d/%m/%Y")
    idade = hoje.year - nascimento.year
    if (hoje.month, hoje.day) < (nascimento.month, nascimento.day):
        idade -= 1
    return idade


def gerar_resposta(status, code: int, message: str, data=None, error: list = None) -> dict:
    resposta = {
        "status": status,
        "code": code,
        "message": message,
        "data": data
    }
    if error is not None:
        resposta["erro"] = error
    return resposta


def normalizar_texto(texto) -> str:
    if texto is None:
        return ""
    texto = str(texto)
    return " ".join(texto.strip().split())
