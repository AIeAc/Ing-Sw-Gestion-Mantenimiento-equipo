# Sistema de mantenimiento predictivo

La aplicación conserva los Sprints 1 y 2 e incorpora el módulo funcional del
**Sprint 3** para variables operativas, mediciones, alertas por rango e
indicadores básicos.

- inicio y cierre de sesión;
- roles de Administrador y Técnico;
- registro, consulta y modificación de equipos;
- clasificación y búsqueda básica del inventario.
- registro y actualización de mantenimientos preventivos y correctivos;
- asociación con equipos y técnicos activos;
- seguimiento de fechas, estados, costos y observaciones;
- consulta del historial por equipo;
- calendario mensual básico de mantenimientos.
- catálogo administrable de variables operativas y rangos permitidos;
- importación CSV con validación y lotes auditables;
- consulta tabular y gráfica de mediciones;
- generación automática y atención de alertas por rango;
- dashboard de disponibilidad, fallas correctivas y costos.

## Estructura del proyecto

```text
mantenimiento-predictivo/
├── app/
│   ├── blueprints/       # Rutas y controladores Flask
│   ├── commands/         # Comandos administrativos de Flask
│   ├── core/             # Conexión a BD y errores compartidos
│   ├── repositories/     # Consultas y operaciones PostgreSQL
│   ├── static/dist/      # Recursos frontend compilados
│   └── templates/        # Vistas Jinja organizadas por módulo
├── database/             # Esquema y migraciones de los Sprints 1, 2 y 3
├── frontend/src/         # CSS, JavaScript e iconos fuente
├── tests/
│   ├── unit/             # Pruebas rápidas y aisladas
│   └── integration/      # Pruebas que requieren PostgreSQL
├── package.json          # Dependencias y comandos de Vite
├── requirements.txt      # Dependencias de Python
└── vite.config.js        # Configuración de compilación frontend
```

`app/__init__.py` funciona como fábrica de la aplicación y registra cada
componente sin mezclar las responsabilidades de las distintas capas.

## Requisitos

- Python 3.11 o posterior.
- PostgreSQL 15 o posterior.

Los recursos del frontend ya están compilados. Node.js no es necesario para
ejecutar la aplicación.

## Instalación en otra laptop Linux

### 1. Copiar el proyecto

Copia toda la carpeta `mantenimiento-predictivo` a la otra computadora y abre
una terminal dentro de ella. No copies `.venv`, `.env` ni `node_modules`: los
dos primeros contienen rutas o configuración propias de cada computadora.

### 2. Instalar PostgreSQL y Python

En Fedora o Nobara:

```bash
sudo dnf install python3 postgresql-server
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql
```

En Ubuntu o Debian:

```bash
sudo apt update
sudo apt install python3 python3-venv postgresql
sudo systemctl enable --now postgresql
```

### 3. Preparar Python

```bash
python3 -m venv --copies .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Si la carpeta `.venv` se copió accidentalmente desde otra computadora,
recréala antes de instalar:

```bash
deactivate 2>/dev/null || true
python3 -m venv --clear --copies .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Crear la base de datos

La aplicación usa el usuario local de Linux para conectarse sin guardar una
contraseña. Crea en PostgreSQL un rol con ese mismo nombre y después prepara
la base:

```bash
sudo -u postgres createuser "$(whoami)"
sudo -u postgres createdb --owner="$(whoami)" mantenimiento_predictivo
psql -d mantenimiento_predictivo -f database/schema.sql
psql -d mantenimiento_predictivo -f database/seed.sql
psql -d mantenimiento_predictivo \
  -f database/migrations/003_sprint_3_variables_alertas.sql
```

Si `createuser` indica que el rol ya existe, es normal: continúa con
`sudo -u postgres createdb`. La base la crea el administrador de PostgreSQL y
queda asignada al usuario local, por lo que este no necesita el permiso global
para crear otras bases.

### 5. Configurar la aplicación

Copia el ejemplo de configuración:

```bash
cp .env.example .env
python -c 'import secrets; print(secrets.token_hex(32))'
```

Copia el valor generado y reemplaza `cambia-este-valor` dentro de `.env`.
El archivo `.env` es privado y Git no lo incluirá.

La conexión predeterminada para Linux es:

```text
postgresql:///mantenimiento_predictivo?host=/var/run/postgresql
```

### 6. Crear el primer Administrador

```bash
flask --app app crear-usuario
```

La contraseña se solicita de forma oculta y se almacena mediante un hash
seguro; nunca se guarda en texto plano.

El comando permite indicar `Administrador` o `Técnico` como rol. Después de
crear el primer Administrador, las demás cuentas se pueden administrar desde
la interfaz.

