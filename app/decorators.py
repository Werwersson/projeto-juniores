from functools import wraps
from flask import abort
from flask_login import current_user


def _role_value(role) -> str:
    """
    Normaliza um role para string lower independente de ser Enum ou String.
    Suporta: UserRole.SUPERVISOR, "supervisor", "SUPERVISOR", "UserRole.SUPERVISOR"
    """
    if hasattr(role, "value"):
        return role.value.lower()
    return str(role).lower().replace("userrole.", "").replace("'", "").strip()


def _user_role_str() -> str:
    """Retorna o role do current_user sempre como string lower."""
    r = current_user.role
    if hasattr(r, "value"):
        return r.value.lower()
    return str(r).lower().replace("userrole.", "").replace("'", "").strip()


def requires_role(*roles):
    """
    Garante que o usuário autenticado possui um dos roles permitidos.
    Robusto a comparação String vs Enum — nunca gera 403 falso positivo.

    Uso:
        @requires_role("supervisor")
        @requires_role("supervisor", "lider")
        @requires_role(UserRole.SUPERVISOR, UserRole.LIDER)
    """
    allowed = {_role_value(r) for r in roles}

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if _user_role_str() not in allowed:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def requires_pgm_access(pgm_id_param: str = "pgm_id"):
    """
    Garante que o usuário tem acesso ao PGM informado na URL.
    Supervisores passam automaticamente; líderes só passam se coordenarem o PGM.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if _user_role_str() == "junior":
                abort(403)
            pgm_id = kwargs.get(pgm_id_param)
            if pgm_id and not current_user.manages_pgm(int(pgm_id)):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def requires_own_profile_or_leader(junior_id_param: str = "junior_id"):
    """
    Permite acesso ao próprio júnior, ao líder do seu PGM e ao supervisor.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from app.models.user import User
            from app import db

            if not current_user.is_authenticated:
                abort(401)

            junior_id = kwargs.get(junior_id_param)
            if junior_id is None:
                abort(400)

            junior = db.session.get(User, int(junior_id))
            if not junior:
                abort(404)

            is_own          = current_user.id == junior.id
            is_supervisor   = current_user.is_supervisor
            is_leader_of_pgm = (
                current_user.is_lider
                and junior.pgm_id is not None
                and current_user.manages_pgm(junior.pgm_id)
            )

            if not (is_own or is_supervisor or is_leader_of_pgm):
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator
