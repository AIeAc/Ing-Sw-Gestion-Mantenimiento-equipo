import unittest
from datetime import date, datetime
from unittest.mock import patch

from app import create_app


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "DATABASE_URL": "postgresql://unused",
            }
        )
        self.client = self.app.test_client()
        self.user = {
            "id_usuario": 4,
            "nombre": "Luis",
            "apellidos": "Mendoza",
            "correo": "luis@example.com",
            "rol": "Técnico",
        }
        self.equipment = [
            {
                "id_equipo": 3,
                "codigo_interno": "EQ-003",
                "nombre": "Compresor",
                "estado": "OPERATIVO",
            }
        ]
        self.technicians = [
            {"id_usuario": 4, "nombre": "Luis", "apellidos": "Mendoza"}
        ]
        with self.client.session_transaction() as session:
            session["user_id"] = 4
            session["csrf_token"] = "valid-token"

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.maintenance.maintenance.list_maintenance", return_value=[])
    def test_search_and_filters_are_forwarded(self, list_items, find_user):
        find_user.return_value = self.user
        response = self.client.get(
            "/mantenimientos?q=compresor&tipo=PREVENTIVO&estado=PROGRAMADO"
        )

        self.assertEqual(response.status_code, 200)
        list_items.assert_called_once_with("compresor", "PREVENTIVO", "PROGRAMADO")
        self.assertIn(b"No se encontraron mantenimientos", response.data)

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.maintenance.maintenance.list_active_technicians")
    @patch("app.blueprints.maintenance.maintenance.list_equipment_options")
    @patch("app.blueprints.maintenance.maintenance.active_technician_exists", return_value=True)
    @patch("app.blueprints.maintenance.maintenance.equipment_exists", return_value=True)
    @patch("app.blueprints.maintenance.maintenance.create_maintenance", return_value=18)
    def test_valid_maintenance_is_created(
        self,
        create_maintenance,
        _equipment_exists,
        _technician_exists,
        equipment_options,
        technician_options,
        find_user,
    ):
        find_user.return_value = self.user
        equipment_options.return_value = self.equipment
        technician_options.return_value = self.technicians

        response = self.client.post(
            "/mantenimientos/nuevo",
            data={
                "csrf_token": "valid-token",
                "id_equipo": "3",
                "id_tecnico": "4",
                "tipo": "PREVENTIVO",
                "estado": "PROGRAMADO",
                "fecha_programada": "2026-10-15T09:30",
                "fecha_inicio": "",
                "fecha_fin": "",
                "costo": "1250.50",
                "descripcion": "Cambio de filtros y revisión general",
                "observaciones": "Requiere detener el equipo",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/mantenimientos/18"))
        created_data, registered_by = create_maintenance.call_args.args
        self.assertEqual(registered_by, 4)
        self.assertEqual(created_data["id_equipo"], 3)
        self.assertEqual(created_data["costo"], 1250.50)

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.maintenance.maintenance.list_active_technicians")
    @patch("app.blueprints.maintenance.maintenance.list_equipment_options")
    @patch("app.blueprints.maintenance.maintenance.active_technician_exists", return_value=True)
    @patch("app.blueprints.maintenance.maintenance.equipment_exists", return_value=True)
    @patch("app.blueprints.maintenance.maintenance.create_maintenance")
    def test_completed_maintenance_requires_consistent_dates(
        self,
        create_maintenance,
        _equipment_exists,
        _technician_exists,
        equipment_options,
        technician_options,
        find_user,
    ):
        find_user.return_value = self.user
        equipment_options.return_value = self.equipment
        technician_options.return_value = self.technicians

        response = self.client.post(
            "/mantenimientos/nuevo",
            data={
                "csrf_token": "valid-token",
                "id_equipo": "3",
                "id_tecnico": "4",
                "tipo": "CORRECTIVO",
                "estado": "COMPLETADO",
                "fecha_inicio": "2026-10-15T12:00",
                "fecha_fin": "2026-10-15T10:00",
                "descripcion": "Sustitución de sello",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"La fecha final no puede ser anterior", response.data)
        create_maintenance.assert_not_called()

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.maintenance.maintenance.calendar_entries")
    def test_calendar_groups_entries_by_day(self, calendar_entries, find_user):
        find_user.return_value = self.user
        calendar_entries.return_value = [
            {
                "id_mantenimiento": 8,
                "fecha": date(2026, 10, 15),
                "fecha_programada": datetime(2026, 10, 15, 9, 30),
                "tipo": "PREVENTIVO",
                "estado": "PROGRAMADO",
                "equipo": "Compresor",
            }
        ]

        response = self.client.get("/mantenimientos/calendario?mes=2026-10")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Octubre de 2026", response.data)
        self.assertIn(b"Compresor", response.data)
        calendar_entries.assert_called_once_with(date(2026, 10, 1), date(2026, 11, 1))


if __name__ == "__main__":
    unittest.main()
