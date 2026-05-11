PROJETO NORA - SPRINT 4
Disciplina: Computational Thinking Using Python
Instituicao: FIAP - ADS

==============================================================
1. OBJETIVO DO PROJETO
==============================================================
O Projeto Nora e um sistema de terminal desenvolvido em Python
para apoiar uma ONG odontologica na gestao de triagens de
pacientes, aprovacao de casos, cadastro de pacientes e
associacao a dentistas voluntarios.

==============================================================
2. REGRA DE NEGOCIO CRITICA - FAIXA ETARIA
==============================================================
O Projeto Nora atende EXCLUSIVAMENTE adolescentes de 11 a 17
anos de idade (inclusive). Qualquer tentativa de cadastrar
triagem ou paciente com idade fora dessa faixa sera recusada
com mensagem explicativa em todas as etapas do sistema.

Isso inclui:
  - Validacao da idade na criacao de triagem
  - Validacao da idade na atualizacao de triagem
  - Validacao da data de nascimento no cadastro de paciente
  - Verificacao cruzada: a data de nascimento deve gerar uma
    idade compativel com a registrada na triagem (tolerancia
    de 1 ano para casos de aniversario recente)

==============================================================
3. FLUXO DE NEGOCIO
==============================================================
1. Cadastra-se uma triagem (dados do paciente + descricao).
2. A triagem e avaliada: aprovada ou reprovada.
3. Triagem aprovada dispara o cadastro do paciente:
   - Data de nascimento validada (faixa 11-17 anos)
   - Endereco preenchido via ViaCEP (API publica)
   - Associacao opcional com dentista voluntario
4. A sugestao de dentista usa proximidade por CEP (academica).
5. Vaga do dentista e decrementada ao confirmar associacao.
6. Consultas filtradas podem ser exportadas para JSON.

==============================================================
4. INSTALAR DEPENDENCIAS
==============================================================
Execute no terminal, dentro da pasta do projeto:

    pip install -r requirements.txt

As unicas dependencias sao: oracledb e requests.

==============================================================
5. CONFIGURAR O BANCO ORACLE
==============================================================
O arquivo .env NAO e incluido no ZIP (contem credenciais).
Voce precisa cria-lo antes de executar o sistema.

Passo a passo:
  1. Copie o arquivo de exemplo:
        .env.example  ->  .env
     (ou crie o arquivo .env manualmente na raiz do projeto)

  2. Preencha com suas credenciais:
        DB_USER=seu_usuario_oracle
        DB_PASSWORD=sua_senha_oracle
        DB_DSN=oracle.fiap.com.br:1521/ORCL

O sistema carrega o .env automaticamente ao iniciar.
Se o .env nao existir ou as credenciais forem invalidas,
o sistema exibe aviso e continua (sem acesso ao banco).

Alternativamente, defina variaveis de ambiente no sistema
antes de executar: DB_USER, DB_PASSWORD, DB_DSN.

==============================================================
6. CRIAR AS TABELAS NO BANCO
==============================================================
Abra o arquivo scripts_oracle.txt no SQL Developer ou sqlplus
e execute todo o conteudo. A ordem interna ja esta correta:
  DROP -> CREATE TB_DENTISTA -> CREATE TB_TRIAGEM ->
  CREATE TB_PACIENTE -> INSERTs -> COMMIT

IMPORTANTE: o script usa CHECK (IDADE BETWEEN 11 AND 17) em
TB_TRIAGEM e TB_PACIENTE, refletindo a regra de faixa etaria
do projeto. Nao altere essa constraint.

==============================================================
7. EXECUTAR O SISTEMA
==============================================================
No terminal, dentro da pasta do projeto:

    python main.py

O sistema testa a conexao com o Oracle ao iniciar e exibe
aviso se nao conseguir conectar (o menu ainda abre, mas as
operacoes de dados retornarao erro).

==============================================================
8. ESTRUTURA DE MENUS
==============================================================
Menu principal com 4 areas de trabalho:

  1. Triagens
     - Criar nova triagem
     - Listar triagens
     - Buscar triagem por ID
     - Atualizar triagem
     - Aprovar triagem (inicia cadastro do paciente)
     - Reprovar triagem
     - Excluir triagem
     - Listar triagens por status   (consulta filtrada + JSON)
     - Listar triagens por prioridade (consulta filtrada + JSON)

  2. Pacientes
     - Listar pacientes
     - Buscar paciente por ID
     - Listar pacientes com dentista
     - Listar pacientes sem dentista (consulta filtrada + JSON)
     - Associar paciente a dentista

  3. Dentistas
     - Listar dentistas
     - Buscar dentista por ID
     - Listar pacientes de um dentista (consulta filtrada + JSON)
     - Listar dentistas com vagas disponíveis (consulta + JSON)

  4. Sobre o sistema

  0. Sair

==============================================================
9. EXPORTACAO JSON
==============================================================
Apos cada consulta filtrada, o sistema pergunta:
  "Deseja exportar este resultado para JSON?"

Os arquivos sao salvos em exports/ com timestamp no nome.
Formato: <consulta>_YYYYMMDD_HHMMSS.json

Estrutura do arquivo:
  {
      "consulta": "triagens_por_status",
      "filtro": { "status": "em analise" },
      "total_registros": 4,
      "data_exportacao": "2026-05-09 14:30:00",
      "dados": [ ... ]
  }

==============================================================
10. API VIACEP
==============================================================
A API ViaCEP (https://viacep.com.br) e gratuita, publica e
nao requer chave de acesso. E usada automaticamente no fluxo
de aprovacao de triagem para preencher logradouro, bairro,
cidade e UF a partir do CEP informado. Requer conexao com a
internet. O sistema trata falhas de conexao e CEPs invalidos
com mensagens amigaveis.

==============================================================
11. APROXIMACAO DE DISTANCIA DENTISTA-PACIENTE
==============================================================
O algoritmo de sugestao de dentista usa:
  1. Prioridade: mesma cidade do paciente
  2. Fallback: mesma UF
  3. Desempate: menor diferenca numerica entre CEPs

A diferenca numerica entre CEPs e uma simplificacao academica
intencional. Nao representa distancia real em km nem usa
geolocalizacao. Documentar isso no video de apresentacao.
