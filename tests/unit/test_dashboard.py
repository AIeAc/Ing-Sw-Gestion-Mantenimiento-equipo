import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from app import create_app
from app.blueprints.dashboard import _build_period_analysis


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "DATABASE_URL": "postgresql://unused",
            }
        )
        self.client = self.app.test_client()
        self.admin = {
            "id_usuario": 1,
            "nombre": "Ana",
            "apellidos": "Torres",
            "correo": "ana@example.com",
            "rol": "Administrador",
        }
        with self.client.session_transaction() as session:
            session["user_id"] = 1

    @staticmethod
    def monthly_items():
        costs = (100, 200, 300, 500, 700, 900)
        return [
            {
                "month": date(2026, month, 1),
                "cost": Decimal(cost),
                "correctives": 1 if month % 2 else 0,
                "preventives": 1,
                "maintenances": 2,
            }
            for month, cost in enumerate(costs, start=5)
        ]

    def test_period_analysis_surfaces_cost_and_corrective_priorities(self):
        summary = {"equipos_fuera_de_servicio": 2}
        equipment = [
            {
                "nombre": "Compresor",
                "codigo_interno": "EQ-003",
                "cost": Decimal("1200"),
                "correctives": 2,
                "alerts": 1,
            }
        ]

        analysis = _build_period_analysis(self.monthly_items(), equipment, summary)

        self.assertEqual(analysis["total_cost"], Decimal("2700"))
        self.assertEqual(analysis["total_correctives"], 3)
        self.assertEqual(analysis["corrective_share"], Decimal("33.3"))
        self.assertEqual(analysis["peak_label"], "Oct 26")
        self.assertEqual(analysis["decisions"][0]["level"], "alert")

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.dashboard.dashboard.recent_alerts", return_value=[])
    @patch("app.blueprints.dashboard.dashboard.equipment_impact")
    @patch("app.blueprints.dashboard.dashboard.maintenance_totals_by_month")
    @patch("app.blueprints.dashboard.dashboard.get_summary")
    def test_dashboard_includes_decision_summary_and_equipment_ranking(
        self, get_summary, monthly, equipment_impact, _alerts, find_user
    ):
        find_user.return_value = self.admin
        get_summary.return_value = {
            "disponibilidad_porcentaje": Decimal("80"),
            "equipos_operativos": 8,
            "total_equipos_activos": 10,
            "equipos_fuera_de_servicio": 2,
            "mantenimientos_correctivos": 3,
            "costo_mantenimiento_total": Decimal("2700"),
            "alertas_rango_pendientes": 1,
        }
        monthly.return_value = self.monthly_items()
        equipment_impact.return_value = [
            {
                "id_equipo": 3,
                "nombre": "Compresor",
                "codigo_interno": "EQ-003",
                "cost": Decimal("1200"),
                "correctives": 2,
                "alerts": 1,
            }
        ]

        response = self.client.get("/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Prioridades actuales".encode(), response.data)
        self.assertIn(b"data-impact-chart", response.data)
        self.assertIn("Recuperar disponibilidad".encode(), response.data)
        self.assertIn(b'"preventives": 1', response.data)


if __name__ == "__main__":
    unittest.main()
