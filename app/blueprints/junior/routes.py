from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.blueprints.junior import junior_bp
from app.decorators import requires_role
from app.models.user import UserRole
from app.models.activity import ActivityType, ActivitySource, ChecklistLog, ManualLog, PremilesBalance
from app import db
from datetime import date


@junior_bp.route("/dashboard")
@login_required
@requires_role(UserRole.JUNIOR)
def dashboard():
    balance = current_user.balance
    saldo = balance.total_balance if balance else 0
    return render_template("junior/dashboard.html", saldo=saldo)


@junior_bp.route("/checklist", methods=["GET", "POST"])
@login_required
@requires_role(UserRole.JUNIOR)
def checklist():
    today = date.today()

    activities = db.session.execute(
        db.select(ActivityType).where(
            ActivityType.source == ActivitySource.JUNIOR,
            ActivityType.is_active == True  # noqa: E712
        )
    ).scalars().all()

    already_done_ids = set(
        row.activity_type_id
        for row in db.session.execute(
            db.select(ChecklistLog.activity_type_id).where(
                ChecklistLog.junior_id == current_user.id,
                ChecklistLog.activity_date == today,
            )
        ).all()
    )

    if request.method == "POST":
        activity_type_id = int(request.form["activity_type_id"])

        if activity_type_id in already_done_ids:
            flash("Você já marcou esta atividade hoje.", "warning")
            return redirect(url_for("junior.checklist"))

        activity = db.get_or_404(ActivityType, activity_type_id)

        # Segurança: confirma que é atividade do tipo junior
        if activity.source != ActivitySource.JUNIOR:
            flash("Atividade inválida.", "danger")
            return redirect(url_for("junior.checklist"))

        # Valor de Premiles vem do campo default_premiles da atividade
        premiles = activity.default_premiles or 10

        log = ChecklistLog(
            junior_id=current_user.id,
            activity_type_id=activity_type_id,
            activity_date=today,
            premiles_awarded=premiles,
            credited_by=None,
        )
        db.session.add(log)

        balance = current_user.balance
        if balance:
            balance.total_balance += premiles
        else:
            db.session.add(PremilesBalance(
                junior_id=current_user.id,
                total_balance=premiles
            ))

        db.session.commit()
        flash(f"+{premiles} Premiles! Continue assim! 🎉", "success")
        return redirect(url_for("junior.checklist"))

    return render_template(
        "junior/checklist.html",
        activities=activities,
        already_done_ids=already_done_ids,
        today=today,
    )


@junior_bp.route("/extrato")
@login_required
@requires_role(UserRole.JUNIOR)
def extrato():
    """Histórico completo de Premiles do junior logado. BUG CORRIGIDO: query única."""
    checklist_logs = db.session.execute(
        db.select(ChecklistLog)
        .where(ChecklistLog.junior_id == current_user.id)
        .order_by(ChecklistLog.created_at.desc())
    ).scalars().all()

    manual_logs = db.session.execute(
        db.select(ManualLog)
        .where(ManualLog.junior_id == current_user.id)
        .order_by(ManualLog.created_at.desc())
    ).scalars().all()

    balance = current_user.balance
    saldo = balance.total_balance if balance else 0

    return render_template(
        "junior/extrato.html",
        checklist_logs=checklist_logs,
        manual_logs=manual_logs,
        saldo=saldo,
    )
