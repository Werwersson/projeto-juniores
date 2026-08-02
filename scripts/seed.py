"""
Popula o banco com:
  - 3 PGMs
  - 2 supervisores (Everson, Keyla)
  - 9 líderes (3 por PGM)
  - Atividades padrão (leader e junior)

Uso:
  flask --app run shell
  >>> from scripts.seed import seed; seed()

Ou diretamente:
  python -c "from run import app; from scripts.seed import seed; app.app_context().push(); seed()"
"""
from app import db
from app.models.pgm import PGM, PGMLeader
from app.models.user import User, UserRole
from app.models.activity import ActivityType, ActivitySource


PGMS_DATA = [
    {"name": "PGM 1"},  # Nome provisório — será alterado pelas crianças
    {"name": "PGM 2"},
    {"name": "PGM 3"},
]

SUPERVISORS = [
    {"name": "Everson", "email": "everson@juniores.app"},
    {"name": "Keyla", "email": "keyla@juniores.app"},
]

LEADERS = [
    # (nome, email, índice do PGM 0-based)
    ("Ivan",              "ivan@juniores.app",        0),
    ("Cida",              "cida@juniores.app",         0),
    ("Jaciara",           "jaciara@juniores.app",      0),
    ("Valter Vitoria",    "valtervitoria@juniores.app",1),
    ("Ana Paula",         "anapaula@juniores.app",     1),
    ("Sanmaria",          "sanmaria@juniores.app",     1),
    ("Leo",               "leo@juniores.app",          2),
    ("Katiuscia",         "katiuscia@juniores.app",    2),
    ("Natália Lourenço",  "natalia@juniores.app",      2),
]

LEADER_ACTIVITIES = [
    "Presença",
    "Levar a Bíblia",
    "Participação no PGM",
    "Levar um Visitante",
    "Senha do Dia",
]

JUNIOR_ACTIVITIES = [
    "Leitura diária",
    "Estudo da lição",
    "5 minutos com Deus",
]

DEFAULT_PASSWORD = "juniores2025"


def seed():
    # PGMs
    pgms = []
    for data in PGMS_DATA:
        pgm = PGM(name=data["name"])
        db.session.add(pgm)
        pgms.append(pgm)
    db.session.flush()  # Gera IDs

    # Supervisores
    for s in SUPERVISORS:
        existing = db.session.execute(
            db.select(User).where(User.email == s["email"])
        ).scalar_one_or_none()
        if not existing:
            user = User(name=s["name"], email=s["email"], role=UserRole.SUPERVISOR)
            user.set_password(DEFAULT_PASSWORD)
            db.session.add(user)

    # Líderes
    for name, email, pgm_idx in LEADERS:
        existing = db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar_one_or_none()
        if not existing:
            user = User(name=name, email=email, role=UserRole.LIDER)
            user.set_password(DEFAULT_PASSWORD)
            db.session.add(user)
            db.session.flush()
            db.session.add(PGMLeader(user_id=user.id, pgm_id=pgms[pgm_idx].id))

    # Atividades
    for act_name in LEADER_ACTIVITIES:
        existing = db.session.execute(
            db.select(ActivityType).where(ActivityType.name == act_name)
        ).scalar_one_or_none()
        if not existing:
            db.session.add(ActivityType(name=act_name, source=ActivitySource.LEADER))

    for act_name in JUNIOR_ACTIVITIES:
        existing = db.session.execute(
            db.select(ActivityType).where(ActivityType.name == act_name)
        ).scalar_one_or_none()
        if not existing:
            db.session.add(ActivityType(name=act_name, source=ActivitySource.JUNIOR))

    db.session.commit()
    print("✅ Seed concluído! Senha padrão:", DEFAULT_PASSWORD)
    print("⚠️  Lembre-se de trocar as senhas em produção.")
