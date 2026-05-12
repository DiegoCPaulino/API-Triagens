from flask import jsonify

_CODIGOS_VALIDOS = {200, 201, 204, 400, 401, 403, 404, 405, 409, 422, 500, 502, 503, 504}


def responder_http(resposta: dict):
    code = resposta.get("code")
    if not isinstance(code, int) or code not in _CODIGOS_VALIDOS:
        code = 500
    return jsonify(resposta), code
