import oracledb
from src.banco.database import obter_conexao
from src.apoio.utils import gerar_resposta, normalizar_texto
from src.apoio.validators import validar_id_numerico, validar_dados_complementares_paciente


def _row_para_dict(row, colunas) -> dict:
    resultado = {}
    for i, col in enumerate(colunas):
        valor = row[i]
        if hasattr(valor, "strftime"):
            valor = valor.strftime("%Y-%m-%d %H:%M:%S")
        resultado[col.lower()] = valor
    return resultado


def criar_paciente_a_partir_de_triagem(id_triagem, dados_complementares: dict) -> dict:
    from src.modulos.triagens import buscar_triagem_por_id
    resultado_id = validar_id_numerico(id_triagem)
    if not resultado_id["status"]:
        return resultado_id

    resultado_val = validar_dados_complementares_paciente(dados_complementares)
    if not resultado_val["status"]:
        return resultado_val

    resultado_triagem = buscar_triagem_por_id(id_triagem)
    if not resultado_triagem["status"]:
        return resultado_triagem

    triagem = resultado_triagem["data"]
    if triagem["status"] != "aprovada":
        return gerar_resposta(False, 409, "Paciente só pode ser criado a partir de triagem com status 'aprovada'.")

    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")
    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM TB_PACIENTE WHERE ID_TRIAGEM = :id",
                    {"id": resultado_id["data"]}
                )
                if cur.fetchone()[0] > 0:
                    return gerar_resposta(False, 409, "Já existe um paciente vinculado a esta triagem.")

                cur.execute(
                    """
                    INSERT INTO TB_PACIENTE
                        (ID_TRIAGEM, NOME_COMPLETO, CPF, IDADE,
                         DATA_NASCIMENTO, RG, TELEFONE,
                         CEP, LOGRADOURO, NUMERO, COMPLEMENTO, BAIRRO, CIDADE, UF)
                    VALUES
                        (:id_triagem, :nome, :cpf, :idade,
                         :data_nasc, :rg, :telefone,
                         :cep, :logradouro, :numero, :complemento, :bairro, :cidade, :uf)
                    RETURNING ID_PACIENTE INTO :id_out
                    """,
                    {
                        "id_triagem": resultado_id["data"],
                        "nome": normalizar_texto(triagem["nome_completo"]),
                        "cpf": triagem["cpf"],
                        "idade": triagem["idade"],
                        "data_nasc": dados_complementares.get("data_nascimento", ""),
                        "rg": dados_complementares.get("rg", ""),
                        "telefone": dados_complementares.get("telefone", ""),
                        "cep": dados_complementares.get("cep", ""),
                        "logradouro": dados_complementares.get("logradouro", ""),
                        "numero": dados_complementares.get("numero", ""),
                        "complemento": dados_complementares.get("complemento", ""),
                        "bairro": dados_complementares.get("bairro", ""),
                        "cidade": dados_complementares.get("cidade", ""),
                        "uf": dados_complementares.get("uf", ""),
                        "id_out": cur.var(oracledb.NUMBER),
                    }
                )
                id_gerado = int(cur.bindvars["id_out"].getvalue()[0])
                conexao.commit()
        resultado = buscar_paciente_por_id(id_gerado)
        if resultado["status"]:
            resultado["code"] = 201
        return resultado
    except oracledb.DatabaseError as exc:
        try:
            conexao.rollback()
        except Exception:
            pass
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")


def listar_pacientes() -> dict:
    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")
    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute(
                    """
                    SELECT P.*, D.NOME AS NOME_DENTISTA
                    FROM TB_PACIENTE P
                    LEFT JOIN TB_DENTISTA D ON P.ID_DENTISTA = D.ID_DENTISTA
                    ORDER BY P.DATA_CADASTRO DESC
                    """
                )
                colunas = [d[0] for d in cur.description]
                pacientes = [_row_para_dict(row, colunas) for row in cur.fetchall()]
        return gerar_resposta(True, 200, "Pacientes listados com sucesso.", pacientes)
    except oracledb.DatabaseError as exc:
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")


