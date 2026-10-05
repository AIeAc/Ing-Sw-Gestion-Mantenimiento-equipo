import psycopg
from flask import current_app, g
from psycopg.rows import dict_row


def get_db():
    if "db" not in g:
        database_url = current_app.config.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError("Debes configurar DATABASE_URL.")

        g.db = psycopg.connect(database_url, row_factory=dict_row)

    return g.db


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_app(app):
    app.teardown_appcontext(close_db)
