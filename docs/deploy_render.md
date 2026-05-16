# Deploy no Render — Projeto Nora API

## Configurações do serviço

| Campo | Valor |
|---|---|
| **Tipo** | Web Service |
| **Runtime** | Python 3 |
| **Branch** | `main` |
| **Build command** | `pip install -r requirements.txt` |
| **Start command** | `gunicorn app:app` |
| **Health check path** | `/api/health` |

> O `Procfile` na raiz do projeto já define `web: gunicorn app:app`. O Render detecta o `Procfile` automaticamente; o campo "Start command" no painel pode ser deixado em branco.

---

## Variáveis de ambiente obrigatórias

Configurar no painel **Environment > Environment Variables** do serviço no Render. **Nunca commitar esses valores no repositório.**

| Variável | Descrição | Exemplo (fictício) |
|---|---|---|
| `DB_USER` | Usuário Oracle | `rm123456` |
| `DB_PASSWORD` | Senha Oracle | `SenhaSecreta123` |
| `DB_DSN` | Connection string Oracle | `oracle.fiap.com.br:1521/orclpdb` |

**Variáveis opcionais:**

| Variável | Descrição | Default |
|---|---|---|
| `CORS_ORIGINS` | Origens permitidas separadas por vírgula | `*` (aberto) |
| `FLASK_DEBUG` | Ativar debug | `0` (desativado em produção) |
| `PORT` | Porta do servidor | Injetada automaticamente pelo Render |

---

## Checklist de pré-deploy

- [ ] Repositório no GitHub atualizado (branch `main`)
- [ ] `.env` **não** está commitado (verificar `git status` e `.gitignore`)
- [ ] `*.zip` **não** está commitado (`.gitignore` já cobre)
- [ ] `requirements.txt` contém: Flask, flask-cors, gunicorn, oracledb, requests
- [ ] `app.py` usa `os.environ.get("PORT", 5000)` ✓
- [ ] `Procfile` presente na raiz ✓
- [ ] Variáveis `DB_USER`, `DB_PASSWORD`, `DB_DSN` configuradas no painel Render
- [ ] Build executado sem erro
- [ ] `GET /api/health` retorna 200 na URL `.onrender.com`
- [ ] Logs sem credenciais expostas

---

## ⚠ Risco crítico: Oracle externo

O Oracle usado pela FIAP pode **não aceitar conexões externas** vindas do Render. Isso é o risco mais alto do deploy.

**Como validar cedo:**
1. Após fazer o deploy no Render, chamar `GET /api/health` → deve retornar 200 (não depende do Oracle).
2. Chamar `GET /api/triagens/` → se retornar 500, confirmar nos logs que é falha de conexão Oracle.
3. Reportar ao professor/coordenador pedindo liberação da conexão externa para o IP do Render.

---

## Plano B — Demonstração local na banca

Se o Oracle externo bloquear conexão do Render, demonstrar a API localmente:

```bash
# 1. Ativar ambiente virtual
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# 2. Configurar .env (não commitar)
# DB_USER=...
# DB_PASSWORD=...
# DB_DSN=...

# 3. Iniciar o servidor localmente
python app.py

# 4. (Opcional) Expor via ngrok para acesso do front-end remoto
ngrok http 5000
# Usar a URL ngrok como base no front-end durante a banca
```

> `ngrok` é uma ferramenta gratuita para expor localhost temporariamente. Requer criação de conta gratuita em ngrok.com. A URL gerada muda a cada sessão.

---

## Teste de smoke após deploy

```bash
# Verificar que a API está viva
curl https://<seu-app>.onrender.com/api/health

# Listar triagens (requer Oracle acessível)
curl https://<seu-app>.onrender.com/api/triagens/

# Consultar CEP (não requer Oracle)
curl https://<seu-app>.onrender.com/api/enderecos/cep/01310100
```
