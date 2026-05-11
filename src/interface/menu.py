import os
import re
from src.modulos import triagens as svc_triagem
from src.modulos import pacientes as svc_paciente
from src.modulos import dentistas as svc_dentista
from src.modulos import associacao as svc_associacao
from src.modulos import consultas as svc_consulta
from src.servicos import exportador_json as exportador
from src.servicos.api import consultar_cep
from src.apoio.validators import validar_id_numerico, validar_data_nascimento
from src.apoio.utils import calcular_idade_por_data_nascimento

PRIORIDADE_OPCOES = {"1": "baixa", "2": "média", "3": "alta"}
STATUS_OPCOES = {"1": "em análise", "2": "aprovada", "3": "reprovada"}


# ─── helpers de terminal ───────────────────────────────────────────────────────

def limpar_tela():
    if os.name == "nt":
        os.system("cls")
    elif os.getenv("TERM"):
        os.system("clear")

def pausar():
    input("\nPressione Enter para continuar...")

def mostrar_titulo(titulo: str):
    limpar_tela()
    print("=" * 60)
    print(titulo.center(60))
    print("=" * 60)

def mostrar_subtitulo(texto: str):
    print(f"\n{texto}")
    print("-" * 60)

def ler_opcao(mensagem: str, opcoes_validas):
    while True:
        opcao = input(mensagem).strip()
        if opcao in opcoes_validas:
            return opcao
        print("Opcao invalida. Tente novamente.")

def exibir_mensagem_resposta(resposta: dict):
    mensagem = resposta.get("message", "Operacao finalizada.")
    print(f"\n{mensagem}")
    erros = resposta.get("erro")
    if erros:
        print("\nDetalhes:")
        for erro in erros:
            campo = erro.get("campo", "campo")
            descricao = erro.get("erro", "Erro nao especificado.")
            print(f"  - {campo}: {descricao}")


# ─── leitores de campo ────────────────────────────────────────────────────────

def ler_nome() -> str:
    while True:
        nome = input("Nome completo: ").strip()
        if nome:
            return nome
        print("O nome nao pode ficar vazio.")

def ler_cpf() -> str:
    while True:
        cpf = input("CPF (somente numeros): ").strip()
        cpf_limpo = re.sub(r"\D", "", cpf)
        if len(cpf_limpo) == 11:
            return cpf_limpo
        print("CPF deve ter 11 digitos numericos.")

def ler_idade() -> int:
    while True:
        valor = input("Idade: ").strip()
        try:
            idade = int(valor)
            if 11 <= idade <= 17:
                return idade
            print("A idade deve estar entre 11 e 17 anos. O Projeto Nora atende apenas adolescentes nessa faixa.")
        except ValueError:
            print("Digite uma idade valida usando apenas numeros.")

def ler_descricao() -> str:
    while True:
        desc = input("Descricao do caso: ").strip()
        if len(desc) < 10:
            print("Descricao deve ter pelo menos 10 caracteres.")
        elif len(desc) > 300:
            print("Descricao deve ter no maximo 300 caracteres.")
        else:
            return desc

def ler_prioridade() -> str:
    while True:
        print("\nPrioridade: 1-Baixa  2-Media  3-Alta")
        opcao = input("Escolha: ").strip()
        if opcao in PRIORIDADE_OPCOES:
            return PRIORIDADE_OPCOES[opcao]
        texto = opcao.lower()
        if texto in PRIORIDADE_OPCOES.values():
            return texto
        print("Escolha 1, 2 ou 3.")

def ler_observacoes() -> str:
    return input("Observacoes (opcional): ").strip()

def ler_id_numerico(descricao: str):
    while True:
        valor = input(f"ID {descricao} (0 para voltar): ").strip()
        if valor == "0":
            return None
        resultado = validar_id_numerico(valor)
        if resultado["status"]:
            return resultado["data"]
        print(resultado["message"])

def ler_cep() -> str:
    while True:
        cep = input("CEP (8 digitos): ").strip()
        cep_limpo = re.sub(r"\D", "", cep)
        if len(cep_limpo) == 8:
            return cep_limpo
        print("CEP deve ter 8 digitos numericos.")

def ler_telefone() -> str:
    while True:
        tel = input("Telefone (com DDD, somente numeros): ").strip()
        tel_limpo = re.sub(r"\D", "", tel)
        if len(tel_limpo) in (10, 11):
            return tel_limpo
        print("Telefone deve ter 10 ou 11 digitos.")

