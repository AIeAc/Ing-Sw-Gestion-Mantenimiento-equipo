import os
import re
import unittest
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from werkzeug.security import generate_password_hash

from app import create_app


@unittest.skipUnless(
    os.environ.get("TEST_DATABASE_URL"),
    "TEST_DATABASE_URL no está configurada",
)
class PostgreSQLIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.database_url = os.environ["TEST_DATABASE_URL"]
        self.suffix = uuid4().hex[:8]
        self.admin_email = f"admin-{self.suffix}@example.com"
        self.technician_email = f"tecnico-{self.suffix}@example.com"
        self.category_name = f"Bombas {self.suffix}"
        self.equipment_code = f"EQ-{self.suffix.upper()}"
        self.serial_number = f"SN-{self.suffix.upper()}"
        self.connection = psycopg.connect(self.database_url, row_factory=dict_row)
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT id_rol FROM roles WHERE nombre = 'Administrador'"
            )
            administrator_role = cursor.fetchone()["id_rol"]
            cursor.execute(
                """
                INSERT INTO usuarios (
                    id_rol, nombre, apellidos, correo, contrasena_hash
                )
                VALUES (%s, 'Mariana', 'Soto', %s, %s)
                """,
                (
                    administrator_role,
                    self.admin_email,
                    generate_password_hash("Admin-segura-2026"),
                ),
            )
        self.connection.commit()

        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "integration-secret",
                "DATABASE_URL": self.database_url,
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM mantenimientos
                WHERE id_equipo IN (
                    SELECT id_equipo FROM equipos WHERE codigo_interno = %s
                )
                """,
                (self.equipment_code,),
            )
            cursor.execute(
                "DELETE FROM equipos WHERE codigo_interno = %s",
                (self.equipment_code,),
            )
            cursor.execute(
                "DELETE FROM usuarios WHERE correo IN (%s, %s)",
                (self.admin_email, self.technician_email),
            )
            cursor.execute(
                "DELETE FROM categorias WHERE nombre = %s",
                (self.category_name,),
            )
        self.connection.commit()
        self.connection.close()

    def csrf(self, response):
        match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
        self.assertIsNotNone(match)
        return match.group(1).decode()

    def login(self, email, password):
        login_page = self.client.get("/iniciar-sesion")
        return self.client.post(
            "/iniciar-sesion",
            data={
                "csrf_token": self.csrf(login_page),
                "correo": email,
                "contrasena": password,
            },
            follow_redirects=True,
        )

    def test_complete_sprint_inventory_flow(self):
        inventory_page = self.login(self.admin_email, "Admin-segura-2026")
        self.assertEqual(inventory_page.status_code, 200)
        self.assertIn(b"Equipos", inventory_page.data)
        token = self.csrf(inventory_page)

        category_response = self.client.post(
            "/clasificaciones/nueva",
            data={
                "csrf_token": token,
                "nombre": self.category_name,
                "descripcion": "Equipos de impulsión de fluidos",
            },
            follow_redirects=True,
        )
        self.assertIn(b"Categor\xc3\xada creada correctamente", category_response.data)

        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT id_categoria FROM categorias WHERE nombre = %s",
                (self.category_name,),
            )
            category_id = cursor.fetchone()["id_categoria"]
            cursor.execute("SELECT id_rol FROM roles WHERE nombre = 'Técnico'")
            technician_role = cursor.fetchone()["id_rol"]

        user_response = self.client.post(
            "/usuarios/nuevo",
            data={
                "csrf_token": token,
                "nombre": "Diego",
                "apellidos": "Luna",
                "correo": self.technician_email,
                "id_rol": str(technician_role),
                "contrasena": "Tecnico-segura-2026",
                "confirmacion": "Tecnico-segura-2026",
            },
            follow_redirects=True,
        )
        self.assertIn(b"Usuario creado correctamente", user_response.data)

        equipment_response = self.client.post(
            "/equipos/nuevo",
            data={
                "csrf_token": token,
                "id_categoria": str(category_id),
                "codigo_interno": self.equipment_code,
                "nombre": "Bomba centrífuga principal",
                "marca": "KSB",
                "modelo": "Etanorm",
                "numero_serie": self.serial_number,
                "ubicacion": "Planta norte",
                "estado": "OPERATIVO",
                "descripcion": "Bomba del circuito principal",
                "fecha_adquisicion": "2024-04-18",
            },
            follow_redirects=True,
        )
        expected_name = "Bomba centrífuga principal".encode()
        self.assertIn(expected_name, equipment_response.data)

        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT id_usuario FROM usuarios WHERE correo = %s",
                (self.technician_email,),
            )
            technician_id = cursor.fetchone()["id_usuario"]
            cursor.execute(
                "SELECT id_equipo FROM equipos WHERE codigo_interno = %s",
                (self.equipment_code,),
            )
            equipment_id = cursor.fetchone()["id_equipo"]

        maintenance_response = self.client.post(
            "/mantenimientos/nuevo",
            data={
                "csrf_token": token,
                "id_equipo": str(equipment_id),
                "id_tecnico": str(technician_id),
                "tipo": "PREVENTIVO",
                "estado": "PROGRAMADO",
                "fecha_programada": "2026-10-15T09:30",
                "fecha_inicio": "",
                "fecha_fin": "",
                "costo": "850.00",
                "descripcion": "Inspección y lubricación preventiva",
                "observaciones": "Verificar el sello principal",
            },
            follow_redirects=True,
        )
        self.assertIn(b"Mantenimiento registrado correctamente", maintenance_response.data)
        self.assertIn(
            "Inspección y lubricación".encode(), maintenance_response.data
        )

        history_response = self.client.get(
            f"/mantenimientos/equipo/{equipment_id}/historial"
        )
        self.assertIn(b"Historial de mantenimiento", history_response.data)
        self.assertIn(
            "Inspección y lubricación".encode(), history_response.data
        )

        calendar_response = self.client.get(
            "/mantenimientos/calendario?mes=2026-10"
        )
        self.assertIn(expected_name, calendar_response.data)
        self.assertIn(b"Preventivo", calendar_response.data)

        search_response = self.client.get(f"/equipos?q={self.serial_number}")
        self.assertIn(self.equipment_code.encode(), search_response.data)
        self.assertIn(expected_name, search_response.data)

        logout_response = self.client.post(
            "/cerrar-sesion", data={"csrf_token": token}, follow_redirects=True
        )
        self.assertIn(b"Iniciar sesi\xc3\xb3n", logout_response.data)

        technician_page = self.login(
            self.technician_email, "Tecnico-segura-2026"
        )
        self.assertIn(expected_name, technician_page.data)
        self.assertEqual(self.client.get("/usuarios").status_code, 403)
        self.assertEqual(self.client.get("/clasificaciones").status_code, 403)


if __name__ == "__main__":
    unittest.main()
