BEGIN;

DO $$
DECLARE
    v_equipo BIGINT;
    v_tecnico BIGINT;
    v_administrador BIGINT;
    v_mantenimiento BIGINT;
    v_rechazo_invalido BOOLEAN := FALSE;
BEGIN
    SELECT id_equipo
    INTO v_equipo
    FROM equipos
    ORDER BY id_equipo
    LIMIT 1;

    SELECT u.id_usuario
    INTO v_tecnico
    FROM usuarios AS u
    JOIN roles AS r ON r.id_rol = u.id_rol
    WHERE u.activo
      AND r.activo
      AND LOWER(r.nombre) = LOWER('Técnico')
    ORDER BY u.id_usuario
    LIMIT 1;

    SELECT u.id_usuario
    INTO v_administrador
    FROM usuarios AS u
    JOIN roles AS r ON r.id_rol = u.id_rol
    WHERE u.activo
      AND r.activo
      AND LOWER(r.nombre) = LOWER('Administrador')
    ORDER BY u.id_usuario
    LIMIT 1;

    IF v_equipo IS NULL OR v_tecnico IS NULL OR v_administrador IS NULL THEN
        RAISE EXCEPTION
            'La prueba requiere un equipo, un Técnico y un Administrador activos';
    END IF;

    INSERT INTO mantenimientos (
        id_equipo,
        id_tecnico,
        registrado_por,
        tipo,
        estado,
        fecha_programada,
        descripcion,
        observaciones
    )
    VALUES (
        v_equipo,
        v_tecnico,
        v_administrador,
        'PREVENTIVO',
        'PROGRAMADO',
        CURRENT_TIMESTAMP + INTERVAL '7 days',
        'Prueba temporal del mantenimiento preventivo',
        'Este registro se revierte al finalizar la prueba.'
    )
    RETURNING id_mantenimiento INTO v_mantenimiento;

    IF NOT EXISTS (
        SELECT 1
        FROM historial_mantenimientos_equipo
        WHERE id_mantenimiento = v_mantenimiento
          AND id_equipo = v_equipo
          AND id_tecnico = v_tecnico
    ) THEN
        RAISE EXCEPTION 'El mantenimiento no apareció en el historial';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM calendario_mantenimientos
        WHERE id_mantenimiento = v_mantenimiento
    ) THEN
        RAISE EXCEPTION 'El mantenimiento no apareció en el calendario';
    END IF;

    BEGIN
        INSERT INTO mantenimientos (
            id_equipo,
            id_tecnico,
            registrado_por,
            tipo,
            estado,
            fecha_programada,
            descripcion
        )
        VALUES (
            v_equipo,
            v_administrador,
            v_administrador,
            'CORRECTIVO',
            'PROGRAMADO',
            CURRENT_TIMESTAMP + INTERVAL '1 day',
            'Asignación inválida para comprobar la restricción'
        );
    EXCEPTION
        WHEN OTHERS THEN
            v_rechazo_invalido := SQLERRM LIKE 'El usuario % no es un técnico activo';
    END;

    IF NOT v_rechazo_invalido THEN
        RAISE EXCEPTION 'La base permitió asignar como técnico a un Administrador';
    END IF;

    RAISE NOTICE 'Pruebas del Sprint 2 completadas correctamente';
END;
$$;

ROLLBACK;
