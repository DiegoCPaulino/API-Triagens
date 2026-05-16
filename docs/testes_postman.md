# Testes Manuais — Projeto Nora API

## Configuração

| Item | Valor |
|---|---|
| URL base (local) | `http://localhost:5000` |
| Header obrigatório | `Content-Type: application/json` |
| Iniciar servidor | `python app.py` (ou `.venv/Scripts/python app.py` no Windows) |

---

## Fluxo de banca (9 passos — executar em ordem)

### Passo 1 — Verificar saúde da API

```
GET http://localhost:5000/api/health
```

**Resposta esperada:** 200 OK
```json
{ "status": true, "code": 200, "message": "API do Projeto Nora ativa.", "data": { "service": "Projeto Nora API" } }
```

---

### Passo 2 — Criar triagem

```
POST http://localhost:5000/api/triagens/
Content-Type: application/json
```

```json
{
  "nome_completo": "Lucas Ferreira dos Santos",
  "cpf": "11122233344",
  "idade": 14,
  "descricao_caso": "Adolescente com dor de dente persistente e necessidade de avaliação odontológica urgente.",
  "prioridade": "alta",
  "observacoes": "Paciente relatou dor há duas semanas."
}
```

**Resposta esperada:** 201 Created — objeto da triagem criada com `status: "em análise"`.

Anote o `id_triagem` retornado — será usado nos passos seguintes.

---

### Passo 3 — Listar triagens

```
GET http://localhost:5000/api/triagens/
```

**Resposta esperada:** 200 OK — array com a triagem criada no Passo 2.

---

### Passo 4 — Aprovar triagem

```
PATCH http://localhost:5000/api/triagens/<id_triagem>/aprovar
```

(sem body)

**Resposta esperada:** 200 OK
```json
{ "status": true, "code": 200, "message": "Triagem aprovada com sucesso. Prossiga para o cadastro do paciente." }
```

---

### Passo 5 — Criar paciente a partir da triagem aprovada

```
POST http://localhost:5000/api/triagens/<id_triagem>/paciente
Content-Type: application/json
```

```json
{
  "data_nascimento": "10/03/2011",
  "rg": "123456789",
  "telefone": "11999887766",
  "cep": "01310100",
  "logradouro": "Avenida Paulista",
  "numero": "900",
  "complemento": "Apto 42",
  "bairro": "Bela Vista",
  "cidade": "Sao Paulo",
  "uf": "SP"
}
```

**Resposta esperada:** 201 Created — objeto do paciente criado. Anote o `id_paciente`.

---

### Passo 6 — Consultar CEP via ViaCEP

```
GET http://localhost:5000/api/enderecos/cep/01310100
```

**Resposta esperada:** 200 OK — retorna logradouro, bairro, cidade, UF.

> Este endpoint é usado pelo front-end para preencher automaticamente os campos de endereço do paciente. Não calcula distância.

---

### Passo 7 — Listar dentistas com vagas

```
GET http://localhost:5000/api/dentistas/com-vagas
```

**Resposta esperada:** 200 OK — lista de dentistas com `vagas_disponiveis > 0`.

---

### Passo 8 — Sugerir dentista para o paciente

```
GET http://localhost:5000/api/pacientes/<id_paciente>/sugestao-dentista
```

**Resposta esperada:** 200 OK

Verificar no response:
- `data.metodo_calculo`: `"nominatim_haversine"` (se Nominatim respondeu) ou `"cep_fallback"` (se houve fallback)
- `data.distancia_km`: número float (ou `null` no fallback)
- `data.criterio_fallback`: `null` ou `"mesma_cidade"` / `"mesma_uf"` / `"cep_aproximado"`
- `data.observacao`: texto explicando o método

Anote o `data.dentista_sugerido.id_dentista` para o Passo 9.

---

### Passo 9 — Vincular paciente ao dentista

```
PATCH http://localhost:5000/api/pacientes/<id_paciente>/dentista
Content-Type: application/json
```

```json
{ "id_dentista": <id_dentista_sugerido> }
```

**Resposta esperada:** 200 OK

---

## Casos de erro recomendados

| Cenário | Endpoint | Resposta esperada |
|---|---|---|
| CEP com 7 dígitos | `GET /api/enderecos/cep/0131010` | 400 — "CEP deve ter 8 dígitos numéricos." |
| CEP não existente | `GET /api/enderecos/cep/00000000` | 404 — "CEP não encontrado." |
| Status inválido | `GET /api/triagens/status/invalido` | 400 — "Status inválido." |
| Prioridade inválida | `GET /api/triagens/prioridade/urgente` | 400 — "Prioridade inválida." |
| Paciente inexistente | `GET /api/pacientes/99999/sugestao-dentista` | 404 — "Paciente não encontrado." |
| Dentista sem vagas | `PATCH /api/pacientes/<id>/dentista` body: `{"id_dentista": <id_sem_vaga>}` | 409 — "Dentista não possui vagas disponíveis." |
| Triagem já aprovada | `PATCH /api/triagens/<id_aprovada>/aprovar` | 409 — "Triagem não pode ser aprovada pois está com status 'aprovada'." |
| Criar paciente sem triagem aprovada | `POST /api/triagens/<id_em_analise>/paciente` | 409 — "Paciente só pode ser criado a partir de triagem com status 'aprovada'." |
| Payload JSON ausente | `POST /api/triagens/` sem body | 400 — "Payload JSON ausente ou inválido." |
| ID não numérico | `GET /api/pacientes/abc` | 404 — Flask retorna 404 via conversor `<int:>` |

---

## Dicas para banca

- **Mostrar o `metodo_calculo`** ao vivo no Passo 8 — este é o diferencial técnico do projeto.
- **Simular fallback**: desligar a rede momentaneamente antes do Passo 8 (ou usar dados de paciente com endereço incompleto) para demonstrar que o sistema continua funcionando com `metodo_calculo: "cep_fallback"`.
- **Filtros**: demonstrar `GET /api/triagens/status/aprovada` e `GET /api/triagens/prioridade/alta` para mostrar consultas filtradas.
- A ordem dos passos acima é o **fluxo central do Projeto Nora** — triagem → aprovação → paciente → sugestão geográfica → vínculo.
