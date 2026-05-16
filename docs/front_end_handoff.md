# Front-end Handoff — Projeto Nora API

## URLs base

| Ambiente | URL |
|---|---|
| Local (desenvolvimento) | `http://localhost:5000` |
| Render (produção) | A definir após deploy — preencher aqui após publicação |

## CORS

CORS está habilitado para todas as origens (`*`) na versão atual. Antes do deploy, configurar a variável `CORS_ORIGINS` no Render com a URL real do front-end.

## Formato padrão de resposta

**Sucesso:**
```json
{
  "status": true,
  "code": 200,
  "message": "Mensagem em português.",
  "data": { }
}
```

**Erro:**
```json
{
  "status": false,
  "code": 400,
  "message": "Mensagem geral do erro.",
  "data": null,
  "erro": [
    { "campo": "nome_campo", "erro": "Descrição do problema." }
  ]
}
```

**Tratamento genérico recomendado:**
- Mostrar `message` ao usuário quando `status === false`.
- Iterar `erro[]` para exibir erros por campo (formulários).
- Logar o response completo para debug.

---

## Endpoints por domínio

### Saúde

| Endpoint | Método | Resposta sucesso |
|---|---|---|
| `/api/health` | GET | 200 — status da API |

### Triagens

| Endpoint | Método | Payload | Resposta sucesso | Erros possíveis |
|---|---|---|---|---|
| `/api/triagens/` | GET | — | 200 + array | — |
| `/api/triagens/<id>` | GET | — | 200 + objeto | 404 |
| `/api/triagens/` | POST | JSON (ver abaixo) | **201** + objeto | 400, 409 |
| `/api/triagens/<id>` | PUT | JSON parcial | 200 + objeto | 400, 404, 409 |
| `/api/triagens/<id>` | DELETE | — | 200 | 404, 409 |
| `/api/triagens/<id>/aprovar` | PATCH | sem body | 200 | 404, 409 |
| `/api/triagens/<id>/reprovar` | PATCH | sem body | 200 | 404, 409 |
| `/api/triagens/<id>/paciente` | POST | JSON (ver abaixo) | **201** + objeto | 400, 404, 409 |
| `/api/triagens/status/<status>` | GET | — | 200 + array | 400 (status inválido) |
| `/api/triagens/prioridade/<prioridade>` | GET | — | 200 + array | 400 (prioridade inválida) |

**Payload POST /api/triagens/:**
```json
{
  "nome_completo": "Nome Sobrenome",
  "cpf": "99988877766",
  "idade": 15,
  "descricao_caso": "Descrição com 10 a 300 caracteres.",
  "prioridade": "alta",
  "observacoes": "Opcional."
}
```

**Payload POST /api/triagens/\<id\>/paciente:**
```json
{
  "data_nascimento": "10/03/2011",
  "rg": "123456789",
  "telefone": "11999887766",
  "cep": "01310100",
  "logradouro": "Avenida Paulista",
  "numero": "900",
  "complemento": "Apto 42 (opcional)",
  "bairro": "Bela Vista",
  "cidade": "Sao Paulo",
  "uf": "SP"
}
```

### Pacientes

| Endpoint | Método | Payload | Resposta sucesso | Erros possíveis |
|---|---|---|---|---|
| `/api/pacientes/` | GET | — | 200 + array | — |
| `/api/pacientes/<id>` | GET | — | 200 + objeto | 404 |
| `/api/pacientes/sem-dentista` | GET | — | 200 + array | — |
| `/api/pacientes/com-dentista` | GET | — | 200 + array | — |
| `/api/pacientes/<id>/sugestao-dentista` | GET | — | 200 + objeto (ver seção especial) | 404 |
| `/api/pacientes/<id>/dentista` | PATCH | `{"id_dentista": N}` | 200 | 400, 404, 409 |

### Dentistas

| Endpoint | Método | Resposta sucesso | Erros possíveis |
|---|---|---|---|
| `/api/dentistas/` | GET | 200 + array | — |
| `/api/dentistas/<id>` | GET | 200 + objeto | 404 |
| `/api/dentistas/com-vagas` | GET | 200 + array | — |
| `/api/dentistas/<id>/pacientes` | GET | 200 + array | 404 |

### Endereços

| Endpoint | Método | Resposta sucesso | Erros possíveis |
|---|---|---|---|
| `/api/enderecos/cep/<cep>` | GET | 200 + objeto endereço | 400, 404, 502, 503, 504 |

---

## Contrato especial: GET /api/pacientes/\<id\>/sugestao-dentista

Este é o endpoint de maior valor para a banca — retorna o dentista mais adequado com explicação do método usado.

### Campos da resposta `data`

