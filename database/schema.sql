BEGIN;

CREATE TABLE roles (
    id_rol BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    descripcion VARCHAR(255),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT roles_nombre_no_vacio CHECK (BTRIM(nombre) <> '')
);

CREATE UNIQUE INDEX uq_roles_nombre
    ON roles (LOWER(nombre));

CREATE TABLE usuarios (
    id_usuario BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_rol BIGINT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(150) NOT NULL,
    correo VARCHAR(254) NOT NULL,
    contrasena_hash VARCHAR(255) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    ultimo_acceso TIMESTAMPTZ,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usuarios_roles
        FOREIGN KEY (id_rol)
        REFERENCES roles (id_rol)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT usuarios_nombre_no_vacio CHECK (BTRIM(nombre) <> ''),
    CONSTRAINT usuarios_apellidos_no_vacios CHECK (BTRIM(apellidos) <> ''),
    CONSTRAINT usuarios_correo_no_vacio CHECK (BTRIM(correo) <> ''),
    CONSTRAINT usuarios_correo_formato CHECK (
        correo ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'
    ),
    CONSTRAINT usuarios_contrasena_hash_no_vacia
        CHECK (BTRIM(contrasena_hash) <> '')
);

CREATE UNIQUE INDEX uq_usuarios_correo
    ON usuarios (LOWER(correo));

CREATE INDEX idx_usuarios_rol
    ON usuarios (id_rol);

CREATE TABLE categorias (
    id_categoria BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT categorias_nombre_no_vacio CHECK (BTRIM(nombre) <> '')
);

CREATE UNIQUE INDEX uq_categorias_nombre
    ON categorias (LOWER(nombre));

CREATE TABLE equipos (
    id_equipo BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_categoria BIGINT NOT NULL,
    registrado_por BIGINT NOT NULL,
    codigo_interno VARCHAR(50) NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    marca VARCHAR(100),
    modelo VARCHAR(100),
    numero_serie VARCHAR(100),
    ubicacion VARCHAR(150),
    estado VARCHAR(25) NOT NULL DEFAULT 'OPERATIVO',
    descripcion TEXT,
    fecha_adquisicion DATE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_equipos_categorias
        FOREIGN KEY (id_categoria)
        REFERENCES categorias (id_categoria)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_equipos_usuarios
        FOREIGN KEY (registrado_por)
        REFERENCES usuarios (id_usuario)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT equipos_codigo_no_vacio CHECK (BTRIM(codigo_interno) <> ''),
    CONSTRAINT equipos_nombre_no_vacio CHECK (BTRIM(nombre) <> ''),
    CONSTRAINT equipos_numero_serie_no_vacio CHECK (
        numero_serie IS NULL OR BTRIM(numero_serie) <> ''
    ),
    CONSTRAINT equipos_estado_valido CHECK (
        estado IN ('OPERATIVO', 'FUERA_DE_SERVICIO', 'DADO_DE_BAJA')
    )
);

CREATE UNIQUE INDEX uq_equipos_codigo_interno
    ON equipos (LOWER(codigo_interno));

CREATE UNIQUE INDEX uq_equipos_numero_serie
    ON equipos (LOWER(numero_serie))
    WHERE numero_serie IS NOT NULL;

CREATE INDEX idx_equipos_categoria
    ON equipos (id_categoria);

CREATE INDEX idx_equipos_registrado_por
    ON equipos (registrado_por);

CREATE INDEX idx_equipos_nombre
    ON equipos (LOWER(nombre));

CREATE INDEX idx_equipos_marca
    ON equipos (LOWER(marca));

CREATE INDEX idx_equipos_modelo
    ON equipos (LOWER(modelo));

CREATE INDEX idx_equipos_estado
    ON equipos (estado);

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

CREATE OR REPLACE FUNCTION establecer_actualizado_en()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.actualizado_en = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_roles_actualizado_en
BEFORE UPDATE ON roles
FOR EACH ROW
EXECUTE FUNCTION establecer_actualizado_en();

CREATE TRIGGER trg_usuarios_actualizado_en
BEFORE UPDATE ON usuarios
FOR EACH ROW
EXECUTE FUNCTION establecer_actualizado_en();

CREATE TRIGGER trg_categorias_actualizado_en
BEFORE UPDATE ON categorias
FOR EACH ROW
EXECUTE FUNCTION establecer_actualizado_en();

CREATE TRIGGER trg_equipos_actualizado_en
BEFORE UPDATE ON equipos
FOR EACH ROW
EXECUTE FUNCTION establecer_actualizado_en();

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
