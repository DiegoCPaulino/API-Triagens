# Contratos da API — Projeto Nora

## 1. Visão geral

Esta API é o back-end Flask do **Projeto Nora**, desenvolvido originalmente como Sprint 4 Python da disciplina *Computational Thinking Using Python* da FIAP e evoluído incrementalmente para o **back-end do Projeto Banca FIAP**.

O domínio é **triagem odontológica para adolescentes (11 a 17 anos)**, com o fluxo central: triagem → aprovação → paciente → dentista voluntário. A API é consumida por um front-end separado e expõe recursos REST com respostas JSON padronizadas.

**Stack:** Python 3, Flask, flask-cors, oracledb, requests (ViaCEP).
**Estado:** em construção incremental. No momento desta documentação, **19 endpoints** estão implementados: `GET /api/health`, as 5 rotas CRUD de triagens, as 2 rotas de aprovação/reprovação, `POST /api/triagens/<id>/paciente`, as 4 rotas de pacientes, as 4 rotas de dentistas e as 2 rotas de associação paciente-dentista. Os 3 restantes são contrato planejado.

---

## 2. URL base

| Ambiente | URL |
|---|---|
| Local (desenvolvimento) | `http://localhost:5000` |
| Render (produção) | A definir — depende da validação de deploy e da disponibilidade da conexão Oracle externa |

---

## 3. Padrão de resposta JSON

Toda resposta da API segue o mesmo envelope JSON, independentemente do domínio ou do resultado.

### Sucesso

