from flask import Blueprint, request

from src.modulos.triagens import (
    listar_triagens, buscar_triagem_por_id,
    criar_triagem, atualizar_triagem, excluir_triagem,
    aprovar_triagem, reprovar_triagem,
)
from src.modulos.pacientes import criar_paciente_a_partir_de_triagem
from src.apoio.respostas_http import responder_http
from src.apoio.utils import gerar_resposta

bp_triagens = Blueprint("triagens", __name__, url_prefix="/api/triagens")


@bp_triagens.route("/", methods=["GET"])
def listar():
    return responder_http(listar_triagens())


@bp_triagens.route("/<int:id_triagem>", methods=["GET"])
def buscar(id_triagem):
    return responder_http(buscar_triagem_por_id(id_triagem))


@bp_triagens.route("/", methods=["POST"])
def criar():
    payload = request.get_json(silent=True)
    if payload is None:
        return responder_http(gerar_resposta(False, 400, "Payload JSON ausente ou inválido.", error=[]))
    return responder_http(criar_triagem(payload))


@bp_triagens.route("/<int:id_triagem>", methods=["PUT"])
def atualizar(id_triagem):
    payload = request.get_json(silent=True)
    if payload is None:
        return responder_http(gerar_resposta(False, 400, "Payload JSON ausente ou inválido.", error=[]))
    return responder_http(atualizar_triagem(id_triagem, payload))


@bp_triagens.route("/<int:id_triagem>", methods=["DELETE"])
def excluir(id_triagem):
    return responder_http(excluir_triagem(id_triagem))


@bp_triagens.route("/<int:id_triagem>/aprovar", methods=["PATCH"])
def aprovar(id_triagem):
    return responder_http(aprovar_triagem(id_triagem))


@bp_triagens.route("/<int:id_triagem>/reprovar", methods=["PATCH"])
def reprovar(id_triagem):
    return responder_http(reprovar_triagem(id_triagem))


@bp_triagens.route("/<int:id_triagem>/paciente", methods=["POST"])
def criar_paciente(id_triagem):
    payload = request.get_json(silent=True)
    if payload is None:
        return responder_http(gerar_resposta(False, 400, "Payload JSON ausente ou inválido.", error=[]))
    return responder_http(criar_paciente_a_partir_de_triagem(id_triagem, payload))
