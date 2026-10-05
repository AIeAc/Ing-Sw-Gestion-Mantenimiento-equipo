from app.core.database import get_db


def list_equipment_options():
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT id_equipo, codigo_interno, nombre
            FROM equipos
            WHERE estado <> 'DADO_DE_BAJA'
            ORDER BY nombre, codigo_interno
            """
        )
        return cursor.fetchall()


def list_variable_options(active_only=False):
    active_filter = "WHERE activo = TRUE" if active_only else ""
    with get_db().cursor() as cursor:
        cursor.execute(
            f"""
            SELECT id_variable, codigo, nombre, unidad,
                   valor_minimo, valor_maximo, activo
            FROM variables_operativas
            {active_filter}
            ORDER BY nombre, codigo
            """
        )
        return cursor.fetchall()


def import_lookups():
    equipment_items = list_equipment_options()
    variable_items = list_variable_options(active_only=True)
    return (
        {item["codigo_interno"].casefold(): item for item in equipment_items},
        {item["codigo"].casefold(): item for item in variable_items},
    )


def list_measurements(
    equipment_id=None,
    variable_id=None,
    start_date=None,
    end_date=None,
    batch_id=None,
    limit=300,
):
    filters = []
    parameters = []
    if equipment_id is not None:
        filters.append("id_equipo = %s")
        parameters.append(equipment_id)
    if variable_id is not None:
        filters.append("id_variable = %s")
        parameters.append(variable_id)
    if start_date is not None:
        filters.append("medido_en >= %s")
        parameters.append(start_date)
    if end_date is not None:
        filters.append("medido_en < %s")
        parameters.append(end_date)
    if batch_id is not None:
        filters.append("id_lote = %s")
        parameters.append(batch_id)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    parameters.append(limit)
    with get_db().cursor() as cursor:
        cursor.execute(
            f"""
            SELECT *
            FROM mediciones_para_grafica
            {where_clause}
            ORDER BY medido_en DESC, id_medicion DESC
            LIMIT %s
            """,
            parameters,
        )
        return cursor.fetchall()


def list_recent_batches(limit=10):
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT
                l.*,
                CONCAT_WS(' ', u.nombre, u.apellidos) AS registrador
            FROM lotes_mediciones AS l
            INNER JOIN usuarios AS u ON u.id_usuario = l.registrado_por
            ORDER BY l.iniciado_en DESC, l.id_lote DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cursor.fetchall()


def import_batch(records, total_rows, rejected_rows, filename, errors, user_id):
    connection = get_db()
    detail = "\n".join(errors[:50]) or None
    final_status = "COMPLETADO" if records else "FALLIDO"
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO lotes_mediciones (
                registrado_por, tipo_origen, estado, nombre_archivo,
                registros_totales, registros_validos,
                registros_rechazados, detalle_error
            )
            VALUES (%s, 'IMPORTACION', 'PROCESANDO', %s, %s, 0, 0, %s)
            RETURNING id_lote
            """,
            (user_id, filename, total_rows, detail),
        )
        batch_id = cursor.fetchone()["id_lote"]

        for record in records:
            cursor.execute(
                """
                INSERT INTO mediciones_operativas (
                    id_equipo, id_variable, id_lote, valor, medido_en
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    record["id_equipo"],
                    record["id_variable"],
                    batch_id,
                    record["valor"],
                    record["medido_en"],
                ),
            )

        cursor.execute(
            """
            UPDATE lotes_mediciones
            SET estado = %s,
                registros_validos = %s,
                registros_rechazados = %s,
                finalizado_en = CURRENT_TIMESTAMP
            WHERE id_lote = %s
            """,
            (final_status, len(records), rejected_rows, batch_id),
        )
    connection.commit()
    return batch_id
