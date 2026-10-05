import re
import unittest
from unittest.mock import patch

from werkzeug.security import generate_password_hash

from app import create_app


class AuthenticationTests(unittest.TestCase):
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
            "id_usuario": 7,
            "nombre": "Ana",
            "apellidos": "Torres",
            "correo": "ana@example.com",
            "contrasena_hash": generate_password_hash("correcta-segura"),
            "rol": "Administrador",
        }

    def csrf_token(self, path="/iniciar-sesion"):
        response = self.client.get(path)
        match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
        self.assertIsNotNone(match)
        return match.group(1).decode()

    @patch("app.blueprints.auth.users.find_active_user_by_id", return_value=None)
    def test_protected_home_redirects_to_login(self, _find_by_id):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/iniciar-sesion", response.headers["Location"])

    @patch("app.blueprints.auth.users.find_active_user_by_email", return_value=None)
    def test_invalid_credentials_show_generic_message(self, _find_by_email):
        token = self.csrf_token()
        response = self.client.post(
            "/iniciar-sesion",
            data={
                "correo": "nadie@example.com",
                "contrasena": "incorrecta",
                "csrf_token": token,
            },
            follow_redirects=True,
        )
        self.assertIn(
            "El correo o la contraseña son incorrectos".encode(), response.data
        )

    def test_login_rejects_missing_csrf_token(self):
        response = self.client.post(
            "/iniciar-sesion",
            data={"correo": "ana@example.com", "contrasena": "correcta-segura"},
        )
        self.assertEqual(response.status_code, 400)

    @patch("app.blueprints.auth.users.register_last_access")
    @patch("app.blueprints.auth.users.find_active_user_by_email")
    def test_valid_credentials_start_session(self, find_by_email, register_access):
        find_by_email.return_value = self.user
        token = self.csrf_token()
        response = self.client.post(
            "/iniciar-sesion",
            data={
                "correo": " ANA@example.com ",
                "contrasena": "correcta-segura",
                "csrf_token": token,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/equipos")
        find_by_email.assert_called_once_with("ana@example.com")
        register_access.assert_called_once_with(7)
        with self.client.session_transaction() as session:
            self.assertEqual(session["user_id"], 7)
            self.assertIn("csrf_token", session)

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    def test_logout_clears_session(self, find_by_id):
        find_by_id.return_value = self.user
        with self.client.session_transaction() as session:
            session["user_id"] = 7
            session["csrf_token"] = "valid-token"

        response = self.client.post(
            "/cerrar-sesion", data={"csrf_token": "valid-token"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/iniciar-sesion"))
        with self.client.session_transaction() as session:
            self.assertNotIn("user_id", session)


if __name__ == "__main__":
    unittest.main()
