from flask import Blueprint, current_app, render_template

from app.ml.decision import PRIORITY_ORDER, analyze_priority_and_cost
from app.ml.features import normalize_feature_row
from app.ml.prediction import (
    IncompatibleModelError,
    ModelUnavailableError,
    load_model_artifact,
    model_public_metadata,
    predict_equipment_risk,
)
from app.repositories import risks

from .auth import login_required

bp = Blueprint("risks", __name__, url_prefix="/riesgos")
LEVEL_ORDER = {"ALTO": 0, "MEDIO": 1, "BAJO": 2, "SIN_DATOS": 3}
COST_SOURCE_LABELS = {
    "EQUIPO": "Historial del equipo",
    "CATEGORIA": "Promedio de la categoría",
    "GENERAL": "Promedio general",
    "SIN_HISTORIAL": "Sin historial de costos",
}


@bp.get("")
@login_required
def index():
    feature_rows = risks.list_equipment_feature_rows()
    feature_items = [normalize_feature_row(row) for row in feature_rows]
    row_by_equipment = {int(row["id_equipo"]): row for row in feature_rows}
    model_error = None
    metadata = None
    risk_items = []
    try:
        artifact = load_model_artifact(current_app.config["RISK_MODEL_PATH"])
    except (ModelUnavailableError, IncompatibleModelError) as error:
        model_error = str(error)
    else:
        metadata = model_public_metadata(artifact)
        maximum_cost = max(
            (float(row.get("estimated_corrective_cost") or 0) for row in feature_rows),
            default=0,
        )
        for features in feature_items:
            assessment = predict_equipment_risk(features, artifact)
            source_row = row_by_equipment[features.id_equipo]
            decision = analyze_priority_and_cost(
                assessment["probability"],
                source_row.get("estimated_corrective_cost") or 0,
                maximum_cost,
            )
            risk_items.append(
                {
                    "equipment": features,
                    **assessment,
                    **decision,
                    "cost_source_label": COST_SOURCE_LABELS.get(
                        source_row.get("cost_source"), "Sin historial de costos"
                    ),
                    "cost_observations": int(
                        source_row.get("cost_observations") or 0
                    ),
                    "percentage": (
                        round(assessment["probability"] * 100, 1)
                        if assessment["probability"] is not None
                        else None
                    ),
                }
            )
        risk_items.sort(
            key=lambda item: (
                PRIORITY_ORDER[item["priority"]],
                -(item["priority_score"] or -1),
                -(item["financial_exposure"] or -1),
                item["equipment"].nombre,
            )
        )

    summary = {
        level: sum(item["level"] == level for item in risk_items)
        for level in LEVEL_ORDER
    }
    decision_summary = {
        "immediate": sum(item["priority"] == "INMEDIATA" for item in risk_items),
        "high": sum(item["priority"] == "ALTA" for item in risk_items),
        "financial_exposure": sum(
            item["financial_exposure"] or 0 for item in risk_items
        ),
        "average_cost": (
            sum(item["estimated_cost"] for item in risk_items) / len(risk_items)
            if risk_items
            else 0
        ),
    }
    return render_template(
        "risks/index.html",
        risk_items=risk_items,
        summary=summary,
        decision_summary=decision_summary,
        metadata=metadata,
        model_error=model_error,
    )


def init_app(app):
    app.register_blueprint(bp)
