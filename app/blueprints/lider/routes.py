from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.blueprints.lider import lider_bp
from app.decorators import requires_role, requires_pgm_access, requires_own_profile_or_leader
from app.models.user import UserRole, User
from app.models.pgm import PGM
from app.models.activity import ActivityType, ActivitySource, ManualLog, ChecklistLog
from app import db
from datetime import date


@lider_bp.route("/dashboard")
@login_required
@requires_role(UserRole.LIDER)
def dashboard():
    # Pega todos os PGMs que este líder coordena
    pgm_ids = [pl.pgm_id for pl in current_user.led_pgms]
    pgms = db.session.execute(
        db.select(PGM).where(PGM.id.in_(pgm_ids))
    ).scalars().all()
    return render_template("lider/dashboard.html", pgms=pgms)


@lider_bp.route("/pgm/<int:pgm_id>/renomear", methods=["POST"])
@login_required
@requires_role(UserRole.SUPERVISOR, UserRole.LIDER)
@requires_pgm_access("pgm_id")
def renomear_pgm(pgm_id: int):
    pgm = db.get_or_404(PGM, pgm_id)
    novo_nome = request.form.get("nome", "").strip()
    if not novo_nome:
        flash("O nome do PGM não pode estar vazio.", "warning")
        return redirect(request.referrer or url_for("lider.dashboard"))
    pgm.name = novo_nome
    db.session.commit()
    flash(f'PGM renomeado para "{novo_nome}".', "success")
    return redirect(request.referrer or url_for("lider.dashboard"))


@lider_bp.route("/junior/<int:junior_id>")
@login_required
@requires_role(UserRole.SUPERVISOR, UserRole.LIDER)
@requires_own_profile_or_leader("junior_id")
def junior_detail(junior_id: int):
    junior = db.get_or_404(User, junior_id)
    return render_template("lider/junior_detail.html", junior=junior)


@lider_bp.route("/lancamento", methods=["GET", "POST"])
@login_required
@requires_role(UserRole.SUPERVISOR, UserRole.LIDER)
def lancamento():
    """Lançamento manual de atividades (Presença, Bíblia, etc.)."""
    # Líderes só veem juniores dos seus PGMs
    if current_user.is_supervisor:
        juniors = db.session.execute(
            db.select(User).where(User.role == UserRole.JUNIOR)
        ).scalars().all()
    else:
        pgm_ids = [pl.pgm_id for pl in current_user.led_pgms]
        juniors = db.session.execute(
            db.select(User).where(
                User.role == UserRole.JUNIOR,
                User.pgm_id.in_(pgm_ids)
            )
        ).scalars().all()

    activities = db.session.execute(
        db.select(ActivityType).where(
            ActivityType.source == ActivitySource.LEADER,
            ActivityType.is_active == True  # noqa: E712
        )
    ).scalars().all()

    checklist_activities = db.session.execute(
        db.select(ActivityType).where(
            ActivityType.source == ActivitySource.JUNIOR,
            ActivityType.is_active == True  # noqa: E712
        )
    ).scalars().all()

    if request.method == "POST":
        junior_id = int(request.form["junior_id"])
        activity_type_id = int(request.form["activity_type_id"])
        premiles = int(request.form["premiles"])
        notes = request.form.get("notes", "")

        # Valida que o líder tem acesso ao junior
        junior = db.get_or_404(User, junior_id)
        if not current_user.is_supervisor and not current_user.manages_pgm(junior.pgm_id):
            flash("Acesso negado a este júnior.", "danger")
            return redirect(url_for("lider.lancamento"))

        log = ManualLog(
            junior_id=junior_id,
            activity_type_id=activity_type_id,
            premiles_awarded=premiles,
            notes=notes,
            launched_by=current_user.id,
        )
        db.session.add(log)

        # Atualiza saldo
        balance = junior.balance
        if balance:
            balance.total_balance += premiles
        else:
            from app.models.activity import PremilesBalance
            db.session.add(PremilesBalance(junior_id=junior_id, total_balance=premiles))

        db.session.commit()
        flash(f"{premiles} Premiles creditados com sucesso!", "success")
        return redirect(url_for("lider.lancamento"))

    return render_template("lider/lancamento.html", juniors=juniors,
                           activities=activities,
                           checklist_activities=checklist_activities)


