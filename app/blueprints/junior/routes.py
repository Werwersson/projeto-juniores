from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.blueprints.junior import junior_bp
from app.decorators import requires_role
from app.models.user import UserRole
from app.models.audit import log as audit_log, LogAction
from app.models.activity import (ActivityType, ActivitySource, ChecklistLog,
                                  ManualLog, PremilesBalance, SummaryStatus)
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

    # Logs de hoje (para saber status de cada atividade)
    logs_hoje = {
        row.activity_type_id: row
        for row in db.session.execute(
            db.select(ChecklistLog).where(
                ChecklistLog.junior_id == current_user.id,
                ChecklistLog.activity_date == today,
            )
        ).scalars().all()
    }

    already_done_ids = set(
        aid for aid, log in logs_hoje.items()
        if log.summary_status != SummaryStatus.REJEITADO
    )

    if request.method == "POST":
        activity_type_id = int(request.form["activity_type_id"])
        summary = request.form.get("summary", "").strip()

        activity = db.get_or_404(ActivityType, activity_type_id)

        if activity.source != ActivitySource.JUNIOR:
            flash("Atividade inválida.", "danger")
            return redirect(url_for("junior.checklist"))

        if activity.requires_summary and not summary:
            flash("Por favor, escreva um resumo da sua leitura.", "warning")
            return redirect(url_for("junior.checklist"))

        if activity.requires_summary and len(summary) < 10:
            flash("Resumo muito curto. Escreva pelo menos 10 caracteres.", "warning")
            return redirect(url_for("junior.checklist"))

        premiles = activity.default_premiles or 10

        # Se foi rejeitado hoje, atualiza o log existente em vez de criar novo
        log_existente = logs_hoje.get(activity_type_id)
        if log_existente and log_existente.summary_status == SummaryStatus.REJEITADO:
            log_existente.summary        = summary
            log_existente.summary_status = SummaryStatus.PENDENTE
            log_existente.validated_by   = None
            log_existente.validator_note = None
            log_existente.validated_at   = None
            # Recredita os Premiles que foram revertidos
            balance = current_user.balance
            if balance:
                balance.total_balance += premiles
            else:
                db.session.add(PremilesBalance(
                    junior_id=current_user.id, total_balance=premiles))
            audit_log(LogAction.RESUMO_REENVIADO,
                      f"{current_user.name} reenviou resumo de '{activity.name}'",
                      actor=current_user)
            db.session.commit()
            flash(f"Resumo reenviado! +{premiles} Premiles creditados novamente. 🎉", "success")
            return redirect(url_for("junior.checklist"))

        # Checagem de duplicidade normal
        if activity_type_id in already_done_ids:
            flash("Você já marcou esta atividade hoje.", "warning")
            return redirect(url_for("junior.checklist"))

        log = ChecklistLog(
            junior_id=current_user.id,
            activity_type_id=activity_type_id,
            activity_date=today,
            premiles_awarded=premiles,
            summary=summary if summary else None,
            summary_status=SummaryStatus.PENDENTE if (summary and activity.requires_summary) else None,
            credited_by=None,
        )
        db.session.add(log)

        balance = current_user.balance
        if balance:
            balance.total_balance += premiles
        else:
            db.session.add(PremilesBalance(
                junior_id=current_user.id, total_balance=premiles))

        audit_log(LogAction.CHECKLIST_MARCADO,
                  f"{current_user.name} marcou '{activity.name}' (+{premiles} Premiles)",
                  actor=current_user)
        db.session.commit()
        flash(f"+{premiles} Premiles! Continue assim! 🎉", "success")
        return redirect(url_for("junior.checklist"))

    return render_template(
        "junior/checklist.html",
        activities=activities,
        already_done_ids=already_done_ids,
        logs_hoje=logs_hoje,
        today=today,
    )


@junior_bp.route("/extrato")
@login_required
@requires_role(UserRole.JUNIOR)
def extrato():
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


# ── Perfil do júnior ──────────────────────────────────────────────────────────

@junior_bp.route("/perfil", methods=["GET", "POST"])
@login_required
@requires_role(UserRole.JUNIOR)
def perfil():
    from datetime import date as date_type

    if request.method == "POST":
        nome_completo   = request.form.get("nome_completo", "").strip() or None
        whatsapp        = request.form.get("whatsapp", "").strip() or None
        nome_pai        = request.form.get("nome_pai", "").strip() or None
        nome_mae        = request.form.get("nome_mae", "").strip() or None
        responsavel     = request.form.get("responsavel", "").strip() or None
        alergias        = request.form.get("alergias", "").strip() or None
        nasc_str        = request.form.get("data_nascimento", "").strip()

        data_nascimento = None
        if nasc_str:
            try:
                data_nascimento = date_type.fromisoformat(nasc_str)
            except ValueError:
                flash("Data de nascimento inválida.", "danger")
                return render_template("junior/perfil.html")

        current_user.nome_completo   = nome_completo
        current_user.whatsapp        = whatsapp
        current_user.nome_pai        = nome_pai
        current_user.nome_mae        = nome_mae
        current_user.responsavel     = responsavel
        current_user.alergias        = alergias
        current_user.data_nascimento = data_nascimento

        db.session.commit()
        flash("Perfil atualizado com sucesso! ✅", "success")
        return redirect(url_for("junior.perfil"))

    return render_template("junior/perfil.html")
