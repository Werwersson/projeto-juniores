"""
Popula o banco com:
  - 3 PGMs
  - 2 supervisores (Everson, Keyla)
  - 9 líderes (3 por PGM)
  - Atividades padrão (leader e junior)

Uso (da raiz do projeto):
  python -c "from run import app; from scripts.seed import seed; app.app_context().push(); seed()"
"""
from app import db
from app.models.pgm import PGM, PGMLeader
from app.models.user import User, UserRole
from app.models.activity import ActivityType, ActivitySource, PremilesBalance

PGMS_DATA = [
    {"name": "PGM 1"},
    {"name": "PGM 2"},
    {"name": "PGM 3"},
]

SUPERVISORS = [
    {"name": "Everson", "email": "everson@juniores.app"},
    {"name": "Keyla",   "email": "keyla@juniores.app"},
]

LEADERS = [
    ("Ivan",             "ivan@juniores.app",        0),
    ("Cida",             "cida@juniores.app",         0),
    ("Jaciara",          "jaciara@juniores.app",      0),
    ("Valter Vitoria",   "valter@juniores.app",       1),
    ("Ana Paula",        "anapaula@juniores.app",     1),
    ("Sanmaria",         "sanmaria@juniores.app",     1),
    ("Leo",              "leo@juniores.app",          2),
    ("Katiuscia",        "katiuscia@juniores.app",    2),
    ("Natália Lourenço", "natalia@juniores.app",      2),
]

LEADER_ACTIVITIES = [
    ("Presença",            20),
    ("Levar a Bíblia",      10),
    ("Participação no PGM", 15),
    ("Levar um Visitante",  30),
    ("Senha do Dia",        10),
]

JUNIOR_ACTIVITIES = [
    ("Leitura diária",     10, True),
    ("Estudo da lição",    10, False),
    ("5 minutos com Deus", 10, False),
]

DEFAULT_PASSWORD = "juniores2025"


def seed():
    # PGMs
    pgms = []
    for data in PGMS_DATA:
        existing = db.session.execute(
            db.select(PGM).where(PGM.name == data["name"])
        ).scalar_one_or_none()
        if not existing:
            pgm = PGM(name=data["name"])
            db.session.add(pgm)
            pgms.append(pgm)
        else:
            pgms.append(existing)
    db.session.flush()

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
    for act_name, pts in LEADER_ACTIVITIES:
        existing = db.session.execute(
            db.select(ActivityType).where(ActivityType.name == act_name)
        ).scalar_one_or_none()
        if not existing:
            db.session.add(ActivityType(
                name=act_name, source=ActivitySource.LEADER, default_premiles=pts
            ))

    for act_name, pts, req_summary in JUNIOR_ACTIVITIES:
        existing = db.session.execute(
            db.select(ActivityType).where(ActivityType.name == act_name)
        ).scalar_one_or_none()
        if not existing:
            db.session.add(ActivityType(
                name=act_name, source=ActivitySource.JUNIOR,
                default_premiles=pts, requires_summary=req_summary
            ))

    db.session.commit()
    print("✅ Seed concluído! Senha padrão:", DEFAULT_PASSWORD)
    print("   Supervisores: everson@juniores.app, keyla@juniores.app")
    print("   Líderes: ivan@, cida@, jaciara@, valter@, anapaula@, sanmaria@, leo@, katiuscia@, natalia@juniores.app")
    print("⚠️  Solicite a troca de senha no primeiro acesso.")
