"""
Testes simples para src/servicos/exportador_json.py
Execute a partir da raiz do projeto: python -m tests.test_exportador_json
"""
import json
import os
from pathlib import Path
from datetime import datetime
from src.servicos.exportador_json import _converter_para_serializavel, exportar_resultado_consulta


def test_converter_tipos_simples():
    entrada = {"nome": "Ana", "idade": 15, "ativo": True}
    saida = _converter_para_serializavel(entrada)
    assert saida == entrada
    print("  converter tipos simples: OK")


def test_converter_datetime():
    agora = datetime(2026, 5, 9, 10, 30, 0)
    entrada = {"criacao": agora}
    saida = _converter_para_serializavel(entrada)
    assert saida["criacao"] == "2026-05-09 10:30:00"
    print("  converter datetime para string: OK")


def test_converter_lista_aninhada():
    entrada = [{"nome": "Ana"}, {"nome": "Bruno"}]
    saida = _converter_para_serializavel(entrada)
    assert len(saida) == 2
    assert saida[0]["nome"] == "Ana"
    print("  converter lista aninhada: OK")


def test_exportar_cria_arquivo():
    dados = [{"id": 1, "nome": "Teste"}]
    resposta = exportar_resultado_consulta("teste_exportacao", {"filtro": "x"}, dados)
    assert resposta["status"] is True, f"Exportacao falhou: {resposta['message']}"

    caminho = resposta["data"]["arquivo"]
    assert os.path.isfile(caminho), "Arquivo nao foi criado"

    with open(caminho, encoding="utf-8") as f:
        conteudo = json.load(f)

    assert conteudo["consulta"] == "teste_exportacao"
    assert conteudo["total_registros"] == 1
    assert len(conteudo["dados"]) == 1

    # Limpeza do arquivo de teste
    os.remove(caminho)
    print("  exportar_resultado_consulta cria arquivo valido: OK")


def test_exportar_lista_vazia():
    resposta = exportar_resultado_consulta("teste_vazio", {}, [])
    assert resposta["status"] is True
    caminho = resposta["data"]["arquivo"]
    with open(caminho, encoding="utf-8") as f:
        conteudo = json.load(f)
    assert conteudo["total_registros"] == 0
    os.remove(caminho)
    print("  exportar lista vazia: OK")


if __name__ == "__main__":
    print("=== Testes: exportador_json ===")
    test_converter_tipos_simples()
    test_converter_datetime()
    test_converter_lista_aninhada()
    test_exportar_cria_arquivo()
    test_exportar_lista_vazia()
    print("\nTodos os testes passaram.")
