BEGIN;

CREATE TABLE variables_operativas (
    id_variable BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    unidad VARCHAR(30) NOT NULL,
    descripcion VARCHAR(255),
    valor_minimo NUMERIC(18, 6) NOT NULL,
    valor_maximo NUMERIC(18, 6) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT variables_codigo_no_vacio CHECK (BTRIM(codigo) <> ''),
    CONSTRAINT variables_nombre_no_vacio CHECK (BTRIM(nombre) <> ''),
    CONSTRAINT variables_unidad_no_vacia CHECK (BTRIM(unidad) <> ''),
    CONSTRAINT variables_rango_valido CHECK (valor_minimo < valor_maximo)
);

CREATE UNIQUE INDEX uq_variables_codigo
    ON variables_operativas (LOWER(codigo));

CREATE UNIQUE INDEX uq_variables_nombre
    ON variables_operativas (LOWER(nombre));

CREATE TABLE lotes_mediciones (
    id_lote BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    registrado_por BIGINT NOT NULL,
    tipo_origen VARCHAR(15) NOT NULL,
    estado VARCHAR(15) NOT NULL DEFAULT 'PENDIENTE',
    nombre_archivo VARCHAR(255),
    registros_totales INTEGER NOT NULL DEFAULT 0,
    registros_validos INTEGER NOT NULL DEFAULT 0,
    registros_rechazados INTEGER NOT NULL DEFAULT 0,
    detalle_error TEXT,
    iniciado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finalizado_en TIMESTAMPTZ,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_lotes_mediciones_usuarios
        FOREIGN KEY (registrado_por)
        REFERENCES usuarios (id_usuario)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT lotes_tipo_origen_valido CHECK (
        tipo_origen IN ('SIMULADOR', 'IMPORTACION')
    ),
    CONSTRAINT lotes_estado_valido CHECK (
        estado IN ('PENDIENTE', 'PROCESANDO', 'COMPLETADO', 'FALLIDO')
    ),
    CONSTRAINT lotes_cantidades_validas CHECK (
        registros_totales >= 0
        AND registros_validos >= 0
        AND registros_rechazados >= 0
        AND registros_validos + registros_rechazados <= registros_totales
    ),
    CONSTRAINT lotes_fechas_validas CHECK (
        finalizado_en IS NULL OR finalizado_en >= iniciado_en
    ),
    CONSTRAINT lotes_finalizados_con_fecha CHECK (
        estado NOT IN ('COMPLETADO', 'FALLIDO') OR finalizado_en IS NOT NULL
    )
);

CREATE INDEX idx_lotes_mediciones_estado
    ON lotes_mediciones (estado);

CREATE INDEX idx_lotes_mediciones_origen
    ON lotes_mediciones (tipo_origen, iniciado_en DESC);

CREATE TABLE mediciones_operativas (
    id_medicion BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_equipo BIGINT NOT NULL,
    id_variable BIGINT NOT NULL,
    id_lote BIGINT NOT NULL,
    valor NUMERIC(18, 6) NOT NULL,
    medido_en TIMESTAMPTZ NOT NULL,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_mediciones_equipos
        FOREIGN KEY (id_equipo)
        REFERENCES equipos (id_equipo)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_mediciones_variables
        FOREIGN KEY (id_variable)
        REFERENCES variables_operativas (id_variable)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_mediciones_lotes
        FOREIGN KEY (id_lote)
        REFERENCES lotes_mediciones (id_lote)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE INDEX idx_mediciones_equipo_fecha
    ON mediciones_operativas (id_equipo, medido_en DESC);

CREATE INDEX idx_mediciones_variable_fecha
    ON mediciones_operativas (id_variable, medido_en DESC);

CREATE INDEX idx_mediciones_equipo_variable_fecha
    ON mediciones_operativas (id_equipo, id_variable, medido_en DESC);

CREATE INDEX idx_mediciones_lote
    ON mediciones_operativas (id_lote);

CREATE TABLE alertas_rango (
    id_alerta BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_medicion BIGINT NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    estado VARCHAR(15) NOT NULL DEFAULT 'PENDIENTE',
    valor_medido NUMERIC(18, 6) NOT NULL,
    valor_minimo NUMERIC(18, 6) NOT NULL,
    valor_maximo NUMERIC(18, 6) NOT NULL,
    atendida_por BIGINT,
    atendida_en TIMESTAMPTZ,
    observaciones TEXT,
    generada_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_alertas_medicion UNIQUE (id_medicion),
    CONSTRAINT fk_alertas_mediciones
        FOREIGN KEY (id_medicion)
        REFERENCES mediciones_operativas (id_medicion)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_alertas_usuarios
        FOREIGN KEY (atendida_por)
        REFERENCES usuarios (id_usuario)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT alertas_tipo_valido CHECK (
        tipo IN ('LIMITE_INFERIOR', 'LIMITE_SUPERIOR')
    ),
    CONSTRAINT alertas_estado_valido CHECK (
        estado IN ('PENDIENTE', 'ATENDIDA', 'DESCARTADA')
    ),
    CONSTRAINT alertas_rango_valido CHECK (valor_minimo < valor_maximo),
    CONSTRAINT alertas_atencion_valida CHECK (
        (estado = 'PENDIENTE'
            AND atendida_por IS NULL
            AND atendida_en IS NULL)
        OR
        (estado IN ('ATENDIDA', 'DESCARTADA')
            AND atendida_por IS NOT NULL
            AND atendida_en IS NOT NULL)
    )
);

CREATE INDEX idx_alertas_estado_fecha
    ON alertas_rango (estado, generada_en DESC);

CREATE OR REPLACE FUNCTION validar_medicion_operativa()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM equipos
        WHERE id_equipo = NEW.id_equipo
          AND estado <> 'DADO_DE_BAJA'
    ) THEN
        RAISE EXCEPTION
            'El equipo % no está disponible para registrar mediciones',
            NEW.id_equipo;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM variables_operativas
        WHERE id_variable = NEW.id_variable
          AND activo
    ) THEN
        RAISE EXCEPTION
            'La variable operativa % no está activa', NEW.id_variable;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM lotes_mediciones
        WHERE id_lote = NEW.id_lote
          AND estado IN ('PENDIENTE', 'PROCESANDO')
    ) THEN
        RAISE EXCEPTION
            'El lote % no admite nuevas mediciones', NEW.id_lote;
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION generar_alerta_medicion_fuera_rango()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_minimo NUMERIC(18, 6);
    v_maximo NUMERIC(18, 6);
    v_tipo VARCHAR(20);
