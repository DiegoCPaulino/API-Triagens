import oracledb
from src.banco.database import obter_conexao
from src.apoio.utils import gerar_resposta, normalizar_texto
from src.apoio.validators import validar_dados_triagem, validar_dados_atualizacao, validar_id_numerico

CAMPOS_EDITAVEIS = {"nome_completo", "idade", "descricao_caso", "prioridade", "observacoes"}


def _normalizar_dados(dados: dict) -> dict:
    normalizados = {}
    if "nome_completo" in dados:
        normalizados["nome_completo"] = normalizar_texto(dados["nome_completo"])
    if "cpf" in dados:
        import re
        normalizados["cpf"] = re.sub(r"\D", "", str(dados["cpf"]))
    if "idade" in dados:
        normalizados["idade"] = int(str(dados["idade"]).strip())
    if "descricao_caso" in dados:
        normalizados["descricao_caso"] = normalizar_texto(dados["descricao_caso"])
    if "prioridade" in dados:
        normalizados["prioridade"] = normalizar_texto(dados["prioridade"]).lower()
    if "observacoes" in dados:
        normalizados["observacoes"] = normalizar_texto(dados.get("observacoes") or "")
    return normalizados


def _row_para_dict(row, colunas) -> dict:
    resultado = {}
    for i, col in enumerate(colunas):
        valor = row[i]
        if hasattr(valor, "strftime"):
            valor = valor.strftime("%Y-%m-%d %H:%M:%S")
        resultado[col.lower()] = valor
    return resultado


