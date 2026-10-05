from flask import render_template


def _render_error(status_code, title, message):
    return (
        render_template(
            "error.html", status_code=status_code, title=title, message=message
        ),
        status_code,
    )


def bad_request(_error):
    return _render_error(400, "Solicitud no válida", "Actualiza la página e inténtalo de nuevo.")


def forbidden(_error):
    return _render_error(
        403,
        "Acceso restringido",
        "Tu rol no tiene permiso para abrir esta sección.",
    )


def not_found(_error):
    return _render_error(404, "Página no encontrada", "El recurso solicitado no existe.")


def payload_too_large(_error):
    return _render_error(
        413,
        "Archivo demasiado grande",
        "El archivo supera el límite permitido de 2 MB.",
    )


def init_app(app):
    app.register_error_handler(400, bad_request)
    app.register_error_handler(403, forbidden)
    app.register_error_handler(404, not_found)
    app.register_error_handler(413, payload_too_large)
