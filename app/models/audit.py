import enum
from app import db


class LogAction(str, enum.Enum):
    # Auth
    LOGIN_OK       = "login_ok"
    LOGIN_FAIL     = "login_fail"
    LOGOUT         = "logout"
    SENHA_TROCADA  = "senha_trocada"
    SENHA_REDEFINIDA = "senha_redefinida"
    RESET_GERADO   = "reset_gerado"
    PERFIL_EDITADO = "perfil_editado"

    # Usuários
    USUARIO_CRIADO  = "usuario_criado"
    USUARIO_EDITADO = "usuario_editado"
    USUARIO_EXCLUIDO = "usuario_excluido"

    # Premiles
    CHECKLIST_MARCADO   = "checklist_marcado"
    LANCAMENTO_MANUAL   = "lancamento_manual"
    LANCAMENTO_LOTE     = "lancamento_lote"
    LANCAMENTO_EXCLUIDO = "lancamento_excluido"
    CREDITO_RETROATIVO  = "credito_retroativo"

    # Resumos
    RESUMO_ENVIADO   = "resumo_enviado"
    RESUMO_APROVADO  = "resumo_aprovado"
    RESUMO_REJEITADO = "resumo_rejeitado"
    RESUMO_REENVIADO = "resumo_reenviado"

    # PGM
    PGM_RENOMEADO = "pgm_renomeado"

    # Períodos
    PERIODO_CRIADO    = "periodo_criado"
    PERIODO_ENCERRADO = "periodo_encerrado"

    # Atividades
    ATIVIDADE_CRIADA  = "atividade_criada"
    ATIVIDADE_EDITADA = "atividade_editada"
    ATIVIDADE_TOGGLE  = "atividade_toggle"


class AuditLog(db.Model):
    """
    Registro de auditoria de todas as ações relevantes do sistema.
    Imutável — nunca é editado ou excluído pelo sistema.
    """
    __tablename__ = "audit_logs"

    id          = db.Column(db.Integer, primary_key=True)

    # Quem fez a ação (None = ação não autenticada, ex: login_fail)
    actor_id    = db.Column(db.Integer, db.ForeignKey("users.id",
                            ondelete="SET NULL"), nullable=True)
    actor_name  = db.Column(db.String(120), nullable=True)  # Snapshot do nome

    # Ação realizada
    action      = db.Column(db.Enum(LogAction), nullable=False)
    description = db.Column(db.String(500), nullable=False)

    # Usuário alvo (quando a ação envolve outro usuário)
    target_user_id   = db.Column(db.Integer, db.ForeignKey("users.id",
                                  ondelete="SET NULL"), nullable=True)
    target_user_name = db.Column(db.String(120), nullable=True)

    # Metadados
    ip_address  = db.Column(db.String(45), nullable=True)
    created_at  = db.Column(db.DateTime, server_default=db.func.now(), index=True)

    actor  = db.relationship("User", foreign_keys=[actor_id])
    target = db.relationship("User", foreign_keys=[target_user_id])

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.actor_name}>"


def log(action: LogAction, description: str,
        actor=None, target_user=None, ip: str = None):
    """
    Registra uma entrada de auditoria.

    Uso:
        from app.models.audit import log, LogAction
        log(LogAction.LOGIN_OK, f"{user.name} fez login", actor=user, ip=ip)
    """
    from flask import request as flask_request
    try:
        ip_addr = ip or flask_request.headers.get(
            "X-Forwarded-For", flask_request.remote_addr or ""
        ).split(",")[0].strip()
    except RuntimeError:
        ip_addr = None

    entry = AuditLog(
        actor_id=actor.id if actor else None,
        actor_name=actor.name if actor else None,
        action=action,
        description=description,
        target_user_id=target_user.id if target_user else None,
        target_user_name=target_user.name if target_user else None,
        ip_address=ip_addr,
    )
    db.session.add(entry)
    # Não dá commit aqui — o commit fica na rota chamadora,
    # garantindo que log e ação sejam atômicos.