def ler_rg() -> str:
    while True:
        rg = input("RG: ").strip()
        rg_limpo = re.sub(r"[^A-Za-z0-9]", "", rg)
        if 5 <= len(rg_limpo) <= 14:
            return rg
        print("RG deve ter entre 5 e 14 caracteres alfanumericos.")

def ler_data_nascimento() -> str:
    while True:
        data = input("Data de nascimento (DD/MM/AAAA): ").strip()
        resultado = validar_data_nascimento(data)
        if resultado["status"]:
            return data
        print(resultado["message"])

def ler_numero_endereco() -> str:
    while True:
        numero = input("Numero: ").strip()
        if numero:
            return numero
        print("O numero nao pode ficar vazio.")


# ─── formatadores de exibição ─────────────────────────────────────────────────

def exibir_triagem(triagem: dict):
    print("-" * 60)
    obs = triagem.get("observacoes") or "Nao informado"
    print(f"ID         : {triagem.get('id_triagem', '-')}")
    print(f"Paciente   : {triagem.get('nome_completo', '-')}")
    print(f"CPF        : {triagem.get('cpf', '-')}")
    print(f"Idade      : {triagem.get('idade', '-')}")
    print(f"Descricao  : {triagem.get('descricao_caso', '-')}")
    print(f"Prioridade : {triagem.get('prioridade', '-')}")
    print(f"Status     : {triagem.get('status', '-')}")
    print(f"Criacao    : {triagem.get('data_criacao', '-')}")
    print(f"Observacoes: {obs}")
    print("-" * 60)

def exibir_lista_triagens(triagens: list):
    if not triagens:
        print("\nNenhuma triagem encontrada.")
        return
    print(f"\nTotal: {len(triagens)}")
    for t in triagens:
        exibir_triagem(t)

def exibir_paciente(paciente: dict):
    print("-" * 60)
    dentista = paciente.get("nome_dentista") or "Sem dentista vinculado"
    print(f"ID Paciente : {paciente.get('id_paciente', '-')}")
    print(f"Nome        : {paciente.get('nome_completo', '-')}")
    print(f"CPF         : {paciente.get('cpf', '-')}")
    print(f"Idade       : {paciente.get('idade', '-')}")
    print(f"Nasc.       : {paciente.get('data_nascimento', '-')}")
    print(f"RG          : {paciente.get('rg', '-')}")
    print(f"Telefone    : {paciente.get('telefone', '-')}")
    print(f"Endereco    : {paciente.get('logradouro', '-')}, {paciente.get('numero', '-')}")
    print(f"Bairro/Cid  : {paciente.get('bairro', '-')} - {paciente.get('cidade', '-')}/{paciente.get('uf', '-')}")
    print(f"CEP         : {paciente.get('cep', '-')}")
    print(f"Dentista    : {dentista}")
    print(f"Cadastro    : {paciente.get('data_cadastro', '-')}")
    print("-" * 60)

def exibir_dentista(dentista: dict):
    print("-" * 60)
    print(f"ID         : {dentista.get('id_dentista', '-')}")
    print(f"Nome       : {dentista.get('nome', '-')}")
    print(f"CRO        : {dentista.get('cro', '-')}")
    print(f"Esp.       : {dentista.get('especialidade', '-')}")
    print(f"Cidade/UF  : {dentista.get('cidade', '-')}/{dentista.get('uf', '-')}")
    print(f"CEP        : {dentista.get('cep', '-')}")
    print(f"Telefone   : {dentista.get('telefone', '-')}")
    print(f"Vagas      : {dentista.get('vagas_disponiveis', '-')}")
    print("-" * 60)

def exibir_lista_generica(lista: list):
    if not lista:
        print("\nNenhum resultado encontrado.")
        return
    print(f"\nTotal: {len(lista)}")
    for item in lista:
        print("-" * 60)
        for chave, valor in item.items():
            print(f"  {chave}: {valor}")
    print("-" * 60)

def oferecer_exportacao(nome_consulta: str, filtro: dict, dados: list):
    if not dados:
        return
    print("\nDeseja exportar este resultado para JSON?")
    print("1. Sim")
    print("2. Nao")
    opcao = ler_opcao("Escolha: ", ("1", "2"))
    if opcao == "1":
        resposta = exportador.exportar_resultado_consulta(nome_consulta, filtro, dados)
        exibir_mensagem_resposta(resposta)


