import json
import os
from pathlib import Path
from datetime import datetime
from src.apoio.utils import gerar_resposta, gerar_data_atual


def _converter_para_serializavel(obj):
    if isinstance(obj, dict):
        return {k: _converter_para_serializavel(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_converter_para_serializavel(item) for item in obj]
    if hasattr(obj, "strftime"):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    return obj


def exportar_resultado_consulta(nome_consulta: str, filtro: dict, dados: list) -> dict:
    try:
        pasta = Path("exports")
        pasta.mkdir(exist_ok=True)
    except OSError as exc:
        return gerar_resposta(False, 500, f"Não foi possível criar a pasta exports: {exc}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"{nome_consulta}_{timestamp}.json"
    caminho = pasta / nome_arquivo

    payload = {
        "consulta": nome_consulta,
        "filtro": filtro,
        "total_registros": len(dados),
        "data_exportacao": gerar_data_atual(),
        "dados": _converter_para_serializavel(dados),
    }

    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)
    except (OSError, TypeError, ValueError) as exc:
        return gerar_resposta(False, 500, f"Erro ao salvar o arquivo JSON: {exc}")

    return gerar_resposta(True, 200, f"Exportado com sucesso: {caminho}", {"arquivo": str(caminho)})
