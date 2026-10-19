from app.core.database import get_db


def get_summary():
    with get_db().cursor() as cursor:
        cursor.execute("SELECT * FROM resumen_indicadores_dashboard")
        return cursor.fetchone()


def recent_alerts(limit=5):
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT
                a.id_alerta,
                a.tipo,
                a.valor_medido,
                a.generada_en,
                e.nombre AS equipo,
                v.nombre AS variable,
                v.unidad
            FROM alertas_rango AS a
            INNER JOIN mediciones_operativas AS m
                ON m.id_medicion = a.id_medicion
            INNER JOIN equipos AS e ON e.id_equipo = m.id_equipo
            INNER JOIN variables_operativas AS v
                ON v.id_variable = m.id_variable
            WHERE a.estado = 'PENDIENTE'
            ORDER BY a.generada_en DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cursor.fetchall()


def maintenance_totals_by_month(months=6):
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            WITH months AS (
                SELECT generate_series(
                    DATE_TRUNC('month', CURRENT_DATE) - (%s - 1) * INTERVAL '1 month',
                    DATE_TRUNC('month', CURRENT_DATE),
                    INTERVAL '1 month'
                ) AS month
            )
            SELECT
                months.month::DATE AS month,
                COUNT(m.id_mantenimiento) FILTER (
                    WHERE m.tipo = 'CORRECTIVO'
                ) AS correctives,
                COUNT(m.id_mantenimiento) FILTER (
                    WHERE m.tipo = 'PREVENTIVO'
                ) AS preventives,
                COUNT(m.id_mantenimiento) AS maintenances,
                COALESCE(SUM(m.costo) FILTER (
                    WHERE m.estado = 'COMPLETADO'
                ), 0) AS cost
            FROM months
            LEFT JOIN mantenimientos AS m
                ON COALESCE(m.fecha_fin, m.fecha_inicio, m.fecha_programada)::DATE
                   >= months.month::DATE
               AND COALESCE(m.fecha_fin, m.fecha_inicio, m.fecha_programada)::DATE
                   < (months.month + INTERVAL '1 month')::DATE
            GROUP BY months.month
            ORDER BY months.month
            """,
            (months,),
        )
        return cursor.fetchall()


def equipment_impact(months=6, limit=5):
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            WITH maintenance_impact AS (
                SELECT
                    e.id_equipo,
                    e.nombre,
                    e.codigo_interno,
                    COALESCE(SUM(m.costo) FILTER (
                        WHERE m.estado = 'COMPLETADO'
                    ), 0) AS cost,
                    COUNT(m.id_mantenimiento) FILTER (
                        WHERE m.tipo = 'CORRECTIVO'
                    ) AS correctives
                FROM equipos AS e
                LEFT JOIN mantenimientos AS m
                    ON m.id_equipo = e.id_equipo
                   AND COALESCE(m.fecha_fin, m.fecha_inicio, m.fecha_programada)::DATE
                       >= DATE_TRUNC('month', CURRENT_DATE) - (%s - 1) * INTERVAL '1 month'
                   AND COALESCE(m.fecha_fin, m.fecha_inicio, m.fecha_programada)::DATE
                       < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
                WHERE e.estado <> 'DADO_DE_BAJA'
                GROUP BY e.id_equipo, e.nombre, e.codigo_interno
            ), pending_alerts AS (
                SELECT m.id_equipo, COUNT(*) AS alerts
                FROM alertas_rango AS a
                INNER JOIN mediciones_operativas AS m
                    ON m.id_medicion = a.id_medicion
                WHERE a.estado = 'PENDIENTE'
                GROUP BY m.id_equipo
            )
            SELECT
                impact.*,
                COALESCE(alerts.alerts, 0) AS alerts
            FROM maintenance_impact AS impact
            LEFT JOIN pending_alerts AS alerts
                ON alerts.id_equipo = impact.id_equipo
            WHERE impact.cost > 0
               OR impact.correctives > 0
               OR COALESCE(alerts.alerts, 0) > 0
            ORDER BY
                impact.cost DESC,
                impact.correctives DESC,
                COALESCE(alerts.alerts, 0) DESC,
                impact.nombre
            LIMIT %s
            """,
            (months, limit),
        )
        return cursor.fetchall()
