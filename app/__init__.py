import os

from flask import Flask

from .blueprints import (
    admin,
    alerts,
    auth,
    classifications,
    dashboard,
    inventory,
    maintenance,
    measurements,
    variables,
)
from .commands import users as user_commands
from .core import database, errors


DEFAULT_DATABASE_URL = (
    "postgresql:///mantenimiento_predictivo?host=/var/run/postgresql"
)


def _format_number(value):
    if value is None:
        return ""
    try:
        return f"{value:,.6f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return str(value)


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        DATABASE_URL=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "").lower()
        in {"1", "true", "yes"},
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    )

    if test_config is not None:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("Debes configurar SECRET_KEY.")

    database.init_app(app)
    app.add_template_filter(_format_number, "number")
    auth.init_app(app)
    inventory.init_app(app)
    maintenance.init_app(app)
    variables.init_app(app)
    measurements.init_app(app)
    alerts.init_app(app)
    dashboard.init_app(app)
    classifications.init_app(app)
    admin.init_app(app)
    errors.init_app(app)
    user_commands.init_app(app)
    return app