def buscar_paciente_por_id(id_paciente) -> dict:
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
                    SELECT P.*, D.NOME AS NOME_DENTISTA
                    FROM TB_PACIENTE P
                    LEFT JOIN TB_DENTISTA D ON P.ID_DENTISTA = D.ID_DENTISTA
                    WHERE P.ID_PACIENTE = :id
                    """,
                    {"id": resultado_id["data"]}
                )
                colunas = [d[0] for d in cur.description]
                row = cur.fetchone()
        if row is None:
            return gerar_resposta(False, 404, "Paciente não encontrado.")
        return gerar_resposta(True, 200, "Paciente encontrado.", _row_para_dict(row, colunas))
    except oracledb.DatabaseError as exc:
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")


def listar_pacientes_com_dentista() -> dict:
    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")
    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute(
                    """
                    SELECT P.*, D.NOME AS NOME_DENTISTA
                    FROM TB_PACIENTE P
                    JOIN TB_DENTISTA D ON P.ID_DENTISTA = D.ID_DENTISTA
                    ORDER BY P.DATA_CADASTRO DESC
                    """
                )
                colunas = [d[0] for d in cur.description]
                pacientes = [_row_para_dict(row, colunas) for row in cur.fetchall()]
        return gerar_resposta(True, 200, "Pacientes com dentista listados.", pacientes)
    except oracledb.DatabaseError as exc:
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")


def listar_pacientes_sem_dentista() -> dict:
    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")
    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM TB_PACIENTE
                    WHERE ID_DENTISTA IS NULL
                    ORDER BY DATA_CADASTRO DESC
                    """
                )
                colunas = [d[0] for d in cur.description]
                pacientes = [_row_para_dict(row, colunas) for row in cur.fetchall()]
        return gerar_resposta(True, 200, "Pacientes sem dentista listados.", pacientes)
    except oracledb.DatabaseError as exc:
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")


def vincular_dentista_ao_paciente(id_paciente, id_dentista) -> dict:
    resultado_id_p = validar_id_numerico(id_paciente)
    resultado_id_d = validar_id_numerico(id_dentista)
    if not resultado_id_p["status"]:
        return resultado_id_p
    if not resultado_id_d["status"]:
        return resultado_id_d

    id_p = resultado_id_p["data"]
    id_d = resultado_id_d["data"]

    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")
    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute(
                    "SELECT ID_DENTISTA FROM TB_PACIENTE WHERE ID_PACIENTE = :id",
                    {"id": id_p}
                )
                row_p = cur.fetchone()
                if row_p is None:
                    return gerar_resposta(False, 404, "Paciente não encontrado.")
                id_dentista_atual = row_p[0]

                if id_dentista_atual == id_d:
                    return gerar_resposta(True, 200, "Paciente já está vinculado a este dentista. Nenhuma alteração realizada.")

                cur.execute(
                    "SELECT VAGAS_DISPONIVEIS FROM TB_DENTISTA WHERE ID_DENTISTA = :id",
                    {"id": id_d}
                )
                row_d = cur.fetchone()
                if row_d is None:
                    return gerar_resposta(False, 404, "Dentista não encontrado.")
                if row_d[0] <= 0:
                    return gerar_resposta(False, 409, "Dentista não possui vagas disponíveis.")

                cur.execute(
                    "UPDATE TB_PACIENTE SET ID_DENTISTA = :id_d WHERE ID_PACIENTE = :id_p",
                    {"id_d": id_d, "id_p": id_p}
                )

                if id_dentista_atual is not None:
                    cur.execute(
                        "UPDATE TB_DENTISTA SET VAGAS_DISPONIVEIS = VAGAS_DISPONIVEIS + 1 WHERE ID_DENTISTA = :id",
                        {"id": id_dentista_atual}
                    )

                cur.execute(
                    "UPDATE TB_DENTISTA SET VAGAS_DISPONIVEIS = VAGAS_DISPONIVEIS - 1 WHERE ID_DENTISTA = :id",
                    {"id": id_d}
                )

                conexao.commit()

        if id_dentista_atual is None:
            return gerar_resposta(True, 200, "Dentista vinculado ao paciente com sucesso.")
        return gerar_resposta(True, 200, "Paciente reassociado com sucesso. Dentista anterior recebeu +1 vaga; novo dentista recebeu -1 vaga.")
    except oracledb.DatabaseError as exc:
        try:
            conexao.rollback()
        except Exception:
            pass
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")
