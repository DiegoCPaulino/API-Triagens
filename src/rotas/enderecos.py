from flask import Blueprint

from src.servicos.api import consultar_cep
from src.apoio.respostas_http import responder_http

bp_enderecos = Blueprint("enderecos", __name__, url_prefix="/api/enderecos")


@bp_enderecos.route("/cep/<string:cep>", methods=["GET"])
def buscar_cep(cep):
    return responder_http(consultar_cep(cep))
