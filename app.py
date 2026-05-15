import os

from flask import Flask
from flask_cors import CORS

from src.apoio.utils import gerar_resposta
from src.apoio.respostas_http import responder_http
from src.rotas.triagens import bp_triagens
from src.rotas.pacientes import bp_pacientes
from src.rotas.dentistas import bp_dentistas
from src.rotas.enderecos import bp_enderecos

app = Flask(__name__)

# CORS permissivo por default para desenvolvimento.
# Em produção, setar CORS_ORIGINS="http://localhost:3000,https://nora-front.onrender.com"
# A restrição definitiva por origem virá na etapa de integração com o front-end.
_cors_origins = os.environ.get("CORS_ORIGINS", "*")
if _cors_origins == "*":
    CORS(app)
else:
    CORS(app, resources={r"/api/*": {"origins": [o.strip() for o in _cors_origins.split(",")]}})

app.register_blueprint(bp_triagens)
app.register_blueprint(bp_pacientes)
app.register_blueprint(bp_dentistas)
app.register_blueprint(bp_enderecos)


@app.route("/api/health", methods=["GET"])
def health():
    resposta = gerar_resposta(True, 200, "API do Projeto Nora ativa.", {
        "service": "Projeto Nora API",
        "version": "0.1.0",
    })
    return responder_http(resposta)


@app.errorhandler(404)
def erro_404(_):
    return responder_http(gerar_resposta(False, 404, "Recurso não encontrado.", error=[]))


@app.errorhandler(405)
def erro_405(_):
    return responder_http(gerar_resposta(False, 405, "Método HTTP não permitido para este recurso.", error=[]))


@app.errorhandler(500)
def erro_500(_):
    return responder_http(gerar_resposta(False, 500, "Erro interno do servidor.", error=[]))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