# ─── fluxo: triagens ──────────────────────────────────────────────────────────

def _coletar_dados_nova_triagem() -> dict:
    mostrar_subtitulo("Preencha os dados da nova triagem")
    return {
        "nome_completo": ler_nome(),
        "cpf": ler_cpf(),
        "idade": ler_idade(),
        "descricao_caso": ler_descricao(),
        "prioridade": ler_prioridade(),
        "observacoes": ler_observacoes(),
    }

def fluxo_criar_triagem():
    mostrar_titulo("CRIAR TRIAGEM")
    dados = _coletar_dados_nova_triagem()
    print("\n1. Confirmar criacao")
    print("2. Cancelar")
    if ler_opcao("Escolha: ", ("1", "2")) == "2":
        print("\nCriacao cancelada.")
        pausar()
        return
    resposta = svc_triagem.criar_triagem(dados)
    exibir_mensagem_resposta(resposta)
    if resposta.get("status") and resposta.get("data"):
        exibir_triagem(resposta["data"])
    pausar()

def fluxo_listar_todas_triagens():
    mostrar_titulo("LISTAR TODAS AS TRIAGENS")
    resposta = svc_triagem.listar_triagens()
    exibir_mensagem_resposta(resposta)
    exibir_lista_triagens(resposta.get("data", []))
    pausar()

def fluxo_buscar_triagem():
    mostrar_titulo("BUSCAR TRIAGEM POR ID")
    id_triagem = ler_id_numerico("da triagem")
    if id_triagem is None:
        return
    resposta = svc_triagem.buscar_triagem_por_id(id_triagem)
    exibir_mensagem_resposta(resposta)
    if resposta.get("status") and resposta.get("data"):
        exibir_triagem(resposta["data"])
    pausar()

def fluxo_atualizar_triagem():
    mostrar_titulo("ATUALIZAR TRIAGEM")
    id_triagem = ler_id_numerico("da triagem")
    if id_triagem is None:
        return

    resposta_busca = svc_triagem.buscar_triagem_por_id(id_triagem)
    if not resposta_busca.get("status"):
        exibir_mensagem_resposta(resposta_busca)
        pausar()
        return

    triagem_atual = resposta_busca["data"]
    if triagem_atual.get("status") != "em análise":
        print(f"\nNao e possivel atualizar: status atual e '{triagem_atual.get('status')}'.")
        pausar()
        return

    exibir_triagem(triagem_atual)
    mostrar_subtitulo("Pressione Enter para manter o valor atual")

    dados = {}
    novo_nome = input(f"Nome [{triagem_atual.get('nome_completo')}]: ").strip()
    if novo_nome:
        dados["nome_completo"] = novo_nome

    valor_idade = input(f"Idade [{triagem_atual.get('idade')}]: ").strip()
    if valor_idade:
        try:
            nova_idade = int(valor_idade)
            if 11 <= nova_idade <= 17:
                dados["idade"] = nova_idade
            else:
                print("Idade ignorada (deve estar entre 11 e 17).")
        except ValueError:
            print("Idade ignorada (valor invalido).")

    nova_desc = input(f"Descricao [{triagem_atual.get('descricao_caso')}]: ").strip()
    if nova_desc:
        dados["descricao_caso"] = nova_desc

    print(f"\nPrioridade atual: {triagem_atual.get('prioridade')}")
    print("1-Baixa  2-Media  3-Alta  Enter-Manter")
    op_prio = input("Escolha: ").strip()
    if op_prio in PRIORIDADE_OPCOES:
        dados["prioridade"] = PRIORIDADE_OPCOES[op_prio]

    nova_obs = input(f"Observacoes [{triagem_atual.get('observacoes') or 'vazia'}]: ").strip()
    if nova_obs:
        dados["observacoes"] = nova_obs

    if not dados:
        print("\nNenhum campo alterado.")
        pausar()
        return

    print("\n1. Confirmar atualizacao")
    print("2. Cancelar")
    if ler_opcao("Escolha: ", ("1", "2")) == "2":
        print("\nAtualizacao cancelada.")
        pausar()
        return

    resposta = svc_triagem.atualizar_triagem(id_triagem, dados)
    exibir_mensagem_resposta(resposta)
    if resposta.get("status") and resposta.get("data"):
        exibir_triagem(resposta["data"])
    pausar()

