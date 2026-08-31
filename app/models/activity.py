import enum
from app import db


class ActivitySource(str, enum.Enum):
    LEADER = "leader"
    JUNIOR = "junior"


class SummaryStatus(str, enum.Enum):
    PENDENTE  = "pendente"   # Aguardando validação do líder
    APROVADO  = "aprovado"   # Líder aprovou
    REJEITADO = "rejeitado"  # Líder rejeitou — junior deve reescrever


class ActivityType(db.Model):
    __tablename__ = "activity_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    source = db.Column(db.Enum(ActivitySource), nullable=False)
    default_premiles = db.Column(db.Integer, default=10, nullable=False)
    requires_summary = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    checklist_logs = db.relationship("ChecklistLog", back_populates="activity_type")
    manual_logs    = db.relationship("ManualLog",    back_populates="activity_type")

    def __repr__(self):
        return f"<ActivityType {self.name} [{self.source}]>"


class ChecklistLog(db.Model):
    __tablename__ = "checklist_logs"

    id               = db.Column(db.Integer, primary_key=True)
    junior_id        = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    activity_type_id = db.Column(db.Integer, db.ForeignKey("activity_types.id"), nullable=False)
    activity_date    = db.Column(db.Date, nullable=False)
    premiles_awarded = db.Column(db.Integer, nullable=False)

    # Resumo da leitura
    summary        = db.Column(db.Text, nullable=True)
    summary_status = db.Column(db.Enum(SummaryStatus),
                               default=SummaryStatus.PENDENTE, nullable=True)
    # Quem validou e feedback
    validated_by   = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    validator_note = db.Column(db.String(255), nullable=True)
    validated_at   = db.Column(db.DateTime, nullable=True)

    credited_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at  = db.Column(db.DateTime, server_default=db.func.now())

    __table_args__ = (
        db.UniqueConstraint("junior_id", "activity_type_id", "activity_date",
                            name="uq_checklist_daily"),
    )

    junior         = db.relationship("User", back_populates="checklist_logs",
                                     foreign_keys=[junior_id])
    activity_type  = db.relationship("ActivityType", back_populates="checklist_logs")
    credited_by_user = db.relationship("User", foreign_keys=[credited_by])
    validator      = db.relationship("User", foreign_keys=[validated_by])


class ManualLog(db.Model):
    __tablename__ = "manual_logs"

    id               = db.Column(db.Integer, primary_key=True)
    junior_id        = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    activity_type_id = db.Column(db.Integer, db.ForeignKey("activity_types.id"), nullable=False)
    activity_date    = db.Column(db.Date, nullable=False, server_default=db.func.current_date())
    premiles_awarded = db.Column(db.Integer, nullable=False)
    notes            = db.Column(db.String(255), nullable=True)
    launched_by      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at       = db.Column(db.DateTime, server_default=db.func.now())

    junior        = db.relationship("User", back_populates="manual_logs",
                                    foreign_keys=[junior_id])
    activity_type = db.relationship("ActivityType", back_populates="manual_logs")
    launcher      = db.relationship("User", foreign_keys=[launched_by])


class PremilesBalance(db.Model):
    __tablename__ = "premiles_balance"

    id            = db.Column(db.Integer, primary_key=True)
    junior_id     = db.Column(db.Integer, db.ForeignKey("users.id"),
                               unique=True, nullable=False)
    total_balance = db.Column(db.Integer, default=0, nullable=False)
    updated_at    = db.Column(db.DateTime, server_default=db.func.now(),
                               onupdate=db.func.now())

    junior = db.relationship("User", back_populates="balance")
