BEGIN;

INSERT INTO roles (nombre, descripcion)
VALUES
    ('Administrador', 'Administra usuarios, roles y el inventario de equipos.'),
    ('Técnico', 'Consulta y gestiona el inventario de equipos.')
ON CONFLICT DO NOTHING;

COMMIT;