### 7. Agregar datos de demostración (opcional)

Ejecuta este paso después de crear el primer usuario. Para poblar también el
historial y el calendario de mantenimiento debe existir al menos un usuario
con el rol Técnico:

```bash
psql -d mantenimiento_predictivo -f database/demo_seed.sql
```

El conjunto incluye equipos, variables operativas, mantenimientos, mediciones
recientes y alertas de rango en distintos estados. Puede volver a ejecutarse
sin duplicar los registros de demostración.

### 8. Ejecutar

```bash
flask --app app run --debug
```

Abre `http://127.0.0.1:5000/iniciar-sesion`.

No abras los archivos de `app/templates` directamente en el navegador; esas
plantillas solamente funcionan cuando Flask las sirve desde la dirección
anterior.

## Conservar los registros de esta laptop

Si quieres llevar también los usuarios, categorías y equipos actuales, crea
un respaldo en la laptop original:

```bash
pg_dump -Fc mantenimiento_predictivo -f mantenimiento_predictivo.dump
```

Copia `mantenimiento_predictivo.dump` a la raíz del proyecto en la nueva
laptop. Después de crear la base vacía, restáurala en lugar de ejecutar
`schema.sql`, `seed.sql` y `demo_seed.sql`:

```bash
pg_restore --clean --if-exists --no-owner \
  -d mantenimiento_predictivo mantenimiento_predictivo.dump
```

El respaldo puede contener cuentas y datos del inventario; no debe subirse a
un repositorio público.

## Desarrollo del frontend

El frontend usa Vite para compilar los estilos, la interacción y los iconos.
Esta sección solamente es necesaria cuando se modifican archivos dentro de
`frontend/src/`.

Requiere Node.js 20.19 o posterior y pnpm:

```bash
corepack enable
pnpm install
pnpm run build
```

El resultado se genera en `app/static/dist/` y Flask lo sirve directamente.

## Funciones y permisos

| Función | Administrador | Técnico |
|---|:---:|:---:|
| Iniciar y cerrar sesión | Sí | Sí |
| Consultar y buscar equipos | Sí | Sí |
| Registrar y modificar equipos | Sí | Sí |
| Registrar y actualizar mantenimientos | Sí | Sí |
| Consultar historial por equipo | Sí | Sí |
| Consultar calendario de mantenimientos | Sí | Sí |
| Consultar variables operativas | Sí | Sí |
| Administrar variables operativas | Sí | No |
| Importar y consultar mediciones | Sí | Sí |
| Consultar y atender alertas por rango | Sí | Sí |
| Consultar dashboard operativo | Sí | Sí |
| Administrar clasificaciones | Sí | No |
| Crear usuarios y asignar roles | Sí | No |

La búsqueda básica admite código interno, nombre, marca, modelo y número de
serie. También permite filtrar por categoría y estado.

## Pruebas

```bash
python -m unittest discover -v
```

Las pruebas cubren el acceso a rutas protegidas, credenciales inválidas,
protección CSRF, inicio de sesión, permisos por rol, inventario, validación de
mantenimientos, historial, calendario, catálogo de variables, importación CSV,
gráficas de mediciones, atención de alertas y cierre de sesión.

La prueba integral requiere una base PostgreSQL exclusiva para pruebas con el
esquema y los datos iniciales ya cargados:

```bash
export TEST_DATABASE_URL="postgresql:///mantenimiento_predictivo_test?host=/var/run/postgresql"
python -m unittest tests.integration.test_postgres -v
```

Esta prueba recorre el flujo completo: acceso del Administrador, creación de
categoría, alta de Técnico, registro y búsqueda de equipo, registro de un
mantenimiento, consulta de historial y calendario, y restricciones de acceso
del Técnico.

Las reglas de rangos, generación automática de alertas, inmutabilidad de las
mediciones y vistas del dashboard se validan directamente en PostgreSQL:

```bash
psql -v ON_ERROR_STOP=1 -d mantenimiento_predictivo \
  -f database/tests/sprint3_database.sql
```

La prueba usa una transacción y revierte todos sus datos temporales.

## Formato para importar mediciones

La opción **Mediciones → Importar CSV** acepta archivos UTF-8 de hasta 2 MB y
2,000 filas. Las columnas obligatorias son:

```text
codigo_equipo,codigo_variable,valor,medido_en
```

`medido_en` utiliza formato ISO, por ejemplo `2026-10-04T10:30:00`. La
pantalla de importación permite descargar una plantilla y muestra el resultado
de cada lote, incluyendo filas válidas y rechazadas.
