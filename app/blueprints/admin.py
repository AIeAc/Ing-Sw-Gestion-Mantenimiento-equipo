import re

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from psycopg.errors import UniqueViolation
from werkzeug.security import generate_password_hash

from app.core.database import get_db
from app.repositories import users

from .auth import roles_required, validate_csrf

bp = Blueprint("admin", __name__, url_prefix="/usuarios")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _form_data(source, include_password=False):
    data = {
        "nombre": source.get("nombre", "").strip(),
        "apellidos": source.get("apellidos", "").strip(),
        "correo": source.get("correo", "").strip().lower(),
        "id_rol": str(source.get("id_rol", "")).strip(),
        "activo": source.get("activo", "") in (True, "on", "true", "1"),
    }
    if include_password:
        data["contrasena"] = source.get("contrasena", "")
        data["confirmacion"] = source.get("confirmacion", "")
    return data


def _validate(data, include_password=False):
    errors = {}
    if not data["nombre"]:
        errors["nombre"] = "Ingresa el nombre."
    elif len(data["nombre"]) > 100:
        errors["nombre"] = "Usa 100 caracteres o menos."
    if not data["apellidos"]:
        errors["apellidos"] = "Ingresa los apellidos."
    elif len(data["apellidos"]) > 150:
        errors["apellidos"] = "Usa 150 caracteres o menos."
    if not EMAIL_PATTERN.fullmatch(data["correo"]):
        errors["correo"] = "Ingresa un correo válido."
    elif len(data["correo"]) > 254:
        errors["correo"] = "Usa 254 caracteres o menos."

    try:
        role_id = int(data["id_rol"])
    except (TypeError, ValueError):
        errors["id_rol"] = "Selecciona un rol."
        role_id = None
    if role_id is not None and not users.role_exists(role_id):
        errors["id_rol"] = "Selecciona un rol activo."

    if include_password:
        if len(data["contrasena"]) < 10:
            errors["contrasena"] = "Usa al menos 10 caracteres."
        elif data["contrasena"] != data["confirmacion"]:
            errors["confirmacion"] = "Las contraseñas no coinciden."

    if errors:
        return None, errors
    cleaned = data.copy()
    cleaned["id_rol"] = role_id
    return cleaned, {}


@bp.get("")
@roles_required("Administrador")
def list_users():
    return render_template("admin/users.html", users=users.list_users())


@bp.route("/nuevo", methods=("GET", "POST"))
@roles_required("Administrador")
def create_user():
    data = _form_data(request.form, True) if request.method == "POST" else {
        "nombre": "",
        "apellidos": "",
        "correo": "",
        "id_rol": "",
        "activo": True,
        "contrasena": "",
        "confirmacion": "",
    }
    errors = {}
    if request.method == "POST":
        validate_csrf()
        cleaned, errors = _validate(data, True)
        if not errors:
            try:
                users.create_user(
                    cleaned, generate_password_hash(cleaned["contrasena"])
                )
            except UniqueViolation:
                get_db().rollback()
                errors["correo"] = "Ese correo ya está registrado."
            else:
                flash("Usuario creado correctamente.", "success")
                return redirect(url_for("admin.list_users"))

    return render_template(
        "admin/user_form.html",
        data=data,
        errors=errors,
        roles=users.list_active_roles(),
        mode="create",
    )


@bp.route("/<int:user_id>/editar", methods=("GET", "POST"))
@roles_required("Administrador")
def edit_user(user_id):
    user = users.find_user_by_id(user_id)
    if user is None:
        abort(404)

    data = _form_data(request.form if request.method == "POST" else user)
    errors = {}
    if request.method == "POST":
        validate_csrf()
        cleaned, errors = _validate(data)
        if user_id == g.user["id_usuario"] and not data["activo"]:
            errors["activo"] = "No puedes desactivar tu propia cuenta."
        if (
            user_id == g.user["id_usuario"]
            and str(user["id_rol"]) != data["id_rol"]
        ):
            errors["id_rol"] = "No puedes cambiar el rol de tu propia cuenta."

        if not errors:
            try:
                users.update_user(user_id, cleaned)
            except UniqueViolation:
                get_db().rollback()
                errors["correo"] = "Ese correo ya está registrado."
            else:
                flash("Usuario actualizado correctamente.", "success")
                return redirect(url_for("admin.list_users"))

    return render_template(
        "admin/user_form.html",
        data=data,
        errors=errors,
        roles=users.list_active_roles(),
        mode="edit",
        edited_user=user,
    )


def init_app(app):
    app.register_blueprint(bp)
