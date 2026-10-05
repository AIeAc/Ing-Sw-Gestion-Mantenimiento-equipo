BEGIN;

-- Datos visuales de demostración para los Sprints 1, 2 y 3.
-- Las inserciones son repetibles: cada registro usa una clave o referencia
-- DEMO estable para conservar los datos existentes al ejecutar el archivo de
-- nuevo. Las fechas se calculan respecto al día de carga para que el dashboard,
-- el calendario y las gráficas siempre tengan información reciente.

INSERT INTO categorias (nombre, descripcion)
VALUES
    ('Equipo industrial', 'Maquinaria utilizada en los procesos de producción.'),
    ('Equipo eléctrico', 'Equipos de alimentación, distribución y respaldo eléctrico.'),
    ('Climatización', 'Equipos de ventilación y control de temperatura.'),
    ('PC', 'Equipos de cómputo utilizados para supervisión y servicios internos.')
ON CONFLICT DO NOTHING;

WITH usuario_registrador AS (
    SELECT id_usuario
    FROM usuarios
    WHERE activo = TRUE
    ORDER BY id_usuario
    LIMIT 1
),
datos_equipo (
    categoria,
    codigo_interno,
    nombre,
    marca,
    modelo,
    numero_serie,
    ubicacion,
    estado,
    descripcion,
    fecha_adquisicion
) AS (
    VALUES
        (
            'Equipo industrial', 'DEMO-EQ-001', 'Bomba centrífuga',
            'KSB', 'Etanorm 050-032-160', 'SN-DEMO-001',
            'Planta 1 · Línea A', 'OPERATIVO',
            'Bomba principal del circuito de recirculación.', DATE '2023-04-18'
        ),
        (
            'Equipo eléctrico', 'DEMO-EQ-002', 'Motor eléctrico principal',
            'Siemens', 'SIMOTICS GP', 'SN-DEMO-002',
            'Planta 1 · Línea A', 'OPERATIVO',
            'Motor trifásico acoplado a la línea de producción.', DATE '2022-09-07'
        ),
        (
            'Equipo industrial', 'DEMO-EQ-003', 'Compresor de aire',
            'Atlas Copco', 'GA 15', 'SN-DEMO-003',
            'Cuarto de máquinas', 'FUERA_DE_SERVICIO',
            'Compresor de tornillo; pendiente de revisión técnica.', DATE '2021-11-12'
        ),
        (
            'Equipo eléctrico', 'DEMO-EQ-004', 'Tablero de distribución',
            'Schneider Electric', 'PrismaSeT P', 'SN-DEMO-004',
            'Subestación', 'OPERATIVO',
            'Tablero general de baja tensión del área productiva.', DATE '2024-02-21'
        ),
        (
            'Climatización', 'DEMO-EQ-005', 'Unidad de aire acondicionado',
            'Trane', 'Voyager', 'SN-DEMO-005',
            'Edificio administrativo', 'OPERATIVO',
            'Unidad de climatización de las oficinas principales.', DATE '2020-06-30'
        ),
        (
            'Equipo industrial', 'DEMO-EQ-006', 'Extractor industrial',
            'Soler & Palau', 'HXM-400', 'SN-DEMO-006',
            'Área de producción', 'DADO_DE_BAJA',
            'Extractor retirado del servicio y conservado para referencia.', DATE '2018-03-15'
        ),
        (
            'PC', 'DEMO-EQ-007', 'Estación de monitoreo',
            'Dell', 'Precision 3660', 'SN-DEMO-007',
            'Sala de control', 'OPERATIVO',
            'Equipo utilizado para supervisar el inventario de planta.', DATE '2024-08-09'
        ),
        (
            'PC', 'DEMO-EQ-008', 'Servidor de inventario',
            'HPE', 'ProLiant ML30', 'SN-DEMO-008',
            'Centro de datos', 'OPERATIVO',
            'Servidor local para los servicios internos del sistema.', DATE '2023-12-05'
        ),
        (
            'Equipo eléctrico', 'DEMO-EQ-009', 'Generador de respaldo',
            'Generac', 'SG032', 'SN-DEMO-009',
            'Patio técnico', 'FUERA_DE_SERVICIO',
            'Generador en espera de una inspección eléctrica.', DATE '2019-10-22'
        ),
        (
            'Equipo industrial', 'DEMO-EQ-010', 'Bomba de respaldo',
            'Grundfos', 'CR 10-6', 'SN-DEMO-010',
            'Planta 2 · Servicios', 'OPERATIVO',
            'Bomba auxiliar disponible para contingencias.', DATE '2025-01-16'
        )
)
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
SELECT
    categoria.id_categoria,
    usuario_registrador.id_usuario,
    datos_equipo.codigo_interno,
    datos_equipo.nombre,
    datos_equipo.marca,
    datos_equipo.modelo,
    datos_equipo.numero_serie,
    datos_equipo.ubicacion,
    datos_equipo.estado,
    datos_equipo.descripcion,
    datos_equipo.fecha_adquisicion
