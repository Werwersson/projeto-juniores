import enum
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class UserRole(str, enum.Enum):
    SUPERVISOR = "supervisor"
    LIDER      = "lider"
    JUNIOR     = "junior"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(120), nullable=False)          # Nome exibido
    username      = db.Column(db.String(60), unique=True, nullable=False, index=True)  # Login
    email         = db.Column(db.String(120), unique=True, nullable=True, index=True)  # Opcional
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.JUNIOR)
    pgm_id        = db.Column(db.Integer, db.ForeignKey("pgms.id"), nullable=True)
    created_at    = db.Column(db.DateTime, server_default=db.func.now())

    # Relacionamentos com cascade
    pgm           = db.relationship("PGM", back_populates="juniors", foreign_keys=[pgm_id])
    led_pgms      = db.relationship("PGMLeader", back_populates="leader",
                                    cascade="all, delete-orphan")
    balance       = db.relationship("PremilesBalance", back_populates="junior",
                                    uselist=False, cascade="all, delete-orphan")
    checklist_logs = db.relationship("ChecklistLog", back_populates="junior",
                                     foreign_keys="ChecklistLog.junior_id",
                                     cascade="all, delete-orphan")
    manual_logs   = db.relationship("ManualLog", back_populates="junior",
                                    foreign_keys="ManualLog.junior_id",
                                    cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

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
        if self.is_supervisor:
            return True
        if self.is_lider:
            return any(pl.pgm_id == pgm_id for pl in self.led_pgms)
        return False

    def __repr__(self) -> str:
        return f"<User {self.username} [{self.role}]>"


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))
