import re
from datetime import datetime
from src.apoio.utils import gerar_resposta, normalizar_texto

PRIORIDADES_VALIDAS = ("baixa", "média", "alta")
STATUS_VALIDOS = ("em análise", "aprovada", "reprovada")


def _resposta_erro_validacao(message: str, erros: list) -> dict:
    return gerar_resposta(False, 400, message, error=erros)


def validar_nome(nome) -> dict:
    if nome is None:
        return gerar_resposta(False, 400, "Nome é obrigatório.")
    if not isinstance(nome, str):
        return gerar_resposta(False, 400, "Nome deve ser um texto.")
    nome = normalizar_texto(nome)
    if not nome:
        return gerar_resposta(False, 400, "Nome é obrigatório.")
    regex = r"^[A-Za-zÀ-ÖØ-öø-ÿ]+(?:[ '-][A-Za-zÀ-ÖØ-öø-ÿ]+)+$"
    if not re.fullmatch(regex, nome):
        return gerar_resposta(False, 400, "Informe o nome completo (mínimo nome e sobrenome).")
    return gerar_resposta(True, 200, "Nome válido.")


def validar_cpf(cpf) -> dict:
    if cpf is None:
        return gerar_resposta(False, 400, "CPF é obrigatório.")
    cpf = re.sub(r"\D", "", str(cpf))
    if len(cpf) != 11:
        return gerar_resposta(False, 400, "CPF deve ter 11 dígitos numéricos.")
    return gerar_resposta(True, 200, "CPF válido.", cpf)


def validar_idade(idade) -> dict:
    if idade is None:
        return gerar_resposta(False, 400, "Idade é obrigatória.")
    if isinstance(idade, bool):
        return gerar_resposta(False, 400, "Idade deve ser um número inteiro.")
    if isinstance(idade, str):
        idade = normalizar_texto(idade)
        if not idade:
            return gerar_resposta(False, 400, "Idade é obrigatória.")
        if not idade.isdigit():
            return gerar_resposta(False, 400, "Idade deve ser um número inteiro.")
        idade = int(idade)
    elif not isinstance(idade, int):
        return gerar_resposta(False, 400, "Idade deve ser um número inteiro.")
    if idade < 11 or idade > 17:
        return gerar_resposta(False, 400, "A idade deve estar entre 11 e 17 anos. O Projeto Nora atende apenas adolescentes nessa faixa.")
    return gerar_resposta(True, 200, "Idade válida.")


def validar_descricao_caso(descricao) -> dict:
    if descricao is None:
        return gerar_resposta(False, 400, "Descrição do caso é obrigatória.")
    if not isinstance(descricao, str):
        return gerar_resposta(False, 400, "Descrição do caso deve ser um texto.")
    descricao = normalizar_texto(descricao)
    if not descricao:
        return gerar_resposta(False, 400, "Descrição do caso é obrigatória.")
    if len(descricao) < 10 or len(descricao) > 300:
        return gerar_resposta(False, 400, "Descrição do caso deve ter entre 10 e 300 caracteres.")
    return gerar_resposta(True, 200, "Descrição do caso válida.")


def validar_prioridade(prioridade) -> dict:
    if prioridade is None:
        return gerar_resposta(False, 400, "Prioridade é obrigatória.")
    if not isinstance(prioridade, str):
        return gerar_resposta(False, 400, "Prioridade deve ser um texto.")
    prioridade = normalizar_texto(prioridade).lower()
    if not prioridade:
        return gerar_resposta(False, 400, "Prioridade é obrigatória.")
    if prioridade not in PRIORIDADES_VALIDAS:
        return gerar_resposta(False, 400, "Prioridade inválida. Use: baixa, média ou alta.")
    return gerar_resposta(True, 200, "Prioridade válida.")


def validar_status(status) -> dict:
    if status is None:
        return gerar_resposta(False, 400, "Status é obrigatório.")
    if not isinstance(status, str):
        return gerar_resposta(False, 400, "Status deve ser um texto.")
    status = normalizar_texto(status).lower()
    if not status:
        return gerar_resposta(False, 400, "Status é obrigatório.")
    if status not in STATUS_VALIDOS:
        return gerar_resposta(False, 400, "Status inválido. Use: em análise, aprovada ou reprovada.")
    return gerar_resposta(True, 200, "Status válido.")


def validar_observacoes(observacoes) -> dict:
    if observacoes is None:
        return gerar_resposta(True, 200, "Observações válidas.")
    if not isinstance(observacoes, str):
        return gerar_resposta(False, 400, "Observações devem ser um texto.")
    observacoes = normalizar_texto(observacoes)
    if len(observacoes) > 300:
        return gerar_resposta(False, 400, "Observações devem ter no máximo 300 caracteres.")
    return gerar_resposta(True, 200, "Observações válidas.")


def validar_cep(cep) -> dict:
    if cep is None:
        return gerar_resposta(False, 400, "CEP é obrigatório.")
    cep = re.sub(r"\D", "", str(cep))
    if len(cep) != 8:
        return gerar_resposta(False, 400, "CEP deve ter 8 dígitos numéricos.")
    return gerar_resposta(True, 200, "CEP válido.", cep)