def fluxo_triagens_por_status():
    mostrar_titulo("TRIAGENS POR STATUS")
    print("1. Em analise")
    print("2. Aprovada")
    print("3. Reprovada")
    opcao = ler_opcao("Escolha: ", ("1", "2", "3"))
    status_mapa = {"1": "em análise", "2": "aprovada", "3": "reprovada"}
    status = status_mapa[opcao]
    resposta = svc_consulta.consultar_triagens_por_status(status)
    exibir_mensagem_resposta(resposta)
    dados = resposta.get("data", [])
    exibir_lista_triagens(dados)
    oferecer_exportacao("triagens_por_status", {"status": status}, dados)
    pausar()

def fluxo_triagens_por_prioridade():
    mostrar_titulo("TRIAGENS POR PRIORIDADE")
    print("1. Baixa")
    print("2. Media")
    print("3. Alta")
    opcao = ler_opcao("Escolha: ", ("1", "2", "3"))
    prioridade = PRIORIDADE_OPCOES[opcao]
    resposta = svc_consulta.consultar_triagens_por_prioridade(prioridade)
    exibir_mensagem_resposta(resposta)
    dados = resposta.get("data", [])
    exibir_lista_triagens(dados)
    oferecer_exportacao("triagens_por_prioridade", {"prioridade": prioridade}, dados)
    pausar()

def submenu_listar_triagens():
    while True:
        mostrar_titulo("LISTAR TRIAGENS")
        print("1. Listar todas as triagens")
        print("2. Listar triagens por status")
        print("3. Listar triagens por prioridade")
        print("0. Voltar")
        opcao = ler_opcao("\nEscolha: ", ("1", "2", "3", "0"))
        if opcao == "0":
            return
        acoes = {
            "1": fluxo_listar_todas_triagens,
            "2": fluxo_triagens_por_status,
            "3": fluxo_triagens_por_prioridade,
        }
        acoes[opcao]()

def _coletar_dados_complementares_paciente(triagem: dict):
    """Coleta dados do futuro paciente. Retorna dict com dados ou None se o usuario cancelar."""
    print(f"Paciente: {triagem.get('nome_completo')} | CPF: {triagem.get('cpf')}\n")

    # Data de nascimento com validacao cruzada de idade
    while True:
        data_nasc = ler_data_nascimento()
        idade_calc = calcular_idade_por_data_nascimento(data_nasc)
        idade_triagem = triagem.get("idade", 0)
        if abs(idade_calc - idade_triagem) > 1:
            print(f"\nAtencao: a data informada gera idade {idade_calc} ano(s),")
            print(f"mas a triagem registra {idade_triagem} ano(s). Verifique e informe novamente.")
            print("1. Informar nova data de nascimento")
            print("2. Cancelar")
            if ler_opcao("Escolha: ", ("1", "2")) == "2":
                return None
        else:
            break

    rg = ler_rg()
    telefone = ler_telefone()
    cep = ler_cep()

    print("\nConsultando CEP no ViaCEP...")
    resp_cep = consultar_cep(cep)
    exibir_mensagem_resposta(resp_cep)

    logradouro = bairro = cidade = uf = complemento = ""
    if resp_cep.get("status") and resp_cep.get("data"):
        end = resp_cep["data"]
        logradouro = end.get("logradouro", "")
        bairro = end.get("bairro", "")
        cidade = end.get("cidade", "")
        uf = end.get("uf", "")
        complemento = end.get("complemento", "")
        print(f"Logradouro : {logradouro}")
        print(f"Bairro     : {bairro}")
        print(f"Cidade/UF  : {cidade}/{uf}")
    else:
        print("CEP nao localizado. Preencha o endereco manualmente.")
        while not logradouro:
            logradouro = input("Logradouro: ").strip()
            if not logradouro:
                print("Logradouro nao pode ficar em branco.")
        while not bairro:
            bairro = input("Bairro: ").strip()
            if not bairro:
                print("Bairro nao pode ficar em branco.")
        while not cidade:
            cidade = input("Cidade: ").strip()
            if not cidade:
                print("Cidade nao pode ficar em branco.")
        while not uf or len(uf) != 2:
            uf = input("UF (2 letras): ").strip().upper()
            if not uf or len(uf) != 2:
                print("UF deve ter exatamente 2 letras.")

    numero = ler_numero_endereco()
    complemento_input = input(f"Complemento [{complemento or 'vazio'}]: ").strip()
    if complemento_input:
        complemento = complemento_input

    return {
        "data_nascimento": data_nasc,
        "rg": rg,
        "telefone": telefone,
        "cep": cep,
        "logradouro": logradouro,
        "numero": numero,
        "complemento": complemento,
        "bairro": bairro,
        "cidade": cidade,
        "uf": uf,
    }

