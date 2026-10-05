from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from psycopg.errors import UniqueViolation

from app.core.database import get_db
from app.repositories import categories

from .auth import roles_required, validate_csrf

bp = Blueprint("classifications", __name__, url_prefix="/clasificaciones")


def _form_data(source):
    return {
        "nombre": str(source.get("nombre") or "").strip(),
        "descripcion": str(source.get("descripcion") or "").strip(),
        "activo": source.get("activo", "") in (True, "on", "true", "1"),
    }


def _validate(data):
    errors = {}
    if not data["nombre"]:
        errors["nombre"] = "Ingresa el nombre de la categoría."
    elif len(data["nombre"]) > 100:
        errors["nombre"] = "Usa 100 caracteres o menos."
    if len(data["descripcion"]) > 255:
        errors["descripcion"] = "Usa 255 caracteres o menos."
    return errors


@bp.get("")
@roles_required("Administrador")
def list_categories():
    return render_template(
        "classifications/list.html",
        categories=categories.list_categories(),
    )


@bp.route("/nueva", methods=("GET", "POST"))
@roles_required("Administrador")
def create_category():
    data = _form_data(request.form) if request.method == "POST" else {
        "nombre": "",
        "descripcion": "",
        "activo": True,
    }
    errors = {}
    if request.method == "POST":
        validate_csrf()
        errors = _validate(data)
        if not errors:
            try:
                categories.create_category(data)
            except UniqueViolation:
                get_db().rollback()
                errors["nombre"] = "Ya existe una categoría con ese nombre."
            else:
                flash("Categoría creada correctamente.", "success")
                return redirect(url_for("classifications.list_categories"))

    return render_template(
        "classifications/form.html", data=data, errors=errors, mode="create"
    )


@bp.route("/<int:category_id>/editar", methods=("GET", "POST"))
@roles_required("Administrador")
def edit_category(category_id):
    category = categories.find_category(category_id)
    if category is None:
        abort(404)

    data = _form_data(request.form if request.method == "POST" else category)
    errors = {}
    if request.method == "POST":
        validate_csrf()
        errors = _validate(data)
        if category["activo"] and not data["activo"] and categories.category_in_use(
            category_id
        ):
            errors["activo"] = (
                "No se puede desactivar porque hay equipos en esta categoría."
            )
        if not errors:
            try:
                categories.update_category(category_id, data)
            except UniqueViolation:
                get_db().rollback()
                errors["nombre"] = "Ya existe una categoría con ese nombre."
            else:
                flash("Categoría actualizada correctamente.", "success")
                return redirect(url_for("classifications.list_categories"))

    return render_template(
        "classifications/form.html",
        data=data,
        errors=errors,
        mode="edit",
        category=category,
    )


def init_app(app):
    app.register_blueprint(bp)
