import io
import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from app import create_app


class OperationalModuleTests(unittest.TestCase):
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
            session["csrf_token"] = "valid-token"

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.variables.variables.create_variable", return_value=3)
    def test_valid_operational_variable_is_created(self, create_variable, find_user):
        find_user.return_value = self.admin
        response = self.client.post(
            "/variables/nueva",
            data={
                "csrf_token": "valid-token",
                "codigo": " temp ",
                "nombre": "Temperatura",
                "unidad": "°C",
                "descripcion": "Temperatura de operación",
                "valor_minimo": "10.5",
                "valor_maximo": "85.25",
            },
        )

        self.assertEqual(response.status_code, 302)
        created = create_variable.call_args.args[0]
        self.assertEqual(created["codigo"], "TEMP")
        self.assertEqual(created["valor_minimo"], Decimal("10.5"))

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.variables.variables.create_variable")
    def test_invalid_range_is_rejected(self, create_variable, find_user):
        find_user.return_value = self.admin
        response = self.client.post(
            "/variables/nueva",
            data={
                "csrf_token": "valid-token",
                "codigo": "PRES",
                "nombre": "Presión",
                "unidad": "bar",
                "valor_minimo": "100",
                "valor_maximo": "20",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("El máximo debe ser mayor".encode(), response.data)
        create_variable.assert_not_called()

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.measurements.measurements.list_recent_batches", return_value=[])
    @patch("app.blueprints.measurements.measurements.import_lookups")
    @patch("app.blueprints.measurements.measurements.import_batch", return_value=9)
    def test_csv_import_stores_valid_rows_and_reports_rejections(
        self, import_batch, import_lookups, _batches, find_user
    ):
        find_user.return_value = self.admin
        import_lookups.return_value = (
            {
                "eq-001": {
                    "id_equipo": 4,
                    "codigo_interno": "EQ-001",
                    "nombre": "Bomba",
                }
            },
            {
                "temp": {
                    "id_variable": 2,
                    "codigo": "TEMP",
                    "nombre": "Temperatura",
                }
            },
        )
        csv_content = (
            "codigo_equipo,codigo_variable,valor,medido_en\n"
            "EQ-001,TEMP,42.5,2026-10-04T10:30:00\n"
            "NO-EXISTE,TEMP,15,2026-10-04T11:00:00\n"
        ).encode()

        response = self.client.post(
            "/mediciones/importar",
            data={
                "csrf_token": "valid-token",
                "archivo": (io.BytesIO(csv_content), "mediciones.csv"),
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/mediciones?lote=9"))
        records, total, rejected, filename, errors, user_id = import_batch.call_args.args
        self.assertEqual((len(records), total, rejected), (1, 2, 1))
        self.assertEqual(filename, "mediciones.csv")
        self.assertEqual(user_id, 1)
        self.assertIn("equipo inexistente", errors[0])

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.measurements.measurements.list_variable_options", return_value=[])
    @patch("app.blueprints.measurements.measurements.list_equipment_options", return_value=[])
    @patch("app.blueprints.measurements.measurements.list_measurements")
    def test_measurements_for_one_variable_include_chart_data(
        self, list_measurements, _equipment, _variables, find_user
    ):
        find_user.return_value = self.admin
        list_measurements.return_value = [
            {
                "id_medicion": 7,
                "valor": Decimal("25"),
                "valor_minimo": Decimal("10"),
                "valor_maximo": Decimal("20"),
                "medido_en": datetime(2026, 10, 4, 10, 30),
                "fuera_de_rango": True,
                "equipo": "Bomba",
                "codigo_interno": "EQ-001",
                "variable": "Temperatura",
                "codigo_variable": "TEMP",
                "unidad": "°C",
                "tipo_origen": "IMPORTACION",
                "id_lote": 3,
            }
        ]

        response = self.client.get("/mediciones?equipo=4&variable=2&desde=2026-10-01")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'data-line-chart', response.data)
        self.assertIn(b'"outOfRange": true', response.data)
        list_measurements.assert_called_once_with(
            4, 2, date(2026, 10, 1), None, None
        )

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.alerts.alerts.resolve_alert", return_value=True)
    @patch("app.blueprints.alerts.alerts.find_alert")
    def test_pending_alert_can_be_resolved(self, find_alert, resolve_alert, find_user):
        find_user.return_value = self.admin
        find_alert.return_value = {"id_alerta": 5, "estado": "PENDIENTE"}

        response = self.client.post(
            "/alertas/5",
            data={
                "csrf_token": "valid-token",
                "estado": "ATENDIDA",
                "observaciones": "Se revisó el sensor.",
            },
        )

        self.assertEqual(response.status_code, 302)
        resolve_alert.assert_called_once_with(
            5, "ATENDIDA", "Se revisó el sensor.", 1
        )


if __name__ == "__main__":
    unittest.main()
