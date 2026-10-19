import csv
import io
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import (
    Blueprint,
    Response,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from psycopg import IntegrityError
from werkzeug.utils import secure_filename

from app.core.database import get_db
from app.repositories import measurements

from .auth import login_required, validate_csrf

bp = Blueprint("measurements", __name__, url_prefix="/mediciones")
REQUIRED_COLUMNS = {
    "codigo_equipo",
    "codigo_variable",
    "valor",
    "medido_en",
}
MAX_CSV_ROWS = 2000


def _build_measurement_analysis(items):
    """Resume un conjunto homogéneo de mediciones sin realizar predicciones."""
    if not items:
        return None

    chronological = list(reversed(items))
    values = [Decimal(str(item["valor"])) for item in chronological]
    first = chronological[0]
    latest = chronological[-1]
    minimum = Decimal(str(latest["valor_minimo"]))
    maximum = Decimal(str(latest["valor_maximo"]))
    allowed_span = maximum - minimum
    average = (sum(values, Decimal("0")) / len(values)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    below = sum(value < minimum for value in values)
    above = sum(value > maximum for value in values)
    normal = len(values) - below - above
    compliance = (Decimal(normal) * Decimal("100") / len(values)).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )

    delta = values[-1] - values[0]
    stable_margin = abs(allowed_span) * Decimal("0.02")
    if abs(delta) <= stable_margin:
        direction = "stable"
        direction_label = "Estable"
    elif delta > 0:
        direction = "up"
        direction_label = "Al alza"
    else:
        direction = "down"
        direction_label = "A la baja"

    change_percent = None
    if values[0] != 0:
        change_percent = (delta * Decimal("100") / abs(values[0])).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP
        )

    range_position = Decimal("50")
    if allowed_span > 0:
        range_position = (values[-1] - minimum) * Decimal("100") / allowed_span

    latest_out_of_range = values[-1] < minimum or values[-1] > maximum
    if latest_out_of_range:
        decision = {
            "level": "alert",
            "title": "Revisión inmediata",
            "message": "La lectura más reciente está fuera del rango permitido. Conviene verificar el equipo y el origen de la medición.",
        }
    elif below or above:
        decision = {
            "level": "warning",
            "title": "Revisar las desviaciones",
            "message": f"Se detectaron {below + above} lecturas fuera de rango en el periodo. Consulta los puntos rojos y valida si existe un patrón operativo.",
        }
    elif direction == "up" and range_position >= Decimal("80"):
        decision = {
            "level": "warning",
            "title": "Vigilar el límite superior",
            "message": "La serie subió durante el periodo y la última lectura se encuentra en el tramo superior del rango permitido.",
        }
    elif direction == "down" and range_position <= Decimal("20"):
        decision = {
            "level": "warning",
            "title": "Vigilar el límite inferior",
            "message": "La serie bajó durante el periodo y la última lectura se encuentra en el tramo inferior del rango permitido.",
        }
    else:
        decision = {
            "level": "success",
            "title": "Comportamiento dentro de rango",
            "message": "Las lecturas del periodo permanecen dentro de los límites configurados. Mantén el seguimiento habitual.",
        }

    return {
        "equipment": latest["equipo"],
        "equipment_code": latest["codigo_interno"],
        "variable": latest["variable"],
        "unit": latest["unidad"],
        "count": len(values),
        "latest": values[-1],
        "latest_at": latest["medido_en"],
        "average": average,
        "observed_minimum": min(values),
        "observed_maximum": max(values),
        "allowed_minimum": minimum,
        "allowed_maximum": maximum,
        "normal": normal,
        "below": below,
        "above": above,
        "compliance": compliance,
        "delta": delta,
        "change_percent": change_percent,
        "direction": direction,
        "direction_label": direction_label,
        "period_start": first["medido_en"],
        "period_end": latest["medido_en"],
        "decision": decision,
    }


def _positive_id(raw_value):
    try:
        value = int(raw_value)
        return value if value > 0 else None
    except (TypeError, ValueError):
        return None


def _date_value(raw_value):
    if not raw_value:
        return None
    try:
        return date.fromisoformat(raw_value)
    except ValueError:
        return None


def _measurement_value(raw_value):
    try:
        value = Decimal(str(raw_value).strip())
    except InvalidOperation:
        return None
    if not value.is_finite():
        return None
    if abs(value) > Decimal("999999999999.999999"):
        return None
    if value.as_tuple().exponent < -6:
        return None
    return value


