# Projeto Nora — Back-end Flask/API

**Projeto Banca FIAP** | Disciplina: Computational Thinking Using Python | FIAP — ADS

---

## Identidade do projeto

O Projeto Nora é um sistema de **triagem odontológica para adolescentes de 11 a 17 anos**, desenvolvido originalmente como Sprint 4 Python e evoluído para um back-end Flask/API REST consumido por um front-end separado.

**Domínio:** triagem odontológica → aprovação → cadastro de paciente → sugestão geográfica de dentista voluntário → vínculo.

---

## Diferencial técnico

A sugestão de dentista para o paciente é feita de forma **explicável e defensável**:

1. **Pré-filtragem por cidade/UF/CEP** — seleciona até 5 candidatos mais próximos.
2. **Geocodificação com Nominatim/OpenStreetMap** — converte endereços em coordenadas geográficas.
3. **Cálculo de distância com Haversine** — distância aproximada em linha reta entre paciente e dentista.
4. **Fallback obrigatório** — se Nominatim estiver indisponível (timeout, erro, sem internet), o sistema continua funcionando com sugestão por cidade/UF/CEP e retorna `distancia_km: null` com `metodo_calculo: "cep_fallback"`.
5. **Resposta JSON explicável** — sempre inclui `distancia_km`, `metodo_calculo`, `criterio_fallback` e `observacao`.

> A distância retornada é **aproximada em linha reta**. Não considera rota viária, trânsito ou tempo de deslocamento.
>
> Dados de geocodificação: © OpenStreetMap contributors, via Nominatim. ViaCEP fornecido por viacep.com.br.

---

## Stack

| Tecnologia | Papel |
|---|---|
| Python 3 | Linguagem base |
| Flask + flask-cors | Framework web e CORS |
| gunicorn | WSGI server (deploy no Render) |
| oracledb | Driver Oracle (banco da FIAP) |
| requests | Cliente HTTP (ViaCEP e Nominatim) |
| math (stdlib) | Fórmula de Haversine |
| Oracle Database | Persistência de dados |
| ViaCEP | Complemento de endereço (logradouro, bairro, cidade, UF) |
| Nominatim/OpenStreetMap | Geocodificação (endereço → coordenadas) |
| Render | Plataforma de deploy |

---

## Endpoints principais (22 no total)

| Grupo | Endpoints |
|---|---|
| Saúde | `GET /api/health` |
| Triagens | `GET /api/triagens/`, `GET /api/triagens/<id>`, `POST /api/triagens/`, `PUT /api/triagens/<id>`, `DELETE /api/triagens/<id>`, `PATCH /api/triagens/<id>/aprovar`, `PATCH /api/triagens/<id>/reprovar`, `POST /api/triagens/<id>/paciente`, `GET /api/triagens/status/<status>`, `GET /api/triagens/prioridade/<prioridade>` |
| Pacientes | `GET /api/pacientes/`, `GET /api/pacientes/<id>`, `GET /api/pacientes/sem-dentista`, `GET /api/pacientes/com-dentista`, **`GET /api/pacientes/<id>/sugestao-dentista`**, `PATCH /api/pacientes/<id>/dentista` |
| Dentistas | `GET /api/dentistas/`, `GET /api/dentistas/<id>`, `GET /api/dentistas/com-vagas`, `GET /api/dentistas/<id>/pacientes` |
| Endereços | `GET /api/enderecos/cep/<cep>` |

O contrato detalhado de cada endpoint está em [`docs/api_contratos.md`](docs/api_contratos.md).

---

## Como rodar localmente

```bash
# 1. Criar e ativar o ambiente virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar variáveis de ambiente
#    Copie .env.example para .env e preencha com suas credenciais:
#    DB_USER=...
#    DB_PASSWORD=...
#    DB_DSN=oracle.fiap.com.br:1521/ORCL

# 4. Criar tabelas no Oracle (apenas na primeira vez)
#    Execute docs/scripts_oracle.txt no SQL Developer

# 5. Iniciar a API
python app.py
# Servidor disponível em http://localhost:5000

# 6. Verificar saúde
curl http://localhost:5000/api/health
```

---

## Como testar

**Testes automatizados:**

```bash
python -m tests.test_geocodificacao    # Nominatim + Haversine (com mock)
python -m tests.test_associacao        # Pipeline de sugestão (com mock)
python -m tests.test_validators        # Validações
python -m tests.test_exportador_json   # Exportação legada
```

> Zero chamadas reais ao Nominatim nos testes automatizados — `requests.get` é sempre mockado.

**Testes manuais com Postman/Insomnia:**

Importar o fluxo em [`docs/testes_postman.md`](docs/testes_postman.md). O fluxo central tem 9 passos: health → triagem → listar → aprovar → paciente → CEP → dentistas → sugestão → vínculo.

---

## Deploy no Render

Ver [`docs/deploy_render.md`](docs/deploy_render.md) para o passo a passo completo.

| Item | Valor |
|---|---|
| Build command | `pip install -r requirements.txt` |
| Start command | `gunicorn app:app` |
| Health check | `/api/health` |
| Variáveis obrigatórias | `DB_USER`, `DB_PASSWORD`, `DB_DSN` |

> **Risco:** o Oracle da FIAP pode não aceitar conexões externas vindas do Render. Plano B: demonstrar localmente com `python app.py`. Ver `docs/deploy_render.md`.

---

## Documentação adicional

| Arquivo | Conteúdo |
|---|---|
| [`docs/api_contratos.md`](docs/api_contratos.md) | Contrato detalhado dos 22 endpoints com exemplos JSON |
| [`docs/testes_postman.md`](docs/testes_postman.md) | Fluxo de banca (9 passos) + casos de erro |
| [`docs/front_end_handoff.md`](docs/front_end_handoff.md) | Contrato para integração com o front-end, com lógica de renderização |
| [`docs/deploy_render.md`](docs/deploy_render.md) | Configurações de deploy, variáveis de ambiente e plano B |
| [`docs/scripts_oracle.txt`](docs/scripts_oracle.txt) | Schema Oracle (DDL + seed) |

---

## Roteiro de banca (7 passos)

1. **`GET /api/health`** → mostrar que a API está viva e respondendo.
2. **`POST /api/triagens/`** → criar triagem para adolescente (idade entre 11 e 17).
3. **`PATCH /api/triagens/<id>/aprovar`** → aprovar a triagem.
4. **`POST /api/triagens/<id>/paciente`** → criar paciente com endereço completo (demonstrar validação de CEP e data de nascimento).
5. **`GET /api/pacientes/<id>/sugestao-dentista`** → mostrar a resposta com `metodo_calculo`, `distancia_km` e `observacao`. Este é o diferencial técnico — explicar Nominatim + Haversine ao vivo.
6. **`PATCH /api/pacientes/<id>/dentista`** → confirmar o vínculo paciente-dentista.
7. **(Bônus) Demonstrar fallback** → simular indisponibilidade da rede e mostrar que a API retorna 200 com `metodo_calculo: "cep_fallback"` em vez de 500. Isso demonstra resiliência.

---

## Origem do projeto

Este repositório é a evolução da Sprint 4 Python (entrega acadêmica individual já finalizada). O terminal legado (`main.py`, `src/interface/menu.py`) permanece no repositório como referência e não é o produto final da banca.

| Sprint 4 | Banca FIAP |
|---|---|
| Aplicação de terminal | Back-end Flask/API REST |
| `python main.py` | `python app.py` (ou gunicorn) |
| Associação por CEP (simplificação acadêmica) | Nominatim + Haversine + fallback CEP |
