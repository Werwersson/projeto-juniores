from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.blueprints.supervisor import supervisor_bp
from app.decorators import requires_role
from app.models.user import UserRole, User
from app.models.pgm import PGM, PGMLeader
from app.models.activity import PremilesBalance
from app import db


@supervisor_bp.route("/dashboard")
@login_required
@requires_role(UserRole.SUPERVISOR)
def dashboard():
    from app.services.period_service import get_active_period
    from app.models.activity import ChecklistLog, ManualLog
    from datetime import date as _date

    pgms = db.session.execute(db.select(PGM)).scalars().all()
    periodo_ativo = get_active_period()

    # Premiles creditados hoje
    hoje = _date.today()
    premiles_hoje = db.session.execute(
        db.select(db.func.sum(ManualLog.premiles_awarded))
        .where(db.func.date(ManualLog.created_at) == hoje)
    ).scalar() or 0
    premiles_hoje += db.session.execute(
        db.select(db.func.sum(ChecklistLog.premiles_awarded))
        .where(ChecklistLog.activity_date == hoje)
    ).scalar() or 0

    return render_template("supervisor/dashboard.html",
                           pgms=pgms,
                           periodo_ativo=periodo_ativo,
                           premiles_hoje=premiles_hoje)


@supervisor_bp.route("/pgm/<int:pgm_id>")
@login_required
@requires_role(UserRole.SUPERVISOR)
def pgm_detail(pgm_id):
    pgm = db.get_or_404(PGM, pgm_id)
    juniors = db.session.execute(
        db.select(User).where(User.pgm_id == pgm_id)
    ).scalars().all()
    return render_template("supervisor/pgm_detail.html", pgm=pgm, juniors=juniors)


@supervisor_bp.route("/junior/<int:junior_id>")
@login_required
@requires_role(UserRole.SUPERVISOR)
def junior_detail(junior_id):
    junior = db.get_or_404(User, junior_id)
    return render_template("supervisor/junior_detail.html", junior=junior)


# ── CRUD de Usuários ──────────────────────────────────────────────────────────

@supervisor_bp.route("/usuarios")
@login_required
@requires_role(UserRole.SUPERVISOR)
def usuarios():
    todos = db.session.execute(
        db.select(User).order_by(User.role, User.name)
    ).scalars().all()
    pgms = db.session.execute(db.select(PGM).order_by(PGM.name)).scalars().all()
    return render_template("supervisor/usuarios.html", usuarios=todos, pgms=pgms)