def _measured_at(raw_value):
    value = str(raw_value or "").strip()
    if not value:
        return None
    if value.endswith("Z"):
        value = f"{value[:-1]}+00:00"
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _parse_csv(file_storage):
    errors = []
    try:
        content = file_storage.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return [], 0, ["El archivo debe estar codificado en UTF-8."]

    reader = csv.DictReader(io.StringIO(content))
    headers = {str(name or "").strip().lower() for name in (reader.fieldnames or [])}
    missing = REQUIRED_COLUMNS - headers
    if missing:
        names = ", ".join(sorted(missing))
        return [], 0, [f"Faltan las columnas obligatorias: {names}."]

    equipment_lookup, variable_lookup = measurements.import_lookups()
    records = []
    total = 0
    for row_number, original_row in enumerate(reader, start=2):
        row = {
            str(key or "").strip().lower(): str(value or "").strip()
            for key, value in original_row.items()
        }
        if not any(row.values()):
            continue
        total += 1
        if total > MAX_CSV_ROWS:
            errors.append(f"El archivo excede el límite de {MAX_CSV_ROWS} filas.")
            break

        row_errors = []
        equipment = equipment_lookup.get(row.get("codigo_equipo", "").casefold())
        variable = variable_lookup.get(row.get("codigo_variable", "").casefold())
        value = _measurement_value(row.get("valor", ""))
        measured_at = _measured_at(row.get("medido_en", ""))
        if equipment is None:
            row_errors.append("equipo inexistente o dado de baja")
        if variable is None:
            row_errors.append("variable inexistente o inactiva")
        if value is None:
            row_errors.append("valor inválido")
        if measured_at is None:
            row_errors.append("fecha y hora inválidas")

        if row_errors:
            errors.append(f"Fila {row_number}: {', '.join(row_errors)}.")
            continue
        records.append(
            {
                "id_equipo": equipment["id_equipo"],
                "id_variable": variable["id_variable"],
                "valor": value,
                "medido_en": measured_at,
            }
        )
    return records, total, errors


@bp.get("")
@login_required
def list_measurements():
    equipment_id = _positive_id(request.args.get("equipo"))
    variable_id = _positive_id(request.args.get("variable"))
    batch_id = _positive_id(request.args.get("lote"))
    start_date = _date_value(request.args.get("desde", "").strip())
    end_date = _date_value(request.args.get("hasta", "").strip())
    exclusive_end = end_date + timedelta(days=1) if end_date else None

    items = measurements.list_measurements(
        equipment_id, variable_id, start_date, exclusive_end, batch_id
    )
    chart_data = []
    measurement_analysis = None
    chart_summary = None
    if equipment_id and variable_id:
        measurement_analysis = _build_measurement_analysis(items)
        if measurement_analysis:
            chart_summary = {
                "average": float(measurement_analysis["average"]),
                "unit": measurement_analysis["unit"],
                "normal": measurement_analysis["normal"],
                "below": measurement_analysis["below"],
                "above": measurement_analysis["above"],
            }
        chart_data = [
            {
                "value": float(item["valor"]),
                "minimum": float(item["valor_minimo"]),
                "maximum": float(item["valor_maximo"]),
                "measuredAt": item["medido_en"].isoformat(),
                "outOfRange": item["fuera_de_rango"],
            }
            for item in reversed(items)
        ]

    return render_template(
        "measurements/list.html",
        measurement_items=items,
        equipment_items=measurements.list_equipment_options(),
        variable_items=measurements.list_variable_options(),
        chart_data=chart_data,
        chart_summary=chart_summary,
        measurement_analysis=measurement_analysis,
        filters={
            "equipo": str(equipment_id or ""),
            "variable": str(variable_id or ""),
            "desde": start_date.isoformat() if start_date else "",
            "hasta": end_date.isoformat() if end_date else "",
            "lote": str(batch_id or ""),
        },
    )


@bp.route("/importar", methods=("GET", "POST"))
@login_required
def import_measurements():
    errors = []
    if request.method == "POST":
        validate_csrf()
        uploaded_file = request.files.get("archivo")
        if uploaded_file is None or not uploaded_file.filename:
            errors.append("Selecciona un archivo CSV.")
        elif not uploaded_file.filename.lower().endswith(".csv"):
            errors.append("El archivo debe tener extensión .csv.")
        else:
            records, total, errors = _parse_csv(uploaded_file)
            if total == 0 and not errors:
                errors.append("El archivo no contiene mediciones.")
            if total > 0:
                filename = secure_filename(uploaded_file.filename)[:255]
                rejected = total - len(records)
                try:
                    batch_id = measurements.import_batch(
                        records,
                        total,
                        rejected,
                        filename,
                        errors,
                        g.user["id_usuario"],
                    )
                except IntegrityError:
                    get_db().rollback()
                    errors.append(
                        "La base rechazó el lote porque un equipo o variable cambió durante la importación."
                    )
                else:
                    if records:
                        flash(
                            f"Importación completada: {len(records)} registros válidos y {rejected} rechazados.",
                            "success" if rejected == 0 else "warning",
                        )
                        return redirect(
                            url_for("measurements.list_measurements", lote=batch_id)
                        )
                    flash(
                        "El lote fue registrado, pero ninguna fila fue válida.",
                        "warning",
                    )

    return render_template(
        "measurements/import.html",
        errors=errors,
        batches=measurements.list_recent_batches(),
    )


@bp.get("/plantilla.csv")
@login_required
def csv_template():
    content = (
        "codigo_equipo,codigo_variable,valor,medido_en\n"
        "DEMO-EQ-001,TEMP,72.5,2026-10-04T10:30:00\n"
    )
    return Response(
        content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=plantilla_mediciones.csv"},
    )


def init_app(app):
    app.register_blueprint(bp)
