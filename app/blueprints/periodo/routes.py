from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.blueprints.periodo import periodo_bp
from app.decorators import requires_role
from app.models.user import UserRole
from app.models.period import Period
from app.services.period_service import (
    get_active_period, criar_periodo,
    encerrar_periodo, get_historico, get_ranking_periodo
)
from app import db
from datetime import date


@periodo_bp.route("/")
@login_required
@requires_role(UserRole.SUPERVISOR)
def index():
    ativo    = get_active_period()
    historico = get_historico()
    return render_template("periodo/index.html",
                           ativo=ativo, historico=historico, hoje=date.today())


@periodo_bp.route("/novo", methods=["POST"])
@login_required
@requires_role(UserRole.SUPERVISOR)
def novo():
    name       = request.form.get("name", "").strip()
    start_str  = request.form.get("start_date", "")
    end_str    = request.form.get("end_date", "")

    if not name:
        flash("Informe um nome para o período.", "danger")
        return redirect(url_for("periodo.index"))

    try:
        start_date = date.fromisoformat(start_str)
    except ValueError:
        flash("Data de início inválida.", "danger")
        return redirect(url_for("periodo.index"))

    end_date = None
    if end_str:
        try:
            end_date = date.fromisoformat(end_str)
            if end_date <= start_date:
                flash("A data de fim deve ser posterior à data de início.", "danger")
                return redirect(url_for("periodo.index"))
        except ValueError:
            flash("Data de fim inválida.", "danger")
            return redirect(url_for("periodo.index"))

    try:
        p = criar_periodo(name, start_date, end_date, current_user.id)
        flash(f'Período "{p.name}" criado e ativado com sucesso! 🎉', "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("periodo.index"))


@periodo_bp.route("/<int:periodo_id>/encerrar", methods=["POST"])
@login_required
@requires_role(UserRole.SUPERVISOR)
def encerrar(periodo_id):
    try:
        resultado = encerrar_periodo(periodo_id)
        flash(
            f'Período "{resultado["periodo"]}" encerrado! '
            f'{resultado["snapshots"]} juniores arquivados e saldos zerados. '
            f'Encerrado em {resultado["encerrado_em"]}.',
            "success"
        )
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("periodo.index"))


@periodo_bp.route("/<int:periodo_id>")
@login_required
@requires_role(UserRole.SUPERVISOR)
def detalhe(periodo_id):
    periodo  = db.get_or_404(Period, periodo_id)
    ranking  = get_ranking_periodo(periodo_id)

    # Agrupa por PGM para exibição
    por_pgm = {}
    for snap in ranking:
        nome_pgm = snap.pgm.name if snap.pgm else "Sem PGM"
        por_pgm.setdefault(nome_pgm, []).append(snap)

    return render_template("periodo/detalhe.html",
                           periodo=periodo, ranking=ranking, por_pgm=por_pgm)
