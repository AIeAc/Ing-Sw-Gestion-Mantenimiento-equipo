import hmac
import secrets
from functools import wraps

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from app.repositories import users

bp = Blueprint("auth", __name__)


def _csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def _valid_csrf_token(token):
    expected = session.get("csrf_token", "")
    return bool(token and expected and hmac.compare_digest(token, expected))


def validate_csrf():
    if not _valid_csrf_token(request.form.get("csrf_token")):
        abort(400, description="La solicitud no es válida.")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = None if user_id is None else users.find_active_user_by_id(user_id)

    if user_id is not None and g.user is None:
        session.clear()


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login", next=request.path))
        return view(**kwargs)

    return wrapped_view


def roles_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped_view(**kwargs):
            if g.user["rol"] not in allowed_roles:
                abort(403)
            return view(**kwargs)

        return wrapped_view

    return decorator


@bp.route("/iniciar-sesion", methods=("GET", "POST"))
def login():
    if g.user is not None:
        return redirect(url_for("auth.home"))

    if request.method == "POST":
        validate_csrf()

        email = request.form.get("correo", "").strip().lower()
        password = request.form.get("contrasena", "")
        user = users.find_active_user_by_email(email) if email and password else None

        password_is_valid = False
        if user is not None:
            try:
                password_is_valid = check_password_hash(
                    user["contrasena_hash"], password
                )
            except (TypeError, ValueError):
                password_is_valid = False

        if not password_is_valid:
            flash("El correo o la contraseña son incorrectos.", "error")
        else:
            users.register_last_access(user["id_usuario"])
            session.clear()
            session["user_id"] = user["id_usuario"]
            session["csrf_token"] = secrets.token_urlsafe(32)
            return redirect(url_for("inventory.list_equipment"))

    return render_template("auth/login.html")


@bp.post("/cerrar-sesion")
@login_required
def logout():
    validate_csrf()
    session.clear()
    return redirect(url_for("auth.login"))


@bp.get("/")
@login_required
def home():
    return redirect(url_for("inventory.list_equipment"))


def init_app(app):
    app.register_blueprint(bp)
    app.context_processor(lambda: {"csrf_token": _csrf_token})