FROM datos_equipo
JOIN categorias AS categoria
    ON LOWER(categoria.nombre) = LOWER(datos_equipo.categoria)
CROSS JOIN usuario_registrador
ON CONFLICT DO NOTHING;

INSERT INTO variables_operativas (
    codigo,
    nombre,
    unidad,
    descripcion,
    valor_minimo,
    valor_maximo
)
VALUES
    (
        'TEMP-ROD', 'Temperatura de rodamiento', '°C',
        'Temperatura superficial registrada en el rodamiento principal.',
        20, 85
    ),
    (
        'VIB-RMS', 'Vibración RMS', 'mm/s',
        'Velocidad eficaz de vibración del equipo durante la operación.',
        0, 7.1
    ),
    (
        'PRES-DESC', 'Presión de descarga', 'bar',
        'Presión medida en la descarga de bombas y compresores.',
        4.5, 8.5
    ),
    (
        'CORRIENTE-L1', 'Corriente de línea L1', 'A',
        'Corriente eléctrica de la primera fase durante la operación.',
        0, 30
    ),
    (
        'VOLTAJE-L1', 'Voltaje de línea L1', 'V',
        'Voltaje entre la primera fase y neutro.',
        210, 240
    )
ON CONFLICT DO NOTHING;

-- Historial suficiente para poblar la lista, el detalle, el calendario y los
-- seis meses del dashboard. Se reutiliza el primer Técnico activo para respetar
-- la misma regla de negocio que la aplicación.
WITH usuario_registrador AS (
    SELECT id_usuario
    FROM usuarios
    WHERE activo = TRUE
    ORDER BY id_usuario
    LIMIT 1
),
tecnico AS (
    SELECT u.id_usuario
    FROM usuarios AS u
    JOIN roles AS r ON r.id_rol = u.id_rol
    WHERE u.activo = TRUE
      AND r.activo = TRUE
      AND LOWER(r.nombre) = LOWER('Técnico')
    ORDER BY u.id_usuario
    LIMIT 1
),
datos_mantenimiento (
    referencia,
    codigo_equipo,
    tipo,
    estado,
    dias_programado,
    dias_inicio,
    dias_fin,
    hora_programada,
    hora_inicio,
    hora_fin,
    costo,
    descripcion,
    observaciones
) AS (
    VALUES
        ('MP-DEMO-001', 'DEMO-EQ-001', 'PREVENTIVO', 'COMPLETADO', -158, -158, -158, TIME '08:00', TIME '08:12', TIME '10:05', 1280.00, 'Inspección, lubricación y ajuste de acoplamiento', 'Sin fugas; sello mecánico dentro de especificación.'),
        ('MP-DEMO-002', 'DEMO-EQ-002', 'CORRECTIVO', 'COMPLETADO', -137, -137, -137, TIME '13:00', TIME '13:18', TIME '17:40', 4650.00, 'Sustitución de contactor y revisión del aislamiento', 'El equipo recuperó su consumo nominal después de la intervención.'),
        ('MP-DEMO-003', 'DEMO-EQ-005', 'PREVENTIVO', 'COMPLETADO', -112, -112, -112, TIME '09:00', TIME '09:05', TIME '11:20', 1850.00, 'Limpieza de serpentines y cambio de filtros', 'Flujo de aire estable al finalizar las pruebas.'),
        ('MP-DEMO-004', 'DEMO-EQ-003', 'CORRECTIVO', 'COMPLETADO', -91, -91, -90, TIME '07:30', TIME '07:45', TIME '12:10', 7890.00, 'Reparación de fuga en la línea de descarga', 'Se reemplazaron empaques y se realizó prueba de hermeticidad.'),
        ('MP-DEMO-005', 'DEMO-EQ-004', 'PREVENTIVO', 'COMPLETADO', -69, -69, -69, TIME '16:00', TIME '16:10', TIME '18:00', 980.00, 'Termografía y reapriete de conexiones eléctricas', 'No se detectaron puntos calientes después del reapriete.'),
        ('MP-DEMO-006', 'DEMO-EQ-009', 'CORRECTIVO', 'COMPLETADO', -48, -48, -47, TIME '10:00', TIME '10:25', TIME '15:35', 12350.00, 'Diagnóstico del regulador de voltaje del generador', 'Se confirmó daño del regulador; el equipo permanece fuera de servicio.'),
        ('MP-DEMO-007', 'DEMO-EQ-001', 'PREVENTIVO', 'COMPLETADO', -24, -24, -24, TIME '08:00', TIME '08:08', TIME '09:50', 1360.00, 'Revisión mensual de bomba y sello mecánico', 'Operación normal; se ajustó ligeramente la alineación.'),
        ('MP-DEMO-008', 'DEMO-EQ-002', 'CORRECTIVO', 'COMPLETADO', -12, -12, -12, TIME '14:00', TIME '14:10', TIME '16:45', 2980.00, 'Corrección de vibración en el motor principal', 'Se ajustó la base y se verificó la alineación del conjunto.'),
        ('MP-DEMO-009', 'DEMO-EQ-003', 'CORRECTIVO', 'EN_PROCESO', -1, -1, NULL, TIME '07:00', TIME '07:20', NULL, 4200.00, 'Revisión de temperatura y presión del compresor', 'Diagnóstico en curso; pendiente validar el enfriador de aceite.'),
        ('MP-DEMO-010', 'DEMO-EQ-005', 'PREVENTIVO', 'PROGRAMADO', 3, NULL, NULL, TIME '09:30', NULL, NULL, 2100.00, 'Servicio trimestral de climatización', 'Preparar filtros, limpiador de serpentín y manómetros.'),
        ('MP-DEMO-011', 'DEMO-EQ-004', 'PREVENTIVO', 'PROGRAMADO', 8, NULL, NULL, TIME '16:00', NULL, NULL, 1150.00, 'Inspección del tablero de distribución', 'Coordinar ventana de desenergización con Producción.'),
        ('MP-DEMO-012', 'DEMO-EQ-010', 'PREVENTIVO', 'PROGRAMADO', 15, NULL, NULL, TIME '08:00', NULL, NULL, 1450.00, 'Prueba funcional de la bomba de respaldo', 'Comprobar presión, vibración y condición del acoplamiento.'),
        ('MP-DEMO-013', 'DEMO-EQ-009', 'CORRECTIVO', 'CANCELADO', -31, NULL, NULL, TIME '11:00', NULL, NULL, NULL, 'Prueba del generador bajo carga', 'Cancelada hasta instalar el nuevo regulador de voltaje.')
)
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
SELECT
    e.id_equipo,
    t.id_usuario,
    u.id_usuario,
    d.tipo,
    d.estado,
    CURRENT_DATE + d.dias_programado + d.hora_programada,
    CASE
        WHEN d.dias_inicio IS NULL THEN NULL
        ELSE CURRENT_DATE + d.dias_inicio + d.hora_inicio
    END,
    CASE
        WHEN d.dias_fin IS NULL THEN NULL
        ELSE CURRENT_DATE + d.dias_fin + d.hora_fin
    END,
    d.costo,
    d.descripcion,
    d.observaciones || ' [Referencia demo: ' || d.referencia || ']'
