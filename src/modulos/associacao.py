import oracledb
from src.banco.database import obter_conexao
from src.apoio.utils import gerar_resposta
from src.apoio.validators import validar_id_numerico

# A distancia entre CEPs e uma aproximacao academica simples (diferenca numerica).
# Nao representa distancia geografica real.


def _distancia_cep(cep_a, cep_b) -> int:
    try:
        return abs(int(cep_a) - int(cep_b))
    except (ValueError, TypeError):
        return 999999999


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
                    "SELECT CEP, CIDADE, UF FROM TB_PACIENTE WHERE ID_PACIENTE = :id",
                    {"id": resultado_id["data"]}
                )
                row_paciente = cur.fetchone()
                if row_paciente is None:
                    return gerar_resposta(False, 404, "Paciente não encontrado.")

                cep_paciente = row_paciente[0] or ""
                cidade_paciente = (row_paciente[1] or "").strip().lower()
                uf_paciente = (row_paciente[2] or "").strip().upper()

                cur.execute(
                    """
                    SELECT ID_DENTISTA, NOME, CEP, CIDADE, UF, VAGAS_DISPONIVEIS
                    FROM TB_DENTISTA
                    WHERE VAGAS_DISPONIVEIS > 0
                    ORDER BY ID_DENTISTA
                    """
                )
                dentistas = cur.fetchall()

        if not dentistas:
            return gerar_resposta(False, 404, "Nenhum dentista com vagas disponíveis encontrado.")

        # Prioridade: mesma cidade → mesma UF → qualquer um com vaga
        candidatos_cidade = [d for d in dentistas if (d[3] or "").strip().lower() == cidade_paciente]
        candidatos_uf = [d for d in dentistas if (d[4] or "").strip().upper() == uf_paciente]

        if candidatos_cidade:
            pool = candidatos_cidade
        elif candidatos_uf:
            pool = candidatos_uf
        else:
            pool = list(dentistas)

        # Desempate por menor diferenca de CEP
        melhor = min(pool, key=lambda d: (_distancia_cep(cep_paciente, d[2]), d[0]))

        sugestao = {
            "id_dentista": melhor[0],
            "nome": melhor[1],
            "cep": melhor[2],
            "cidade": melhor[3],
            "uf": melhor[4],
            "vagas_disponiveis": melhor[5],
        }
        return gerar_resposta(True, 200, "Dentista sugerido com sucesso.", sugestao)

    except oracledb.DatabaseError as exc:
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")
