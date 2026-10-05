import calendar
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from psycopg import IntegrityError

from app.core.database import get_db
from app.repositories import equipment, maintenance

from .auth import login_required, validate_csrf

bp = Blueprint("maintenance", __name__, url_prefix="/mantenimientos")

MAINTENANCE_TYPES = (
    ("PREVENTIVO", "Preventivo"),
    ("CORRECTIVO", "Correctivo"),
)
MAINTENANCE_STATUSES = (
    ("PROGRAMADO", "Programado"),
    ("EN_PROCESO", "En proceso"),
    ("COMPLETADO", "Completado"),
    ("CANCELADO", "Cancelado"),
)
VALID_TYPES = {value for value, _label in MAINTENANCE_TYPES}
VALID_STATUSES = {value for value, _label in MAINTENANCE_STATUSES}
MONTH_NAMES = (
    "",
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def _datetime_value(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%dT%H:%M")
    return str(value or "").strip()


def _form_data(source):
    return {
        "id_equipo": str(source.get("id_equipo") or "").strip(),
        "id_tecnico": str(source.get("id_tecnico") or "").strip(),
        "tipo": str(source.get("tipo") or "PREVENTIVO").strip(),
        "estado": str(source.get("estado") or "PROGRAMADO").strip(),
        "fecha_programada": _datetime_value(source.get("fecha_programada")),
        "fecha_inicio": _datetime_value(source.get("fecha_inicio")),
        "fecha_fin": _datetime_value(source.get("fecha_fin")),
        "costo": str(source.get("costo") or "").strip(),
        "descripcion": str(source.get("descripcion") or "").strip(),
        "observaciones": str(source.get("observaciones") or "").strip(),
    }


def _parse_datetime(value, field, errors):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        errors[field] = "Ingresa una fecha y hora válidas."
        return None


def _parse_id(value, field, message, errors):
    try:
        return int(value)
    except (TypeError, ValueError):
        errors[field] = message
        return None


def _validate(data):
    errors = {}
    equipment_id = _parse_id(
        data["id_equipo"], "id_equipo", "Selecciona un equipo.", errors
    )
    technician_id = _parse_id(
        data["id_tecnico"], "id_tecnico", "Selecciona un técnico.", errors
    )

    if equipment_id is not None and not maintenance.equipment_exists(equipment_id):
        errors["id_equipo"] = "Selecciona un equipo válido."
    if technician_id is not None and not maintenance.active_technician_exists(
        technician_id
    ):
        errors["id_tecnico"] = "Selecciona un técnico activo."
    if data["tipo"] not in VALID_TYPES:
        errors["tipo"] = "Selecciona un tipo válido."
    if data["estado"] not in VALID_STATUSES:
        errors["estado"] = "Selecciona un estado válido."
    if not data["descripcion"]:
        errors["descripcion"] = "Describe el mantenimiento a realizar."

    scheduled_at = _parse_datetime(
        data["fecha_programada"], "fecha_programada", errors
    )
    started_at = _parse_datetime(data["fecha_inicio"], "fecha_inicio", errors)
    finished_at = _parse_datetime(data["fecha_fin"], "fecha_fin", errors)

    if data["estado"] == "PROGRAMADO" and scheduled_at is None:
        errors["fecha_programada"] = "Indica cuándo está programado."
    if data["estado"] == "EN_PROCESO" and started_at is None:
        errors["fecha_inicio"] = "Indica cuándo comenzó el mantenimiento."
    if data["estado"] == "COMPLETADO":
        if started_at is None:
            errors["fecha_inicio"] = "Indica cuándo comenzó el mantenimiento."
        if finished_at is None:
            errors["fecha_fin"] = "Indica cuándo terminó el mantenimiento."
    if finished_at is not None and started_at is None:
        errors["fecha_inicio"] = "La fecha de inicio es necesaria si hay fecha final."
    elif started_at is not None and finished_at is not None and finished_at < started_at:
        errors["fecha_fin"] = "La fecha final no puede ser anterior al inicio."

    cost = None
    if data["costo"]:
        try:
            cost = Decimal(data["costo"])
        except InvalidOperation:
            errors["costo"] = "Ingresa un costo válido."
        else:
            if not cost.is_finite() or cost < 0:
                errors["costo"] = "El costo no puede ser negativo."
            elif cost > Decimal("9999999999.99"):
                errors["costo"] = "El costo excede el máximo permitido."
            elif cost.as_tuple().exponent < -2:
                errors["costo"] = "Usa como máximo dos decimales."

    if errors:
        return None, errors

    cleaned = data.copy()
    cleaned.update(
        {
            "id_equipo": equipment_id,
            "id_tecnico": technician_id,
            "fecha_programada": scheduled_at,
            "fecha_inicio": started_at,
            "fecha_fin": finished_at,
            "costo": cost,
            "observaciones": data["observaciones"] or None,
        }
    )
    return cleaned, {}


def _form_options():
    return {
        "equipment_items": maintenance.list_equipment_options(),
        "technicians": maintenance.list_active_technicians(),
    }


@bp.get("")
@login_required
def list_maintenance():
    search = request.args.get("q", "").strip()[:100]
    maintenance_type = request.args.get("tipo", "").strip()
    status = request.args.get("estado", "").strip()
    if maintenance_type not in VALID_TYPES:
        maintenance_type = ""
    if status not in VALID_STATUSES:
        status = ""

    items = maintenance.list_maintenance(search, maintenance_type, status)
    return render_template(
        "maintenance/list.html",
        maintenance_items=items,
        types=MAINTENANCE_TYPES,
        statuses=MAINTENANCE_STATUSES,
        filters={"q": search, "tipo": maintenance_type, "estado": status},
    )


@bp.route("/nuevo", methods=("GET", "POST"))
@login_required
def create_maintenance():
    options = _form_options()
    if not options["equipment_items"] or not options["technicians"]:
        missing = "un equipo" if not options["equipment_items"] else "un técnico activo"
        flash(f"Se requiere {missing} para registrar un mantenimiento.", "warning")
        return redirect(url_for("maintenance.list_maintenance"))

    if request.method == "POST":
        data = _form_data(request.form)
    else:
        data = _form_data({"id_equipo": request.args.get("equipo", "")})
    errors = {}

    if request.method == "POST":
        validate_csrf()
        cleaned, errors = _validate(data)
        if not errors:
            try:
                maintenance_id = maintenance.create_maintenance(
                    cleaned, g.user["id_usuario"]
                )
            except IntegrityError:
                get_db().rollback()
                flash(
                    "No fue posible guardar el mantenimiento. Revisa que el equipo y el técnico sigan disponibles.",
                    "error",
                )
            else:
                flash("Mantenimiento registrado correctamente.", "success")
                return redirect(
                    url_for(
                        "maintenance.maintenance_detail",
                        maintenance_id=maintenance_id,
                    )
                )

    return render_template(
        "maintenance/form.html",
        data=data,
        errors=errors,
        types=MAINTENANCE_TYPES,
        statuses=MAINTENANCE_STATUSES,
        mode="create",
        **options,
    )


@bp.get("/<int:maintenance_id>")
@login_required
def maintenance_detail(maintenance_id):
    item = maintenance.find_maintenance(maintenance_id)
    if item is None:
        abort(404)
    return render_template(
        "maintenance/detail.html",
        item=item,
        types=dict(MAINTENANCE_TYPES),
        statuses=dict(MAINTENANCE_STATUSES),
    )


@bp.route("/<int:maintenance_id>/editar", methods=("GET", "POST"))
@login_required
def edit_maintenance(maintenance_id):
    item = maintenance.find_maintenance(maintenance_id)
    if item is None:
        abort(404)

    options = _form_options()
    data = _form_data(request.form if request.method == "POST" else item)
    errors = {}
    if request.method == "POST":
        validate_csrf()
        cleaned, errors = _validate(data)
        if not errors:
            try:
                maintenance.update_maintenance(maintenance_id, cleaned)
            except IntegrityError:
                get_db().rollback()
                flash(
                    "No fue posible guardar los cambios. Revisa las fechas y las asociaciones.",
                    "error",
                )
            else:
                flash("Mantenimiento actualizado correctamente.", "success")
                return redirect(
                    url_for(
                        "maintenance.maintenance_detail",
                        maintenance_id=maintenance_id,
                    )
                )

    return render_template(
        "maintenance/form.html",
        data=data,
        errors=errors,
        types=MAINTENANCE_TYPES,
        statuses=MAINTENANCE_STATUSES,
        mode="edit",
        item=item,
        **options,
    )


@bp.get("/equipo/<int:equipment_id>/historial")
@login_required
def equipment_history(equipment_id):
    item = equipment.find_equipment(equipment_id)
    if item is None:
        abort(404)
    return render_template(
        "maintenance/history.html",
        item=item,
        maintenance_items=maintenance.equipment_history(equipment_id),
        types=dict(MAINTENANCE_TYPES),
        statuses=dict(MAINTENANCE_STATUSES),
    )


def _selected_month(raw_value):
    if raw_value:
        try:
            parsed = datetime.strptime(raw_value, "%Y-%m").date()
            return parsed.replace(day=1)
        except ValueError:
            pass
    return date.today().replace(day=1)


def _shift_month(value, offset):
    month_index = value.year * 12 + value.month - 1 + offset
    return date(month_index // 12, month_index % 12 + 1, 1)


@bp.get("/calendario")
@login_required
def maintenance_calendar():
    selected_month = _selected_month(request.args.get("mes", "").strip())
    next_month = _shift_month(selected_month, 1)
    entries = maintenance.calendar_entries(selected_month, next_month)
    entries_by_day = {}
    for entry in entries:
        entries_by_day.setdefault(entry["fecha"].day, []).append(entry)

    weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(
        selected_month.year, selected_month.month
    )
    return render_template(
        "maintenance/calendar.html",
        entries=entries,
        entries_by_day=entries_by_day,
        weeks=weeks,
        selected_month=selected_month,
        month_label=f"{MONTH_NAMES[selected_month.month]} de {selected_month.year}",
        previous_month=_shift_month(selected_month, -1).strftime("%Y-%m"),
        next_month=next_month.strftime("%Y-%m"),
        statuses=dict(MAINTENANCE_STATUSES),
    )


def init_app(app):
    app.register_blueprint(bp)