@supervisor_bp.route("/usuarios/novo", methods=["GET", "POST"])
@login_required
@requires_role(UserRole.SUPERVISOR)
def novo_usuario():
    pgms = db.session.execute(db.select(PGM).order_by(PGM.name)).scalars().all()

    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip().lower()
        email    = request.form.get("email", "").strip().lower() or None
        role     = request.form.get("role")
        pgm_id   = request.form.get("pgm_id") or None
        password = request.form.get("password", "").strip()

        errors = []
        if not name:
            errors.append("Nome completo é obrigatório.")
        if not username:
            errors.append("Nome de usuário é obrigatório.")
        if len(username) < 3:
            errors.append("Nome de usuário deve ter ao menos 3 caracteres.")
        if role not in [r.value for r in UserRole]:
            errors.append("Papel inválido.")
        if not password or len(password) < 6:
            errors.append("Senha deve ter ao menos 6 caracteres.")

        # Verifica username duplicado
        if username and db.session.execute(
            db.select(User).where(User.username == username)
        ).scalar_one_or_none():
            errors.append(f'O nome de usuário "{username}" já está em uso.')

        # Verifica email duplicado (só se preenchido)
        if email and db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar_one_or_none():
            errors.append("Já existe um usuário com este e-mail.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("supervisor/form_usuario.html",
                                   pgms=pgms, modo="novo", form=request.form)

        user = User(
            name=name,
            username=username,
            email=email,
            role=UserRole(role),
            pgm_id=int(pgm_id) if pgm_id and role == UserRole.JUNIOR.value else None,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        if user.role == UserRole.JUNIOR:
            db.session.add(PremilesBalance(junior_id=user.id, total_balance=0))
        if user.role == UserRole.LIDER and pgm_id:
            db.session.add(PGMLeader(user_id=user.id, pgm_id=int(pgm_id)))

        db.session.commit()
        flash(f"Usuário {name} cadastrado com sucesso!", "success")
        return redirect(url_for("supervisor.usuarios"))

    return render_template("supervisor/form_usuario.html",
                           pgms=pgms, modo="novo", form={})


@supervisor_bp.route("/usuarios/<int:user_id>/editar", methods=["GET", "POST"])
@login_required
@requires_role(UserRole.SUPERVISOR)
def editar_usuario(user_id):
    user = db.get_or_404(User, user_id)
    pgms = db.session.execute(db.select(PGM).order_by(PGM.name)).scalars().all()

    if request.method == "POST":
        name       = request.form.get("name", "").strip()
        username   = request.form.get("username", "").strip().lower()
        email      = request.form.get("email", "").strip().lower() or None
        pgm_id     = request.form.get("pgm_id") or None
        nova_senha = request.form.get("password", "").strip()

        errors = []
        if not name:
            errors.append("Nome completo é obrigatório.")
        if not username or len(username) < 3:
            errors.append("Nome de usuário deve ter ao menos 3 caracteres.")

        if username and db.session.execute(
            db.select(User).where(User.username == username, User.id != user_id)
        ).scalar_one_or_none():
            errors.append(f'O nome de usuário "{username}" já está em uso.')

        if email and db.session.execute(
            db.select(User).where(User.email == email, User.id != user_id)
        ).scalar_one_or_none():
            errors.append("Já existe outro usuário com este e-mail.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("supervisor/form_usuario.html",
                                   pgms=pgms, modo="editar",
                                   user=user, form=request.form)

        user.name     = name
        user.username = username
        user.email    = email

        # Atualiza PGM do júnior
        if user.role == UserRole.JUNIOR and pgm_id:
            user.pgm_id = int(pgm_id)

        # Atualiza vínculo do líder
        if user.role == UserRole.LIDER and pgm_id:
            vínculo = db.session.execute(
                db.select(PGMLeader).where(PGMLeader.user_id == user_id)
            ).scalar_one_or_none()
            if vínculo:
                vínculo.pgm_id = int(pgm_id)
            else:
                db.session.add(PGMLeader(user_id=user_id, pgm_id=int(pgm_id)))

        if nova_senha and len(nova_senha) >= 6:
            user.set_password(nova_senha)

        db.session.commit()
        flash(f"Usuário {name} atualizado com sucesso!", "success")
        return redirect(url_for("supervisor.usuarios"))

    return render_template("supervisor/form_usuario.html",
                           pgms=pgms, modo="editar",
                           user=user, form={})


@supervisor_bp.route("/usuarios/<int:user_id>/excluir", methods=["POST"])
@login_required
@requires_role(UserRole.SUPERVISOR)
def excluir_usuario(user_id):
    user = db.get_or_404(User, user_id)

    # Impede auto-exclusão
    if user.id == current_user.id:
        flash("Você não pode excluir sua própria conta.", "danger")
        return redirect(url_for("supervisor.usuarios"))

    nome = user.name
    db.session.delete(user)
    db.session.commit()
    flash(f"Usuário {nome} removido.", "info")
    return redirect(url_for("supervisor.usuarios"))


# ── Ranking ───────────────────────────────────────────────────────────────────

@supervisor_bp.route("/ranking")
@login_required
@requires_role(UserRole.SUPERVISOR)
def ranking():
    pgms = db.session.execute(db.select(PGM)).scalars().all()

    # Todos os juniores ordenados por saldo desc
    juniors = db.session.execute(
        db.select(User)
        .where(User.role == UserRole.JUNIOR)
        .join(PremilesBalance, PremilesBalance.junior_id == User.id, isouter=True)
        .order_by(db.desc(PremilesBalance.total_balance))
    ).scalars().all()

    return render_template("supervisor/ranking.html", juniors=juniors, pgms=pgms)


# ── Exportação de relatórios ──────────────────────────────────────────────────

@supervisor_bp.route("/relatorio/excel")
@login_required
@requires_role(UserRole.SUPERVISOR)
def relatorio_excel():
    from flask import send_file
    from app.services.relatorio_service import gerar_excel
    from datetime import datetime

    pgms = db.session.execute(db.select(PGM)).scalars().all()
    buf = gerar_excel(pgms, titulo="Relatório de Premiles — Projeto Juniores")

    nome = f"premiles_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=nome,
    )


@supervisor_bp.route("/relatorio/pdf")
@login_required
@requires_role(UserRole.SUPERVISOR)
def relatorio_pdf():
    from flask import send_file
    from app.services.relatorio_service import gerar_pdf
    from datetime import datetime

    pgms = db.session.execute(db.select(PGM)).scalars().all()
    buf = gerar_pdf(pgms, titulo="Relatório de Premiles — Projeto Juniores")

    nome = f"premiles_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return send_file(
        buf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=nome,
    )


@supervisor_bp.route("/relatorios")
@login_required
@requires_role(UserRole.SUPERVISOR)
def relatorios():
    pgms = db.session.execute(db.select(PGM)).scalars().all()
    return render_template("supervisor/relatorios.html", pgms=pgms)
