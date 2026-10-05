BEGIN;

DO $$
DECLARE
    v_equipo BIGINT;
    v_usuario BIGINT;
    v_variable BIGINT;
    v_lote BIGINT;
    v_medicion_normal BIGINT;
    v_medicion_alerta BIGINT;
    v_rechazo_rango BOOLEAN := FALSE;
    v_rechazo_modificacion BOOLEAN := FALSE;
BEGIN
    SELECT id_equipo
    INTO v_equipo
    FROM equipos
    WHERE estado <> 'DADO_DE_BAJA'
    ORDER BY id_equipo
    LIMIT 1;

    SELECT id_usuario
    INTO v_usuario
    FROM usuarios
    WHERE activo
    ORDER BY id_usuario
    LIMIT 1;

    IF v_equipo IS NULL OR v_usuario IS NULL THEN
        RAISE EXCEPTION
            'La prueba requiere un equipo disponible y un usuario activo';
    END IF;

    BEGIN
        INSERT INTO variables_operativas (
            codigo,
            nombre,
            unidad,
            valor_minimo,
            valor_maximo
        )
        VALUES ('PRUEBA-RANGO', 'Variable inválida', 'u', 100, 10);
    EXCEPTION
        WHEN check_violation THEN
            v_rechazo_rango := TRUE;
    END;

    IF NOT v_rechazo_rango THEN
        RAISE EXCEPTION 'La base permitió un rango mínimo/máximo inválido';
    END IF;

    INSERT INTO variables_operativas (
        codigo,
        nombre,
        unidad,
        descripcion,
        valor_minimo,
        valor_maximo
    )
    VALUES (
        'PRUEBA-TEMP',
        'Temperatura de prueba',
        '°C',
        'Variable temporal de la prueba transaccional.',
        10,
        20
    )
    RETURNING id_variable INTO v_variable;

    INSERT INTO lotes_mediciones (
        registrado_por,
        tipo_origen,
        estado,
        registros_totales
    )
    VALUES (v_usuario, 'SIMULADOR', 'PROCESANDO', 2)
    RETURNING id_lote INTO v_lote;

    INSERT INTO mediciones_operativas (
        id_equipo,
        id_variable,
        id_lote,
        valor,
        medido_en
    )
    VALUES (v_equipo, v_variable, v_lote, 15, CURRENT_TIMESTAMP)
    RETURNING id_medicion INTO v_medicion_normal;

    IF EXISTS (
        SELECT 1
        FROM alertas_rango
        WHERE id_medicion = v_medicion_normal
    ) THEN
        RAISE EXCEPTION 'Una medición dentro del rango generó una alerta';
    END IF;

    INSERT INTO mediciones_operativas (
        id_equipo,
        id_variable,
        id_lote,
        valor,
        medido_en
    )
    VALUES (v_equipo, v_variable, v_lote, 25, CURRENT_TIMESTAMP)
    RETURNING id_medicion INTO v_medicion_alerta;

    IF NOT EXISTS (
        SELECT 1
        FROM alertas_rango
        WHERE id_medicion = v_medicion_alerta
          AND tipo = 'LIMITE_SUPERIOR'
          AND estado = 'PENDIENTE'
          AND valor_medido = 25
          AND valor_maximo = 20
    ) THEN
        RAISE EXCEPTION 'La medición fuera de rango no generó la alerta esperada';
    END IF;

    IF (
        SELECT COUNT(*)
        FROM mediciones_para_grafica
        WHERE id_medicion IN (v_medicion_normal, v_medicion_alerta)
    ) <> 2 THEN
        RAISE EXCEPTION 'Las mediciones no aparecieron en la vista para gráficas';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM resumen_indicadores_dashboard) THEN
        RAISE EXCEPTION 'La vista de indicadores no devolvió resultados';
    END IF;

    BEGIN
        UPDATE mediciones_operativas
        SET valor = 18
        WHERE id_medicion = v_medicion_normal;
    EXCEPTION
        WHEN OTHERS THEN
            v_rechazo_modificacion :=
                SQLERRM LIKE 'Las mediciones almacenadas son inmutables%';
    END;

    IF NOT v_rechazo_modificacion THEN
        RAISE EXCEPTION 'La base permitió modificar una medición almacenada';
    END IF;

    UPDATE lotes_mediciones
    SET estado = 'COMPLETADO',
        registros_validos = 2,
        finalizado_en = CURRENT_TIMESTAMP
    WHERE id_lote = v_lote;

    RAISE NOTICE 'Pruebas del Sprint 3 completadas correctamente';
END;
$$;

ROLLBACK;
