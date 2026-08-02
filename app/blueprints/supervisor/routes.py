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
    pgms = db.session.execute(db.select(PGM)).scalars().all()
    return render_template("supervisor/dashboard.html", pgms=pgms)


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
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        role = request.form.get("role")
        pgm_id = request.form.get("pgm_id") or None
        password = request.form.get("password", "").strip()

        # Validações
        errors = []
        if not name:
            errors.append("Nome é obrigatório.")
        if not email:
            errors.append("E-mail é obrigatório.")
        if role not in [r.value for r in UserRole]:
            errors.append("Papel inválido.")
        if not password or len(password) < 6:
            errors.append("Senha deve ter ao menos 6 caracteres.")

        existing = db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar_one_or_none()
        if existing:
            errors.append("Já existe um usuário com este e-mail.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("supervisor/form_usuario.html",
                                   pgms=pgms, modo="novo",
                                   form=request.form)

        user = User(
            name=name,
            email=email,
            role=UserRole(role),
            pgm_id=int(pgm_id) if pgm_id and role == UserRole.JUNIOR.value else None,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # gera o ID

        # Se for júnior, cria o saldo zerado
        if user.role == UserRole.JUNIOR:
            db.session.add(PremilesBalance(junior_id=user.id, total_balance=0))

        # Se for líder, vincula ao PGM escolhido
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
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        pgm_id = request.form.get("pgm_id") or None
        nova_senha = request.form.get("password", "").strip()

        errors = []
        if not name:
            errors.append("Nome é obrigatório.")
        if not email:
            errors.append("E-mail é obrigatório.")

        conflito = db.session.execute(
            db.select(User).where(User.email == email, User.id != user_id)
        ).scalar_one_or_none()
        if conflito:
            errors.append("Já existe outro usuário com este e-mail.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("supervisor/form_usuario.html",
                                   pgms=pgms, modo="editar",
                                   user=user, form=request.form)

        user.name = name
        user.email = email

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
