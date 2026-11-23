"""Comprueba cortes históricos contra PostgreSQL sin conservar datos de prueba."""

import os
import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
from flask import g
from psycopg.rows import dict_row

from app import create_app
from app.repositories.risks import list_historical_training_rows


@unittest.skipUnless(
    os.environ.get("TEST_DATABASE_URL"),
    "TEST_DATABASE_URL no está configurada",
)
class RiskDatasetPostgreSQLTests(unittest.TestCase):
    def test_historical_cut_uses_prior_readings_and_complete_future(self):
        app = create_app({
            "TESTING": True,
            "SECRET_KEY": "risk-integration-secret",
            "DATABASE_URL": os.environ["TEST_DATABASE_URL"],
        })
        connection = psycopg.connect(os.environ["TEST_DATABASE_URL"], row_factory=dict_row)
        suffix = uuid4().hex[:10]
        now = datetime.now(timezone.utc)
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO categorias (nombre) VALUES (%s) RETURNING id_categoria",
                    (f"Riesgo {suffix}",),
                )
                category_id = cursor.fetchone()["id_categoria"]
                cursor.execute("SELECT id_rol FROM roles WHERE nombre = 'Administrador'")
                admin_role = cursor.fetchone()["id_rol"]
                cursor.execute("SELECT id_rol FROM roles WHERE nombre = 'Técnico'")
                technician_role = cursor.fetchone()["id_rol"]
                user_ids = []
                for role, label in ((admin_role, "admin"), (technician_role, "tech")):
                    cursor.execute(
                        """INSERT INTO usuarios
                           (id_rol, nombre, apellidos, correo, contrasena_hash)
                           VALUES (%s, 'Prueba', 'Riesgo', %s, 'hash')
                           RETURNING id_usuario""",
                        (role, f"{label}-{suffix}@example.com"),
                    )
                    user_ids.append(cursor.fetchone()["id_usuario"])
                cursor.execute(
                    """INSERT INTO equipos
                       (id_categoria, registrado_por, codigo_interno, nombre)
                       VALUES (%s, %s, %s, 'Equipo de prueba')
                       RETURNING id_equipo""",
                    (category_id, user_ids[0], f"RISK-{suffix}"),
                )
                equipment_id = cursor.fetchone()["id_equipo"]
                cursor.execute(
                    """INSERT INTO variables_operativas
                       (codigo, nombre, unidad, valor_minimo, valor_maximo)
                       VALUES (%s, %s, 'C', 0, 100) RETURNING id_variable""",
                    (f"V-{suffix}", f"Variable {suffix}"),
                )
                variable_id = cursor.fetchone()["id_variable"]
                cursor.execute(
                    """INSERT INTO lotes_mediciones (registrado_por, tipo_origen)
                       VALUES (%s, 'SIMULADOR') RETURNING id_lote""",
                    (user_ids[0],),
                )
                lot_id = cursor.fetchone()["id_lote"]
                for days_ago in (80, 20):
                    for minute in range(5):
                        cursor.execute(
                            """INSERT INTO mediciones_operativas
                               (id_equipo, id_variable, id_lote, valor, medido_en)
                               VALUES (%s, %s, %s, 50, %s)""",
                            (equipment_id, variable_id, lot_id,
                             now - timedelta(days=days_ago, minutes=minute)),
                        )
                cursor.execute(
                    """INSERT INTO mantenimientos
                       (id_equipo, id_tecnico, registrado_por, tipo, estado,
                        fecha_inicio, fecha_fin, descripcion)
                       VALUES (%s, %s, %s, 'CORRECTIVO', 'COMPLETADO',
                               %s, %s, 'Correctivo de prueba')""",
                    (equipment_id, user_ids[1], user_ids[0],
                     now - timedelta(days=55), now - timedelta(days=54)),
                )
            with app.app_context():
                g.db = connection
                try:
                    rows = [
                        row for row in list_historical_training_rows()
                        if row["id_equipo"] == equipment_id
                    ]
                finally:
                    g.pop("db")
            self.assertTrue(rows)
            self.assertTrue(any(row["target"] == 1 for row in rows))
            self.assertTrue(all(row["measurement_count"] == 5 for row in rows))
            self.assertTrue(all(row["snapshot_at"].replace(tzinfo=timezone.utc)
                                <= now - timedelta(days=30) for row in rows))
        finally:
            connection.rollback()
            connection.close()


if __name__ == "__main__":
    unittest.main()
