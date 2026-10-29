from app.core.database import get_db


def list_equipment_feature_rows():
    """Obtiene agregados operativos; no realiza predicciones en PostgreSQL."""
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            WITH normalized_measurements AS (
                SELECT
                    m.id_equipo,
                    m.medido_en,
                    CASE
                        WHEN v.valor_maximo = v.valor_minimo THEN 0::DOUBLE PRECISION
                        ELSE (
                            (m.valor - v.valor_minimo)
                            / (v.valor_maximo - v.valor_minimo)
                        )::DOUBLE PRECISION
                    END AS range_position,
                    CASE
                        WHEN m.valor < v.valor_minimo THEN (
                            (v.valor_minimo - m.valor)
                            / NULLIF(v.valor_maximo - v.valor_minimo, 0)
                        )::DOUBLE PRECISION
                        WHEN m.valor > v.valor_maximo THEN (
                            (m.valor - v.valor_maximo)
                            / NULLIF(v.valor_maximo - v.valor_minimo, 0)
                        )::DOUBLE PRECISION
                        ELSE 0::DOUBLE PRECISION
                    END AS deviation
                FROM mediciones_operativas AS m
                INNER JOIN variables_operativas AS v
                    ON v.id_variable = m.id_variable
                WHERE m.medido_en >= CURRENT_TIMESTAMP - INTERVAL '30 days'
                  AND m.medido_en <= CURRENT_TIMESTAMP + INTERVAL '1 day'
            ), measurement_stats AS (
                SELECT
                    id_equipo,
                    COUNT(*) AS measurement_count,
                    AVG((deviation > 0)::INTEGER)::DOUBLE PRECISION
                        AS out_of_range_ratio,
                    AVG(deviation)::DOUBLE PRECISION AS mean_deviation,
                    MAX(deviation)::DOUBLE PRECISION AS maximum_deviation,
                    COALESCE(
                        REGR_SLOPE(
                            range_position,
                            EXTRACT(EPOCH FROM medido_en) / 86400
                        ),
                        0
                    )::DOUBLE PRECISION AS trend_per_day,
                    MAX(medido_en) AS last_measurement
                FROM normalized_measurements
                GROUP BY id_equipo
            ), maintenance_stats AS (
                SELECT
                    id_equipo,
                    COUNT(*) FILTER (
                        WHERE tipo = 'CORRECTIVO'
                          AND estado <> 'CANCELADO'
                          AND COALESCE(fecha_fin, fecha_inicio, fecha_programada)
                              >= CURRENT_TIMESTAMP - INTERVAL '180 days'
                    ) AS correctives_180d,
                    MAX(COALESCE(fecha_fin, fecha_inicio, fecha_programada)) FILTER (
                        WHERE estado = 'COMPLETADO'
                    ) AS last_maintenance
                FROM mantenimientos
                GROUP BY id_equipo
            ), equipment_costs AS (
                SELECT
                    id_equipo,
                    AVG(costo)::DOUBLE PRECISION AS average_cost,
                    COUNT(costo) AS observations
                FROM mantenimientos
                WHERE tipo = 'CORRECTIVO'
                  AND estado = 'COMPLETADO'
                  AND costo IS NOT NULL
                GROUP BY id_equipo
            ), category_costs AS (
                SELECT
                    e.id_categoria,
                    AVG(m.costo)::DOUBLE PRECISION AS average_cost,
                    COUNT(m.costo) AS observations
                FROM mantenimientos AS m
                INNER JOIN equipos AS e ON e.id_equipo = m.id_equipo
                WHERE m.tipo = 'CORRECTIVO'
                  AND m.estado = 'COMPLETADO'
                  AND m.costo IS NOT NULL
                GROUP BY e.id_categoria
            ), global_cost AS (
                SELECT
                    COALESCE(AVG(costo), 0)::DOUBLE PRECISION AS average_cost,
                    COUNT(costo) AS observations
                FROM mantenimientos
                WHERE tipo = 'CORRECTIVO'
                  AND estado = 'COMPLETADO'
                  AND costo IS NOT NULL
            )
            SELECT
                e.id_equipo,
                e.codigo_interno,
                e.nombre,
                e.estado,
                COALESCE(ms.measurement_count, 0) AS measurement_count,
                COALESCE(ms.out_of_range_ratio, 0) AS out_of_range_ratio,
                COALESCE(ms.mean_deviation, 0) AS mean_deviation,
                COALESCE(ms.maximum_deviation, 0) AS maximum_deviation,
                COALESCE(ms.trend_per_day, 0) AS trend_per_day,
                COALESCE(mt.correctives_180d, 0) AS correctives_180d,
                LEAST(
                    730,
                    GREATEST(
                        0,
                        COALESCE(
                            EXTRACT(EPOCH FROM (
                                CURRENT_TIMESTAMP - mt.last_maintenance
                            )) / 86400,
                            365
                        )
                    )
                ) AS days_since_maintenance,
                LEAST(
                    365,
                    GREATEST(
                        0,
                        COALESCE(
                            EXTRACT(EPOCH FROM (
                                CURRENT_TIMESTAMP - ms.last_measurement
                            )) / 86400,
                            365
                        )
                    )
                ) AS days_since_last_measurement
                ,COALESCE(ec.average_cost, cc.average_cost, gc.average_cost, 0)
                    AS estimated_corrective_cost
                ,CASE
                    WHEN ec.average_cost IS NOT NULL THEN 'EQUIPO'
                    WHEN cc.average_cost IS NOT NULL THEN 'CATEGORIA'
                    WHEN gc.observations > 0 THEN 'GENERAL'
                    ELSE 'SIN_HISTORIAL'
                END AS cost_source
                ,COALESCE(ec.observations, cc.observations, gc.observations, 0)
                    AS cost_observations
            FROM equipos AS e
            LEFT JOIN measurement_stats AS ms ON ms.id_equipo = e.id_equipo
            LEFT JOIN maintenance_stats AS mt ON mt.id_equipo = e.id_equipo
            LEFT JOIN equipment_costs AS ec ON ec.id_equipo = e.id_equipo
            LEFT JOIN category_costs AS cc ON cc.id_categoria = e.id_categoria
            CROSS JOIN global_cost AS gc
            WHERE e.estado <> 'DADO_DE_BAJA'
            ORDER BY e.nombre, e.codigo_interno
            """
        )
        return cursor.fetchall()


def list_historical_training_rows():
    """Construye cortes semanales pasados sin usar mediciones posteriores al corte."""
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            WITH measurement_bounds AS (
                SELECT
                    MIN(medido_en)::DATE AS first_day,
                    MAX(medido_en)::DATE AS last_day
                FROM mediciones_operativas
            ), snapshots AS (
                SELECT snapshot_day::TIMESTAMP + TIME '23:59:59' AS snapshot_at
                FROM measurement_bounds AS bounds
                CROSS JOIN LATERAL GENERATE_SERIES(
                    bounds.first_day + 14,
                    bounds.last_day,
                    INTERVAL '7 days'
                ) AS snapshot_day
                WHERE bounds.first_day IS NOT NULL
            ), equipment_snapshots AS (
                SELECT
                    e.id_equipo,
                    e.codigo_interno,
                    e.nombre,
                    -- No existe historial de estados del equipo. Se usa un
                    -- estado neutro para no filtrar el estado actual al pasado.
                    'OPERATIVO'::TEXT AS estado,
                    s.snapshot_at
                FROM equipos AS e
                CROSS JOIN snapshots AS s
                WHERE e.estado <> 'DADO_DE_BAJA'
            ), normalized_measurements AS (
                SELECT
                    es.id_equipo,
                    es.snapshot_at,
                    m.medido_en,
                    CASE
                        WHEN v.valor_maximo = v.valor_minimo THEN 0::DOUBLE PRECISION
                        ELSE (
                            (m.valor - v.valor_minimo)
                            / (v.valor_maximo - v.valor_minimo)
                        )::DOUBLE PRECISION
                    END AS range_position,
                    CASE
                        WHEN m.valor < v.valor_minimo THEN (
                            (v.valor_minimo - m.valor)
                            / NULLIF(v.valor_maximo - v.valor_minimo, 0)
                        )::DOUBLE PRECISION
                        WHEN m.valor > v.valor_maximo THEN (
                            (m.valor - v.valor_maximo)
                            / NULLIF(v.valor_maximo - v.valor_minimo, 0)
                        )::DOUBLE PRECISION
                        ELSE 0::DOUBLE PRECISION
                    END AS deviation
                FROM equipment_snapshots AS es
                INNER JOIN mediciones_operativas AS m
                    ON m.id_equipo = es.id_equipo
                   AND m.medido_en > es.snapshot_at - INTERVAL '30 days'
                   AND m.medido_en <= es.snapshot_at
                INNER JOIN variables_operativas AS v
                    ON v.id_variable = m.id_variable
            ), measurement_stats AS (
                SELECT
                    id_equipo,
                    snapshot_at,
                    COUNT(*) AS measurement_count,
                    AVG((deviation > 0)::INTEGER)::DOUBLE PRECISION
                        AS out_of_range_ratio,
                    AVG(deviation)::DOUBLE PRECISION AS mean_deviation,
                    MAX(deviation)::DOUBLE PRECISION AS maximum_deviation,
                    COALESCE(
                        REGR_SLOPE(
                            range_position,
                            EXTRACT(EPOCH FROM medido_en) / 86400
                        ),
                        0
                    )::DOUBLE PRECISION AS trend_per_day,
                    MAX(medido_en) AS last_measurement
                FROM normalized_measurements
                GROUP BY id_equipo, snapshot_at
            )
            SELECT
                es.id_equipo,
                es.codigo_interno,
                es.nombre,
                es.estado,
                es.snapshot_at,
                ms.measurement_count,
                ms.out_of_range_ratio,
                ms.mean_deviation,
                ms.maximum_deviation,
                ms.trend_per_day,
                COUNT(m.id_mantenimiento) FILTER (
                    WHERE m.tipo = 'CORRECTIVO'
                      AND m.estado <> 'CANCELADO'
                      AND COALESCE(m.fecha_fin, m.fecha_inicio, m.fecha_programada)
                          > es.snapshot_at - INTERVAL '180 days'
                      AND COALESCE(m.fecha_fin, m.fecha_inicio, m.fecha_programada)
                          <= es.snapshot_at
                ) AS correctives_180d,
                LEAST(
                    730,
                    GREATEST(
                        0,
                        COALESCE(
                            EXTRACT(EPOCH FROM (
                                es.snapshot_at - MAX(
                                    COALESCE(m.fecha_fin, m.fecha_inicio, m.fecha_programada)
                                ) FILTER (
                                    WHERE m.estado = 'COMPLETADO'
                                      AND COALESCE(m.fecha_fin, m.fecha_inicio, m.fecha_programada)
                                          <= es.snapshot_at
                                )
                            )) / 86400,
                            365
                        )
                    )
                ) AS days_since_maintenance,
                LEAST(
                    365,
                    GREATEST(
                        0,
                        EXTRACT(EPOCH FROM (es.snapshot_at - ms.last_measurement)) / 86400
                    )
                ) AS days_since_last_measurement,
                CASE WHEN EXISTS (
                    SELECT 1
                    FROM mantenimientos AS future_corrective
                    WHERE future_corrective.id_equipo = es.id_equipo
                      AND future_corrective.tipo = 'CORRECTIVO'
                      AND future_corrective.estado <> 'CANCELADO'
                      AND COALESCE(
                          future_corrective.fecha_inicio,
                          future_corrective.fecha_programada
                      ) > es.snapshot_at
                      AND COALESCE(
                          future_corrective.fecha_inicio,
                          future_corrective.fecha_programada
                      ) <= es.snapshot_at + INTERVAL '30 days'
                ) THEN 1 ELSE 0 END AS target
            FROM equipment_snapshots AS es
            INNER JOIN measurement_stats AS ms
                ON ms.id_equipo = es.id_equipo
               AND ms.snapshot_at = es.snapshot_at
            LEFT JOIN mantenimientos AS m ON m.id_equipo = es.id_equipo
            WHERE ms.measurement_count >= 5
            GROUP BY
                es.id_equipo,
                es.codigo_interno,
                es.nombre,
                es.estado,
                es.snapshot_at,
                ms.measurement_count,
                ms.out_of_range_ratio,
                ms.mean_deviation,
                ms.maximum_deviation,
                ms.trend_per_day,
                ms.last_measurement
            ORDER BY es.snapshot_at, es.codigo_interno
            """
        )
        return cursor.fetchall()
