"""
Testes para src/modulos/associacao.py
Execute a partir da raiz: python -m tests.test_associacao
Zero chamadas reais ao Nominatim — geocodificar_endereco é sempre mockado.
Zero chamadas reais ao banco — obter_conexao é sempre mockado.
"""
from unittest.mock import patch, MagicMock

from src.modulos.associacao import _distancia_cep, _pre_filtrar


# ─── _distancia_cep ──────────────────────────────────────────────────────────

def test_distancia_cep_mesmos_ceps():
    assert _distancia_cep("01310100", "01310100") == 0
    print("  distancia mesmos CEPs: OK")


def test_distancia_cep_proximos():
    dist = _distancia_cep("01310100", "01310200")
    assert dist == 100
    print("  distancia CEPs proximos: OK")


def test_distancia_cep_diferentes_estados():
    dist = _distancia_cep("01310100", "90010000")
    assert dist > 0
    print("  distancia CEPs estados diferentes: OK")


def test_distancia_cep_invalido():
    assert _distancia_cep(None, "01310100") == 999_999_999
    assert _distancia_cep("nao-e-cep", "01310100") == 999_999_999
    print("  distancia CEP invalido: OK")


# ─── _pre_filtrar ─────────────────────────────────────────────────────────────

def _dent(id_, cidade, uf, cep):
    return {
        "id_dentista": id_, "nome": f"Dr.{id_}", "especialidade": "",
        "cep": cep, "logradouro": "", "numero": "", "bairro": "",
        "cidade": cidade, "uf": uf, "vagas_disponiveis": 3,
    }


def test_pre_filtrar_mesma_cidade():
    dentistas = [
        _dent(1, "São Paulo", "SP", "01310100"),
        _dent(2, "Campinas", "SP", "13000000"),
        _dent(3, "Rio de Janeiro", "RJ", "20040020"),
    ]
    pool, criterio = _pre_filtrar(dentistas, "são paulo", "SP", "01001000")
    assert criterio == "mesma_cidade"
    assert all(d["cidade"] == "São Paulo" for d in pool)
    print("  _pre_filtrar mesma_cidade: OK")


def test_pre_filtrar_mesma_uf():
    dentistas = [
        _dent(1, "Campinas", "SP", "13000000"),
        _dent(2, "Rio de Janeiro", "RJ", "20040020"),
    ]
    pool, criterio = _pre_filtrar(dentistas, "são paulo", "SP", "01001000")
    assert criterio == "mesma_uf"
    assert all(d["uf"] == "SP" for d in pool)
    print("  _pre_filtrar mesma_uf: OK")


def test_pre_filtrar_cep_aproximado():
    dentistas = [
        _dent(1, "Manaus", "AM", "69000000"),
        _dent(2, "Belém", "PA", "66000000"),
    ]
    pool, criterio = _pre_filtrar(dentistas, "são paulo", "SP", "01001000")
    assert criterio == "cep_aproximado"
    assert len(pool) <= 5
    print("  _pre_filtrar cep_aproximado: OK")


def test_pre_filtrar_limite_cinco():
    dentistas = [_dent(i, "São Paulo", "SP", f"0131010{i}") for i in range(10)]
    pool, criterio = _pre_filtrar(dentistas, "são paulo", "SP", "01310100")
    assert len(pool) <= 5
    assert criterio == "mesma_cidade"
    print("  _pre_filtrar limite 5 candidatos: OK")


# ─── sugerir_dentista_para_paciente (pipeline completo, mockado) ──────────────

def _make_mock_conexao(row_paciente, rows_dentistas):
    """Cria mock de conexão Oracle com dados pré-definidos."""
    mock_cur = MagicMock()
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)
    mock_cur.fetchone.return_value = row_paciente
    mock_cur.fetchall.return_value = rows_dentistas

    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value = mock_cur

    return mock_conn


# Tupla que simula row de paciente:
# ID_PACIENTE, NOME_COMPLETO, LOGRADOURO, NUMERO, BAIRRO, CIDADE, UF, CEP
_PAC_ROW = (12, "João Silva", "Av Paulista", "900", "Bela Vista", "São Paulo", "SP", "01310100")

