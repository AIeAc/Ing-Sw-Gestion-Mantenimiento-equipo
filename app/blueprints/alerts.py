from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.repositories import alerts

from .auth import login_required, validate_csrf

bp = Blueprint("alerts", __name__, url_prefix="/alertas")
ALERT_STATUSES = (
    ("PENDIENTE", "Pendiente"),
    ("ATENDIDA", "Atendida"),
    ("DESCARTADA", "Descartada"),
)
ALERT_TYPES = (
    ("LIMITE_INFERIOR", "Límite inferior"),
    ("LIMITE_SUPERIOR", "Límite superior"),
)
RESOLUTION_STATUSES = {"ATENDIDA", "DESCARTADA"}


@bp.get("")
@login_required
def list_alerts():
    status = request.args.get("estado", "").strip()
    alert_type = request.args.get("tipo", "").strip()
    if status not in {value for value, _label in ALERT_STATUSES}:
        status = ""
    if alert_type not in {value for value, _label in ALERT_TYPES}:
        alert_type = ""
    return render_template(
        "alerts/list.html",
        alert_items=alerts.list_alerts(status, alert_type),
        statuses=ALERT_STATUSES,
        types=ALERT_TYPES,
        filters={"estado": status, "tipo": alert_type},
    )


@bp.route("/<int:alert_id>", methods=("GET", "POST"))
@login_required
def alert_detail(alert_id):
    item = alerts.find_alert(alert_id)
    if item is None:
        abort(404)
    errors = {}
    data = {
        "estado": request.form.get("estado", "ATENDIDA").strip(),
        "observaciones": request.form.get("observaciones", "").strip(),
    }
    if request.method == "POST":
        validate_csrf()
        if item["estado"] != "PENDIENTE":
            flash("La alerta ya fue atendida anteriormente.", "warning")
            return redirect(url_for("alerts.alert_detail", alert_id=alert_id))
        if data["estado"] not in RESOLUTION_STATUSES:
            errors["estado"] = "Selecciona una resolución válida."
        if len(data["observaciones"]) > 2000:
            errors["observaciones"] = "Usa 2000 caracteres o menos."
        if not errors:
            updated = alerts.resolve_alert(
                alert_id,
                data["estado"],
                data["observaciones"] or None,
                g.user["id_usuario"],
            )
            if updated:
                flash("Alerta actualizada correctamente.", "success")
            else:
                flash("La alerta ya no estaba pendiente.", "warning")
            return redirect(url_for("alerts.alert_detail", alert_id=alert_id))

    return render_template(
        "alerts/detail.html",
        item=item,
        data=data,
        errors=errors,
        statuses=dict(ALERT_STATUSES),
        types=dict(ALERT_TYPES),
    )


def init_app(app):
    app.register_blueprint(bp)
