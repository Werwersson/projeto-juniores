from app import db
from datetime import date


class Period(db.Model):
    """
    Representa um ciclo de acumulação de Premiles.
    Apenas um período pode estar ativo por vez (is_active=True).
    Ao encerrar, o saldo é arquivado em PeriodSnapshot e os saldos
    da premiles_balance são zerados para o próximo ciclo.
    """
    __tablename__ = "periods"

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(120), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date   = db.Column(db.Date, nullable=True)   # NULL = em aberto
    is_active  = db.Column(db.Boolean, default=False, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    closed_at  = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    creator    = db.relationship("User", foreign_keys=[created_by])
    snapshots  = db.relationship("PeriodSnapshot", back_populates="period",
                                 cascade="all, delete-orphan",
                                 order_by="PeriodSnapshot.total_premiles.desc()")

    @property
    def is_open(self):
        return self.end_date is None or self.end_date >= date.today()

    @property
    def duration_days(self):
        end = self.end_date or date.today()
        return (end - self.start_date).days

    def __repr__(self):
        return f"<Period {self.name} active={self.is_active}>"


class PeriodSnapshot(db.Model):
    """
    Guarda o saldo de cada junior no momento do encerramento do período.
    Permite histórico completo sem perder os dados ao zerar os saldos.
    """
    __tablename__ = "period_snapshots"

    id             = db.Column(db.Integer, primary_key=True)
    period_id      = db.Column(db.Integer, db.ForeignKey("periods.id"), nullable=False)
    junior_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    pgm_id         = db.Column(db.Integer, db.ForeignKey("pgms.id"), nullable=True)
    total_premiles = db.Column(db.Integer, default=0, nullable=False)
    position       = db.Column(db.Integer, nullable=True)  # Colocação geral
    pgm_position   = db.Column(db.Integer, nullable=True)  # Colocação dentro do PGM
    created_at     = db.Column(db.DateTime, server_default=db.func.now())

    period = db.relationship("Period", back_populates="snapshots")
    junior = db.relationship("User", foreign_keys=[junior_id])
    pgm    = db.relationship("PGM",  foreign_keys=[pgm_id])

    def __repr__(self):
        return f"<PeriodSnapshot period={self.period_id} junior={self.junior_id} pts={self.total_premiles}>"
