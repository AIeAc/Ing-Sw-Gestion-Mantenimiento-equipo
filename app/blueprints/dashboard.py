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


@bp.get("")
@login_required
def index():
    monthly = dashboard.maintenance_totals_by_month()
    monthly_data = [
        {
            "label": f"{MONTH_NAMES[item['month'].month]} {str(item['month'].year)[2:]}",
            "cost": float(item["cost"]),
            "correctives": item["correctives"],
        }
        for item in monthly
    ]
    return render_template(
        "dashboard/index.html",
        summary=dashboard.get_summary(),
        recent_alerts=dashboard.recent_alerts(),
        monthly_data=monthly_data,
    )


def init_app(app):
    app.register_blueprint(bp)