| Campo | Tipo | Descrição |
|---|---|---|
| `paciente` | object | Resumo do paciente |
| `dentista_sugerido` | object \| null | Dentista sugerido; `null` quando nenhum disponível |
| `distancia_km` | float \| null | Distância em km (linha reta); `null` no fallback |
| `metodo_calculo` | string | `"nominatim_haversine"`, `"cep_fallback"` ou `"sem_dentista_disponivel"` |
| `criterio_fallback` | string \| null | `null` no cálculo real; `"mesma_cidade"`, `"mesma_uf"`, `"cep_aproximado"` ou `"qualquer_com_vaga"` no fallback |
| `observacao` | string | Texto explicativo sobre o método e seus limites |
| `diagnostico_calculo` | object | Detalhes internos do pipeline |

### Lógica de renderização no front-end

```js
switch (data.metodo_calculo) {
  case "nominatim_haversine":
    // Exibir: distância calculada
    // Mostrar: data.distancia_km + " km (linha reta aproximada)"
    // Ocultar: campo de critério de fallback
    break;

  case "cep_fallback":
    // Exibir: sugestão por aproximação
    // Ocultar: campo de distância (null)
    // Mostrar tradução de criterio_fallback:
    const traducoes = {
      "mesma_cidade": "Sugestão por mesma cidade — distância não calculada",
      "mesma_uf": "Sugestão por mesmo estado — distância não calculada",
      "cep_aproximado": "Sugestão por CEP aproximado — distância não calculada",
      "qualquer_com_vaga": "Sugestão por disponibilidade — distância não calculada"
    };
    // Mostrar: traducoes[data.criterio_fallback]
    break;

  case "sem_dentista_disponivel":
    // Nenhum dentista disponível — mostrar mensagem informativa
    // Não exibir cartão de dentista
    // Sugerir que o usuário tente novamente mais tarde
    break;
}
```

### Exemplos de resposta

**Sucesso com distância calculada (nominatim_haversine):**
```json
{
  "status": true, "code": 200, "message": "Dentista sugerido com sucesso.",
  "data": {
    "paciente": { "id_paciente": 12, "nome": "Lucas Santos", "cidade": "São Paulo", "uf": "SP", "cep": "01310100" },
    "dentista_sugerido": { "id_dentista": 3, "nome": "Dra. Ana Paula Ferreira", "especialidade": "Ortodontia", "cidade": "São Paulo", "uf": "SP", "cep": "01310100", "vagas_disponiveis": 4 },
    "distancia_km": 4.27,
    "metodo_calculo": "nominatim_haversine",
    "criterio_fallback": null,
    "observacao": "Distância aproximada em linha reta via OpenStreetMap/Nominatim. Não considera rota viária, trânsito ou tempo de deslocamento."
  }
}
```

**Fallback (Nominatim indisponível):**
```json
{
  "status": true, "code": 200, "message": "Dentista sugerido por fallback de proximidade.",
  "data": {
    "dentista_sugerido": { "id_dentista": 3, "nome": "Dra. Ana Paula Ferreira", "cidade": "São Paulo", "uf": "SP", "cep": "01310100", "vagas_disponiveis": 4 },
    "distancia_km": null,
    "metodo_calculo": "cep_fallback",
    "criterio_fallback": "mesma_cidade",
    "observacao": "Geocodificação indisponível; sugestão feita por cidade, UF e aproximação de CEP. Distância real não calculada."
  }
}
```

---

## Fluxo de telas recomendado

1. **Tela inicial / dashboard** → listar triagens (`GET /api/triagens/`)
2. **Formulário de nova triagem** → `POST /api/triagens/`
3. **Detalhe da triagem** → aprovar/reprovar (`PATCH /aprovar` ou `/reprovar`)
4. **Formulário de cadastro do paciente** → preencher endereço com `GET /api/enderecos/cep/<cep>` → `POST /api/triagens/<id>/paciente`
5. **Sugestão de dentista** → `GET /api/pacientes/<id>/sugestao-dentista` → exibir resultado com `metodo_calculo`
6. **Confirmação do vínculo** → `PATCH /api/pacientes/<id>/dentista`
7. **Dashboard de acompanhamento** → `GET /api/pacientes/com-dentista` e `GET /api/pacientes/sem-dentista`

---

## Observações

- O campo `Content-Type: application/json` é obrigatório em todas as requisições com body.
- IDs são inteiros positivos. Enviar string ou negativo retorna 400 ou 404.
- Geocodificação pode demorar até ~6 segundos (5s timeout Nominatim + processamento). Exibir loading no Passo 5.
- A distância retornada é **aproximada em linha reta**. Não representa tempo de deslocamento, rota ou transporte público.
- Dados de geocodificação: © OpenStreetMap contributors, via Nominatim.
- Dados de CEP: ViaCEP (viacep.com.br).
