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
        ),
        (
            'Equipo industrial', 'DEMO-EQ-011', 'Transportador de banda',
            'Dorner', '3200 Series', 'SN-DEMO-011',
            'Planta 1 · Línea B', 'OPERATIVO',
            'Transportador principal de producto entre ensamble y empaque.', DATE '2022-05-11'
        ),
        (
            'Equipo industrial', 'DEMO-EQ-012', 'Prensa hidráulica',
            'Bosch Rexroth', 'HDP 160', 'SN-DEMO-012',
            'Planta 2 · Formado', 'OPERATIVO',
            'Prensa de 160 toneladas para formado de componentes.', DATE '2021-08-23'
        ),
        (
            'Climatización', 'DEMO-EQ-013', 'Chiller de proceso',
            'Carrier', 'AquaForce 30XA', 'SN-DEMO-013',
            'Azotea · Producción', 'OPERATIVO',
            'Enfriador de agua para el circuito de proceso.', DATE '2023-02-14'
        ),
        (
            'Equipo eléctrico', 'DEMO-EQ-014', 'Transformador seco',
            'Schneider Electric', 'Trihal 500 kVA', 'SN-DEMO-014',
            'Subestación norte', 'OPERATIVO',
            'Transformador seco que alimenta las líneas A y B.', DATE '2020-12-03'
        ),
        (
            'Equipo industrial', 'DEMO-EQ-015', 'Colector de polvo',
            'Donaldson', 'Torit DFO 3-6', 'SN-DEMO-015',
            'Planta 2 · Corte', 'FUERA_DE_SERVICIO',
            'Sistema de extracción de partículas del área de corte.', DATE '2019-07-19'
        ),
        (
            'Climatización', 'DEMO-EQ-016', 'Ventilador de extracción',
            'Greenheck', 'Centrifugal BC-18', 'SN-DEMO-016',
            'Planta 1 · Techo', 'OPERATIVO',
            'Ventilador centrífugo para renovación de aire del área productiva.', DATE '2022-10-27'
        ),
        (
            'Equipo industrial', 'DEMO-EQ-017', 'Empacadora automática',
            'Sidel', 'Cermex WB46', 'SN-DEMO-017',
            'Planta 1 · Empaque', 'OPERATIVO',
            'Equipo automático de formado y cerrado de cajas.', DATE '2024-03-08'
        ),
        (
            'Equipo eléctrico', 'DEMO-EQ-018', 'UPS de sala de control',
            'APC', 'Galaxy VS 40kW', 'SN-DEMO-018',
            'Sala eléctrica 1', 'OPERATIVO',
            'Respaldo eléctrico para controladores y estaciones de operación.', DATE '2024-06-17'
        ),
        (
            'Equipo industrial', 'DEMO-EQ-019', 'Bomba de agua tratada',
            'Wilo', 'CronoBloc BL 50/160', 'SN-DEMO-019',
            'Servicios · Tratamiento', 'OPERATIVO',
            'Bomba de impulsión del circuito de agua tratada.', DATE '2023-09-29'
        ),
        (
            'Equipo industrial', 'DEMO-EQ-020', 'Secador de aire comprimido',
            'Kaeser', 'SECOTEC TG 520', 'SN-DEMO-020',
            'Cuarto de máquinas', 'FUERA_DE_SERVICIO',
            'Secador frigorífico del sistema de aire comprimido.', DATE '2020-04-06'
        ),
        (
            'Equipo industrial', 'DEMO-EQ-021', 'Centro de maquinado CNC',
            'Haas', 'VF-2SS', 'SN-DEMO-021',
            'Planta 2 · Maquinado', 'OPERATIVO',
            'Centro de maquinado vertical para componentes de precisión.', DATE '2025-02-10'
        ),
        (
            'Equipo industrial', 'DEMO-EQ-022', 'Horno de curado',
            'Despatch', 'LAC2-18', 'SN-DEMO-022',
            'Planta 2 · Acabados', 'FUERA_DE_SERVICIO',
            'Horno eléctrico para curado de recubrimientos.', DATE '2019-11-25'
        ),
        (
            'Climatización', 'DEMO-EQ-023', 'Torre de enfriamiento',
            'BAC', 'Series 3000', 'SN-DEMO-023',
            'Patio de servicios', 'OPERATIVO',
            'Torre de enfriamiento del circuito cerrado de proceso.', DATE '2021-06-18'
        ),
        (
            'Equipo eléctrico', 'DEMO-EQ-024', 'Centro de control de motores',
            'Siemens', 'SIVACON S8', 'SN-DEMO-024',
            'Sala eléctrica 2', 'OPERATIVO',
            'Centro de control para motores de la Planta 2.', DATE '2023-07-12'
        ),
        (
            'Equipo industrial', 'DEMO-EQ-025', 'Compresor auxiliar',
            'Ingersoll Rand', 'R11i', 'SN-DEMO-025',
            'Almacén técnico', 'DADO_DE_BAJA',
            'Compresor retirado por obsolescencia y alto consumo energético.', DATE '2016-01-20'
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
    ),
    (
        'TEMP-ACEITE', 'Temperatura de aceite', '°C',
        'Temperatura del aceite en el circuito de lubricación o hidráulico.',
        35, 95
    ),
    (
        'CAUDAL', 'Caudal de proceso', 'm³/h',
        'Caudal instantáneo del fluido conducido por el equipo.',
        20, 120
    ),
    (
        'RPM', 'Velocidad de rotación', 'rpm',
        'Velocidad de giro del eje principal durante la operación.',
        900, 3600
    ),
    (
        'HUMEDAD', 'Humedad relativa', '%',
        'Humedad relativa medida en el entorno del equipo.',
        20, 70
    ),
    (
        'POTENCIA', 'Potencia activa', 'kW',
        'Potencia eléctrica activa consumida durante la operación.',
        0, 75
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
        ('MP-DEMO-013', 'DEMO-EQ-009', 'CORRECTIVO', 'CANCELADO', -31, NULL, NULL, TIME '11:00', NULL, NULL, NULL, 'Prueba del generador bajo carga', 'Cancelada hasta instalar el nuevo regulador de voltaje.'),
        ('MP-DEMO-014', 'DEMO-EQ-011', 'PREVENTIVO', 'COMPLETADO', -171, -171, -171, TIME '06:30', TIME '06:38', TIME '09:15', 1740.00, 'Alineación y lubricación del transportador', 'Se ajustó la tensión de banda y se lubricaron los rodamientos.'),
        ('MP-DEMO-015', 'DEMO-EQ-012', 'PREVENTIVO', 'COMPLETADO', -162, -162, -162, TIME '07:00', TIME '07:10', TIME '11:30', 2860.00, 'Cambio de filtros del sistema hidráulico', 'Aceite limpio y presión estable después del cambio.'),
        ('MP-DEMO-016', 'DEMO-EQ-013', 'CORRECTIVO', 'COMPLETADO', -151, -151, -150, TIME '10:00', TIME '10:20', TIME '13:40', 9360.00, 'Reparación de fuga de refrigerante', 'Se reparó la unión y se verificó la carga de refrigerante.'),
        ('MP-DEMO-017', 'DEMO-EQ-014', 'PREVENTIVO', 'COMPLETADO', -143, -143, -143, TIME '05:30', TIME '05:42', TIME '08:25', 3420.00, 'Inspección termográfica del transformador', 'Temperaturas uniformes; conexiones sin evidencia de sobrecalentamiento.'),
        ('MP-DEMO-018', 'DEMO-EQ-015', 'CORRECTIVO', 'COMPLETADO', -128, -128, -127, TIME '12:00', TIME '12:30', TIME '09:10', 6840.00, 'Cambio de válvulas de pulso del colector', 'Se sustituyeron cuatro válvulas y se limpió el múltiple.'),
        ('MP-DEMO-019', 'DEMO-EQ-016', 'PREVENTIVO', 'COMPLETADO', -119, -119, -119, TIME '08:00', TIME '08:05', TIME '10:00', 1250.00, 'Limpieza y balanceo del ventilador', 'Vibración final dentro del rango permitido.'),
        ('MP-DEMO-020', 'DEMO-EQ-017', 'PREVENTIVO', 'COMPLETADO', -105, -105, -105, TIME '15:00', TIME '15:10', TIME '18:30', 2380.00, 'Ajuste de cadenas y sensores de la empacadora', 'Sensores de presencia calibrados y cadenas lubricadas.'),
        ('MP-DEMO-021', 'DEMO-EQ-018', 'PREVENTIVO', 'COMPLETADO', -96, -96, -96, TIME '09:00', TIME '09:12', TIME '11:05', 1650.00, 'Prueba de autonomía y revisión del banco de baterías', 'Autonomía medida de 41 minutos con carga operativa.'),
        ('MP-DEMO-022', 'DEMO-EQ-019', 'CORRECTIVO', 'COMPLETADO', -84, -84, -84, TIME '13:00', TIME '13:15', TIME '17:25', 5720.00, 'Sustitución del sello de la bomba de agua tratada', 'Sin fugas durante la prueba de operación de una hora.'),
        ('MP-DEMO-023', 'DEMO-EQ-020', 'PREVENTIVO', 'COMPLETADO', -76, -76, -76, TIME '07:30', TIME '07:38', TIME '10:45', 1980.00, 'Limpieza de condensador y drenaje automático', 'Se retiró acumulación de polvo y se probó el drenaje.'),
        ('MP-DEMO-024', 'DEMO-EQ-021', 'PREVENTIVO', 'COMPLETADO', -64, -64, -64, TIME '06:00', TIME '06:10', TIME '12:20', 4180.00, 'Servicio de husillo y cambio de refrigerante CNC', 'Concentración del refrigerante ajustada a especificación.'),
        ('MP-DEMO-025', 'DEMO-EQ-022', 'CORRECTIVO', 'COMPLETADO', -57, -57, -56, TIME '14:00', TIME '14:25', TIME '10:15', 11240.00, 'Sustitución de resistencias del horno', 'Se reemplazaron dos bancos y se validó uniformidad térmica.'),
        ('MP-DEMO-026', 'DEMO-EQ-023', 'PREVENTIVO', 'COMPLETADO', -44, -44, -44, TIME '07:00', TIME '07:15', TIME '12:00', 3650.00, 'Limpieza de relleno y revisión de boquillas', 'Se recuperó el caudal nominal de recirculación.'),
        ('MP-DEMO-027', 'DEMO-EQ-024', 'PREVENTIVO', 'COMPLETADO', -35, -35, -35, TIME '05:00', TIME '05:12', TIME '08:40', 2740.00, 'Reapriete y limpieza del centro de control', 'Se corrigieron dos conexiones con torque por debajo del valor indicado.'),
        ('MP-DEMO-028', 'DEMO-EQ-011', 'CORRECTIVO', 'COMPLETADO', -27, -27, -27, TIME '11:00', TIME '11:08', TIME '14:35', 3890.00, 'Cambio de rodamiento en polea motriz', 'Rodamiento sustituido; temperatura estable en prueba final.'),
        ('MP-DEMO-029', 'DEMO-EQ-012', 'CORRECTIVO', 'COMPLETADO', -19, -19, -19, TIME '08:00', TIME '08:20', TIME '16:10', 8460.00, 'Corrección de pérdida de presión hidráulica', 'Se reemplazó la válvula de alivio y se ajustó la presión.'),
        ('MP-DEMO-030', 'DEMO-EQ-013', 'PREVENTIVO', 'COMPLETADO', -10, -10, -10, TIME '09:00', TIME '09:05', TIME '12:45', 2960.00, 'Limpieza de condensadores del chiller', 'Aproximación térmica normal después de la limpieza.'),
        ('MP-DEMO-031', 'DEMO-EQ-015', 'CORRECTIVO', 'EN_PROCESO', -2, -2, NULL, TIME '07:00', TIME '07:18', NULL, 6250.00, 'Diagnóstico de baja succión del colector', 'Se revisan filtros, ductos y secuencia de limpieza por pulsos.'),
        ('MP-DEMO-032', 'DEMO-EQ-022', 'CORRECTIVO', 'EN_PROCESO', -1, -1, NULL, TIME '06:30', TIME '06:45', NULL, 7800.00, 'Diagnóstico de variación térmica del horno', 'Pendiente revisar contactores y sensor de la zona posterior.'),
        ('MP-DEMO-033', 'DEMO-EQ-016', 'PREVENTIVO', 'PROGRAMADO', 2, NULL, NULL, TIME '07:30', NULL, NULL, 1380.00, 'Inspección mensual del sistema de extracción', 'Verificar vibración, tensión de bandas y limpieza de aspas.'),
        ('MP-DEMO-034', 'DEMO-EQ-017', 'PREVENTIVO', 'PROGRAMADO', 5, NULL, NULL, TIME '15:30', NULL, NULL, 2450.00, 'Servicio preventivo de la empacadora', 'Reservar kit de cadenas y sensores fotoeléctricos.'),
        ('MP-DEMO-035', 'DEMO-EQ-018', 'PREVENTIVO', 'PROGRAMADO', 10, NULL, NULL, TIME '09:00', NULL, NULL, 1720.00, 'Prueba mensual de transferencia de la UPS', 'Coordinar prueba con el responsable de la sala de control.'),
        ('MP-DEMO-036', 'DEMO-EQ-019', 'PREVENTIVO', 'PROGRAMADO', 13, NULL, NULL, TIME '08:00', NULL, NULL, 1580.00, 'Inspección de bomba y válvula de retención', 'Tomar lectura de presión antes y después del servicio.'),
        ('MP-DEMO-037', 'DEMO-EQ-021', 'PREVENTIVO', 'PROGRAMADO', 18, NULL, NULL, TIME '06:00', NULL, NULL, 4350.00, 'Mantenimiento mensual del centro de maquinado', 'Programar después de completar la orden de producción vigente.'),
        ('MP-DEMO-038', 'DEMO-EQ-023', 'PREVENTIVO', 'PROGRAMADO', 24, NULL, NULL, TIME '07:00', NULL, NULL, 3820.00, 'Tratamiento y limpieza de torre de enfriamiento', 'Coordinar análisis de agua y disponibilidad de biocida.'),
        ('MP-DEMO-039', 'DEMO-EQ-024', 'PREVENTIVO', 'PROGRAMADO', 29, NULL, NULL, TIME '05:30', NULL, NULL, 2890.00, 'Inspección semestral del centro de control', 'Requiere libranza eléctrica autorizada.'),
        ('MP-DEMO-040', 'DEMO-EQ-020', 'CORRECTIVO', 'CANCELADO', -6, NULL, NULL, TIME '12:00', NULL, NULL, NULL, 'Prueba de desempeño del secador', 'Cancelada porque el repuesto todavía no ha sido recibido.')
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

-- Serie histórica de 45 días para los equipos adicionales. Cada combinación
-- equipo/variable contiene una sola excepción deliberada; el resto conserva
-- pequeñas oscilaciones deterministas dentro de su rango permitido.
DO $$
DECLARE
    v_usuario BIGINT;
    v_atendedor BIGINT;
    v_lote BIGINT;
    v_registros INTEGER;
BEGIN
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

    IF v_usuario IS NOT NULL AND NOT EXISTS (
        SELECT 1
        FROM lotes_mediciones
        WHERE nombre_archivo = 'simulacion-historica-demo-45d'
    ) THEN
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
            'simulacion-historica-demo-45d',
            1260
        )
        RETURNING id_lote INTO v_lote;

        WITH series_config (
            numero,
            codigo_equipo,
            codigo_variable,
            valor_base,
            amplitud,
            valor_alerta
        ) AS (
            VALUES
                (1, 'DEMO-EQ-011', 'VIB-RMS', 2.8, 0.7, 8.2),
                (2, 'DEMO-EQ-011', 'CORRIENTE-L1', 17.5, 2.0, 32.5),
                (3, 'DEMO-EQ-012', 'TEMP-ACEITE', 67.0, 5.5, 99.0),
                (4, 'DEMO-EQ-012', 'PRES-DESC', 6.8, 0.5, 4.0),
                (5, 'DEMO-EQ-013', 'TEMP-ROD', 59.0, 4.5, 89.0),
                (6, 'DEMO-EQ-013', 'CORRIENTE-L1', 21.0, 2.4, 32.0),
                (7, 'DEMO-EQ-014', 'VOLTAJE-L1', 226.0, 3.5, 204.0),
                (8, 'DEMO-EQ-014', 'TEMP-ROD', 64.0, 4.0, 88.0),
                (9, 'DEMO-EQ-015', 'VIB-RMS', 4.1, 0.8, 8.5),
                (10, 'DEMO-EQ-015', 'CORRIENTE-L1', 19.0, 2.2, 33.0),
                (11, 'DEMO-EQ-016', 'VIB-RMS', 3.0, 0.6, 7.8),
                (12, 'DEMO-EQ-016', 'RPM', 1740.0, 120.0, 3750.0),
                (13, 'DEMO-EQ-017', 'CORRIENTE-L1', 24.0, 2.6, 32.0),
                (14, 'DEMO-EQ-017', 'RPM', 1480.0, 90.0, 820.0),
                (15, 'DEMO-EQ-018', 'VOLTAJE-L1', 227.0, 3.0, 244.0),
                (16, 'DEMO-EQ-018', 'POTENCIA', 31.0, 4.0, 79.0),
                (17, 'DEMO-EQ-019', 'CAUDAL', 74.0, 8.0, 16.0),
                (18, 'DEMO-EQ-019', 'PRES-DESC', 6.4, 0.6, 9.1),
                (19, 'DEMO-EQ-020', 'TEMP-ROD', 63.0, 5.0, 90.0),
                (20, 'DEMO-EQ-020', 'PRES-DESC', 6.1, 0.5, 4.1),
                (21, 'DEMO-EQ-021', 'VIB-RMS', 2.4, 0.5, 7.7),
                (22, 'DEMO-EQ-021', 'POTENCIA', 42.0, 6.0, 81.0),
                (23, 'DEMO-EQ-022', 'TEMP-ROD', 74.0, 5.5, 91.0),
                (24, 'DEMO-EQ-022', 'TEMP-ACEITE', 72.0, 6.0, 101.0),
                (25, 'DEMO-EQ-023', 'TEMP-ROD', 57.0, 4.0, 18.0),
                (26, 'DEMO-EQ-023', 'CAUDAL', 88.0, 9.0, 126.0),
                (27, 'DEMO-EQ-024', 'VOLTAJE-L1', 225.0, 4.0, 205.0),
                (28, 'DEMO-EQ-024', 'CORRIENTE-L1', 20.0, 2.5, 31.5)
        ),
        puntos AS (
            SELECT
                configuracion.*,
                paso,
                CASE
                    WHEN paso = MOD(configuracion.numero * 7, 45)
                        THEN configuracion.valor_alerta
                    ELSE configuracion.valor_base
                        + SIN((paso + configuracion.numero) / 3.7)
                        * configuracion.amplitud
                END AS valor
            FROM series_config AS configuracion
            CROSS JOIN GENERATE_SERIES(0, 44) AS paso
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
            CURRENT_DATE - (44 - p.paso) + TIME '08:00'
        FROM puntos AS p
        JOIN equipos AS e ON e.codigo_interno = p.codigo_equipo
        JOIN variables_operativas AS v ON v.codigo = p.codigo_variable
        ORDER BY p.numero, p.paso;

        GET DIAGNOSTICS v_registros = ROW_COUNT;

        UPDATE alertas_rango AS a
        SET generada_en = m.medido_en
        FROM mediciones_operativas AS m
        WHERE a.id_medicion = m.id_medicion
          AND m.id_lote = v_lote;

        IF v_atendedor IS NOT NULL THEN
            UPDATE alertas_rango AS a
            SET estado = CASE
                    WHEN RIGHT(e.codigo_interno, 3)::INTEGER % 6 = 0
                        THEN 'DESCARTADA'
                    ELSE 'ATENDIDA'
                END,
                atendida_por = v_atendedor,
                atendida_en = m.medido_en + INTERVAL '2 hours',
                observaciones = CASE
                    WHEN RIGHT(e.codigo_interno, 3)::INTEGER % 6 = 0
                        THEN 'Lectura descartada tras comprobar el sensor con un instrumento patrón.'
                    ELSE 'La condición fue revisada y el equipo regresó a su rango operativo.'
                END
            FROM mediciones_operativas AS m
            JOIN equipos AS e ON e.id_equipo = m.id_equipo
            WHERE a.id_medicion = m.id_medicion
              AND m.id_lote = v_lote
              AND m.medido_en < CURRENT_TIMESTAMP - INTERVAL '5 days';
        END IF;

        UPDATE lotes_mediciones
        SET estado = 'COMPLETADO',
            registros_totales = v_registros,
            registros_validos = v_registros,
            finalizado_en = CURRENT_TIMESTAMP
        WHERE id_lote = v_lote;
    END IF;

    -- Importación de cuatro lecturas diarias durante las dos últimas semanas.
    IF v_usuario IS NOT NULL AND NOT EXISTS (
        SELECT 1
        FROM lotes_mediciones
        WHERE nombre_archivo = 'lecturas-turnos-demo.csv'
    ) THEN
        INSERT INTO lotes_mediciones (
            registrado_por,
            tipo_origen,
            estado,
            nombre_archivo,
            registros_totales,
            detalle_error
        )
        VALUES (
            v_usuario,
            'IMPORTACION',
            'PROCESANDO',
            'lecturas-turnos-demo.csv',
            1076,
            '12 filas rechazadas: valor vacío, fecha inválida o código de equipo inexistente.'
        )
        RETURNING id_lote INTO v_lote;

        WITH series_config (
            numero,
            codigo_equipo,
            codigo_variable,
            valor_base,
            amplitud,
            paso_alerta,
            valor_alerta
        ) AS (
            VALUES
                (1, 'DEMO-EQ-001', 'TEMP-ROD', 62.0, 4.0, 55, 90.0),
                (2, 'DEMO-EQ-001', 'VIB-RMS', 3.2, 0.7, 53, 8.0),
                (3, 'DEMO-EQ-001', 'PRES-DESC', 6.6, 0.4, 51, 4.0),
                (4, 'DEMO-EQ-002', 'TEMP-ROD', 67.0, 4.5, 49, 91.0),
                (5, 'DEMO-EQ-002', 'VIB-RMS', 4.0, 0.8, 47, 7.9),
                (6, 'DEMO-EQ-002', 'CORRIENTE-L1', 22.0, 2.0, 45, 32.0),
                (7, 'DEMO-EQ-003', 'PRES-DESC', 6.7, 0.5, 43, 3.8),
                (8, 'DEMO-EQ-004', 'VOLTAJE-L1', 226.0, 3.2, 41, 244.0),
                (9, 'DEMO-EQ-004', 'CORRIENTE-L1', 18.0, 1.8, 39, 31.0),
                (10, 'DEMO-EQ-005', 'TEMP-ROD', 71.0, 4.0, 37, 89.0),
                (11, 'DEMO-EQ-005', 'HUMEDAD', 46.0, 6.0, 35, 74.0),
                (12, 'DEMO-EQ-011', 'VIB-RMS', 3.0, 0.6, 33, 7.8),
                (13, 'DEMO-EQ-012', 'TEMP-ACEITE', 69.0, 5.0, 31, 99.0),
                (14, 'DEMO-EQ-012', 'PRES-DESC', 6.9, 0.4, 29, 4.2),
                (15, 'DEMO-EQ-013', 'TEMP-ROD', 60.0, 4.0, 27, 88.0),
                (16, 'DEMO-EQ-013', 'CORRIENTE-L1', 21.0, 2.0, 25, 31.5),
                (17, 'DEMO-EQ-017', 'RPM', 1490.0, 80.0, 23, 3700.0),
                (18, 'DEMO-EQ-019', 'CAUDAL', 76.0, 7.0, 21, 18.0),
                (19, 'DEMO-EQ-023', 'CAUDAL', 89.0, 8.0, 19, 125.0)
        ),
        puntos AS (
            SELECT
                configuracion.*,
                paso,
                CASE
                    WHEN paso = configuracion.paso_alerta
                        THEN configuracion.valor_alerta
                    ELSE configuracion.valor_base
                        + SIN((paso + configuracion.numero) / 4.2)
                        * configuracion.amplitud
                END AS valor
            FROM series_config AS configuracion
            CROSS JOIN GENERATE_SERIES(0, 55) AS paso
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
            CURRENT_DATE - 14 + p.paso * INTERVAL '6 hours'
        FROM puntos AS p
        JOIN equipos AS e ON e.codigo_interno = p.codigo_equipo
        JOIN variables_operativas AS v ON v.codigo = p.codigo_variable
        ORDER BY p.numero, p.paso;

        GET DIAGNOSTICS v_registros = ROW_COUNT;

        UPDATE alertas_rango AS a
        SET generada_en = m.medido_en
        FROM mediciones_operativas AS m
        WHERE a.id_medicion = m.id_medicion
          AND m.id_lote = v_lote;

        IF v_atendedor IS NOT NULL THEN
            UPDATE alertas_rango AS a
            SET estado = CASE
                    WHEN RIGHT(e.codigo_interno, 3)::INTEGER % 7 = 0
                        THEN 'DESCARTADA'
                    ELSE 'ATENDIDA'
                END,
                atendida_por = v_atendedor,
                atendida_en = m.medido_en + INTERVAL '90 minutes',
                observaciones = CASE
                    WHEN RIGHT(e.codigo_interno, 3)::INTEGER % 7 = 0
                        THEN 'Dato descartado por inconsistencia detectada durante la revisión del lote.'
                    ELSE 'Alerta revisada durante el siguiente turno; lectura posterior dentro de rango.'
                END
            FROM mediciones_operativas AS m
            JOIN equipos AS e ON e.id_equipo = m.id_equipo
            WHERE a.id_medicion = m.id_medicion
              AND m.id_lote = v_lote
              AND m.medido_en < CURRENT_TIMESTAMP - INTERVAL '2 days';
        END IF;

        UPDATE lotes_mediciones
        SET estado = 'COMPLETADO',
            registros_totales = v_registros + 12,
            registros_validos = v_registros,
            registros_rechazados = 12,
            finalizado_en = CURRENT_TIMESTAMP
        WHERE id_lote = v_lote;
    END IF;

    -- Un lote fallido ayuda a representar de forma realista el historial de
    -- importaciones sin crear mediciones inválidas.
    IF v_usuario IS NOT NULL THEN
        INSERT INTO lotes_mediciones (
            registrado_por,
            tipo_origen,
            estado,
            nombre_archivo,
            registros_totales,
            registros_validos,
            registros_rechazados,
            detalle_error,
            iniciado_en,
            finalizado_en
        )
        SELECT
            v_usuario,
            'IMPORTACION',
            'FALLIDO',
            'sensores-turno-noche-demo.csv',
            45,
            0,
            45,
            'El archivo no contiene la columna obligatoria medido_en.',
            CURRENT_TIMESTAMP - INTERVAL '9 days',
            CURRENT_TIMESTAMP - INTERVAL '9 days' + INTERVAL '2 minutes'
        WHERE NOT EXISTS (
            SELECT 1
            FROM lotes_mediciones
            WHERE nombre_archivo = 'sensores-turno-noche-demo.csv'
        );
    END IF;
END;
$$;

COMMIT;
