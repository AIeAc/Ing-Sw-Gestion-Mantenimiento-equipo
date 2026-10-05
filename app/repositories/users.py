from app.core.database import get_db


def find_active_user_by_email(email):
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT
                u.id_usuario,
                u.nombre,
                u.apellidos,
                u.correo,
                u.contrasena_hash,
                r.nombre AS rol
            FROM usuarios AS u
            INNER JOIN roles AS r ON r.id_rol = u.id_rol
            WHERE LOWER(u.correo) = LOWER(%s)
              AND u.activo = TRUE
              AND r.activo = TRUE
            """,
            (email,),
        )
        return cursor.fetchone()


def find_active_user_by_id(user_id):
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT
                u.id_usuario,
                u.nombre,
                u.apellidos,
                u.correo,
                r.nombre AS rol
            FROM usuarios AS u
            INNER JOIN roles AS r ON r.id_rol = u.id_rol
            WHERE u.id_usuario = %s
              AND u.activo = TRUE
              AND r.activo = TRUE
            """,
            (user_id,),
        )
        return cursor.fetchone()


def register_last_access(user_id):
    connection = get_db()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE usuarios
            SET ultimo_acceso = CURRENT_TIMESTAMP
            WHERE id_usuario = %s
            """,
            (user_id,),
        )
    connection.commit()


def list_users():
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT
                u.id_usuario,
                u.nombre,
                u.apellidos,
                u.correo,
                u.activo,
                u.ultimo_acceso,
                r.id_rol,
                r.nombre AS rol
            FROM usuarios AS u
            INNER JOIN roles AS r ON r.id_rol = u.id_rol
            ORDER BY u.nombre, u.apellidos, u.id_usuario
            """
        )
        return cursor.fetchall()


def find_user_by_id(user_id):
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT
                u.id_usuario,
                u.id_rol,
                u.nombre,
                u.apellidos,
                u.correo,
                u.activo,
                r.nombre AS rol
            FROM usuarios AS u
            INNER JOIN roles AS r ON r.id_rol = u.id_rol
            WHERE u.id_usuario = %s
            """,
            (user_id,),
        )
        return cursor.fetchone()


def list_active_roles():
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT id_rol, nombre, descripcion
            FROM roles
            WHERE activo = TRUE
            ORDER BY nombre
            """
        )
        return cursor.fetchall()


def role_exists(role_id):
    with get_db().cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM roles WHERE id_rol = %s AND activo = TRUE",
            (role_id,),
        )
        return cursor.fetchone() is not None


def create_user(data, password_hash):
    connection = get_db()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO usuarios (
                id_rol, nombre, apellidos, correo, contrasena_hash
            )
            VALUES (%s, %s, %s, LOWER(%s), %s)
            RETURNING id_usuario
            """,
            (
                data["id_rol"],
                data["nombre"],
                data["apellidos"],
                data["correo"],
                password_hash,
            ),
        )
        user_id = cursor.fetchone()["id_usuario"]
    connection.commit()
    return user_id


def update_user(user_id, data):
    connection = get_db()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE usuarios
            SET id_rol = %s,
                nombre = %s,
                apellidos = %s,
                correo = LOWER(%s),
                activo = %s
            WHERE id_usuario = %s
            """,
            (
                data["id_rol"],
                data["nombre"],
                data["apellidos"],
                data["correo"],
                data["activo"],
                user_id,
            ),
        )
    connection.commit()