BEGIN
    SELECT valor_minimo, valor_maximo
    INTO v_minimo, v_maximo
    FROM variables_operativas
    WHERE id_variable = NEW.id_variable;

    IF NEW.valor < v_minimo THEN
        v_tipo := 'LIMITE_INFERIOR';
    ELSIF NEW.valor > v_maximo THEN
        v_tipo := 'LIMITE_SUPERIOR';
    ELSE
        RETURN NEW;
    END IF;

    INSERT INTO alertas_rango (
        id_medicion,
        tipo,
        valor_medido,
        valor_minimo,
        valor_maximo
    )
    VALUES (
        NEW.id_medicion,
        v_tipo,
        NEW.valor,
        v_minimo,
        v_maximo
    );

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION impedir_modificacion_medicion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION
        'Las mediciones almacenadas son inmutables; registre una nueva medición';
END;
$$;

CREATE TRIGGER trg_variables_actualizado_en
BEFORE UPDATE ON variables_operativas
FOR EACH ROW
EXECUTE FUNCTION establecer_actualizado_en();

CREATE TRIGGER trg_lotes_actualizado_en
BEFORE UPDATE ON lotes_mediciones
FOR EACH ROW
EXECUTE FUNCTION establecer_actualizado_en();

CREATE TRIGGER trg_alertas_actualizado_en
BEFORE UPDATE ON alertas_rango
FOR EACH ROW
EXECUTE FUNCTION establecer_actualizado_en();

CREATE TRIGGER trg_mediciones_validar
BEFORE INSERT ON mediciones_operativas
FOR EACH ROW
EXECUTE FUNCTION validar_medicion_operativa();

CREATE TRIGGER trg_mediciones_generar_alerta
AFTER INSERT ON mediciones_operativas
FOR EACH ROW
EXECUTE FUNCTION generar_alerta_medicion_fuera_rango();

CREATE TRIGGER trg_mediciones_inmutables
BEFORE UPDATE OR DELETE ON mediciones_operativas
FOR EACH ROW
EXECUTE FUNCTION impedir_modificacion_medicion();

CREATE VIEW mediciones_para_grafica AS
SELECT
    m.id_medicion,
    m.id_equipo,
    e.codigo_interno,
    e.nombre AS equipo,
    m.id_variable,
    v.codigo AS codigo_variable,
    v.nombre AS variable,
    v.unidad,
    m.valor,
    v.valor_minimo,
    v.valor_maximo,
    (m.valor < v.valor_minimo OR m.valor > v.valor_maximo) AS fuera_de_rango,
    m.medido_en,
    l.id_lote,
    l.tipo_origen
FROM mediciones_operativas AS m
JOIN equipos AS e ON e.id_equipo = m.id_equipo
JOIN variables_operativas AS v ON v.id_variable = m.id_variable
JOIN lotes_mediciones AS l ON l.id_lote = m.id_lote;

CREATE VIEW resumen_indicadores_dashboard AS
WITH inventario AS (
    SELECT
        COUNT(*) FILTER (WHERE estado <> 'DADO_DE_BAJA') AS total_activos,
        COUNT(*) FILTER (WHERE estado = 'OPERATIVO') AS operativos,
        COUNT(*) FILTER (WHERE estado = 'FUERA_DE_SERVICIO') AS fuera_servicio
    FROM equipos
),
mantenimiento AS (
    SELECT
        COUNT(*) FILTER (WHERE tipo = 'CORRECTIVO') AS correctivos,
        COALESCE(
            SUM(costo) FILTER (WHERE estado = 'COMPLETADO'),
            0
        ) AS costo_total
    FROM mantenimientos
),
alertas AS (
    SELECT COUNT(*) FILTER (WHERE estado = 'PENDIENTE') AS pendientes
    FROM alertas_rango
)
SELECT
    i.total_activos AS total_equipos_activos,
    i.operativos AS equipos_operativos,
    i.fuera_servicio AS equipos_fuera_de_servicio,
    CASE
        WHEN i.total_activos = 0 THEN 0::NUMERIC
        ELSE ROUND(i.operativos::NUMERIC * 100 / i.total_activos, 2)
    END AS disponibilidad_porcentaje,
    m.correctivos AS mantenimientos_correctivos,
    a.pendientes AS alertas_rango_pendientes,
    m.costo_total AS costo_mantenimiento_total
FROM inventario AS i
CROSS JOIN mantenimiento AS m
CROSS JOIN alertas AS a;

COMMIT;