```json
{
  "status": true,
  "code": 200,
  "message": "Descrição da operação.",
  "data": { }
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `status` | boolean | `true` em respostas de sucesso |
| `code` | integer | Código HTTP que acompanha a resposta |
| `message` | string | Mensagem em português, sem stack trace |
| `data` | object \| array \| null | Payload da resposta. `null` quando não há dado relevante |

### Erro

```json
{
  "status": false,
  "code": 400,
  "message": "Existem erros de validação nos dados da triagem.",
  "data": null,
  "erro": [
    { "campo": "cpf", "erro": "CPF deve ter 11 dígitos numéricos." },
    { "campo": "idade", "erro": "A idade deve estar entre 11 e 17 anos." }
  ]
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `status` | boolean | `false` em respostas de erro |
| `code` | integer | Código HTTP que acompanha a resposta |
| `message` | string | Mensagem geral do erro, em português |
| `data` | null | Sempre `null` em respostas de erro |
| `erro` | array | Lista de erros detalhados por campo. Pode ser vazia `[]` para erros de roteamento (404, 405) ou erros internos genéricos (500) |

> **Regra de ouro:** respostas de sucesso têm `data`, não têm `erro`. Respostas de erro têm `erro`, têm `data: null`. Os dois campos nunca aparecem simultaneamente com valores preenchidos.

---

## 4. Mapeamento de status HTTP

| Código | Cenário típico |
|---|---|
| **200** | Consulta bem-sucedida; atualização bem-sucedida; aprovação/reprovação de triagem |
| **201** | Criação bem-sucedida (POST que cria um recurso novo) |
| **400** | Payload inválido ou erro de validação de campo |
| **404** | Recurso não encontrado (triagem, paciente ou dentista com ID inexistente) |
| **405** | Método HTTP não permitido para o recurso acessado |
| **409** | Conflito de regra de negócio — exemplos: aprovar triagem já aprovada; criar paciente para triagem não aprovada; criar paciente duplicado para a mesma triagem; vincular dentista sem vagas disponíveis; excluir triagem com paciente vinculado |
| **500** | Erro interno do servidor (inclui falha de conexão Oracle) |
| **502** | Resposta inválida de API externa (ex.: ViaCEP retornou formato inesperado) |
| **503** | API externa indisponível (ex.: ViaCEP fora do ar) |
| **504** | Timeout em API externa (ex.: ViaCEP demorou além do limite) |

---

## 5. Endpoints implementados

### `GET /api/health`

Verifica se a API está ativa. Não realiza nenhuma consulta ao banco de dados Oracle.

**Parâmetros:** nenhum.

**Resposta — 200 OK:**

```json
{
  "code": 200,
  "data": {
    "service": "Projeto Nora API",
    "version": "0.1.0"
  },
  "message": "API do Projeto Nora ativa.",
  "status": true
}
```

---

### Comportamento de erros globais

Os três handlers abaixo são registrados no `app.py` e se aplicam a qualquer rota.

**404 — Rota não encontrada:**

```json
{
  "code": 404,
  "data": null,
  "erro": [],
  "message": "Recurso não encontrado.",
  "status": false
}
```

**405 — Método HTTP não permitido:**

```json
{
  "code": 405,
  "data": null,
  "erro": [],
  "message": "Método HTTP não permitido para este recurso.",
  "status": false
}
```

**500 — Erro interno do servidor:**

```json
{
  "code": 500,
  "data": null,
  "erro": [],
  "message": "Erro interno do servidor.",
  "status": false
}
```

> O stack trace do erro nunca é exposto ao cliente. Ele é registrado no log do servidor via `logging` configurado nos módulos internos.

---

### 5.1 Triagens — CRUD básico (Prompt 09)

Blueprint: `src/rotas/triagens.py` | Módulo: `src/modulos/triagens.py` | Registrado em: `app.py`

#### `GET /api/triagens/`

Retorna todas as triagens, ordenadas por `DATA_CRIACAO DESC`.

**Parâmetros:** nenhum.

**Resposta — 200 OK:** `data` é um array de objetos triagem (pode estar vazio).

---

#### `GET /api/triagens/<id>`

Busca triagem por ID inteiro. O conversor `<int:id_triagem>` garante 404 automático para IDs não numéricos (ex.: `/api/triagens/abc`).

**Parâmetros de path:** `id` — inteiro positivo.

**Resposta — 200 OK (payload real capturado):**

```json
{
  "code": 200,
  "data": {
    "cpf": "99988877766",
    "data_criacao": "2026-05-12 18:48:48",
    "descricao_caso": "Adolescente com dor de dente persistente e necessidade de avaliacao odontologica urgente para triagem.",
    "id_triagem": 142,
    "idade": 15,
    "nome_completo": "Triagem de Teste Prompt Nove",
    "observacoes": "Registro sintetico criado pelo Prompt 09",
    "prioridade": "alta",
    "status": "em análise"
  },
  "message": "Triagem encontrada.",
  "status": true
}
```

**Resposta — 404 (não encontrada):** `{"status": false, "code": 404, "message": "Triagem não encontrada.", "data": null}`

---

#### `POST /api/triagens/`

Cria nova triagem. A triagem nasce com `status = "em análise"` (atribuído pelo banco via `DEFAULT`).

**Payload de entrada (campos obrigatórios):**

```json
{
  "nome_completo": "Nome Sobrenome",
  "cpf": "99988877766",
  "idade": 15,
  "descricao_caso": "Descrição com no mínimo 10 e no máximo 300 caracteres.",
  "prioridade": "alta"
}
```

**Campo opcional:** `observacoes` (string, até 300 caracteres).

**Resposta — 200 OK:** retorna o objeto da triagem criada (mesmo formato do `GET /<id>`).

> **Nota:** o módulo `criar_triagem()` retorna internamente o resultado de `buscar_triagem_por_id()`, que produz `code: 200`. Por essa razão, a criação bem-sucedida retorna 200 em vez de 201. Isso é um comportamento conhecido do módulo da Sprint 4, preservado intencionalmente nesta etapa.

**Resposta — 400 (payload ausente):** `{"status": false, "code": 400, "message": "Payload JSON ausente ou inválido.", "data": null, "erro": []}`

**Resposta — 400 (campos inválidos):** `{"status": false, "code": 400, "message": "Existem erros de validação nos dados da triagem.", "data": null, "erro": [{"campo": "...", "erro": "..."}]}`

**Resposta — 409 (CPF duplicado):** `{"status": false, "code": 409, "message": "Já existe uma triagem com este CPF.", "data": null}`

---

#### `PUT /api/triagens/<id>`

Atualiza campos editáveis de uma triagem. Só é permitido se o `status` da triagem for `"em análise"`.

**Campos editáveis:** `nome_completo`, `idade`, `descricao_caso`, `prioridade`, `observacoes`. O campo `cpf` não é editável.

**Payload de exemplo:**

```json
{
  "prioridade": "baixa",
  "descricao_caso": "Adolescente com dor de dente persistente e necessidade de avaliacao complementar e acompanhamento."
}
```

**Resposta — 200 OK:** retorna o objeto da triagem atualizada.

**Resposta — 409 (triagem não editável):** `{"status": false, "code": 409, "message": "Só é possível atualizar triagens com status 'em análise'.", "data": null}`

---

#### `DELETE /api/triagens/<id>`

Exclui uma triagem. Bloqueado se já houver paciente vinculado.

**Parâmetros de path:** `id` — inteiro positivo.

**Resposta — 200 OK (payload real capturado):**

```json
{
  "code": 200,
  "data": null,
  "message": "Triagem excluída com sucesso.",
  "status": true
}
```

**Resposta — 409 (paciente vinculado):** `{"status": false, "code": 409, "message": "Não é possível excluir esta triagem pois já existe um paciente vinculado a ela.", "data": null}`

---

### 5.2 Triagens — Aprovação e Reprovação (Prompt 10)

Blueprint: `src/rotas/triagens.py` | Módulo: `src/modulos/triagens.py`

#### `PATCH /api/triagens/<id>/aprovar`

Aprova uma triagem. Só é permitido se o `status` atual for `"em análise"`.

**Parâmetros de path:** `id` — inteiro positivo. **Body:** não utilizado.

**Resposta — 200 OK:**

```json
{
  "code": 200,
  "data": null,
  "message": "Triagem aprovada com sucesso. Prossiga para o cadastro do paciente.",
  "status": true
}
```

**Resposta — 409 (triagem não está em análise):**

```json
{
  "code": 409,
  "data": null,
  "message": "Triagem não pode ser aprovada pois está com status 'aprovada'.",
  "status": false
}
```

> A mensagem 409 inclui o status atual da triagem na interpolação — ex.: `"... com status 'reprovada'."` quando a triagem já foi reprovada.

**Resposta — 404 (ID inexistente):** `{"status": false, "code": 404, "message": "Triagem não encontrada.", "data": null}`

---

#### `PATCH /api/triagens/<id>/reprovar`

Reprova uma triagem. Só é permitido se o `status` atual for `"em análise"`.

**Parâmetros de path:** `id` — inteiro positivo. **Body:** não utilizado.

**Resposta — 200 OK:**

```json
{
  "code": 200,
  "data": null,
  "message": "Triagem reprovada com sucesso.",
  "status": true
}
```

**Resposta — 409 (triagem não está em análise):** `{"status": false, "code": 409, "message": "Triagem não pode ser reprovada pois está com status 'reprovada'.", "data": null}`

**Resposta — 404 (ID inexistente):** `{"status": false, "code": 404, "message": "Triagem não encontrada.", "data": null}`

---

### 5.3 Triagens — Criar Paciente (Lote 11-13)

Blueprint: `src/rotas/triagens.py` | Módulo: `src/modulos/pacientes.py`

#### `POST /api/triagens/<id>/paciente`

Cria um paciente a partir de uma triagem já aprovada. A rota reside no blueprint de triagens pois o path inicia com `/api/triagens/<id>`.

**Parâmetros de path:** `id` — ID da triagem aprovada.

**Payload de entrada:**

```json
{
  "data_nascimento": "15/03/2010",
  "rg": "123456789",
  "telefone": "11999887766",
  "cep": "01310100",
  "logradouro": "Avenida Paulista",
  "numero": "1000",
  "complemento": "Apto 42",
  "bairro": "Bela Vista",
  "cidade": "Sao Paulo",
  "uf": "SP"
}
```

`complemento` é opcional. `nome_completo`, `cpf` e `idade` são herdados da triagem e não devem ser enviados no payload.

**Resposta — 200 OK:** retorna o objeto do paciente criado (mesmo formato de `GET /api/pacientes/<id>`).

**Resposta — 409 (triagem não aprovada):** `{"status": false, "code": 409, "message": "A triagem precisa estar com status 'aprovada' para criar um paciente.", "data": null}`

**Resposta — 409 (paciente duplicado):** `{"status": false, "code": 409, "message": "Já existe um paciente vinculado a esta triagem.", "data": null}`

**Resposta — 404 (triagem não encontrada):** `{"status": false, "code": 404, "message": "Triagem não encontrada.", "data": null}`

---

### 5.4 Pacientes (Lote 11-13)

Blueprint: `src/rotas/pacientes.py` | Módulo: `src/modulos/pacientes.py`

#### `GET /api/pacientes/`

Retorna todos os pacientes cadastrados, ordenados por `ID_PACIENTE`.

**Parâmetros:** nenhum.

**Resposta — 200 OK:** `data` é um array de objetos paciente (pode estar vazio).

---

#### `GET /api/pacientes/sem-dentista`

Retorna pacientes sem dentista vinculado (`ID_DENTISTA IS NULL`).

**Parâmetros:** nenhum.

**Resposta — 200 OK:** `data` é um array de objetos paciente (pode estar vazio).

---

#### `GET /api/pacientes/com-dentista`

Retorna pacientes com dentista vinculado (`ID_DENTISTA IS NOT NULL`).

**Parâmetros:** nenhum.

**Resposta — 200 OK:** `data` é um array de objetos paciente (pode estar vazio).

---

#### `GET /api/pacientes/<id>`

Busca paciente por ID. O conversor `<int:id_paciente>` garante 404 automático para IDs não numéricos.

**Parâmetros de path:** `id` — inteiro positivo.

**Resposta — 200 OK:** retorna o objeto do paciente encontrado.

**Resposta — 404 (não encontrado):** `{"status": false, "code": 404, "message": "Paciente não encontrado.", "data": null}`

---

### 5.5 Dentistas (Lote 11-13)

Blueprint: `src/rotas/dentistas.py` | Módulo: `src/modulos/dentistas.py`

#### `GET /api/dentistas/`

Retorna todos os dentistas cadastrados.

**Parâmetros:** nenhum.

**Resposta — 200 OK:** `data` é um array de objetos dentista (pode estar vazio).

---

#### `GET /api/dentistas/com-vagas`

Retorna apenas dentistas com `vagas_disponiveis > 0`.

**Parâmetros:** nenhum.

**Resposta — 200 OK:** `data` é um array de objetos dentista (pode estar vazio se não houver vagas disponíveis).

---

#### `GET /api/dentistas/<id>`

Busca dentista por ID. O conversor `<int:id_dentista>` garante 404 automático para IDs não numéricos.

**Parâmetros de path:** `id` — inteiro positivo.

**Resposta — 200 OK:** retorna o objeto do dentista encontrado.

**Resposta — 404 (não encontrado):** `{"status": false, "code": 404, "message": "Dentista não encontrado.", "data": null}`

---

#### `GET /api/dentistas/<id>/pacientes`

Retorna todos os pacientes atualmente vinculados a um dentista específico.

**Parâmetros de path:** `id` — ID do dentista.

**Resposta — 200 OK:** `data` é um array de objetos paciente (pode estar vazio se o dentista não tiver pacientes vinculados).

**Resposta — 404 (dentista não encontrado):** `{"status": false, "code": 404, "message": "Dentista não encontrado.", "data": null}`

---

### 5.6 Associação Paciente-Dentista (Lote 11-13)

Blueprint: `src/rotas/pacientes.py` | Módulos: `src/modulos/associacao.py` e `src/modulos/pacientes.py`

#### `GET /api/pacientes/<id>/sugestao-dentista`

Sugere o dentista mais compatível com o paciente com base em localização e disponibilidade de vagas. O algoritmo prioriza: mesma cidade → mesma UF → qualquer dentista com vaga. Em caso de empate, usa a menor diferença numérica entre CEPs.

**Parâmetros de path:** `id` — ID do paciente.

**Resposta — 200 OK:** retorna o objeto do dentista sugerido.

**Resposta — 404 (paciente não encontrado):** `{"status": false, "code": 404, "message": "Paciente não encontrado.", "data": null}`

**Resposta — 404 (nenhum dentista com vaga):** `{"status": false, "code": 404, "message": "Nenhum dentista com vagas disponíveis encontrado.", "data": null}`

---

#### `PATCH /api/pacientes/<id>/dentista`

Vincula um dentista ao paciente, decrementando `vagas_disponiveis` do dentista escolhido. Suporta reassociação: se o paciente já tiver um dentista vinculado, a vaga do dentista anterior é restaurada antes do novo vínculo ser criado.

**Parâmetros de path:** `id` — ID do paciente.

**Payload de entrada:**

```json
{ "id_dentista": 1 }
```

**Resposta — 200 OK:** retorna o objeto do paciente atualizado com o novo dentista vinculado.

**Resposta — 400 (campo ausente):** `{"status": false, "code": 400, "message": "Campo 'id_dentista' é obrigatório.", "data": null, "erro": []}`

**Resposta — 400 (tipo inválido):** `{"status": false, "code": 400, "message": "Campo 'id_dentista' deve ser um inteiro positivo.", "data": null, "erro": []}`

**Resposta — 409 (dentista sem vagas):** `{"status": false, "code": 409, "message": "Este dentista não possui vagas disponíveis.", "data": null}`

**Resposta — 404 (paciente ou dentista não encontrado):** `{"status": false, "code": 404, "message": "Paciente não encontrado." | "Dentista não encontrado.", "data": null}`

---

## 6. Endpoints planejados

São **3 endpoints planejados** restantes: 2 de consultas filtradas de triagens e 1 de endereços via ViaCEP.

### Triagens — Consultas filtradas (pendentes)

| Método e Path | Finalidade | Etapa prevista |
|---|---|---|
| `GET /api/triagens/status/<status>` | Filtrar triagens por status | Prompt 14 |
| `GET /api/triagens/prioridade/<prioridade>` | Filtrar triagens por prioridade | Prompt 14 |

> Esses dois endpoints realizam `SELECT ... WHERE` com parâmetro de path em vez de retornar todos os registros. A lógica reside em `src/modulos/consultas.py` (`consultar_triagens_por_status` e `consultar_triagens_por_prioridade`).

### Endereços

| Método e Path | Finalidade | Etapa prevista |
|---|---|---|
| `GET /api/enderecos/cep/<cep>` | Consultar endereço via ViaCEP | Prompt 15 |

> A numeração dos prompts é referência do roadmap e pode ser ajustada conforme o ritmo de implementação.

---

## 7. Valores aceitos para campos de domínio

Confirmados em `src/apoio/validators.py` e nas constraints `CHECK` de `docs/scripts_oracle.txt`. As duas fontes estão em acordo.

| Campo | Valores aceitos | Observação |
|---|---|---|
| `status` (triagem) | `"em análise"`, `"aprovada"`, `"reprovada"` | Default no banco: `"em análise"` |
| `prioridade` (triagem) | `"baixa"`, `"média"`, `"alta"` | Case-insensitive na entrada; normalizado para minúsculas |
| `idade` (triagem/paciente) | 11 a 17 (inclusive) | Faixa etária do Projeto Nora |
| `cpf` | 11 dígitos numéricos | Máscaras aceitas, dígitos extraídos; verificador de dígito não implementado |
| `cep` | 8 dígitos numéricos | Máscaras aceitas, dígitos extraídos |
| `telefone` | 10 ou 11 dígitos numéricos | 10 dígitos = fixo com DDD; 11 = celular com DDD |
| `uf` | Sigla de 2 letras (ex: `SP`, `RJ`) | Convertido para maiúsculas; não validado contra lista oficial de UFs |
| `rg` | 5 a 14 caracteres alfanuméricos | Sem validação de formato por estado |
| `data_nascimento` | Formato `DD/MM/AAAA` | Deve gerar idade entre 11 e 17 anos; não pode ser data futura |
| `descricao_caso` | String, 10 a 300 caracteres | Obrigatória na criação de triagem |
| `observacoes` | String, até 300 caracteres | Opcional |

---

## 8. Fluxo recomendado para o front-end

Quando todos os endpoints estiverem implementados, o fluxo central de uso da API segue esta sequência:

1. **Verificar saúde da API** com `GET /api/health` — confirma que o servidor está ativo antes de qualquer operação.
2. **Criar uma triagem** com `POST /api/triagens` — payload deve conter `nome_completo`, `cpf`, `idade`, `descricao_caso`, `prioridade`, e opcionalmente `observacoes`. A triagem nasce com `status = "em análise"`.
3. **Listar triagens** com `GET /api/triagens` para visualizar casos cadastrados; `GET /api/triagens/<id>` para um caso específico.
4. **Aprovar a triagem** com `PATCH /api/triagens/<id>/aprovar` — somente triagens com `status = "em análise"` podem ser aprovadas.
5. **Criar paciente** com `POST /api/triagens/<id>/paciente` — disponível apenas após aprovação; solicita dados complementares (data de nascimento, RG, telefone, endereço).
6. **(Opcional) Consultar CEP** com `GET /api/enderecos/cep/<cep>` para completar automaticamente os campos de endereço do paciente.
7. **Listar dentistas com vagas** com `GET /api/dentistas/com-vagas` para ver quem está disponível.
8. **Sugerir dentista compatível** com `GET /api/pacientes/<id>/sugestao-dentista` — a API retorna o dentista mais próximo por cidade, UF ou CEP com vaga disponível.
9. **Vincular paciente ao dentista** com `PATCH /api/pacientes/<id>/dentista` — body: `{ "id_dentista": N }`. A vaga do dentista é decrementada automaticamente.
10. **Acompanhar pacientes** com `GET /api/pacientes/com-dentista` e `GET /api/pacientes/sem-dentista` para visualizar o estado geral dos atendimentos.

Cada passo retorna JSON no padrão da seção 3: `{ "status", "code", "message", "data" }` em sucesso ou `{ "status", "code", "message", "data": null, "erro": [...] }` em erro.

---

## 9. Observações importantes

- **Estado de construção:** 19 endpoints implementados — `GET /api/health`, as 5 rotas CRUD de triagens, as 2 rotas de aprovação/reprovação, `POST /api/triagens/<id>/paciente`, as 4 rotas de pacientes, as 4 rotas de dentistas e as 2 rotas de associação paciente-dentista. Os 3 restantes (`GET /api/triagens/status/<status>`, `GET /api/triagens/prioridade/<prioridade>` e `GET /api/enderecos/cep/<cep>`) são contrato planejado; requisições a eles retornarão 404 até serem implementados.
- **Terminal legado:** `main.py` e `src/interface/menu.py` permanecem no repositório como referência durante a transição Sprint 4 → API. Não são o produto final da banca.
- **Conexão Oracle:** depende de variáveis de ambiente configuradas antes de iniciar o servidor. Ver `.env.example` na raiz do projeto para os nomes das variáveis. Em deploy no Render, configurar no painel de *Environment Variables*.
- **Credenciais:** nunca versionar o arquivo `.env`. Ele está no `.gitignore` e deve permanecer assim.
- **CORS:** habilitado de forma permissiva (`*`) para desenvolvimento. A restrição às origens reais do front-end será aplicada via variável de ambiente `CORS_ORIGINS` na etapa de integração e deploy.
- **Mensagens de erro:** sempre em português, sem stack trace. Erros internos são registrados no log do servidor (via `logging` da stdlib), invisíveis ao cliente HTTP.
- **Schema Oracle:** o DDL completo das tabelas (`TB_TRIAGEM`, `TB_PACIENTE`, `TB_DENTISTA`) e os dados de seed estão em `docs/scripts_oracle.txt`.

### Conflitos de negócio previstos (409)

Os cenários abaixo não são erros de validação (400) nem erros internos (500) — são violações de regra de estado que devem retornar **409 Conflict**:

| Operação | Condição de conflito |
|---|---|
| `PATCH /api/triagens/<id>/aprovar` | Triagem já está aprovada ou reprovada |
| `PUT /api/triagens/<id>` | Triagem não está com status `"em análise"` |
| `DELETE /api/triagens/<id>` | Triagem já possui paciente vinculado |
| `POST /api/triagens/<id>/paciente` | Triagem não está aprovada |
| `POST /api/triagens/<id>/paciente` | Já existe paciente vinculado a essa triagem |
| `PATCH /api/pacientes/<id>/dentista` | Dentista não possui vagas disponíveis (`vagas_disponiveis = 0`) |
