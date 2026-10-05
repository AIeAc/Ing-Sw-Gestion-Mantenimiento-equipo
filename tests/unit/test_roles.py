import unittest
from unittest.mock import patch

from app import create_app


class RoleTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "DATABASE_URL": "postgresql://unused",
            }
        )
        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session["user_id"] = 8
            session["csrf_token"] = "valid-token"

    @staticmethod
    def user(role):
        return {
            "id_usuario": 8,
            "nombre": "Elena",
            "apellidos": "Ruiz",
            "correo": "elena@example.com",
            "rol": role,
        }

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.admin.users.list_users")
    def test_technician_cannot_manage_users(self, list_users, find_user):
        find_user.return_value = self.user("Técnico")
        response = self.client.get("/usuarios")
        self.assertEqual(response.status_code, 403)
        list_users.assert_not_called()

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.classifications.categories.list_categories")
    def test_technician_cannot_manage_categories(self, list_categories, find_user):
        find_user.return_value = self.user("Técnico")
        response = self.client.get("/clasificaciones")
        self.assertEqual(response.status_code, 403)
        list_categories.assert_not_called()

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.variables.variables.create_variable")
    def test_technician_cannot_create_variables(self, create_variable, find_user):
        find_user.return_value = self.user("Técnico")
        response = self.client.post(
            "/variables/nueva",
            data={"csrf_token": "valid-token"},
        )
        self.assertEqual(response.status_code, 403)
        create_variable.assert_not_called()

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.admin.users.list_users", return_value=[])
    def test_administrator_can_open_user_management(self, _list_users, find_user):
        find_user.return_value = self.user("Administrador")
        response = self.client.get("/usuarios")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Usuarios y roles", response.data)

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.admin.users.list_active_roles")
    @patch("app.blueprints.admin.users.role_exists", return_value=True)
    @patch("app.blueprints.admin.users.find_user_by_id")
    @patch("app.blueprints.admin.users.update_user")
    def test_administrator_cannot_deactivate_own_account(
        self, update_user, find_edited_user, _role_exists, list_roles, find_user
    ):
        administrator = self.user("Administrador")
        administrator["id_rol"] = 1
        administrator["activo"] = True
        find_user.return_value = administrator
        find_edited_user.return_value = administrator
        list_roles.return_value = [{"id_rol": 1, "nombre": "Administrador"}]

        response = self.client.post(
            "/usuarios/8/editar",
            data={
                "csrf_token": "valid-token",
                "nombre": "Elena",
                "apellidos": "Ruiz",
                "correo": "elena@example.com",
                "id_rol": "1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No puedes desactivar tu propia cuenta", response.data)
        update_user.assert_not_called()


if __name__ == "__main__":
    unittest.main()