FROM datos_mantenimiento AS d
JOIN equipos AS e ON e.codigo_interno = d.codigo_equipo
CROSS JOIN usuario_registrador AS u
CROSS JOIN tecnico AS t
WHERE NOT EXISTS (
    SELECT 1
    FROM mantenimientos AS existente
    WHERE existente.observaciones LIKE '%[Referencia demo: ' || d.referencia || ']%'
);

-- El lote simulado genera 140 mediciones recientes y diez excepciones de
-- rango. Las alertas antiguas se dejan atendidas o descartadas; las recientes
-- permanecen pendientes para que todos los estados sean visibles en la app.
DO $$
DECLARE
    v_usuario BIGINT;
    v_atendedor BIGINT;
    v_lote BIGINT;
    v_registros INTEGER;
BEGIN
    IF EXISTS (
        SELECT 1
        FROM lotes_mediciones
        WHERE nombre_archivo = 'simulacion-planta-demo'
    ) THEN
        RETURN;
    END IF;

    SELECT id_usuario
    INTO v_usuario
    FROM usuarios
    WHERE activo = TRUE
    ORDER BY id_usuario
    LIMIT 1;

    SELECT u.id_usuario
    INTO v_atendedor
    FROM usuarios AS u
    JOIN roles AS r ON r.id_rol = u.id_rol
    WHERE u.activo = TRUE
      AND r.activo = TRUE
      AND LOWER(r.nombre) = LOWER('Técnico')
    ORDER BY u.id_usuario
    LIMIT 1;

    IF v_usuario IS NULL THEN
        RAISE NOTICE 'Se omiten mediciones demo porque no existe un usuario activo';
        RETURN;
    END IF;

    INSERT INTO lotes_mediciones (
        registrado_por,
        tipo_origen,
        estado,
        nombre_archivo,
        registros_totales
    )
    VALUES (
        v_usuario,
        'SIMULADOR',
        'PROCESANDO',
        'simulacion-planta-demo',
        140
    )
    RETURNING id_lote INTO v_lote;

    WITH series_config (
        codigo_equipo,
        codigo_variable,
        valor_base,
        amplitud,
        paso_alerta,
        valor_alerta
    ) AS (
        VALUES
            ('DEMO-EQ-001', 'TEMP-ROD', 61.0, 3.8, 11, 91.2),
            ('DEMO-EQ-001', 'VIB-RMS', 3.1, 0.7, 10, 8.4),
            ('DEMO-EQ-001', 'PRES-DESC', 6.5, 0.4, 8, 4.1),
            ('DEMO-EQ-002', 'TEMP-ROD', 66.0, 4.2, 9, 90.4),
            ('DEMO-EQ-002', 'VIB-RMS', 4.0, 0.9, 7, 7.8),
            ('DEMO-EQ-002', 'CORRIENTE-L1', 22.0, 2.1, 6, 31.8),
            ('DEMO-EQ-003', 'PRES-DESC', 6.9, 0.5, 5, 3.9),
            ('DEMO-EQ-004', 'VOLTAJE-L1', 225.0, 4.0, 4, 245.0),
            ('DEMO-EQ-005', 'TEMP-ROD', 72.0, 4.8, 12, 89.0),
            ('DEMO-EQ-009', 'VOLTAJE-L1', 224.0, 5.0, 13, 204.0)
    ),
    puntos AS (
        SELECT
            configuracion.*,
            paso,
            CASE
                WHEN paso = configuracion.paso_alerta
                    THEN configuracion.valor_alerta
                ELSE configuracion.valor_base
                    + SIN((paso + configuracion.valor_base) / 2.3)
                    * configuracion.amplitud
            END AS valor
        FROM series_config AS configuracion
        CROSS JOIN GENERATE_SERIES(0, 13) AS paso
    )
    INSERT INTO mediciones_operativas (
        id_equipo,
        id_variable,
        id_lote,
        valor,
        medido_en
    )
    SELECT
        e.id_equipo,
        v.id_variable,
        v_lote,
        ROUND(p.valor::NUMERIC, 3),
        CURRENT_DATE - (13 - p.paso) + TIME '08:00'
    FROM puntos AS p
    JOIN equipos AS e ON e.codigo_interno = p.codigo_equipo
    JOIN variables_operativas AS v ON v.codigo = p.codigo_variable
    ORDER BY p.codigo_equipo, p.codigo_variable, p.paso;

    GET DIAGNOSTICS v_registros = ROW_COUNT;

    UPDATE alertas_rango AS a
    SET generada_en = m.medido_en
    FROM mediciones_operativas AS m
    WHERE a.id_medicion = m.id_medicion
      AND m.id_lote = v_lote;

    IF v_atendedor IS NOT NULL THEN
        UPDATE alertas_rango AS a
        SET estado = CASE
                WHEN e.codigo_interno = 'DEMO-EQ-003'
                    THEN 'DESCARTADA'
                ELSE 'ATENDIDA'
            END,
            atendida_por = v_atendedor,
            atendida_en = m.medido_en + INTERVAL '3 hours',
            observaciones = CASE
                WHEN e.codigo_interno = 'DEMO-EQ-003'
                    THEN 'Lectura descartada después de verificar la calibración del sensor.'
                ELSE 'Condición revisada por el técnico; se normalizó la operación.'
            END
        FROM mediciones_operativas AS m
        JOIN equipos AS e ON e.id_equipo = m.id_equipo
        WHERE a.id_medicion = m.id_medicion
          AND m.id_lote = v_lote
          AND m.medido_en < CURRENT_TIMESTAMP - INTERVAL '4 days';
    END IF;

    UPDATE lotes_mediciones
    SET estado = 'COMPLETADO',
        registros_totales = v_registros,
        registros_validos = v_registros,
        finalizado_en = CURRENT_TIMESTAMP
    WHERE id_lote = v_lote;
END;
$$;

COMMIT;