def fluxo_aprovar_triagem():
    mostrar_titulo("APROVAR TRIAGEM")
    id_triagem = ler_id_numerico("da triagem")
    if id_triagem is None:
        return

    resposta_busca = svc_triagem.buscar_triagem_por_id(id_triagem)
    if not resposta_busca.get("status"):
        exibir_mensagem_resposta(resposta_busca)
        pausar()
        return

    triagem = resposta_busca["data"]
    if triagem.get("status") != "em análise":
        print(f"\nTriagem com status '{triagem.get('status')}' nao pode ser aprovada.")
        pausar()
        return

    exibir_triagem(triagem)
    print("\n1. Iniciar fluxo de aprovacao (coleta dados do paciente)")
    print("2. Cancelar")
    if ler_opcao("Escolha: ", ("1", "2")) == "2":
        print("\nOperacao cancelada. Triagem permanece 'em analise'.")
        pausar()
        return

    mostrar_subtitulo("Dados complementares do paciente")
    dados_complementares = _coletar_dados_complementares_paciente(triagem)
    if dados_complementares is None:
        print("\nColeta cancelada. Triagem permanece 'em analise'.")
        pausar()
        return

    # Preview antes da confirmacao final
    mostrar_subtitulo("Resumo da aprovacao")
    print(f"Paciente : {triagem.get('nome_completo')}")
    print(f"CPF      : {triagem.get('cpf')}")
    print(f"Nasc.    : {dados_complementares['data_nascimento']}")
    print(f"Cidade   : {dados_complementares['cidade']}/{dados_complementares['uf']}")
    print(f"CEP      : {dados_complementares['cep']}")
    print("\n1. Confirmar aprovacao e criar paciente")
    print("2. Cancelar")
    if ler_opcao("Escolha: ", ("1", "2")) == "2":
        print("\nOperacao cancelada. Triagem permanece 'em analise'.")
        pausar()
        return

    # Somente aqui o banco e alterado
    resposta_aprovacao = svc_triagem.aprovar_triagem(id_triagem)
    exibir_mensagem_resposta(resposta_aprovacao)
    if not resposta_aprovacao.get("status"):
        pausar()
        return

    resposta_paciente = svc_paciente.criar_paciente_a_partir_de_triagem(id_triagem, dados_complementares)
    exibir_mensagem_resposta(resposta_paciente)

    if not resposta_paciente.get("status"):
        # Falha: reverter triagem para 'em analise'
        resp_reverter = svc_triagem.reverter_para_em_analise(id_triagem)
        if resp_reverter.get("status"):
            print("\nTriagem revertida para 'em analise' devido a falha no cadastro do paciente.")
        else:
            print("\nAVISO: Falha ao reverter triagem. Verifique manualmente o status no banco.")
        pausar()
        return

    paciente = resposta_paciente["data"]
    exibir_paciente(paciente)

    # Sugestao de dentista
    print("\nDeseja associar um dentista a este paciente agora?")
    print("1. Sim")
    print("2. Nao")
    if ler_opcao("Escolha: ", ("1", "2")) == "1":
        id_paciente = paciente.get("id_paciente")
        resp_sug = svc_associacao.sugerir_dentista_para_paciente(id_paciente)
        if resp_sug.get("status") and resp_sug.get("data"):
            sug = resp_sug["data"]
            print(f"\nSugestao de dentista:")
            print(f"  ID     : {sug.get('id_dentista')}")
            print(f"  Nome   : {sug.get('nome')}")
            print(f"  Cidade : {sug.get('cidade')}/{sug.get('uf')}")
            print(f"  Vagas  : {sug.get('vagas_disponiveis')}")
            print("\n1. Confirmar associacao")
            print("2. Cancelar")
            if ler_opcao("Escolha: ", ("1", "2")) == "1":
                resp_vinculo = svc_paciente.vincular_dentista_ao_paciente(
                    id_paciente, sug.get("id_dentista")
                )
                exibir_mensagem_resposta(resp_vinculo)
        else:
            exibir_mensagem_resposta(resp_sug)

    pausar()

