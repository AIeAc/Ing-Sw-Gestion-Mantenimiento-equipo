import unittest
from unittest.mock import patch

from app import create_app


class InventoryTests(unittest.TestCase):
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
        with self.client.session_transaction() as session:
            session["user_id"] = 4
            session["csrf_token"] = "valid-token"

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.inventory.categories.list_categories", return_value=[])
    @patch("app.blueprints.inventory.equipment.list_equipment", return_value=[])
    def test_search_and_filters_are_forwarded(
        self, list_equipment, _list_categories, find_user
    ):
        find_user.return_value = self.user
        response = self.client.get(
            "/equipos?q=bomba&categoria=3&estado=OPERATIVO"
        )

        self.assertEqual(response.status_code, 200)
        list_equipment.assert_called_once_with("bomba", 3, "OPERATIVO")
        self.assertIn(b"No se encontraron equipos", response.data)

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.inventory.categories.list_categories")
    @patch("app.blueprints.inventory.categories.active_category_exists", return_value=True)
    @patch("app.blueprints.inventory.equipment.create_equipment")
    def test_valid_equipment_is_created(
        self, create_equipment, _category_exists, list_categories, find_user
    ):
        find_user.return_value = self.user
        list_categories.return_value = [{"id_categoria": 3, "nombre": "Bombas"}]
        create_equipment.return_value = 12

        response = self.client.post(
            "/equipos/nuevo",
            data={
                "csrf_token": "valid-token",
                "id_categoria": "3",
                "codigo_interno": "EQ-012",
                "nombre": "Bomba centrífuga",
                "marca": "KSB",
                "modelo": "Etanorm",
                "numero_serie": "SN-8841",
                "ubicacion": "Planta 1",
                "estado": "OPERATIVO",
                "descripcion": "Equipo principal de impulsión",
                "fecha_adquisicion": "2024-06-15",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/equipos/12"))
        created_data, registered_by = create_equipment.call_args.args
        self.assertEqual(registered_by, 4)
        self.assertEqual(created_data["id_categoria"], 3)
        self.assertEqual(created_data["codigo_interno"], "EQ-012")

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.inventory.categories.list_categories")
    @patch("app.blueprints.inventory.categories.active_category_exists", return_value=True)
    @patch("app.blueprints.inventory.equipment.create_equipment")
    def test_invalid_equipment_is_not_created(
        self, create_equipment, _category_exists, list_categories, find_user
    ):
        find_user.return_value = self.user
        list_categories.return_value = [{"id_categoria": 3, "nombre": "Bombas"}]

        response = self.client.post(
            "/equipos/nuevo",
            data={
                "csrf_token": "valid-token",
                "id_categoria": "3",
                "codigo_interno": "",
                "nombre": "",
                "estado": "DESCONOCIDO",
                "fecha_adquisicion": "2099-01-01",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Ingresa el c\xc3\xb3digo interno", response.data)
        self.assertIn(b"Selecciona un estado v\xc3\xa1lido", response.data)
        create_equipment.assert_not_called()

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.inventory.equipment.find_equipment", return_value=None)
    def test_missing_equipment_returns_404(self, _find_equipment, find_user):
        find_user.return_value = self.user
        response = self.client.get("/equipos/999")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
