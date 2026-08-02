import enum
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class UserRole(str, enum.Enum):
    SUPERVISOR = "supervisor"
    LIDER = "lider"
    JUNIOR = "junior"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.JUNIOR)

    # Para juniores: FK para o PGM ao qual pertencem.
    # Para líderes e supervisores: NULL (vínculo via pgm_leaders).
    pgm_id = db.Column(db.Integer, db.ForeignKey("pgms.id"), nullable=True)

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relacionamentos
    pgm = db.relationship("PGM", back_populates="juniors", foreign_keys=[pgm_id])
    led_pgms = db.relationship("PGMLeader", back_populates="leader")
    balance = db.relationship("PremilesBalance", back_populates="junior", uselist=False)
    checklist_logs = db.relationship("ChecklistLog", back_populates="junior",
                                     foreign_keys="ChecklistLog.junior_id")
    manual_logs = db.relationship("ManualLog", back_populates="junior",
                                  foreign_keys="ManualLog.junior_id")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # ── Helpers de role ──────────────────────────────────────────────────────
    @property
    def is_supervisor(self) -> bool:
        return self.role == UserRole.SUPERVISOR

    @property
    def is_lider(self) -> bool:
        return self.role == UserRole.LIDER

    @property
    def is_junior(self) -> bool:
        return self.role == UserRole.JUNIOR

    def manages_pgm(self, pgm_id: int) -> bool:
        """Retorna True se o usuário pode administrar o PGM informado."""
        if self.is_supervisor:
            return True
        if self.is_lider:
            return any(pl.pgm_id == pgm_id for pl in self.led_pgms)
        return False

    def __repr__(self) -> str:
        return f"<User {self.name} [{self.role}]>"


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))
