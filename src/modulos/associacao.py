import time
import oracledb
from src.banco.database import obter_conexao
from src.apoio.utils import gerar_resposta
from src.apoio.validators import validar_id_numerico
from src.servicos.geocodificacao import (
    montar_endereco_textual,
    geocodificar_endereco,
    calcular_distancia_km,
)

_MAX_CANDIDATOS = 5


def _distancia_cep(cep_a, cep_b) -> int:
    try:
        return abs(int(cep_a) - int(cep_b))
    except (ValueError, TypeError):
        return 999_999_999


def _pre_filtrar(dentistas, cidade_pac, uf_pac, cep_pac):
    """Retorna (pool, criterio_fallback) com no máximo _MAX_CANDIDATOS dentistas."""
    mesma_cidade = [
        d for d in dentistas
        if (d["cidade"] or "").strip().lower() == cidade_pac
        and (d["uf"] or "").strip().upper() == uf_pac
    ]
    if mesma_cidade:
        pool = sorted(mesma_cidade, key=lambda d: _distancia_cep(cep_pac, d["cep"]))
        return pool[:_MAX_CANDIDATOS], "mesma_cidade"

    mesma_uf = [d for d in dentistas if (d["uf"] or "").strip().upper() == uf_pac]
    if mesma_uf:
        pool = sorted(mesma_uf, key=lambda d: _distancia_cep(cep_pac, d["cep"]))
        return pool[:_MAX_CANDIDATOS], "mesma_uf"

    por_cep = sorted(dentistas, key=lambda d: _distancia_cep(cep_pac, d["cep"]))
    if por_cep:
        return por_cep[:_MAX_CANDIDATOS], "cep_aproximado"

    return dentistas[:_MAX_CANDIDATOS], "qualquer_com_vaga"