@lider_bp.route("/credito-retroativo/<int:junior_id>", methods=["POST"])
@login_required
@requires_role(UserRole.SUPERVISOR, UserRole.LIDER)
@requires_own_profile_or_leader("junior_id")
def credito_retroativo(junior_id: int):
    """
    Permite ao líder creditar uma tarefa de checklist que a criança
    esqueceu de marcar em um dia anterior.
    """
    junior = db.get_or_404(User, junior_id)
    activity_type_id = int(request.form["activity_type_id"])
    activity_date_str = request.form["activity_date"]
    premiles = int(request.form["premiles"])

    try:
        activity_date = date.fromisoformat(activity_date_str)
    except ValueError:
        flash("Data inválida.", "danger")
        return redirect(request.referrer or url_for("lider.dashboard"))

    # Bloqueia datas futuras
    if activity_date > date.today():
        flash("Não é possível creditar atividades de datas futuras.", "warning")
        return redirect(request.referrer or url_for("lider.dashboard"))

    # Verifica duplicidade
    existing = db.session.execute(
        db.select(ChecklistLog).where(
            ChecklistLog.junior_id == junior_id,
            ChecklistLog.activity_type_id == activity_type_id,
            ChecklistLog.activity_date == activity_date,
        )
    ).scalar_one_or_none()

    if existing:
        flash("Esta atividade já foi registrada para este dia.", "warning")
        return redirect(request.referrer or url_for("lider.dashboard"))

    log = ChecklistLog(
        junior_id=junior_id,
        activity_type_id=activity_type_id,
        activity_date=activity_date,
        premiles_awarded=premiles,
        credited_by=current_user.id,  # Rastreabilidade: foi o líder que lançou
    )
    db.session.add(log)

    balance = junior.balance
    if balance:
        balance.total_balance += premiles
    else:
        from app.models.activity import PremilesBalance
        db.session.add(PremilesBalance(junior_id=junior_id, total_balance=premiles))

    db.session.commit()
    flash(f"Crédito retroativo de {premiles} Premiles registrado.", "success")
    return redirect(request.referrer or url_for("lider.dashboard"))


# ── Ranking do PGM ───────────────────────────────────────────────────────────

@lider_bp.route("/ranking")
@login_required
@requires_role(UserRole.SUPERVISOR, UserRole.LIDER)
def ranking():
    from app.models.activity import PremilesBalance

    if current_user.is_supervisor:
        from app.models.pgm import PGM
        pgms = db.session.execute(db.select(PGM)).scalars().all()
        juniors = db.session.execute(
            db.select(User)
            .where(User.role == UserRole.JUNIOR)
            .join(PremilesBalance, PremilesBalance.junior_id == User.id, isouter=True)
            .order_by(db.desc(PremilesBalance.total_balance))
        ).scalars().all()
    else:
        from app.models.pgm import PGM
        pgm_ids = [pl.pgm_id for pl in current_user.led_pgms]
        pgms = db.session.execute(
            db.select(PGM).where(PGM.id.in_(pgm_ids))
        ).scalars().all()
        juniors = db.session.execute(
            db.select(User)
            .where(User.role == UserRole.JUNIOR, User.pgm_id.in_(pgm_ids))
            .join(PremilesBalance, PremilesBalance.junior_id == User.id, isouter=True)
            .order_by(db.desc(PremilesBalance.total_balance))
        ).scalars().all()

    return render_template("lider/ranking.html", juniors=juniors, pgms=pgms)


# ── Histórico de atividades do PGM ───────────────────────────────────────────