def criar_triagem(dados: dict) -> dict:
    resultado_validacao = validar_dados_triagem(dados)
    if not resultado_validacao["status"]:
        return resultado_validacao

    normalizados = _normalizar_dados(dados)
    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")

    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO TB_TRIAGEM
                        (NOME_COMPLETO, CPF, IDADE, DESCRICAO_CASO, PRIORIDADE, OBSERVACOES)
                    VALUES
                        (:nome, :cpf, :idade, :descricao, :prioridade, :observacoes)
                    RETURNING ID_TRIAGEM INTO :id_out
                    """,
                    {
                        "nome": normalizados["nome_completo"],
                        "cpf": normalizados["cpf"],
                        "idade": normalizados["idade"],
                        "descricao": normalizados["descricao_caso"],
                        "prioridade": normalizados["prioridade"],
                        "observacoes": normalizados.get("observacoes", ""),
                        "id_out": cur.var(oracledb.NUMBER),
                    }
                )
                id_gerado = int(cur.bindvars["id_out"].getvalue()[0])
                conexao.commit()

        resultado = buscar_triagem_por_id(id_gerado)
        if resultado["status"]:
            resultado["code"] = 201
        return resultado

    except oracledb.DatabaseError as exc:
        (erro,) = exc.args
        if "ORA-00001" in str(erro):
            return gerar_resposta(False, 409, "Já existe uma triagem com este CPF.")
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")


def listar_triagens() -> dict:
    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")
    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute("SELECT * FROM TB_TRIAGEM ORDER BY DATA_CRIACAO DESC")
                colunas = [d[0] for d in cur.description]
                triagens = [_row_para_dict(row, colunas) for row in cur.fetchall()]
        return gerar_resposta(True, 200, "Triagens listadas com sucesso.", triagens)
    except oracledb.DatabaseError as exc:
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")


def buscar_triagem_por_id(id_triagem) -> dict:
    resultado_id = validar_id_numerico(id_triagem)
    if not resultado_id["status"]:
        return resultado_id

    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")
    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute(
                    "SELECT * FROM TB_TRIAGEM WHERE ID_TRIAGEM = :id",
                    {"id": resultado_id["data"]}
                )
                colunas = [d[0] for d in cur.description]
                row = cur.fetchone()
        if row is None:
            return gerar_resposta(False, 404, "Triagem não encontrada.")
        return gerar_resposta(True, 200, "Triagem encontrada.", _row_para_dict(row, colunas))
    except oracledb.DatabaseError as exc:
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")


def atualizar_triagem(id_triagem, dados: dict) -> dict:
    resultado_busca = buscar_triagem_por_id(id_triagem)
    if not resultado_busca["status"]:
        return resultado_busca

    triagem_atual = resultado_busca["data"]
    if triagem_atual["status"] != "em análise":
        return gerar_resposta(False, 409, "Só é possível atualizar triagens com status 'em análise'.")

    resultado_validacao = validar_dados_atualizacao(dados)
    if not resultado_validacao["status"]:
        return resultado_validacao

    normalizados = _normalizar_dados({k: v for k, v in dados.items() if k in CAMPOS_EDITAVEIS})
    if not normalizados:
        return gerar_resposta(False, 400, "Nenhum campo válido enviado para atualização.")

    partes_set = []
    parametros = {"id": int(str(id_triagem).strip())}
    mapa = {
        "nome_completo": "NOME_COMPLETO",
        "idade": "IDADE",
        "descricao_caso": "DESCRICAO_CASO",
        "prioridade": "PRIORIDADE",
        "observacoes": "OBSERVACOES",
    }
    for campo, coluna in mapa.items():
        if campo in normalizados:
            partes_set.append(f"{coluna} = :{campo}")
            parametros[campo] = normalizados[campo]

    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")
    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute(
                    f"UPDATE TB_TRIAGEM SET {', '.join(partes_set)} WHERE ID_TRIAGEM = :id",
                    parametros
                )
                conexao.commit()
        return buscar_triagem_por_id(id_triagem)
    except oracledb.DatabaseError as exc:
        try:
            conexao.rollback()
        except Exception:
            pass
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")


def aprovar_triagem(id_triagem) -> dict:
    resultado_busca = buscar_triagem_por_id(id_triagem)
    if not resultado_busca["status"]:
        return resultado_busca

    triagem = resultado_busca["data"]
    if triagem["status"] != "em análise":
        return gerar_resposta(False, 409, f"Triagem não pode ser aprovada pois está com status '{triagem['status']}'.")

    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")
    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute(
                    "UPDATE TB_TRIAGEM SET STATUS = 'aprovada' WHERE ID_TRIAGEM = :id",
                    {"id": int(str(id_triagem).strip())}
                )
                conexao.commit()
        return gerar_resposta(True, 200, "Triagem aprovada com sucesso. Prossiga para o cadastro do paciente.")
    except oracledb.DatabaseError as exc:
        try:
            conexao.rollback()
        except Exception:
            pass
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")


def reprovar_triagem(id_triagem) -> dict:
    resultado_busca = buscar_triagem_por_id(id_triagem)
    if not resultado_busca["status"]:
        return resultado_busca

    triagem = resultado_busca["data"]
    if triagem["status"] != "em análise":
        return gerar_resposta(False, 409, f"Triagem não pode ser reprovada pois está com status '{triagem['status']}'.")

    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")
    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute(
                    "UPDATE TB_TRIAGEM SET STATUS = 'reprovada' WHERE ID_TRIAGEM = :id",
                    {"id": int(str(id_triagem).strip())}
                )
                conexao.commit()
        return gerar_resposta(True, 200, "Triagem reprovada com sucesso.")
    except oracledb.DatabaseError as exc:
        try:
            conexao.rollback()
        except Exception:
            pass
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")


def excluir_triagem(id_triagem) -> dict:
    resultado_busca = buscar_triagem_por_id(id_triagem)
    if not resultado_busca["status"]:
        return resultado_busca

    id_int = int(str(id_triagem).strip())
    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")
    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM TB_PACIENTE WHERE ID_TRIAGEM = :id",
                    {"id": id_int}
                )
                total = cur.fetchone()[0]
                if total > 0:
                    return gerar_resposta(False, 409, "Não é possível excluir esta triagem pois já existe um paciente vinculado a ela.")

                cur.execute("DELETE FROM TB_TRIAGEM WHERE ID_TRIAGEM = :id", {"id": id_int})
                conexao.commit()
        return gerar_resposta(True, 200, "Triagem excluída com sucesso.")
    except oracledb.DatabaseError as exc:
        try:
            conexao.rollback()
        except Exception:
            pass
        return gerar_resposta(False, 500, f"Erro no banco: {exc}")


def reverter_para_em_analise(id_triagem) -> dict:
    resultado_id = validar_id_numerico(id_triagem)
    if not resultado_id["status"]:
        return resultado_id

    conexao = obter_conexao()
    if conexao is None:
        return gerar_resposta(False, 500, "Falha ao conectar ao banco.")
    try:
        with conexao:
            with conexao.cursor() as cur:
                cur.execute(
                    "UPDATE TB_TRIAGEM SET STATUS = 'em análise' WHERE ID_TRIAGEM = :id",
                    {"id": resultado_id["data"]}
                )
                conexao.commit()
        return gerar_resposta(True, 200, "Triagem revertida para 'em análise'.")
    except oracledb.DatabaseError as exc:
        try:
            conexao.rollback()
        except Exception:
            pass
        return gerar_resposta(False, 500, f"Erro ao reverter triagem: {exc}")
