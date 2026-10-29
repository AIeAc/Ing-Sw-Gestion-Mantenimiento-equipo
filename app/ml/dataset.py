from __future__ import annotations

import numpy as np

from .features import FEATURE_NAMES


def generate_synthetic_dataset(sample_count: int = 1600, random_state: int = 42):
    """Genera casos académicos reproducibles con relaciones operativas explícitas."""
    if sample_count < 200:
        raise ValueError("Se requieren al menos 200 casos para entrenar y evaluar.")

    rng = np.random.default_rng(random_state)
    measurement_count = rng.integers(5, 181, sample_count)
    out_of_range_ratio = np.clip(rng.beta(1.4, 6.2, sample_count), 0, 1)
    mean_deviation = np.clip(
        out_of_range_ratio * rng.uniform(0.25, 1.35, sample_count)
        + rng.gamma(0.55, 0.08, sample_count),
        0,
        5,
    )
    maximum_deviation = np.clip(
        mean_deviation + rng.gamma(1.25, 0.32, sample_count), 0, 10
    )
    trend_per_day = np.clip(rng.normal(0.015, 0.095, sample_count), -1, 1)
    correctives_180d = np.clip(
        rng.poisson(0.7 + out_of_range_ratio * 3.2, sample_count), 0, 20
    )
    days_since_maintenance = np.clip(
        rng.gamma(2.0, 52.0, sample_count), 0, 730
    )
    days_since_last_measurement = np.clip(
        rng.gamma(1.2, 3.8, sample_count), 0, 365
    )

    operational_pressure = (
        2.8 * out_of_range_ratio
        + 1.5 * mean_deviation
        + 0.7 * maximum_deviation
        + 2.1 * np.maximum(trend_per_day, 0)
        + 0.55 * correctives_180d
        + 0.0028 * days_since_maintenance
        + 0.018 * days_since_last_measurement
    )
    out_of_service_probability = _sigmoid(-3.2 + operational_pressure * 0.75)
    out_of_service = rng.binomial(1, out_of_service_probability)

    failure_score = (
        -2.85
        + operational_pressure
        + 2.2 * out_of_service
        + rng.normal(0, 0.28, sample_count)
    )
    failure_probability = _sigmoid(failure_score)
    target = (failure_probability >= 0.50).astype(int)
    # Un pequeño porcentaje de casos ambiguos evita un conjunto artificialmente
    # perfecto sin ocultar la relación entre deterioro operativo y correctivos.
    ambiguous = rng.random(sample_count) < 0.035
    target[ambiguous] = 1 - target[ambiguous]

    matrix = np.column_stack(
        (
            np.log1p(measurement_count),
            out_of_range_ratio,
            mean_deviation,
            maximum_deviation,
            trend_per_day,
            correctives_180d,
            days_since_maintenance,
            days_since_last_measurement,
            out_of_service,
        )
    ).astype(float)

    if matrix.shape[1] != len(FEATURE_NAMES):
        raise RuntimeError("El conjunto no coincide con las variables del modelo.")
    if np.isnan(matrix).any() or np.isinf(matrix).any():
        raise RuntimeError("El conjunto contiene valores no finitos.")
    if len(np.unique(target)) != 2:
        raise RuntimeError("El conjunto debe incluir casos con y sin falla.")

    return matrix, target


def _sigmoid(values):
    clipped = np.clip(values, -30, 30)
    return 1 / (1 + np.exp(-clipped))
