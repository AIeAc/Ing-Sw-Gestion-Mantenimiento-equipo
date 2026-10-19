from decimal import Decimal, ROUND_HALF_UP

from flask import Blueprint, render_template

from app.repositories import dashboard

from .auth import login_required

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")
MONTH_NAMES = (
    "",
    "Ene",
    "Feb",
    "Mar",
    "Abr",
    "May",
    "Jun",
    "Jul",
    "Ago",
    "Sep",
    "Oct",
    "Nov",
    "Dic",
)


def _build_period_analysis(monthly, equipment_items, summary):
    costs = [Decimal(str(item["cost"])) for item in monthly]
    total_cost = sum(costs, Decimal("0"))
    total_correctives = sum(item["correctives"] for item in monthly)
    total_preventives = sum(item["preventives"] for item in monthly)
    classified = total_correctives + total_preventives
    corrective_share = (
        (Decimal(total_correctives) * Decimal("100") / classified).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP
        )
        if classified
        else Decimal("0")
    )

    midpoint = len(costs) // 2
    previous_cost = sum(costs[:midpoint], Decimal("0"))
    recent_cost = sum(costs[midpoint:], Decimal("0"))
    cost_change = None
    if previous_cost:
        cost_change = (
            (recent_cost - previous_cost) * Decimal("100") / previous_cost
        ).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    peak = max(monthly, key=lambda item: item["cost"], default=None)
    top_equipment = equipment_items[0] if equipment_items else None
    top_share = Decimal("0")
    if top_equipment and total_cost:
        top_share = (
            Decimal(str(top_equipment["cost"])) * Decimal("100") / total_cost
        ).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    decisions = []
    outages = summary["equipos_fuera_de_servicio"]
    if outages:
        decisions.append(
            {
                "level": "alert",
                "icon": "ph-warning-octagon",
                "title": "Recuperar disponibilidad",
                "message": f"{outages} {'equipo está' if outages == 1 else 'equipos están'} fuera de servicio y requieren atención operativa.",
            }
        )
    else:
        decisions.append(
            {
                "level": "success",
                "icon": "ph-check-circle",
                "title": "Continuidad operativa",
                "message": "No hay equipos activos fuera de servicio en este momento.",
            }
        )

    if cost_change is not None and cost_change > Decimal("10"):
        decisions.append(
            {
                "level": "warning",
                "icon": "ph-trend-up",
                "title": "Revisar aumento del gasto",
                "message": f"El costo de los 3 meses recientes subió {cost_change}% frente a los 3 anteriores.",
            }
        )
    elif cost_change is not None:
        direction = "bajó" if cost_change < 0 else "subió" if cost_change > 0 else "se mantuvo"
        decisions.append(
            {
                "level": "info",
                "icon": "ph-chart-line",
                "title": "Evolución del costo",
                "message": f"El gasto de los 3 meses recientes {direction} {abs(cost_change)}% frente a los 3 anteriores.",
            }
        )
    else:
        decisions.append(
            {
                "level": "info",
                "icon": "ph-chart-line",
                "title": "Sin base de comparación",
                "message": "Aún no existe gasto suficiente en ambos trimestres para calcular una variación.",
            }
        )

    if corrective_share >= Decimal("50") and classified:
        decisions.append(
            {
                "level": "warning",
                "icon": "ph-wrench",
                "title": "Alta carga correctiva",
                "message": f"El {corrective_share}% de los mantenimientos del periodo fueron correctivos.",
            }
        )
    else:
        decisions.append(
            {
                "level": "success",
                "icon": "ph-shield-check",
                "title": "Balance de mantenimiento",
                "message": f"Los correctivos representan el {corrective_share}% de los mantenimientos del periodo.",
            }
        )

    return {
        "total_cost": total_cost,
        "total_correctives": total_correctives,
        "total_preventives": total_preventives,
        "corrective_share": corrective_share,
        "recent_cost": recent_cost,
        "previous_cost": previous_cost,
        "cost_change": cost_change,
        "peak": peak,
        "peak_label": (
            f"{MONTH_NAMES[peak['month'].month]} {str(peak['month'].year)[2:]}"
            if peak
            else "Sin datos"
        ),
        "top_equipment": top_equipment,
        "top_share": top_share,
        "decisions": decisions,
    }


@bp.get("")
@login_required
def index():
    monthly = dashboard.maintenance_totals_by_month()
    equipment_items = dashboard.equipment_impact()
    summary = dashboard.get_summary()
    monthly_data = [
        {
            "label": f"{MONTH_NAMES[item['month'].month]} {str(item['month'].year)[2:]}",
            "cost": float(item["cost"]),
            "correctives": item["correctives"],
            "preventives": item["preventives"],
        }
        for item in monthly
    ]
    equipment_data = [
        {
            "label": item["nombre"],
            "code": item["codigo_interno"],
            "cost": float(item["cost"]),
            "correctives": item["correctives"],
            "alerts": item["alerts"],
        }
        for item in equipment_items
    ]
    return render_template(
        "dashboard/index.html",
        summary=summary,
        recent_alerts=dashboard.recent_alerts(),
        monthly_data=monthly_data,
        equipment_data=equipment_data,
        period_analysis=_build_period_analysis(monthly, equipment_items, summary),
    )


def init_app(app):
    app.register_blueprint(bp)