def sugerir_dentista_para_paciente(id_paciente) -> dict:
    resultado_id = validar_id_numerico(id_paciente)
    if not resultado_id["status"]:
        return resultado_id

    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")

    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        PAC.ID_PACIENTE,
                        P.NOME_COMPLETO,
                        E.LOGRADOURO,
                        E.NUMERO,
                        E.BAIRRO,
                        E.CIDADE,
                        E.UF,
                        E.CEP
                    FROM TB_PACIENTE PAC
                    JOIN TB_PESSOA P
                        ON P.ID_PESSOA = PAC.ID_PESSOA
                    JOIN TB_ENDERECO E
                        ON E.ID_ENDERECO = P.ID_ENDERECO
                    WHERE PAC.ID_PACIENTE = :id
                    """,
                    {"id": resultado_id["data"]}
                )
                row_pac = cur.fetchone()
                if row_pac is None:
                    return gerar_resposta(False, 404, "Paciente não encontrado.")

                paciente = {
                    "id_paciente": row_pac[0],
                    "nome": row_pac[1] or "",
                    "logradouro": row_pac[2] or "",
                    "numero": row_pac[3] or "",
                    "bairro": row_pac[4] or "",
                    "cidade": (row_pac[5] or "").strip(),
                    "uf": (row_pac[6] or "").strip().upper(),
                    "cep": row_pac[7] or "",
                }

                cur.execute(
                    """
                    SELECT
                        D.ID_DENTISTA,
                        D.NOME,
                        '' AS ESPECIALIDADE,
                        E.CEP,
                        E.LOGRADOURO,
                        E.NUMERO,
                        E.BAIRRO,
                        E.CIDADE,
                        E.UF,
                        (D.CAP_MENSAL - D.ATIVOS) AS VAGAS_DISPONIVEIS
                    FROM TB_DENTISTA D
                    JOIN TB_ENDERECO E
                        ON E.ID_ENDERECO = D.ID_ENDERECO
                    WHERE UPPER(D.STTS_DENT) = 'ATIVO'
                        AND D.ATIVOS < D.CAP_MENSAL
                    ORDER BY D.ID_DENTISTA
                    """
                    )
                rows_dent = cur.fetchall()

    except oracledb.DatabaseError as exc:
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")

    if not rows_dent:
        data = {
            "paciente": {
                "id_paciente": paciente["id_paciente"],
                "nome": paciente["nome"],
                "cidade": paciente["cidade"],
                "uf": paciente["uf"],
                "cep": paciente["cep"],
            },
            "dentista_sugerido": None,
            "distancia_km": None,
            "metodo_calculo": "sem_dentista_disponivel",
            "criterio_fallback": None,
            "observacao": "Nenhum dentista com vagas disponíveis foi encontrado.",
            "diagnostico_calculo": {"fallback_utilizado": False, "motivo_fallback": None},
        }
        return gerar_resposta(False, 404, "Nenhum dentista com vagas disponíveis encontrado.", data)

    dentistas = [
        {
            "id_dentista": r[0], "nome": r[1], "especialidade": r[2] or "",
            "cep": r[3] or "", "logradouro": r[4] or "", "numero": r[5] or "",
            "bairro": r[6] or "", "cidade": (r[7] or "").strip(),
            "uf": (r[8] or "").strip().upper(), "vagas_disponiveis": r[9],
        }
        for r in rows_dent
    ]

    cidade_pac = paciente["cidade"].lower()
    uf_pac = paciente["uf"]
    cep_pac = paciente["cep"]

    candidatos, criterio = _pre_filtrar(dentistas, cidade_pac, uf_pac, cep_pac)

    # --- Tentativa de geocodificação ---
    end_pac = montar_endereco_textual(
        paciente["logradouro"], paciente["numero"], paciente["bairro"],
        paciente["cidade"], paciente["uf"], paciente["cep"]
    )
    geo_pac = geocodificar_endereco(end_pac)

    geocodificados = []
    if geo_pac["sucesso"]:
        for cand in candidatos:
            end_cand = montar_endereco_textual(
                cand["logradouro"], cand["numero"], cand["bairro"],
                cand["cidade"], cand["uf"], cand["cep"]
            )
            geo_cand = geocodificar_endereco(end_cand)
            if geo_cand["sucesso"]:
                try:
                    dist = calcular_distancia_km(
                        geo_pac["latitude"], geo_pac["longitude"],
                        geo_cand["latitude"], geo_cand["longitude"]
                    )
                    geocodificados.append((cand, dist))
                except ValueError:
                    pass
            time.sleep(1)

    if geocodificados:
        melhor_cand, melhor_dist = min(geocodificados, key=lambda x: x[1])
        dentista_out = {
            "id_dentista": melhor_cand["id_dentista"],
            "nome": melhor_cand["nome"],
            "especialidade": melhor_cand["especialidade"],
            "cidade": melhor_cand["cidade"],
            "uf": melhor_cand["uf"],
            "cep": melhor_cand["cep"],
            "vagas_disponiveis": melhor_cand["vagas_disponiveis"],
        }
        data = {
            "paciente": {
                "id_paciente": paciente["id_paciente"],
                "nome": paciente["nome"],
                "cidade": paciente["cidade"],
                "uf": paciente["uf"],
                "cep": paciente["cep"],
            },
            "dentista_sugerido": dentista_out,
            "distancia_km": melhor_dist,
            "metodo_calculo": "nominatim_haversine",
            "criterio_fallback": None,
            "observacao": (
                "Distância aproximada em linha reta via OpenStreetMap/Nominatim. "
                "Não considera rota viária, trânsito ou tempo de deslocamento."
            ),
            "diagnostico_calculo": {
                "nominatim_utilizado": True,
                "haversine_utilizado": True,
                "fallback_utilizado": False,
                "paciente_geocodificado": True,
                "candidatos_geocodificados": len(geocodificados),
                "total_candidatos": len(candidatos),
                "motivo_fallback": None,
            },
        }
        return gerar_resposta(True, 200, "Dentista sugerido com sucesso.", data)

    # --- Fallback ---
    motivo = "paciente_nao_geocodificado" if not geo_pac["sucesso"] else "candidatos_nao_geocodificados"
    melhor_cand = candidatos[0]
    dentista_out = {
        "id_dentista": melhor_cand["id_dentista"],
        "nome": melhor_cand["nome"],
        "especialidade": melhor_cand["especialidade"],
        "cidade": melhor_cand["cidade"],
        "uf": melhor_cand["uf"],
        "cep": melhor_cand["cep"],
        "vagas_disponiveis": melhor_cand["vagas_disponiveis"],
    }
    criterio_label = {
        "mesma_cidade": "cidade, UF e aproximação de CEP",
        "mesma_uf": "UF e aproximação de CEP",
        "cep_aproximado": "aproximação de CEP",
        "qualquer_com_vaga": "disponibilidade de vaga",
    }.get(criterio, criterio)

    data = {
        "paciente": {
            "id_paciente": paciente["id_paciente"],
            "nome": paciente["nome"],
            "cidade": paciente["cidade"],
            "uf": paciente["uf"],
            "cep": paciente["cep"],
        },
        "dentista_sugerido": dentista_out,
        "distancia_km": None,
        "metodo_calculo": "cep_fallback",
        "criterio_fallback": criterio,
        "observacao": (
            f"Geocodificação indisponível; sugestão feita por {criterio_label}. "
            "Distância real não calculada."
        ),
        "diagnostico_calculo": {
            "nominatim_utilizado": geo_pac["sucesso"],
            "haversine_utilizado": False,
            "fallback_utilizado": True,
            "paciente_geocodificado": geo_pac["sucesso"],
            "candidatos_geocodificados": 0,
            "total_candidatos": len(candidatos),
            "motivo_fallback": motivo,
        },
    }
    return gerar_resposta(True, 200, "Dentista sugerido por fallback de proximidade.", data)
