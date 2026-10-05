BEGIN;

CREATE TABLE mantenimientos (
    id_mantenimiento BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_equipo BIGINT NOT NULL,
    id_tecnico BIGINT NOT NULL,
    registrado_por BIGINT NOT NULL,
    tipo VARCHAR(15) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'PROGRAMADO',
    fecha_programada TIMESTAMPTZ,
    fecha_inicio TIMESTAMPTZ,
    fecha_fin TIMESTAMPTZ,
    costo NUMERIC(12, 2),
    descripcion TEXT NOT NULL,
    observaciones TEXT,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_mantenimientos_equipos
        FOREIGN KEY (id_equipo)
        REFERENCES equipos (id_equipo)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_mantenimientos_tecnicos
        FOREIGN KEY (id_tecnico)
        REFERENCES usuarios (id_usuario)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_mantenimientos_registrado_por
        FOREIGN KEY (registrado_por)
        REFERENCES usuarios (id_usuario)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT mantenimientos_tipo_valido CHECK (
        tipo IN ('PREVENTIVO', 'CORRECTIVO')
    ),
    CONSTRAINT mantenimientos_estado_valido CHECK (
        estado IN ('PROGRAMADO', 'EN_PROCESO', 'COMPLETADO', 'CANCELADO')
    ),
    CONSTRAINT mantenimientos_descripcion_no_vacia CHECK (
        BTRIM(descripcion) <> ''
    ),
    CONSTRAINT mantenimientos_costo_no_negativo CHECK (
        costo IS NULL OR costo >= 0
    ),
    CONSTRAINT mantenimientos_fechas_validas CHECK (
        fecha_fin IS NULL
        OR (fecha_inicio IS NOT NULL AND fecha_fin >= fecha_inicio)
    ),
    CONSTRAINT mantenimientos_programado_con_fecha CHECK (
        estado <> 'PROGRAMADO' OR fecha_programada IS NOT NULL
    ),
    CONSTRAINT mantenimientos_completado_con_fechas CHECK (
        estado <> 'COMPLETADO'
        OR (fecha_inicio IS NOT NULL AND fecha_fin IS NOT NULL)
    )
);

CREATE INDEX idx_mantenimientos_equipo_fecha
    ON mantenimientos (id_equipo, fecha_programada DESC);

CREATE INDEX idx_mantenimientos_tecnico_fecha
    ON mantenimientos (id_tecnico, fecha_programada DESC);

CREATE INDEX idx_mantenimientos_estado
    ON mantenimientos (estado);

CREATE INDEX idx_mantenimientos_tipo
    ON mantenimientos (tipo);

CREATE INDEX idx_mantenimientos_fecha_programada
    ON mantenimientos (fecha_programada)
    WHERE fecha_programada IS NOT NULL;

CREATE TRIGGER trg_mantenimientos_actualizado_en
BEFORE UPDATE ON mantenimientos
FOR EACH ROW
EXECUTE FUNCTION establecer_actualizado_en();

CREATE OR REPLACE FUNCTION validar_tecnico_mantenimiento()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM usuarios AS u
        JOIN roles AS r ON r.id_rol = u.id_rol
        WHERE u.id_usuario = NEW.id_tecnico
          AND u.activo
          AND r.activo
          AND LOWER(r.nombre) = LOWER('Técnico')
    ) THEN
        RAISE EXCEPTION
            'El usuario % no es un técnico activo', NEW.id_tecnico;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_mantenimientos_validar_tecnico
BEFORE INSERT OR UPDATE OF id_tecnico ON mantenimientos
FOR EACH ROW
EXECUTE FUNCTION validar_tecnico_mantenimiento();

CREATE VIEW historial_mantenimientos_equipo AS
SELECT
    m.id_mantenimiento,
    m.id_equipo,
    e.codigo_interno,
    e.nombre AS equipo,
    m.tipo,
    m.estado,
    m.fecha_programada,
    m.fecha_inicio,
    m.fecha_fin,
    COALESCE(
        m.fecha_fin,
        m.fecha_inicio,
        m.fecha_programada,
        m.creado_en
    ) AS fecha_referencia,
    m.costo,
    m.descripcion,
    m.observaciones,
    m.id_tecnico,
    CONCAT_WS(' ', u.nombre, u.apellidos) AS tecnico,
    m.creado_en,
    m.actualizado_en
FROM mantenimientos AS m
JOIN equipos AS e ON e.id_equipo = m.id_equipo
JOIN usuarios AS u ON u.id_usuario = m.id_tecnico;

CREATE VIEW calendario_mantenimientos AS
SELECT
    m.id_mantenimiento,
    m.fecha_programada,
    m.fecha_programada::DATE AS fecha,
    m.tipo,
    m.estado,
    m.descripcion,
    e.id_equipo,
    e.codigo_interno,
    e.nombre AS equipo,
    u.id_usuario AS id_tecnico,
    CONCAT_WS(' ', u.nombre, u.apellidos) AS tecnico
FROM mantenimientos AS m
JOIN equipos AS e ON e.id_equipo = m.id_equipo
JOIN usuarios AS u ON u.id_usuario = m.id_tecnico
WHERE m.fecha_programada IS NOT NULL;

COMMIT;
