from app.core.database import get_db


def list_variables(search="", status=""):
    filters = []
    parameters = []
    if search:
        filters.append("(codigo ILIKE %s OR nombre ILIKE %s OR unidad ILIKE %s)")
        term = f"%{search}%"
        parameters.extend([term, term, term])
    if status == "ACTIVAS":
        filters.append("activo = TRUE")
    elif status == "INACTIVAS":
        filters.append("activo = FALSE")

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    with get_db().cursor() as cursor:
        cursor.execute(
            f"""
            SELECT *
            FROM variables_operativas
            {where_clause}
            ORDER BY activo DESC, nombre, codigo
            """,
            parameters,
        )
        return cursor.fetchall()


def find_variable(variable_id):
    with get_db().cursor() as cursor:
        cursor.execute(
            "SELECT * FROM variables_operativas WHERE id_variable = %s",
            (variable_id,),
        )
        return cursor.fetchone()


def create_variable(data):
    connection = get_db()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO variables_operativas (
                codigo, nombre, unidad, descripcion,
                valor_minimo, valor_maximo
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id_variable
            """,
            (
                data["codigo"],
                data["nombre"],
                data["unidad"],
                data["descripcion"],
                data["valor_minimo"],
                data["valor_maximo"],
            ),
        )
        variable_id = cursor.fetchone()["id_variable"]
    connection.commit()
    return variable_id


def update_variable(variable_id, data):
    connection = get_db()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE variables_operativas
            SET codigo = %s,
                nombre = %s,
                unidad = %s,
                descripcion = %s,
                valor_minimo = %s,
                valor_maximo = %s,
                activo = %s
            WHERE id_variable = %s
            """,
            (
                data["codigo"],
                data["nombre"],
                data["unidad"],
                data["descripcion"],
                data["valor_minimo"],
                data["valor_maximo"],
                data["activo"],
                variable_id,
            ),
        )
    connection.commit()
