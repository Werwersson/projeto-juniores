from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.blueprints.period import period_bp
from app.decorators import requires_role
from app.models.user import UserRole
from app.models.audit import log as audit_log, LogAction
from app.services.period_service import (
    get_active_period, criar_periodo, encerrar_periodo,
    get_historico, get_ranking_periodo
)
from datetime import date


@period_bp.route("/")
@login_required
@requires_role(UserRole.SUPERVISOR)
def index():
    ativo = get_active_period()
    historico = get_historico()
    return render_template("period/index.html", ativo=ativo, historico=historico)


@period_bp.route("/novo", methods=["POST"])
@login_required
@requires_role(UserRole.SUPERVISOR)
def novo():
    name = request.form.get("name", "").strip()
    start_date_str = request.form.get("start_date", "")
    end_date_str = request.form.get("end_date", "").strip()

    if not name:
        flash("O nome do período é obrigatório.", "danger")
        return redirect(url_for("period.index"))

    try:
        start_date = date.fromisoformat(start_date_str)
    except ValueError:
        flash("Data de início inválida.", "danger")
        return redirect(url_for("period.index"))

    end_date = None
    if end_date_str:
        try:
            end_date = date.fromisoformat(end_date_str)
            if end_date <= start_date:
                flash("A data de fim deve ser posterior à data de início.", "danger")
                return redirect(url_for("period.index"))
        except ValueError:
            flash("Data de fim inválida.", "danger")
            return redirect(url_for("period.index"))

    try:
        periodo = criar_periodo(
            name=name,
            start_date=start_date,
            end_date=end_date,
            created_by_id=current_user.id,
        )
        audit_log(LogAction.PERIODO_CRIADO,
                  f'Período "{periodo.name}" iniciado ({start_date})',
                  actor=current_user)
        from app import db; db.session.commit()
        flash(f'Período "{periodo.name}" iniciado com sucesso! ✅', "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("period.index"))


@period_bp.route("/<int:periodo_id>/encerrar", methods=["POST"])
@login_required
@requires_role(UserRole.SUPERVISOR)
def encerrar(periodo_id):
    try:
        resultado = encerrar_periodo(periodo_id)
        audit_log(LogAction.PERIODO_ENCERRADO,
                  f'Período "{resultado["periodo"]}" encerrado com {resultado["snapshots"]} juniores',
                  actor=current_user)
        from app import db; db.session.commit()
        flash(
            f'Período "{resultado["periodo"]}" encerrado! '
            f'{resultado["snapshots"]} saldos arquivados e zerados. '
            f'Encerrado em {resultado["encerrado_em"]}.',
            "success"
        )
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("period.index"))


@period_bp.route("/<int:periodo_id>/resultado")
@login_required
@requires_role(UserRole.SUPERVISOR)
def resultado(periodo_id):
    from app.models.period import Period
    from app import db
    periodo = db.get_or_404(Period, periodo_id)
    snapshots = get_ranking_periodo(periodo_id)
    return render_template("period/resultado.html", periodo=periodo, snapshots=snapshots)
