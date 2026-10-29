from __future__ import annotations

from datetime import datetime
from pathlib import Path

import joblib

from .features import (
    FEATURE_NAMES,
    MINIMUM_MEASUREMENTS,
    MODEL_VERSION,
    EquipmentFeatures,
)


class ModelUnavailableError(RuntimeError):
    pass


class IncompatibleModelError(RuntimeError):
    pass


_MODEL_CACHE = {"path": None, "mtime": None, "artifact": None}


def load_model_artifact(model_path: str | Path):
    path = Path(model_path)
    if not path.is_file():
        raise ModelUnavailableError(
            "El modelo local todavía no ha sido entrenado en esta computadora."
        )

    mtime = path.stat().st_mtime_ns
    if _MODEL_CACHE["path"] == path and _MODEL_CACHE["mtime"] == mtime:
        return _MODEL_CACHE["artifact"]

    artifact = joblib.load(path)
    if artifact.get("model_version") != MODEL_VERSION:
        raise IncompatibleModelError("La versión del modelo no es compatible.")
    if tuple(artifact.get("feature_names", ())) != FEATURE_NAMES:
        raise IncompatibleModelError("Las variables del modelo no son compatibles.")
    if not artifact.get("accepted"):
        raise IncompatibleModelError(
            "El modelo entrenado no cumplió los criterios mínimos de aceptación."
        )

    _MODEL_CACHE.update({"path": path, "mtime": mtime, "artifact": artifact})
    return artifact


def predict_equipment_risk(features: EquipmentFeatures, artifact: dict):
    if features.measurement_count < MINIMUM_MEASUREMENTS:
        return {
            "status": "insufficient",
            "level": "SIN_DATOS",
            "level_label": "Información insuficiente",
            "probability": None,
            "reasons": [
                f"Se requieren al menos {MINIMUM_MEASUREMENTS} mediciones recientes."
            ],
        }

    probability = float(artifact["model"].predict_proba([features.vector()])[0][1])
    thresholds = artifact["risk_thresholds"]
    if probability >= thresholds["high"]:
        level, label = "ALTO", "Riesgo alto"
    elif probability >= thresholds["medium"]:
        level, label = "MEDIO", "Riesgo medio"
    else:
        level, label = "BAJO", "Riesgo bajo"

    return {
        "status": "estimated",
        "level": level,
        "level_label": label,
        "probability": probability,
        "reasons": _explain_operational_factors(features),
    }


def model_public_metadata(artifact: dict):
    selected = artifact["evaluations"][artifact["selected_model"]]
    return {
        "selected_model": artifact["selected_model"],
        "trained_at": datetime.fromisoformat(artifact["trained_at"]),
        "target": artifact["target"],
        "horizon_days": artifact["horizon_days"],
        "dataset": artifact["dataset"],
        "metrics": selected,
        "evaluations": artifact["evaluations"],
    }


def _explain_operational_factors(features: EquipmentFeatures):
    values = features.values
    reasons = []
    if values["out_of_service"]:
        reasons.append("El equipo está fuera de servicio.")
    if values["out_of_range_ratio"] >= 0.20:
        reasons.append(
            f"{values['out_of_range_ratio'] * 100:.0f}% de las lecturas recientes están fuera de rango."
        )
    if values["maximum_deviation"] >= 0.25:
        reasons.append("Se observaron desviaciones relevantes respecto del rango permitido.")
    if values["correctives_180d"] >= 2:
        reasons.append(
            f"Registra {int(values['correctives_180d'])} mantenimientos correctivos recientes."
        )
    if values["trend_per_day"] >= 0.06:
        reasons.append("Las mediciones presentan una tendencia ascendente reciente.")
    if not reasons:
        reasons.append("Las mediciones recientes permanecen mayormente dentro de rango.")
    return reasons[:3]
