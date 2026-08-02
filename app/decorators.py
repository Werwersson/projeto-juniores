from functools import wraps
from flask import abort
from flask_login import current_user
from app.models.user import UserRole


def requires_role(*roles: UserRole):
    """
    Garante que o usuário autenticado possui um dos roles permitidos.

    Uso:
        @requires_role(UserRole.SUPERVISOR)
        @requires_role(UserRole.SUPERVISOR, UserRole.LIDER)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def requires_pgm_access(pgm_id_param: str = "pgm_id"):
    """
    Garante que o usuário (líder ou supervisor) tem acesso ao PGM
    informado na URL.

    Supervisores passam automaticamente.
    Líderes só passam se forem líderes do PGM requisitado.

    Uso:
        @requires_pgm_access("pgm_id")
        def minha_rota(pgm_id):
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role == UserRole.JUNIOR:
                abort(403)
            pgm_id = kwargs.get(pgm_id_param)
            if pgm_id and not current_user.manages_pgm(int(pgm_id)):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def requires_own_profile_or_leader(junior_id_param: str = "junior_id"):
    """
    Permite acesso:
      - ao próprio junior (visualizar seu perfil/checklist)
      - ao líder do PGM do junior
      - ao supervisor

    Uso:
        @requires_own_profile_or_leader("junior_id")
        def ver_extrato(junior_id):
            ...
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

            is_own = current_user.id == junior.id
            is_supervisor = current_user.is_supervisor
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
