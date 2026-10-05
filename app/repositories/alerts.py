from app.core.database import get_db


def list_alerts(status="", alert_type=""):
    filters = []
    parameters = []
    if status:
        filters.append("a.estado = %s")
        parameters.append(status)
    if alert_type:
        filters.append("a.tipo = %s")
        parameters.append(alert_type)
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    with get_db().cursor() as cursor:
        cursor.execute(
            f"""
            SELECT
                a.*,
                m.medido_en,
                e.id_equipo,
                e.codigo_interno,
                e.nombre AS equipo,
                v.id_variable,
                v.codigo AS codigo_variable,
                v.nombre AS variable,
                v.unidad,
                CONCAT_WS(' ', u.nombre, u.apellidos) AS atendida_por_nombre
            FROM alertas_rango AS a
            INNER JOIN mediciones_operativas AS m
                ON m.id_medicion = a.id_medicion
            INNER JOIN equipos AS e ON e.id_equipo = m.id_equipo
            INNER JOIN variables_operativas AS v
                ON v.id_variable = m.id_variable
            LEFT JOIN usuarios AS u ON u.id_usuario = a.atendida_por
            {where_clause}
            ORDER BY
                CASE WHEN a.estado = 'PENDIENTE' THEN 0 ELSE 1 END,
                a.generada_en DESC,
                a.id_alerta DESC
            """,
            parameters,
        )
        return cursor.fetchall()


def find_alert(alert_id):
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT
                a.*,
                m.medido_en,
                e.id_equipo,
                e.codigo_interno,
                e.nombre AS equipo,
                v.id_variable,
                v.codigo AS codigo_variable,
                v.nombre AS variable,
                v.unidad,
                CONCAT_WS(' ', u.nombre, u.apellidos) AS atendida_por_nombre
            FROM alertas_rango AS a
            INNER JOIN mediciones_operativas AS m
                ON m.id_medicion = a.id_medicion
            INNER JOIN equipos AS e ON e.id_equipo = m.id_equipo
            INNER JOIN variables_operativas AS v
                ON v.id_variable = m.id_variable
            LEFT JOIN usuarios AS u ON u.id_usuario = a.atendida_por
            WHERE a.id_alerta = %s
            """,
            (alert_id,),
        )
        return cursor.fetchone()


def resolve_alert(alert_id, status, observations, user_id):
    connection = get_db()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE alertas_rango
            SET estado = %s,
                atendida_por = %s,
                atendida_en = CURRENT_TIMESTAMP,
                observaciones = %s
            WHERE id_alerta = %s AND estado = 'PENDIENTE'
            RETURNING id_alerta
            """,
            (status, user_id, observations, alert_id),
        )
        updated = cursor.fetchone() is not None
    connection.commit()
    return updated