def fluxo_reprovar_triagem():
    mostrar_titulo("REPROVAR TRIAGEM")
    id_triagem = ler_id_numerico("da triagem")
    if id_triagem is None:
        return

    resposta_busca = svc_triagem.buscar_triagem_por_id(id_triagem)
    if not resposta_busca.get("status"):
        exibir_mensagem_resposta(resposta_busca)
        pausar()
        return

    exibir_triagem(resposta_busca["data"])
    print("\n1. Confirmar reprovacao")
    print("2. Cancelar")
    if ler_opcao("Escolha: ", ("1", "2")) == "2":
        print("\nReprovacao cancelada.")
        pausar()
        return

    resposta = svc_triagem.reprovar_triagem(id_triagem)
    exibir_mensagem_resposta(resposta)
    pausar()

def fluxo_excluir_triagem():
    mostrar_titulo("EXCLUIR TRIAGEM")
    id_triagem = ler_id_numerico("da triagem")
    if id_triagem is None:
        return

    resposta_busca = svc_triagem.buscar_triagem_por_id(id_triagem)
    if not resposta_busca.get("status"):
        exibir_mensagem_resposta(resposta_busca)
        pausar()
        return

    exibir_triagem(resposta_busca["data"])
    print("\nATENCAO: Esta acao e irreversivel.")
    print("1. Confirmar exclusao")
    print("2. Cancelar")
    if ler_opcao("Escolha: ", ("1", "2")) == "2":
        print("\nExclusao cancelada.")
        pausar()
        return

    resposta = svc_triagem.excluir_triagem(id_triagem)
    exibir_mensagem_resposta(resposta)
    pausar()

def submenu_triagens():
    while True:
        mostrar_titulo("TRIAGENS")
        print("1. Criar nova triagem")
        print("2. Listar triagens")
        print("3. Buscar triagem por ID")
        print("4. Atualizar triagem")
        print("5. Aprovar triagem")
        print("6. Reprovar triagem")
        print("7. Excluir triagem")
        print("0. Voltar")
        opcao = ler_opcao("\nEscolha: ", ("1", "2", "3", "4", "5", "6", "7", "0"))
        if opcao == "0":
            return
        acoes = {
            "1": fluxo_criar_triagem,
            "2": submenu_listar_triagens,
            "3": fluxo_buscar_triagem,
            "4": fluxo_atualizar_triagem,
            "5": fluxo_aprovar_triagem,
            "6": fluxo_reprovar_triagem,
            "7": fluxo_excluir_triagem,
        }
        acoes[opcao]()


# ─── fluxo: pacientes ─────────────────────────────────────────────────────────

def fluxo_listar_todos_pacientes():
    mostrar_titulo("LISTAR TODOS OS PACIENTES")
    resposta = svc_paciente.listar_pacientes()
    exibir_mensagem_resposta(resposta)
    dados = resposta.get("data", [])
    if dados:
        print(f"\nTotal: {len(dados)}")
        for p in dados:
            exibir_paciente(p)
    else:
        print("\nNenhum paciente encontrado.")
    pausar()

def fluxo_buscar_paciente():
    mostrar_titulo("BUSCAR PACIENTE POR ID")
    id_paciente = ler_id_numerico("do paciente")
    if id_paciente is None:
        return
    resposta = svc_paciente.buscar_paciente_por_id(id_paciente)
    exibir_mensagem_resposta(resposta)
    if resposta.get("status") and resposta.get("data"):
        exibir_paciente(resposta["data"])
    pausar()

def fluxo_listar_pacientes_com_dentista():
    mostrar_titulo("PACIENTES COM DENTISTA")
    resposta = svc_paciente.listar_pacientes_com_dentista()
    exibir_mensagem_resposta(resposta)
    dados = resposta.get("data", [])
    if dados:
        print(f"\nTotal: {len(dados)}")
        for p in dados:
            exibir_paciente(p)
    else:
        print("\nNenhum paciente com dentista encontrado.")
    pausar()

def fluxo_consulta_pacientes_sem_dentista():
    mostrar_titulo("PACIENTES SEM DENTISTA")
    resposta = svc_consulta.consultar_pacientes_sem_dentista()
    exibir_mensagem_resposta(resposta)
    dados = resposta.get("data", [])
    exibir_lista_generica(dados)
    oferecer_exportacao("pacientes_sem_dentista", {}, dados)
    pausar()

