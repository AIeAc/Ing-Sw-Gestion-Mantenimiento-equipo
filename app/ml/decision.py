from __future__ import annotations


PRIORITY_ORDER = {"INMEDIATA": 0, "ALTA": 1, "MEDIA": 2, "BAJA": 3, "SIN_DATOS": 4}


def analyze_priority_and_cost(
    probability: float | None,
    estimated_cost: float,
    maximum_cost: float,
):
    """Convierte riesgo y costo histórico en una recomendación explicable."""
    cost = max(float(estimated_cost or 0), 0)
    if probability is None:
        return {
            "priority": "SIN_DATOS",
            "priority_label": "Sin prioridad",
            "priority_score": None,
            "estimated_cost": cost,
            "financial_exposure": None,
        }

    cost_impact = min(cost / maximum_cost, 1) if maximum_cost > 0 else 0
    priority_score = 0.80 * probability + 0.20 * cost_impact
    if probability >= 0.70 or priority_score >= 0.70:
        priority, label = "INMEDIATA", "Atención inmediata"
    elif probability >= 0.40 or priority_score >= 0.50:
        priority, label = "ALTA", "Prioridad alta"
    elif probability >= 0.20 or priority_score >= 0.30:
        priority, label = "MEDIA", "Prioridad media"
    else:
        priority, label = "BAJA", "Prioridad baja"

    return {
        "priority": priority,
        "priority_label": label,
        "priority_score": round(priority_score, 4),
        "estimated_cost": cost,
        "financial_exposure": round(probability * cost, 2),
    }
