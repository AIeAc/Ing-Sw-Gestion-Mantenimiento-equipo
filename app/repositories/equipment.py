from app.core.database import get_db


def list_equipment(search="", category_id=None, status=""):
    filters = []
    parameters = []

    if search:
        filters.append(
            """
            (
                e.codigo_interno ILIKE %s OR
                e.nombre ILIKE %s OR
                e.marca ILIKE %s OR
                e.modelo ILIKE %s OR
                e.numero_serie ILIKE %s
            )
            """
        )
        term = f"%{search}%"
        parameters.extend([term] * 5)
    if category_id is not None:
        filters.append("e.id_categoria = %s")
        parameters.append(category_id)
    if status:
        filters.append("e.estado = %s")
        parameters.append(status)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    with get_db().cursor() as cursor:
        cursor.execute(
            f"""
            SELECT
                e.id_equipo,
                e.codigo_interno,
                e.nombre,
                e.marca,
                e.modelo,
                e.numero_serie,
                e.ubicacion,
                e.estado,
                e.actualizado_en,
                c.nombre AS categoria
            FROM equipos AS e
            INNER JOIN categorias AS c ON c.id_categoria = e.id_categoria
            {where_clause}
            ORDER BY e.nombre, e.codigo_interno
            """,
            parameters,
        )
        return cursor.fetchall()


def find_equipment(equipment_id):
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT
                e.*,
                c.nombre AS categoria,
                u.nombre AS registrado_nombre,
                u.apellidos AS registrado_apellidos
            FROM equipos AS e
            INNER JOIN categorias AS c ON c.id_categoria = e.id_categoria
            INNER JOIN usuarios AS u ON u.id_usuario = e.registrado_por
            WHERE e.id_equipo = %s
            """,
            (equipment_id,),
        )
        return cursor.fetchone()


def create_equipment(data, registered_by):
    connection = get_db()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO equipos (
                id_categoria,
                registrado_por,
                codigo_interno,
                nombre,
                marca,
                modelo,
                numero_serie,
                ubicacion,
                estado,
                descripcion,
                fecha_adquisicion
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_equipo
            """,
            (
                data["id_categoria"],
                registered_by,
                data["codigo_interno"],
                data["nombre"],
                data["marca"],
                data["modelo"],
                data["numero_serie"],
                data["ubicacion"],
                data["estado"],
                data["descripcion"],
                data["fecha_adquisicion"],
            ),
        )
        equipment_id = cursor.fetchone()["id_equipo"]
    connection.commit()
    return equipment_id


def update_equipment(equipment_id, data):
    connection = get_db()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE equipos
            SET id_categoria = %s,
                codigo_interno = %s,
                nombre = %s,
                marca = %s,
                modelo = %s,
                numero_serie = %s,
                ubicacion = %s,
                estado = %s,
                descripcion = %s,
                fecha_adquisicion = %s
            WHERE id_equipo = %s
            """,
            (
                data["id_categoria"],
                data["codigo_interno"],
                data["nombre"],
                data["marca"],
                data["modelo"],
                data["numero_serie"],
                data["ubicacion"],
                data["estado"],
                data["descripcion"],
                data["fecha_adquisicion"],
                equipment_id,
            ),
        )
    connection.commit()
