from app import db


class PGM(db.Model):
    __tablename__ = "pgms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(),
                           onupdate=db.func.now())

    juniors = db.relationship("User", back_populates="pgm",
                              foreign_keys="User.pgm_id")
    leaders = db.relationship("PGMLeader", back_populates="pgm")

    def __repr__(self) -> str:
        return f"<PGM {self.name}>"


class PGMLeader(db.Model):
    """Tabela pivô: um líder pode coordenar mais de um PGM."""
    __tablename__ = "pgm_leaders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    pgm_id = db.Column(db.Integer, db.ForeignKey("pgms.id"), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "pgm_id", name="uq_pgm_leader"),
    )

    leader = db.relationship("User", back_populates="led_pgms")
    pgm = db.relationship("PGM", back_populates="leaders")
