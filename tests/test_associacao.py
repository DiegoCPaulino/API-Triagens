"""
Testes simples para a logica de distancia de CEP em src/modulos/associacao.py
Execute a partir da raiz do projeto: python -m tests.test_associacao
"""
from src.modulos.associacao import _distancia_cep


def test_distancia_cep_mesmos_ceps():
    assert _distancia_cep("01310100", "01310100") == 0
    print("  distancia mesmos CEPs: OK")


def test_distancia_cep_proximos():
    dist = _distancia_cep("01310100", "01310200")
    assert dist == 100
    print("  distancia CEPs proximos: OK")


def test_distancia_cep_diferentes_estados():
    # CEP SP vs CEP RS — diferenca numerica grande
    dist = _distancia_cep("01310100", "90010000")
    assert dist > 0
    print("  distancia CEPs estados diferentes: OK")


def test_distancia_cep_invalido():
    # CEP invalido retorna valor sentinela alto
    dist = _distancia_cep(None, "01310100")
    assert dist == 999999999
    dist2 = _distancia_cep("nao-e-cep", "01310100")
    assert dist2 == 999999999
    print("  distancia CEP invalido: OK")


def test_ordem_sugestao():
    # Verifica que o dentista com mesma cidade e preferido sobre diferente UF
    dentistas = [
        (1, "Dr. A", "01310200", "Sao Paulo", "SP", 3),   # mesma cidade
        (2, "Dr. B", "20040020", "Rio de Janeiro", "RJ", 5),
    ]
    cidade_paciente = "sao paulo"
    uf_paciente = "SP"
    cep_paciente = "01310100"

    candidatos_cidade = [d for d in dentistas if (d[3] or "").strip().lower() == cidade_paciente]
    candidatos_uf = [d for d in dentistas if (d[4] or "").strip().upper() == uf_paciente]

    if candidatos_cidade:
        pool = candidatos_cidade
    elif candidatos_uf:
        pool = candidatos_uf
    else:
        pool = list(dentistas)

    melhor = min(pool, key=lambda d: (_distancia_cep(cep_paciente, d[2]), d[0]))
    assert melhor[0] == 1, "Dentista da mesma cidade deve ser preferido"
    print("  ordem sugestao por cidade: OK")


if __name__ == "__main__":
    print("=== Testes: associacao (logica de distancia) ===")
    test_distancia_cep_mesmos_ceps()
    test_distancia_cep_proximos()
    test_distancia_cep_diferentes_estados()
    test_distancia_cep_invalido()
    test_ordem_sugestao()
    print("\nTodos os testes passaram.")
