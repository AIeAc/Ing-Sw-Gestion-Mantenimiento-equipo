# Base de datos de los Sprints 1, 2 y 3

La base de datos utiliza PostgreSQL. Conserva el alcance entregado en el
Sprint 1:

- inicio de sesión;
- roles de Administrador y Técnico;
- clasificación básica de equipos;
- registro, consulta y modificación de equipos;
- búsqueda básica del inventario.

El Sprint 2 agrega:

- mantenimientos preventivos y correctivos;
- asociación con equipos y técnicos;
- fechas, estados, costos y observaciones;
- historial por equipo;
- calendario básico de mantenimientos.

El Sprint 3 agrega:

- catálogo de variables operativas y sus rangos permitidos;
- lotes de datos provenientes del simulador o de una importación;
- mediciones operativas inmutables;
- alertas automáticas cuando una medición queda fuera de rango;
- datos preparados para gráficas;
- indicadores básicos de disponibilidad, eventos correctivos, alertas y
  costos.

La clasificación se administra mediante categorías. La búsqueda se limita a
texto libre, categoría y estado; no implementa criterios avanzados.

## Estructura

- `schema.sql`: crea las tablas, relaciones, restricciones, índices y
  disparadores de actualización.
- `seed.sql`: registra los roles iniciales del sistema.
- `demo_seed.sql`: agrega categorías, equipos, mantenimientos, variables,
  mediciones y alertas de demostración sin duplicar datos existentes. Requiere
  al menos un usuario activo; para incluir mantenimientos debe existir también
  un Técnico activo.
- `migrations/002_sprint_2_mantenimiento.sql`: actualiza una base existente
  del Sprint 1 sin borrar sus datos.
- `tests/sprint2_database.sql`: valida las relaciones, el historial, el
  calendario y la asignación del rol Técnico; revierte sus datos de prueba.
- `migrations/003_sprint_3_variables_alertas.sql`: agrega variables, lotes,
  mediciones, alertas y vistas de indicadores a una base del Sprint 2.
- `tests/sprint3_database.sql`: valida rangos, mediciones, alertas y vistas;
  revierte todos sus datos de prueba.

## Creación local

```bash
createdb mantenimiento_predictivo
psql -d mantenimiento_predictivo -f database/schema.sql
psql -d mantenimiento_predictivo -f database/seed.sql
psql -d mantenimiento_predictivo \
  -f database/migrations/003_sprint_3_variables_alertas.sql
```

Para actualizar una base existente del Sprint 1:

```bash
psql -d mantenimiento_predictivo \
  -f database/migrations/002_sprint_2_mantenimiento.sql
```

Para comprobar la migración sin conservar registros ficticios:

```bash
psql -v ON_ERROR_STOP=1 -d mantenimiento_predictivo \
  -f database/tests/sprint2_database.sql
```

Para actualizar del Sprint 2 al Sprint 3:

```bash
psql -v ON_ERROR_STOP=1 -d mantenimiento_predictivo \
  -f database/migrations/003_sprint_3_variables_alertas.sql
```

Para comprobar el Sprint 3 sin conservar registros ficticios:

```bash
psql -v ON_ERROR_STOP=1 -d mantenimiento_predictivo \
  -f database/tests/sprint3_database.sql
```

Para llenar la aplicación con datos de demostración:

```bash
psql -d mantenimiento_predictivo -f database/demo_seed.sql
```

Los equipos de demostración usan códigos entre `DEMO-EQ-001` y
`DEMO-EQ-010`, y los demás registros incluyen referencias `DEMO`, para que
sea fácil distinguirlos de los datos reales. El archivo se puede ejecutar más
de una vez sin duplicar sus registros.

## Conexión local de desarrollo

En Linux, la aplicación se conecta mediante el socket local de PostgreSQL:

- base de datos: `mantenimiento_predictivo`;
- usuario: el mismo nombre de la cuenta local de Linux;
- puerto: `5432`;
- socket: `/var/run/postgresql`;
- servicio: `postgresql.service`.

La cadena de conexión local es:

```text
postgresql:///mantenimiento_predictivo?host=/var/run/postgresql
```

La conexión se puede comprobar con:

```bash
psql "postgresql:///mantenimiento_predictivo?host=/var/run/postgresql"
```

Esta conexión usa la identidad del usuario local y no requiere guardar una
contraseña en el repositorio.

No se incluye un usuario predeterminado porque la contraseña debe almacenarse
como un hash seguro generado por la aplicación, nunca como texto plano.

## Tablas

- `roles`
- `usuarios`
- `categorias`
- `equipos`
- `mantenimientos`
- `variables_operativas`
- `lotes_mediciones`
- `mediciones_operativas`
- `alertas_rango`

## Vistas de los Sprints 2 y 3

- `historial_mantenimientos_equipo`: reúne el mantenimiento, equipo y técnico
  para consultar el historial de un equipo.
- `calendario_mantenimientos`: expone los mantenimientos que tienen fecha
  programada.
- `mediciones_para_grafica`: reúne fecha, equipo, variable, unidad, valor,
  rango y origen de cada medición.
- `resumen_indicadores_dashboard`: devuelve disponibilidad actual, equipos
  fuera de servicio, mantenimientos correctivos, alertas pendientes y costo
  acumulado de mantenimientos completados.

Ejemplo de historial por equipo:

```sql
SELECT *
FROM historial_mantenimientos_equipo
WHERE id_equipo = 1
ORDER BY fecha_referencia DESC;
```

Ejemplo de calendario mensual:

```sql
SELECT *
FROM calendario_mantenimientos
WHERE fecha >= DATE '2026-10-01'
  AND fecha < DATE '2026-11-01'
ORDER BY fecha_programada;
```

La búsqueda se realiza sobre los campos del inventario. Los índices incluidos
permiten filtrar por categoría y estado, y buscar por código, número de serie,
nombre, marca o modelo.

Los modelos predictivos, las alertas predictivas, la programación automática
de mantenimientos y los reportes ejecutivos no forman parte de este esquema
porque corresponden a sprints posteriores.