@lider_bp.route("/historico")
@login_required
@requires_role(UserRole.SUPERVISOR, UserRole.LIDER)
def historico():
    from app.models.activity import ManualLog, ChecklistLog, PremilesBalance

    if current_user.is_supervisor:
        manual_logs = db.session.execute(
            db.select(ManualLog).order_by(ManualLog.created_at.desc()).limit(200)
        ).scalars().all()
        checklist_logs = db.session.execute(
            db.select(ChecklistLog).order_by(ChecklistLog.created_at.desc()).limit(200)
        ).scalars().all()
    else:
        pgm_ids = [pl.pgm_id for pl in current_user.led_pgms]
        junior_ids = [
            u.id for u in db.session.execute(
                db.select(User).where(
                    User.role == UserRole.JUNIOR,
                    User.pgm_id.in_(pgm_ids)
                )
            ).scalars().all()
        ]
        manual_logs = db.session.execute(
            db.select(ManualLog)
            .where(ManualLog.junior_id.in_(junior_ids))
            .order_by(ManualLog.created_at.desc())
            .limit(200)
        ).scalars().all()
        checklist_logs = db.session.execute(
            db.select(ChecklistLog)
            .where(ChecklistLog.junior_id.in_(junior_ids))
            .order_by(ChecklistLog.created_at.desc())
            .limit(200)
        ).scalars().all()

    return render_template("lider/historico.html",
                           manual_logs=manual_logs,
                           checklist_logs=checklist_logs)


# ── Lançamento em lote (presença do PGM inteiro) ─────────────────────────────

@lider_bp.route("/lancamento-lote", methods=["POST"])
@login_required
@requires_role(UserRole.SUPERVISOR, UserRole.LIDER)
def lancamento_lote():
    from app.models.activity import ManualLog, PremilesBalance, ActivityType

    activity_type_id = int(request.form["activity_type_id"])
    premiles = int(request.form["premiles"])
    notes = request.form.get("notes", "")
    junior_ids = request.form.getlist("junior_ids")  # checkboxes

    if not junior_ids:
        flash("Selecione ao menos um júnior.", "warning")
        return redirect(url_for("lider.lancamento"))

    activity = db.get_or_404(ActivityType, activity_type_id)
    creditados = 0

    for jid in junior_ids:
        junior = db.session.get(User, int(jid))
        if not junior:
            continue
        # Segurança: garante que o líder tem acesso a este júnior
        if not current_user.is_supervisor and not current_user.manages_pgm(junior.pgm_id):
            continue

        log = ManualLog(
            junior_id=junior.id,
            activity_type_id=activity_type_id,
            premiles_awarded=premiles,
            notes=notes,
            launched_by=current_user.id,
        )
        db.session.add(log)

        balance = junior.balance
        if balance:
            balance.total_balance += premiles
        else:
            db.session.add(PremilesBalance(junior_id=junior.id, total_balance=premiles))

        creditados += 1

    db.session.commit()
    flash(f"✅ {premiles} Premiles creditados para {creditados} júnior(es) — {activity.name}.", "success")
    return redirect(url_for("lider.lancamento"))


# ── Excluir lançamento manual (com reversão de saldo) ────────────────────────

@lider_bp.route("/lancamento/<int:log_id>/excluir", methods=["POST"])
@login_required
@requires_role(UserRole.SUPERVISOR, UserRole.LIDER)
def excluir_lancamento(log_id: int):
    from app.models.activity import ManualLog

    log = db.get_or_404(ManualLog, log_id)
    junior = db.session.get(User, log.junior_id)

    # Segurança: só o líder do PGM ou supervisor pode excluir
    if not current_user.is_supervisor and not current_user.manages_pgm(junior.pgm_id):
        flash("Acesso negado.", "danger")
        return redirect(url_for("lider.historico"))

    # Reverte o saldo
    if junior and junior.balance:
        junior.balance.total_balance = max(0, junior.balance.total_balance - log.premiles_awarded)

    db.session.delete(log)
    db.session.commit()
    flash(f"Lançamento excluído e {log.premiles_awarded} Premiles revertidos.", "info")
    return redirect(url_for("lider.historico"))
