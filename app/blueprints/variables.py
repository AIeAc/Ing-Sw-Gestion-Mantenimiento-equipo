from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from psycopg.errors import UniqueViolation

from app.core.database import get_db
from app.repositories import variables

from .auth import login_required, roles_required, validate_csrf

bp = Blueprint("variables", __name__, url_prefix="/variables")
VALID_STATUSES = {"", "ACTIVAS", "INACTIVAS"}


def _form_data(source, creating=False):
    return {
        "codigo": str(source.get("codigo") or "").strip().upper(),
        "nombre": str(source.get("nombre") or "").strip(),
        "unidad": str(source.get("unidad") or "").strip(),
        "descripcion": str(source.get("descripcion") or "").strip(),
        "valor_minimo": str(source.get("valor_minimo") or "").strip(),
        "valor_maximo": str(source.get("valor_maximo") or "").strip(),
        "activo": True
        if creating
        else source.get("activo", "") in (True, "on", "true", "1"),
    }


def _decimal_value(value, field, errors):
    try:
        number = Decimal(value)
    except InvalidOperation:
        errors[field] = "Ingresa un número válido."
        return None
    if not number.is_finite():
        errors[field] = "Ingresa un número finito."
        return None
    if abs(number) > Decimal("999999999999.999999"):
        errors[field] = "El valor excede el máximo permitido."
        return None
    if number.as_tuple().exponent < -6:
        errors[field] = "Usa como máximo seis decimales."
        return None
    return number


def _validate(data):
    errors = {}
    limits = {"codigo": 50, "nombre": 100, "unidad": 30, "descripcion": 255}
    for field in ("codigo", "nombre", "unidad"):
        if not data[field]:
            errors[field] = "Este campo es obligatorio."
    for field, limit in limits.items():
        if len(data[field]) > limit:
            errors[field] = f"Usa {limit} caracteres o menos."

    minimum = _decimal_value(data["valor_minimo"], "valor_minimo", errors)
    maximum = _decimal_value(data["valor_maximo"], "valor_maximo", errors)
    if minimum is not None and maximum is not None and minimum >= maximum:
        errors["valor_maximo"] = "El máximo debe ser mayor que el mínimo."
    if errors:
        return None, errors
    cleaned = data.copy()
    cleaned["valor_minimo"] = minimum
    cleaned["valor_maximo"] = maximum
    cleaned["descripcion"] = data["descripcion"] or None
    return cleaned, {}


@bp.get("")
@login_required
def list_variables():
    search = request.args.get("q", "").strip()[:100]
    status = request.args.get("estado", "").strip()
    if status not in VALID_STATUSES:
        status = ""
    return render_template(
        "variables/list.html",
        variable_items=variables.list_variables(search, status),
        filters={"q": search, "estado": status},
    )


@bp.route("/nueva", methods=("GET", "POST"))
@roles_required("Administrador")
def create_variable():
    data = _form_data(request.form, True)
    errors = {}
    if request.method == "POST":
        validate_csrf()
        cleaned, errors = _validate(data)
        if not errors:
            try:
                variables.create_variable(cleaned)
            except UniqueViolation:
                get_db().rollback()
                errors["codigo"] = "El código o nombre ya está registrado."
            else:
                flash("Variable operativa creada correctamente.", "success")
                return redirect(url_for("variables.list_variables"))
    return render_template(
        "variables/form.html", data=data, errors=errors, mode="create"
    )


@bp.route("/<int:variable_id>/editar", methods=("GET", "POST"))
@roles_required("Administrador")
def edit_variable(variable_id):
    item = variables.find_variable(variable_id)
    if item is None:
        abort(404)
    data = _form_data(request.form if request.method == "POST" else item)
    errors = {}
    if request.method == "POST":
        validate_csrf()
        cleaned, errors = _validate(data)
        if not errors:
            try:
                variables.update_variable(variable_id, cleaned)
            except UniqueViolation:
                get_db().rollback()
                errors["codigo"] = "El código o nombre ya está registrado."
            else:
                flash("Variable operativa actualizada correctamente.", "success")
                return redirect(url_for("variables.list_variables"))
    return render_template(
        "variables/form.html",
        data=data,
        errors=errors,
        mode="edit",
        item=item,
    )


def init_app(app):
    app.register_blueprint(bp)
