from app.core.database import get_db


def list_maintenance(search="", maintenance_type="", status=""):
    filters = []
    parameters = []

    if search:
        filters.append(
            """
            (
                e.codigo_interno ILIKE %s OR
                e.nombre ILIKE %s OR
                m.descripcion ILIKE %s OR
                CONCAT_WS(' ', t.nombre, t.apellidos) ILIKE %s
            )
            """
        )
        term = f"%{search}%"
        parameters.extend([term] * 4)
    if maintenance_type:
        filters.append("m.tipo = %s")
        parameters.append(maintenance_type)
    if status:
        filters.append("m.estado = %s")
        parameters.append(status)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    with get_db().cursor() as cursor:
        cursor.execute(
            f"""
            SELECT
                m.id_mantenimiento,
                m.tipo,
                m.estado,
                m.fecha_programada,
                m.fecha_inicio,
                m.fecha_fin,
                m.costo,
                m.descripcion,
                e.id_equipo,
                e.codigo_interno,
                e.nombre AS equipo,
                CONCAT_WS(' ', t.nombre, t.apellidos) AS tecnico
            FROM mantenimientos AS m
            INNER JOIN equipos AS e ON e.id_equipo = m.id_equipo
            INNER JOIN usuarios AS t ON t.id_usuario = m.id_tecnico
            {where_clause}
            ORDER BY
                COALESCE(m.fecha_programada, m.fecha_inicio, m.creado_en) DESC,
                m.id_mantenimiento DESC
            """,
            parameters,
        )
        return cursor.fetchall()


def find_maintenance(maintenance_id):
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT
                m.*,
                e.codigo_interno,
                e.nombre AS equipo,
                CONCAT_WS(' ', t.nombre, t.apellidos) AS tecnico,
                CONCAT_WS(' ', r.nombre, r.apellidos) AS registrador
            FROM mantenimientos AS m
            INNER JOIN equipos AS e ON e.id_equipo = m.id_equipo
            INNER JOIN usuarios AS t ON t.id_usuario = m.id_tecnico
            INNER JOIN usuarios AS r ON r.id_usuario = m.registrado_por
            WHERE m.id_mantenimiento = %s
            """,
            (maintenance_id,),
        )
        return cursor.fetchone()


def list_equipment_options():
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT id_equipo, codigo_interno, nombre, estado
            FROM equipos
            ORDER BY nombre, codigo_interno
            """
        )
        return cursor.fetchall()


def equipment_exists(equipment_id):
    with get_db().cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM equipos WHERE id_equipo = %s",
            (equipment_id,),
        )
        return cursor.fetchone() is not None


def list_active_technicians():
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT u.id_usuario, u.nombre, u.apellidos
            FROM usuarios AS u
            INNER JOIN roles AS r ON r.id_rol = u.id_rol
            WHERE u.activo = TRUE
              AND r.activo = TRUE
              AND LOWER(r.nombre) = LOWER('Técnico')
            ORDER BY u.nombre, u.apellidos
            """
        )
        return cursor.fetchall()


def active_technician_exists(technician_id):
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM usuarios AS u
            INNER JOIN roles AS r ON r.id_rol = u.id_rol
            WHERE u.id_usuario = %s
              AND u.activo = TRUE
              AND r.activo = TRUE
              AND LOWER(r.nombre) = LOWER('Técnico')
            """,
            (technician_id,),
        )
        return cursor.fetchone() is not None


def create_maintenance(data, registered_by):
    connection = get_db()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO mantenimientos (
                id_equipo,
                id_tecnico,
                registrado_por,
                tipo,
                estado,
                fecha_programada,
                fecha_inicio,
                fecha_fin,
                costo,
                descripcion,
                observaciones
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_mantenimiento
            """,
            (
                data["id_equipo"],
                data["id_tecnico"],
                registered_by,
                data["tipo"],
                data["estado"],
                data["fecha_programada"],
                data["fecha_inicio"],
                data["fecha_fin"],
                data["costo"],
                data["descripcion"],
                data["observaciones"],
            ),
        )
        maintenance_id = cursor.fetchone()["id_mantenimiento"]
    connection.commit()
    return maintenance_id


def update_maintenance(maintenance_id, data):
    connection = get_db()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE mantenimientos
            SET id_equipo = %s,
                id_tecnico = %s,
                tipo = %s,
                estado = %s,
                fecha_programada = %s,
                fecha_inicio = %s,
                fecha_fin = %s,
                costo = %s,
                descripcion = %s,
                observaciones = %s
            WHERE id_mantenimiento = %s
            """,
            (
                data["id_equipo"],
                data["id_tecnico"],
                data["tipo"],
                data["estado"],
                data["fecha_programada"],
                data["fecha_inicio"],
                data["fecha_fin"],
                data["costo"],
                data["descripcion"],
                data["observaciones"],
                maintenance_id,
            ),
        )
    connection.commit()


def equipment_history(equipment_id):
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM historial_mantenimientos_equipo
            WHERE id_equipo = %s
            ORDER BY fecha_referencia DESC, id_mantenimiento DESC
            """,
            (equipment_id,),
        )
        return cursor.fetchall()


def calendar_entries(start_date, end_date):
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM calendario_mantenimientos
            WHERE fecha >= %s AND fecha < %s
            ORDER BY fecha_programada, id_mantenimiento
            """,
            (start_date, end_date),
        )
        return cursor.fetchall()
