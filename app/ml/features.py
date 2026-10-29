from __future__ import annotations

from dataclasses import dataclass
from math import log1p


MODEL_VERSION = 1
TARGET_DESCRIPTION = "Mantenimiento correctivo dentro de los próximos 30 días"
PREDICTION_HORIZON_DAYS = 30
MINIMUM_MEASUREMENTS = 5
RISK_THRESHOLDS = {"medium": 0.40, "high": 0.70}

FEATURE_NAMES = (
    "measurement_count_log",
    "out_of_range_ratio",
    "mean_deviation",
    "maximum_deviation",
    "trend_per_day",
    "correctives_180d",
    "days_since_maintenance",
    "days_since_last_measurement",
    "out_of_service",
)

FEATURE_LABELS = {
    "measurement_count_log": "Volumen de mediciones recientes",
    "out_of_range_ratio": "Proporción fuera de rango",
    "mean_deviation": "Desviación promedio",
    "maximum_deviation": "Desviación máxima",
    "trend_per_day": "Tendencia diaria normalizada",
    "correctives_180d": "Correctivos en 180 días",
    "days_since_maintenance": "Días desde el último mantenimiento",
    "days_since_last_measurement": "Antigüedad de la última medición",
    "out_of_service": "Equipo fuera de servicio",
}


@dataclass(frozen=True)
class EquipmentFeatures:
    id_equipo: int
    codigo_interno: str
    nombre: str
    estado: str
    measurement_count: int
    values: dict[str, float]

    def vector(self) -> list[float]:
        return [self.values[name] for name in FEATURE_NAMES]


def normalize_feature_row(row: dict) -> EquipmentFeatures:
    """Convierte agregados de PostgreSQL en las variables esperadas por el modelo."""
    measurement_count = max(int(row.get("measurement_count") or 0), 0)
    values = {
        "measurement_count_log": log1p(measurement_count),
        "out_of_range_ratio": _bounded(row.get("out_of_range_ratio"), 0, 1),
        "mean_deviation": _bounded(row.get("mean_deviation"), 0, 5),
        "maximum_deviation": _bounded(row.get("maximum_deviation"), 0, 10),
        "trend_per_day": _bounded(row.get("trend_per_day"), -1, 1),
        "correctives_180d": _bounded(row.get("correctives_180d"), 0, 20),
        "days_since_maintenance": _bounded(
            row.get("days_since_maintenance"), 0, 730
        ),
        "days_since_last_measurement": _bounded(
            row.get("days_since_last_measurement"), 0, 365
        ),
        "out_of_service": 1.0 if row.get("estado") == "FUERA_DE_SERVICIO" else 0.0,
    }
    return EquipmentFeatures(
        id_equipo=int(row["id_equipo"]),
        codigo_interno=str(row["codigo_interno"]),
        nombre=str(row["nombre"]),
        estado=str(row["estado"]),
        measurement_count=measurement_count,
        values=values,
    )


def _bounded(value, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = minimum
    return min(max(number, minimum), maximum)
