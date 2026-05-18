from flask import Blueprint, request

from src.modulos.pacientes import (
    listar_pacientes, buscar_paciente_por_id,
    listar_pacientes_sem_dentista, listar_pacientes_com_dentista,
    vincular_dentista_ao_paciente,
)
from src.modulos.associacao import sugerir_dentista_para_paciente
from src.apoio.respostas_http import responder_http
from src.apoio.utils import gerar_resposta

# Domínio: paciente criado a partir de triagem aprovada — consultas, vínculo com dentista
# e sugestão geográfica de dentista (Nominatim + Haversine com fallback por CEP).
bp_pacientes = Blueprint("pacientes", __name__, url_prefix="/api/pacientes")


@bp_pacientes.route("/", methods=["GET"])
def listar():
    return responder_http(listar_pacientes())


@bp_pacientes.route("/sem-dentista", methods=["GET"])
def sem_dentista():
    return responder_http(listar_pacientes_sem_dentista())


@bp_pacientes.route("/com-dentista", methods=["GET"])
def com_dentista():
    return responder_http(listar_pacientes_com_dentista())


@bp_pacientes.route("/<int:id_paciente>", methods=["GET"])
def buscar(id_paciente):
    return responder_http(buscar_paciente_por_id(id_paciente))


@bp_pacientes.route("/<int:id_paciente>/sugestao-dentista", methods=["GET"])
def sugestao_dentista(id_paciente):
    return responder_http(sugerir_dentista_para_paciente(id_paciente))


@bp_pacientes.route("/<int:id_paciente>/dentista", methods=["PATCH"])
def vincular_dentista(id_paciente):
    payload = request.get_json(silent=True)
    if payload is None:
        return responder_http(gerar_resposta(False, 400, "Payload JSON ausente ou inválido.", error=[]))
    id_dentista = payload.get("id_dentista")
    if id_dentista is None:
        return responder_http(gerar_resposta(False, 400, "Campo 'id_dentista' é obrigatório.", error=[]))
    if not isinstance(id_dentista, int) or isinstance(id_dentista, bool):
        return responder_http(gerar_resposta(False, 400, "Campo 'id_dentista' deve ser um inteiro positivo.", error=[]))
    return responder_http(vincular_dentista_ao_paciente(id_paciente, id_dentista))