def validar_telefone(telefone) -> dict:
    if telefone is None:
        return gerar_resposta(False, 400, "Telefone é obrigatório.")
    telefone = re.sub(r"\D", "", str(telefone))
    if len(telefone) not in (10, 11):
        return gerar_resposta(False, 400, "Telefone deve ter 10 ou 11 dígitos numéricos.")
    return gerar_resposta(True, 200, "Telefone válido.", telefone)


def validar_rg(rg) -> dict:
    if rg is None:
        return gerar_resposta(False, 400, "RG é obrigatório.")
    rg = normalizar_texto(str(rg))
    rg_limpo = re.sub(r"[^A-Za-z0-9]", "", rg)
    if len(rg_limpo) < 5 or len(rg_limpo) > 14:
        return gerar_resposta(False, 400, "RG deve ter entre 5 e 14 caracteres alfanuméricos.")
    return gerar_resposta(True, 200, "RG válido.")


def validar_data_nascimento(data) -> dict:
    if data is None:
        return gerar_resposta(False, 400, "Data de nascimento é obrigatória.")
    data = normalizar_texto(str(data))
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
        return gerar_resposta(False, 400, "Data de nascimento deve estar no formato DD/MM/AAAA.")
    try:
        nascimento = datetime.strptime(data, "%d/%m/%Y")
        hoje = datetime.now()
        if nascimento > hoje:
            return gerar_resposta(False, 400, "Data de nascimento não pode ser uma data futura.")
        idade = hoje.year - nascimento.year
        if (hoje.month, hoje.day) < (nascimento.month, nascimento.day):
            idade -= 1
        if idade < 11 or idade > 17:
            return gerar_resposta(
                False, 400,
                f"Data de nascimento gera idade fora da faixa atendida (11 a 17 anos). "
                f"O Projeto Nora atende apenas adolescentes. Por favor, verifique a data informada."
            )
    except ValueError:
        return gerar_resposta(False, 400, "Data de nascimento inválida. Verifique o dia, mês e ano informados.")
    return gerar_resposta(True, 200, "Data de nascimento válida.")


def validar_uf(uf) -> dict:
    if uf is None:
        return gerar_resposta(False, 400, "UF é obrigatória.")
    uf = normalizar_texto(str(uf)).upper()
    if not re.fullmatch(r"[A-Z]{2}", uf):
        return gerar_resposta(False, 400, "UF deve ter 2 letras (ex: SP, RJ).")
    return gerar_resposta(True, 200, "UF válida.")


def validar_numero_endereco(numero) -> dict:
    if numero is None or normalizar_texto(str(numero)) == "":
        return gerar_resposta(False, 400, "Número do endereço é obrigatório.")
    return gerar_resposta(True, 200, "Número válido.")


def validar_id_numerico(valor) -> dict:
    try:
        id_int = int(str(valor).strip())
        if id_int <= 0:
            return gerar_resposta(False, 400, "ID deve ser um número positivo.")
        return gerar_resposta(True, 200, "ID válido.", id_int)
    except (ValueError, TypeError):
        return gerar_resposta(False, 400, "ID deve ser um número inteiro positivo.")


def validar_dados_triagem(dados: dict) -> dict:
    if not isinstance(dados, dict):
        return gerar_resposta(False, 400, "Dados da triagem são inválidos.")
    erros = []
    validacoes = {
        "nome_completo": validar_nome(dados.get("nome_completo")),
        "cpf": validar_cpf(dados.get("cpf")),
        "idade": validar_idade(dados.get("idade")),
        "descricao_caso": validar_descricao_caso(dados.get("descricao_caso")),
        "prioridade": validar_prioridade(dados.get("prioridade")),
        "observacoes": validar_observacoes(dados.get("observacoes")),
    }
    for campo, resultado in validacoes.items():
        if not resultado["status"]:
            erros.append({"campo": campo, "erro": resultado["message"]})
    if erros:
        return _resposta_erro_validacao("Existem erros de validação nos dados da triagem.", erros)
    return gerar_resposta(True, 200, "Dados da triagem válidos.")


def validar_dados_atualizacao(dados: dict) -> dict:
    if not isinstance(dados, dict):
        return gerar_resposta(False, 400, "Dados de atualização são inválidos.")
    campos_permitidos = {
        "nome_completo": validar_nome,
        "idade": validar_idade,
        "descricao_caso": validar_descricao_caso,
        "prioridade": validar_prioridade,
        "observacoes": validar_observacoes,
    }
    dados_filtrados = {k: v for k, v in dados.items() if k in campos_permitidos}
    if not dados_filtrados:
        return gerar_resposta(False, 400, "Nenhum campo válido foi enviado para atualização.")
    erros = []
    for campo, valor in dados_filtrados.items():
        resultado = campos_permitidos[campo](valor)
        if not resultado["status"]:
            erros.append({"campo": campo, "erro": resultado["message"]})
    if erros:
        return _resposta_erro_validacao("Existem erros de validação nos dados de atualização.", erros)
    return gerar_resposta(True, 200, "Dados de atualização válidos.")
