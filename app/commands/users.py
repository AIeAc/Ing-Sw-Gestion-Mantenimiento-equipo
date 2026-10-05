import getpass

import click
from flask import current_app
from werkzeug.security import generate_password_hash

from app.core.database import get_db


@click.command("crear-usuario")
@click.option("--nombre", prompt="Nombre")
@click.option("--apellidos", prompt="Apellidos")
@click.option("--correo", prompt="Correo electrónico")
@click.option("--rol", default="Administrador", show_default=True)
def create_user_command(nombre, apellidos, correo, rol):
    """Crea el primer usuario sin guardar su contraseña en texto plano."""
    password = getpass.getpass("Contraseña: ")
    confirmation = getpass.getpass("Confirma la contraseña: ")

    if len(password) < 10:
        raise click.ClickException("La contraseña debe tener al menos 10 caracteres.")
    if password != confirmation:
        raise click.ClickException("Las contraseñas no coinciden.")

    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id_rol FROM roles WHERE LOWER(nombre) = LOWER(%s) AND activo = TRUE",
                (rol,),
            )
            role = cursor.fetchone()
            if role is None:
                raise click.ClickException(f'El rol "{rol}" no existe o está inactivo.')

            cursor.execute(
                """
                INSERT INTO usuarios (
                    id_rol, nombre, apellidos, correo, contrasena_hash
                )
                VALUES (%s, %s, %s, LOWER(%s), %s)
                """,
                (
                    role["id_rol"],
                    nombre.strip(),
                    apellidos.strip(),
                    correo.strip(),
                    generate_password_hash(password),
                ),
            )
        connection.commit()
    except click.ClickException:
        connection.rollback()
        raise
    except Exception as error:
        connection.rollback()
        current_app.logger.exception("No se pudo crear el usuario")
        raise click.ClickException(
            "No se pudo crear el usuario. Verifica que el correo no esté registrado."
        ) from error

    click.echo("Usuario creado correctamente.")


def init_app(app):
    app.cli.add_command(create_user_command)
