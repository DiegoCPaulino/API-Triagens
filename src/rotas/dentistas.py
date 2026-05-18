from flask import Blueprint

from src.modulos.dentistas import (
    listar_dentistas, buscar_dentista_por_id,
    listar_dentistas_com_vagas, listar_pacientes_de_um_dentista,
)
from src.apoio.respostas_http import responder_http

# Domínio: dentistas voluntários — consultas e listagem dos pacientes atendidos.
bp_dentistas = Blueprint("dentistas", __name__, url_prefix="/api/dentistas")


@bp_dentistas.route("/", methods=["GET"])
def listar():
    return responder_http(listar_dentistas())


@bp_dentistas.route("/com-vagas", methods=["GET"])
def com_vagas():
    return responder_http(listar_dentistas_com_vagas())


@bp_dentistas.route("/<int:id_dentista>", methods=["GET"])
def buscar(id_dentista):
    return responder_http(buscar_dentista_por_id(id_dentista))


@bp_dentistas.route("/<int:id_dentista>/pacientes", methods=["GET"])
def pacientes_do_dentista(id_dentista):
    return responder_http(listar_pacientes_de_um_dentista(id_dentista))
