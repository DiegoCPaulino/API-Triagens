import oracledb
from src.banco.database import obter_conexao
from src.apoio.utils import gerar_resposta
from src.apoio.validators import validar_status, validar_prioridade, validar_id_numerico


def _row_para_dict(row, colunas) -> dict:
    resultado = {}
    for i, col in enumerate(colunas):
        valor = row[i]
        if hasattr(valor, "strftime"):
            valor = valor.strftime("%Y-%m-%d %H:%M:%S")
        resultado[col.lower()] = valor
    return resultado


def consultar_triagens_por_status(status: str) -> dict:
    resultado_val = validar_status(status)
    if not resultado_val["status"]:
        return resultado_val

    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")
    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute(
                    "SELECT * FROM TB_TRIAGEM WHERE STATUS = :status ORDER BY DATA_CRIACAO DESC",
                    {"status": status.strip().lower()}
                )
                colunas = [d[0] for d in cur.description]
                dados = [_row_para_dict(row, colunas) for row in cur.fetchall()]
        return gerar_resposta(True, 200, f"Triagens com status '{status}' listadas.", dados)
    except oracledb.DatabaseError as exc:
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")


def consultar_triagens_por_prioridade(prioridade: str) -> dict:
    resultado_val = validar_prioridade(prioridade)
    if not resultado_val["status"]:
        return resultado_val

    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")
    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute(
                    "SELECT * FROM TB_TRIAGEM WHERE PRIORIDADE = :prioridade ORDER BY DATA_CRIACAO DESC",
                    {"prioridade": prioridade.strip().lower()}
                )
                colunas = [d[0] for d in cur.description]
                dados = [_row_para_dict(row, colunas) for row in cur.fetchall()]
        return gerar_resposta(True, 200, f"Triagens com prioridade '{prioridade}' listadas.", dados)
    except oracledb.DatabaseError as exc:
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")


def consultar_pacientes_sem_dentista() -> dict:
    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")
    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute(
                    """
                    SELECT ID_PACIENTE, NOME_COMPLETO, CPF, CIDADE, UF, TELEFONE, DATA_CADASTRO
                    FROM TB_PACIENTE
                    WHERE ID_DENTISTA IS NULL
                    ORDER BY DATA_CADASTRO DESC
                    """
                )
                colunas = [d[0] for d in cur.description]
                dados = [_row_para_dict(row, colunas) for row in cur.fetchall()]
        return gerar_resposta(True, 200, "Pacientes sem dentista listados.", dados)
    except oracledb.DatabaseError as exc:
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")


def consultar_pacientes_por_dentista(id_dentista) -> dict:
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
                    "SELECT NOME FROM TB_DENTISTA WHERE ID_DENTISTA = :id",
                    {"id": resultado_id["data"]}
                )
                row_d = cur.fetchone()
                if row_d is None:
                    return gerar_resposta(False, 404, "Dentista não encontrado.")
                nome_dentista = row_d[0]

                cur.execute(
                    """
                    SELECT P.ID_PACIENTE, P.NOME_COMPLETO, P.CPF, P.CIDADE, P.UF,
                           P.TELEFONE, P.DATA_CADASTRO
                    FROM TB_PACIENTE P
                    WHERE P.ID_DENTISTA = :id
                    ORDER BY P.NOME_COMPLETO
                    """,
                    {"id": resultado_id["data"]}
                )
                colunas = [d[0] for d in cur.description]
                dados = [_row_para_dict(row, colunas) for row in cur.fetchall()]
        return gerar_resposta(True, 200, f"Pacientes do dentista '{nome_dentista}' listados.", dados)
    except oracledb.DatabaseError as exc:
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")


def consultar_dentistas_com_vagas() -> dict:
    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")
    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute(
                    """
                    SELECT ID_DENTISTA, NOME, CRO, ESPECIALIDADE, CIDADE, UF, VAGAS_DISPONIVEIS
                    FROM TB_DENTISTA
                    WHERE VAGAS_DISPONIVEIS > 0
                    ORDER BY VAGAS_DISPONIVEIS DESC, NOME
                    """
                )
                colunas = [d[0] for d in cur.description]
                dados = [_row_para_dict(row, colunas) for row in cur.fetchall()]
        return gerar_resposta(True, 200, "Dentistas com vagas disponíveis listados.", dados)
    except oracledb.DatabaseError as exc:
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")
