BEGIN;

INSERT INTO roles (nombre, descripcion)
VALUES
    ('Administrador', 'Administra usuarios, roles y el inventario de equipos.'),
    ('Técnico', 'Consulta y gestiona el inventario de equipos.'),
    ('DIOS', 'Acceso completo a todas las funciones actuales de la aplicación.')
ON CONFLICT DO NOTHING;

COMMIT;
