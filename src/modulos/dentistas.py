import oracledb
from src.banco.database import obter_conexao
from src.apoio.utils import gerar_resposta
from src.apoio.validators import validar_id_numerico


def _row_para_dict(row, colunas) -> dict:
    resultado = {}
    for i, col in enumerate(colunas):
        valor = row[i]
        if hasattr(valor, "strftime"):
            valor = valor.strftime("%Y-%m-%d %H:%M:%S")
        resultado[col.lower()] = valor
    return resultado


def listar_dentistas() -> dict:
    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")
    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute("SELECT * FROM TB_DENTISTA ORDER BY NOME")
                colunas = [d[0] for d in cur.description]
                dentistas = [_row_para_dict(row, colunas) for row in cur.fetchall()]
        return gerar_resposta(True, 200, "Dentistas listados com sucesso.", dentistas)
    except oracledb.DatabaseError as exc:
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")


def buscar_dentista_por_id(id_dentista) -> dict:
    resultado_id = validar_id_numerico(id_dentista)
    if not resultado_id["status"]:
        return resultado_id

    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")
    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute(
                    "SELECT * FROM TB_DENTISTA WHERE ID_DENTISTA = :id",
                    {"id": resultado_id["data"]}
                )
                colunas = [d[0] for d in cur.description]
                row = cur.fetchone()
        if row is None:
            return gerar_resposta(False, 404, "Dentista não encontrado.")
        return gerar_resposta(True, 200, "Dentista encontrado.", _row_para_dict(row, colunas))
    except oracledb.DatabaseError as exc:
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")


def listar_pacientes_de_um_dentista(id_dentista) -> dict:
    resultado_id = validar_id_numerico(id_dentista)
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
                    SELECT P.ID_PACIENTE, P.NOME_COMPLETO, P.CPF, P.CIDADE, P.UF, P.TELEFONE
                    FROM TB_PACIENTE P
                    WHERE P.ID_DENTISTA = :id
                    ORDER BY P.NOME_COMPLETO
                    """,
                    {"id": resultado_id["data"]}
                )
                colunas = [d[0] for d in cur.description]
                pacientes = [_row_para_dict(row, colunas) for row in cur.fetchall()]
        return gerar_resposta(True, 200, "Pacientes do dentista listados.", pacientes)
    except oracledb.DatabaseError as exc:
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")


def listar_dentistas_com_vagas() -> dict:
    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")
    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute(
                    "SELECT * FROM TB_DENTISTA WHERE VAGAS_DISPONIVEIS > 0 ORDER BY VAGAS_DISPONIVEIS DESC"
                )
                colunas = [d[0] for d in cur.description]
                dentistas = [_row_para_dict(row, colunas) for row in cur.fetchall()]
        return gerar_resposta(True, 200, "Dentistas com vagas listados.", dentistas)
    except oracledb.DatabaseError as exc:
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")
