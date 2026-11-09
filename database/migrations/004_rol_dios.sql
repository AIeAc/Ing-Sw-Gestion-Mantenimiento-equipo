BEGIN;

INSERT INTO roles (nombre, descripcion)
VALUES ('DIOS', 'Acceso completo a todas las funciones actuales de la aplicación.')
ON CONFLICT DO NOTHING;

COMMIT;
