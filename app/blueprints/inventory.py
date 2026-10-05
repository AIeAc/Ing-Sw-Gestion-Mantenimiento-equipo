from datetime import date

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app.core.database import get_db
from app.repositories import categories, equipment

from .auth import login_required, validate_csrf

bp = Blueprint("inventory", __name__, url_prefix="/equipos")

EQUIPMENT_STATUSES = (
    ("OPERATIVO", "Operativo"),
    ("FUERA_DE_SERVICIO", "Fuera de servicio"),
    ("DADO_DE_BAJA", "Dado de baja"),
)
VALID_STATUSES = {value for value, _label in EQUIPMENT_STATUSES}


def _clean_optional(value):
    cleaned = value.strip()
    return cleaned or None


def _form_data(source):
    raw_date = source.get("fecha_adquisicion", "")
    return {
        "id_categoria": str(source.get("id_categoria") or "").strip(),
        "codigo_interno": str(source.get("codigo_interno") or "").strip(),
        "nombre": str(source.get("nombre") or "").strip(),
        "marca": str(source.get("marca") or "").strip(),
        "modelo": str(source.get("modelo") or "").strip(),
        "numero_serie": str(source.get("numero_serie") or "").strip(),
        "ubicacion": str(source.get("ubicacion") or "").strip(),
        "estado": str(source.get("estado") or "OPERATIVO").strip(),
        "descripcion": str(source.get("descripcion") or "").strip(),
        "fecha_adquisicion": raw_date.isoformat()
        if isinstance(raw_date, date)
        else str(raw_date).strip(),
    }


def _validate_equipment(data):
    errors = {}

    if not data["codigo_interno"]:
        errors["codigo_interno"] = "Ingresa el código interno."
    elif len(data["codigo_interno"]) > 50:
        errors["codigo_interno"] = "Usa 50 caracteres o menos."

    if not data["nombre"]:
        errors["nombre"] = "Ingresa el nombre del equipo."
    elif len(data["nombre"]) > 150:
        errors["nombre"] = "Usa 150 caracteres o menos."

    category_id = None
    try:
        category_id = int(data["id_categoria"])
    except (TypeError, ValueError):
        errors["id_categoria"] = "Selecciona una categoría."
    if category_id is not None and not categories.active_category_exists(
        category_id
    ):
        errors["id_categoria"] = "Selecciona una categoría activa."

    if data["estado"] not in VALID_STATUSES:
        errors["estado"] = "Selecciona un estado válido."

    limits = {
        "marca": 100,
        "modelo": 100,
        "numero_serie": 100,
        "ubicacion": 150,
    }
    for field, limit in limits.items():
        if len(data[field]) > limit:
            errors[field] = f"Usa {limit} caracteres o menos."

    parsed_date = None
    if data["fecha_adquisicion"]:
        try:
            parsed_date = date.fromisoformat(data["fecha_adquisicion"])
        except ValueError:
            errors["fecha_adquisicion"] = "Ingresa una fecha válida."
        else:
            if parsed_date > date.today():
                errors["fecha_adquisicion"] = "La fecha no puede estar en el futuro."

    if errors:
        return None, errors

    cleaned = data.copy()
    cleaned["id_categoria"] = category_id
    cleaned["fecha_adquisicion"] = parsed_date
    for field in ("marca", "modelo", "numero_serie", "ubicacion", "descripcion"):
        cleaned[field] = _clean_optional(data[field])
    return cleaned, {}


@bp.get("")
@login_required
def list_equipment():
    search = request.args.get("q", "").strip()[:100]
    status = request.args.get("estado", "").strip()
    if status not in VALID_STATUSES:
        status = ""

    category_id = None
    raw_category = request.args.get("categoria", "").strip()
    if raw_category:
        try:
            category_id = int(raw_category)
        except ValueError:
            raw_category = ""

    items = equipment.list_equipment(search, category_id, status)
    category_items = categories.list_categories(active_only=True)
    return render_template(
        "inventory/list.html",
        equipment_items=items,
        categories=category_items,
        statuses=EQUIPMENT_STATUSES,
        filters={"q": search, "categoria": raw_category, "estado": status},
    )


@bp.route("/nuevo", methods=("GET", "POST"))
@login_required
def create_equipment():
    category_items = categories.list_categories(active_only=True)
    if not category_items:
        flash(
            "Primero debe existir una categoría activa para registrar equipos.",
            "warning",
        )
        destination = (
            "classifications.create_category"
            if g.user["rol"] == "Administrador"
            else "inventory.list_equipment"
        )
        return redirect(url_for(destination))

    data = _form_data(request.form) if request.method == "POST" else _form_data({})
    errors = {}
    if request.method == "POST":
        validate_csrf()
        cleaned, errors = _validate_equipment(data)
        if not errors:
            try:
                equipment_id = equipment.create_equipment(
                    cleaned, g.user["id_usuario"]
                )
            except UniqueViolation:
                get_db().rollback()
                errors["codigo_interno"] = (
                    "El código interno o número de serie ya está registrado."
                )
            except ForeignKeyViolation:
                get_db().rollback()
                errors["id_categoria"] = "La categoría seleccionada ya no está disponible."
            else:
                flash("Equipo registrado correctamente.", "success")
                return redirect(
                    url_for("inventory.equipment_detail", equipment_id=equipment_id)
                )

    return render_template(
        "inventory/form.html",
        data=data,
        errors=errors,
        categories=category_items,
        statuses=EQUIPMENT_STATUSES,
        mode="create",
    )


@bp.get("/<int:equipment_id>")
@login_required
def equipment_detail(equipment_id):
    item = equipment.find_equipment(equipment_id)
    if item is None:
        abort(404)
    return render_template("inventory/detail.html", item=item)


@bp.route("/<int:equipment_id>/editar", methods=("GET", "POST"))
@login_required
def edit_equipment(equipment_id):
    item = equipment.find_equipment(equipment_id)
    if item is None:
        abort(404)

    category_items = categories.list_categories(active_only=True)
    data = _form_data(request.form if request.method == "POST" else item)
    errors = {}
    if request.method == "POST":
        validate_csrf()
        cleaned, errors = _validate_equipment(data)
        if not errors:
            try:
                equipment.update_equipment(equipment_id, cleaned)
            except UniqueViolation:
                get_db().rollback()
                errors["codigo_interno"] = (
                    "El código interno o número de serie ya está registrado."
                )
            except ForeignKeyViolation:
                get_db().rollback()
                errors["id_categoria"] = "La categoría seleccionada ya no está disponible."
            else:
                flash("Cambios guardados correctamente.", "success")
                return redirect(
                    url_for("inventory.equipment_detail", equipment_id=equipment_id)
                )

    return render_template(
        "inventory/form.html",
        data=data,
        errors=errors,
        categories=category_items,
        statuses=EQUIPMENT_STATUSES,
        mode="edit",
        item=item,
    )


def init_app(app):
    app.register_blueprint(bp)
