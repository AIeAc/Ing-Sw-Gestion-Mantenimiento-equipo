from app.core.database import get_db


def list_categories(active_only=False):
    where_clause = "WHERE activo = TRUE" if active_only else ""
    with get_db().cursor() as cursor:
        cursor.execute(
            f"""
            SELECT id_categoria, nombre, descripcion, activo
            FROM categorias
            {where_clause}
            ORDER BY nombre
            """
        )
        return cursor.fetchall()


def find_category(category_id):
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT id_categoria, nombre, descripcion, activo
            FROM categorias
            WHERE id_categoria = %s
            """,
            (category_id,),
        )
        return cursor.fetchone()


def active_category_exists(category_id):
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM categorias
            WHERE id_categoria = %s AND activo = TRUE
            """,
            (category_id,),
        )
        return cursor.fetchone() is not None


def category_in_use(category_id):
    with get_db().cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM equipos WHERE id_categoria = %s LIMIT 1",
            (category_id,),
        )
        return cursor.fetchone() is not None


def create_category(data):
    connection = get_db()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO categorias (nombre, descripcion)
            VALUES (%s, %s)
            RETURNING id_categoria
            """,
            (data["nombre"], data["descripcion"]),
        )
        category_id = cursor.fetchone()["id_categoria"]
    connection.commit()
    return category_id


def update_category(category_id, data):
    connection = get_db()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE categorias
            SET nombre = %s, descripcion = %s, activo = %s
            WHERE id_categoria = %s
            """,
            (data["nombre"], data["descripcion"], data["activo"], category_id),
        )
    connection.commit()
