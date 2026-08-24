import enum
import secrets
from datetime import datetime, timedelta
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
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.JUNIOR)
    pgm_id        = db.Column(db.Integer, db.ForeignKey("pgms.id"), nullable=True)

    # Recuperação de senha
    reset_token        = db.Column(db.String(64), nullable=True, unique=True, index=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # ── Perfil do júnior ──────────────────────────────────────────────────────
    nome_completo   = db.Column(db.String(180), nullable=True)
    sexo            = db.Column(db.String(20), nullable=True)
    data_nascimento = db.Column(db.Date, nullable=True)
    email_contato   = db.Column(db.String(120), nullable=True)
    whatsapp        = db.Column(db.String(20),  nullable=True)
    celular         = db.Column(db.String(20), nullable=True)
    naturalidade    = db.Column(db.String(120), nullable=True)
    cpf             = db.Column(db.String(14), nullable=True, unique=True, index=True)
    nome_pai        = db.Column(db.String(120), nullable=True)
    nome_mae        = db.Column(db.String(120), nullable=True)
    responsavel     = db.Column(db.String(120), nullable=True)  # Opcional
    alergias        = db.Column(db.Text, nullable=True)

    # ── Endereço ─────────────────────────────────────────────────────────────
    endereco_rua    = db.Column(db.String(200), nullable=True)
    endereco_numero = db.Column(db.String(20), nullable=True)
    endereco_bairro = db.Column(db.String(100), nullable=True)
    endereco_cidade = db.Column(db.String(100), nullable=True)
    endereco_estado = db.Column(db.String(2), nullable=True)
    endereco_cep    = db.Column(db.String(10), nullable=True)

    pgm            = db.relationship("PGM", back_populates="juniors", foreign_keys=[pgm_id])
    led_pgms       = db.relationship("PGMLeader", back_populates="leader",
                                     cascade="all, delete-orphan")
    balance        = db.relationship("PremilesBalance", back_populates="junior",
                                     uselist=False, cascade="all, delete-orphan")
    checklist_logs = db.relationship("ChecklistLog", back_populates="junior",
                                     foreign_keys="ChecklistLog.junior_id",
                                     cascade="all, delete-orphan")
    manual_logs    = db.relationship("ManualLog", back_populates="junior",
                                     foreign_keys="ManualLog.junior_id",
                                     cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self, hours: int = 24) -> str:
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.now() + timedelta(hours=hours)
        return self.reset_token

    def clear_reset_token(self) -> None:
        self.reset_token = None
        self.reset_token_expiry = None

    @property
    def reset_token_valid(self) -> bool:
        if not self.reset_token or not self.reset_token_expiry:
            return False
        return datetime.now() < self.reset_token_expiry

    # ── Helpers de role — robustos a String e Enum ───────────────────────────
    def _role_str(self) -> str:
        """Retorna o valor do role sempre como string lower, independente do tipo."""
        r = self.role
        if isinstance(r, UserRole):
            return r.value
        return str(r).lower().replace("userrole.", "").replace("'", "").strip()

    @property
    def is_supervisor(self) -> bool:
        return self._role_str() == "supervisor"

    @property
    def is_lider(self) -> bool:
        return self._role_str() == "lider"

    @property
    def is_junior(self) -> bool:
        return self._role_str() == "junior"

    def manages_pgm(self, pgm_id: int) -> bool:
        if self.is_supervisor:
            return True
        if self.is_lider:
            return any(pl.pgm_id == pgm_id for pl in self.led_pgms)
        return False

    def __repr__(self) -> str:
        return f"<User {self.email} [{self.role}]>"


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))