def submenu_listar_pacientes():
    while True:
        mostrar_titulo("LISTAR PACIENTES")
        print("1. Listar todos os pacientes")
        print("2. Listar pacientes com dentista")
        print("3. Listar pacientes sem dentista")
        print("0. Voltar")
        opcao = ler_opcao("\nEscolha: ", ("1", "2", "3", "0"))
        if opcao == "0":
            return
        acoes = {
            "1": fluxo_listar_todos_pacientes,
            "2": fluxo_listar_pacientes_com_dentista,
            "3": fluxo_consulta_pacientes_sem_dentista,
        }
        acoes[opcao]()

def fluxo_associar_dentista():
    mostrar_titulo("ASSOCIAR/REASSOCIAR DENTISTA A PACIENTE")
    id_paciente = ler_id_numerico("do paciente")
    if id_paciente is None:
        return

    resp_paciente = svc_paciente.buscar_paciente_por_id(id_paciente)
    if not resp_paciente.get("status"):
        exibir_mensagem_resposta(resp_paciente)
        pausar()
        return

    paciente = resp_paciente["data"]
    exibir_paciente(paciente)

    id_dentista_atual = paciente.get("id_dentista")
    nome_dentista_atual = paciente.get("nome_dentista") or "Nenhum"
    if id_dentista_atual:
        print(f"\nDentista atual: {nome_dentista_atual} (ID: {id_dentista_atual})")
    else:
        print("\nPaciente sem dentista vinculado.")

    resp_sug = svc_associacao.sugerir_dentista_para_paciente(id_paciente)
    if not resp_sug.get("status"):
        exibir_mensagem_resposta(resp_sug)
        pausar()
        return

    sug = resp_sug["data"]
    print(f"\nDentista sugerido:")
    print(f"  ID     : {sug.get('id_dentista')}")
    print(f"  Nome   : {sug.get('nome')}")
    print(f"  Cidade : {sug.get('cidade')}/{sug.get('uf')}")
    print(f"  Vagas  : {sug.get('vagas_disponiveis')}")

    if id_dentista_atual:
        print(f"\nATENCAO: Esta operacao ira:")
        print(f"  - Devolver 1 vaga ao dentista atual ({nome_dentista_atual})")
        print(f"  - Consumir 1 vaga do novo dentista")

    print("\n1. Aceitar sugestao")
    print("2. Informar ID de outro dentista")
    print("3. Cancelar")
    opcao = ler_opcao("Escolha: ", ("1", "2", "3"))

    if opcao == "3":
        print("\nAssociacao cancelada.")
        pausar()
        return

    if opcao == "1":
        id_dentista = sug.get("id_dentista")
    else:
        id_dentista = ler_id_numerico("do dentista")
        if id_dentista is None:
            pausar()
            return

    resposta = svc_paciente.vincular_dentista_ao_paciente(id_paciente, id_dentista)
    exibir_mensagem_resposta(resposta)
    pausar()

def submenu_pacientes():
    while True:
        mostrar_titulo("PACIENTES")
        print("1. Listar pacientes")
        print("2. Buscar paciente por ID")
        print("3. Associar/Reassociar paciente a dentista")
        print("0. Voltar")
        opcao = ler_opcao("\nEscolha: ", ("1", "2", "3", "0"))
        if opcao == "0":
            return
        acoes = {
            "1": submenu_listar_pacientes,
            "2": fluxo_buscar_paciente,
            "3": fluxo_associar_dentista,
        }
        acoes[opcao]()


# ─── fluxo: dentistas ─────────────────────────────────────────────────────────

def fluxo_listar_todos_dentistas():
    mostrar_titulo("LISTAR TODOS OS DENTISTAS")
    resposta = svc_dentista.listar_dentistas()
    exibir_mensagem_resposta(resposta)
    dados = resposta.get("data", [])
    if dados:
        print(f"\nTotal: {len(dados)}")
        for d in dados:
            exibir_dentista(d)
    else:
        print("\nNenhum dentista encontrado.")
    pausar()

def fluxo_buscar_dentista():
    mostrar_titulo("BUSCAR DENTISTA POR ID")
    id_dentista = ler_id_numerico("do dentista")
    if id_dentista is None:
        return
    resposta = svc_dentista.buscar_dentista_por_id(id_dentista)
    exibir_mensagem_resposta(resposta)
    if resposta.get("status") and resposta.get("data"):
        exibir_dentista(resposta["data"])
    pausar()