# Tupla que simula row de dentista:
# ID_DENTISTA, NOME, ESPECIALIDADE, CEP, LOGRADOURO, NUMERO, BAIRRO, CIDADE, UF, VAGAS_DISPONIVEIS
_DENT_ROW = (3, "Dra. Ana Paula", "Ortodontia", "01310200", "Av Paulista", "1000", "Bela Vista", "São Paulo", "SP", 4)


def test_sugestao_sem_dentista_com_vaga():
    from src.modulos.associacao import sugerir_dentista_para_paciente
    mock_conn = _make_mock_conexao(_PAC_ROW, [])

    with patch("src.modulos.associacao.obter_conexao", return_value=mock_conn):
        resultado = sugerir_dentista_para_paciente(12)

    assert resultado["status"] is False
    assert resultado["code"] == 404
    assert resultado["data"]["metodo_calculo"] == "sem_dentista_disponivel"
    assert resultado["data"]["distancia_km"] is None
    print("  sugestao_sem_dentista_com_vaga: OK")


def test_sugestao_fallback_mesma_cidade():
    from src.modulos.associacao import sugerir_dentista_para_paciente
    mock_conn = _make_mock_conexao(_PAC_ROW, [_DENT_ROW])

    geo_falha = {"sucesso": False, "latitude": None, "longitude": None, "motivo_falha": "timeout"}

    with patch("src.modulos.associacao.obter_conexao", return_value=mock_conn), \
         patch("src.modulos.associacao.geocodificar_endereco", return_value=geo_falha):
        resultado = sugerir_dentista_para_paciente(12)

    assert resultado["status"] is True
    assert resultado["code"] == 200
    data = resultado["data"]
    assert data["metodo_calculo"] == "cep_fallback"
    assert data["distancia_km"] is None
    assert data["criterio_fallback"] == "mesma_cidade"
    assert data["diagnostico_calculo"]["fallback_utilizado"] is True
    print("  sugestao_fallback_mesma_cidade: OK")


def test_sugestao_caminho_feliz():
    from src.modulos.associacao import sugerir_dentista_para_paciente
    mock_conn = _make_mock_conexao(_PAC_ROW, [_DENT_ROW])

    geo_ok_pac = {"sucesso": True, "latitude": -23.561684, "longitude": -46.655981, "motivo_falha": None}
    geo_ok_dent = {"sucesso": True, "latitude": -23.563000, "longitude": -46.657000, "motivo_falha": None}

    with patch("src.modulos.associacao.obter_conexao", return_value=mock_conn), \
         patch("src.modulos.associacao.geocodificar_endereco", side_effect=[geo_ok_pac, geo_ok_dent]), \
         patch("src.modulos.associacao.time.sleep"):
        resultado = sugerir_dentista_para_paciente(12)

    assert resultado["status"] is True
    assert resultado["code"] == 200
    data = resultado["data"]
    assert data["metodo_calculo"] == "nominatim_haversine"
    assert isinstance(data["distancia_km"], float)
    assert data["distancia_km"] >= 0
    assert data["criterio_fallback"] is None
    assert data["diagnostico_calculo"]["fallback_utilizado"] is False
    print(f"  sugestao_caminho_feliz: distancia={data['distancia_km']} km — OK")


if __name__ == "__main__":
    print("=== Testes: associacao ===")
    test_distancia_cep_mesmos_ceps()
    test_distancia_cep_proximos()
    test_distancia_cep_diferentes_estados()
    test_distancia_cep_invalido()
    test_pre_filtrar_mesma_cidade()
    test_pre_filtrar_mesma_uf()
    test_pre_filtrar_cep_aproximado()
    test_pre_filtrar_limite_cinco()
    test_sugestao_sem_dentista_com_vaga()
    test_sugestao_fallback_mesma_cidade()
    test_sugestao_caminho_feliz()
    print("\nTodos os testes passaram.")