def fluxo_consulta_pacientes_por_dentista():
    mostrar_titulo("PACIENTES DE UM DENTISTA")
    id_dentista = ler_id_numerico("do dentista")
    if id_dentista is None:
        return
    resposta = svc_consulta.consultar_pacientes_por_dentista(id_dentista)
    exibir_mensagem_resposta(resposta)
    dados = resposta.get("data", [])
    exibir_lista_generica(dados)
    oferecer_exportacao("pacientes_por_dentista", {"id_dentista": id_dentista}, dados)
    pausar()

def fluxo_consulta_dentistas_com_vagas():
    mostrar_titulo("DENTISTAS COM VAGAS")
    resposta = svc_consulta.consultar_dentistas_com_vagas()
    exibir_mensagem_resposta(resposta)
    dados = resposta.get("data", [])
    if dados:
        print(f"\nTotal: {len(dados)}")
        for d in dados:
            exibir_dentista(d)
    else:
        print("\nNenhum dentista com vagas encontrado.")
    oferecer_exportacao("dentistas_com_vagas", {}, dados)
    pausar()

def submenu_listar_dentistas():
    while True:
        mostrar_titulo("LISTAR DENTISTAS")
        print("1. Listar todos os dentistas")
        print("2. Listar dentistas com vagas disponiveis")
        print("0. Voltar")
        opcao = ler_opcao("\nEscolha: ", ("1", "2", "0"))
        if opcao == "0":
            return
        acoes = {
            "1": fluxo_listar_todos_dentistas,
            "2": fluxo_consulta_dentistas_com_vagas,
        }
        acoes[opcao]()

def submenu_dentistas():
    while True:
        mostrar_titulo("DENTISTAS")
        print("1. Listar dentistas")
        print("2. Buscar dentista por ID")
        print("3. Listar pacientes de um dentista")
        print("0. Voltar")
        opcao = ler_opcao("\nEscolha: ", ("1", "2", "3", "0"))
        if opcao == "0":
            return
        acoes = {
            "1": submenu_listar_dentistas,
            "2": fluxo_buscar_dentista,
            "3": fluxo_consulta_pacientes_por_dentista,
        }
        acoes[opcao]()


# ─── sobre o sistema ──────────────────────────────────────────────────────────

def exibir_sobre():
    mostrar_titulo("SOBRE O SISTEMA")
    print("\nProjeto Nora - Sprint 4")
    print("Disciplina: Computational Thinking Using Python")
    print("Instituicao: FIAP - Faculdade de Informatica e Administracao Paulista")
    print("\nDescricao:")
    print("  Sistema de apoio a uma ONG odontologica para gestao de triagens,")
    print("  criacao de pacientes a partir de triagens aprovadas e associacao")
    print("  a dentistas voluntarios por proximidade geografica aproximada.")
    print("\nPublico atendido:")
    print("  Exclusivamente adolescentes de 11 a 17 anos.")
    print("  Idades fora dessa faixa sao recusadas em todas as etapas do sistema.")
    print("\nFluxo principal:")
    print("  Triagem -> Aprovacao -> Paciente -> CEP (ViaCEP) -> Dentista")
    print("\nPersistencia: Oracle (via oracledb)")
    print("API externa : ViaCEP (https://viacep.com.br) - preenchimento de endereco")
    print("Exportacao  : JSON em exports/ para consultas filtradas")
    print("\nTrabalho academico - Sprint 4 - FIAP")
    pausar()


# ─── menu principal ───────────────────────────────────────────────────────────

def executar_menu():
    mostrar_titulo("PROJETO NORA")
    print("\nBem-vindo ao sistema de triagens odontologicas.")
    print("Pressione Enter para continuar.")
    input()

    while True:
        mostrar_titulo("MENU PRINCIPAL")
        print("1. Triagens")
        print("2. Pacientes")
        print("3. Dentistas")
        print("4. Sobre o sistema")
        print("0. Sair")

        opcao = ler_opcao("\nEscolha: ", ("1", "2", "3", "4", "0"))

        if opcao == "0":
            mostrar_titulo("ENCERRANDO")
            print("Sistema encerrado. Ate logo!")
            break

        acoes = {
            "1": submenu_triagens,
            "2": submenu_pacientes,
            "3": submenu_dentistas,
            "4": exibir_sobre,
        }
        acoes[opcao]()


if __name__ == "__main__":
    executar_menu()
