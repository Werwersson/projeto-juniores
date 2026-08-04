from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.blueprints.auth import auth_bp
from app.models.user import User, UserRole
from app import db

SENHA_PADRAO = "juniores2025"


def _dashboard_url():
    if current_user.role == UserRole.SUPERVISOR:
        return url_for("supervisor.dashboard")
    if current_user.role == UserRole.LIDER:
        return url_for("lider.dashboard")
    return url_for("junior.dashboard")


@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(_dashboard_url())
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_dashboard_url())

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = db.session.execute(
            db.select(User).where(User.username == username)
        ).scalar_one_or_none()

        if user and user.check_password(password):
            login_user(user, remember=remember)

            if password == SENHA_PADRAO:
                session["force_password_change"] = True
                flash("Por segurança, defina uma nova senha antes de continuar.", "warning")
                return redirect(url_for("auth.trocar_senha"))

            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(_dashboard_url())

        flash("Nome de usuário ou senha incorretos.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Até logo!", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/trocar-senha", methods=["GET", "POST"])
@login_required
def trocar_senha():
    force = session.get("force_password_change", False)

    if request.method == "POST":
        senha_atual = request.form.get("senha_atual", "")
        nova_senha  = request.form.get("nova_senha", "")
        confirmar   = request.form.get("confirmar", "")

        if not current_user.check_password(senha_atual):
            flash("Senha atual incorreta.", "danger")
            return render_template("auth/trocar_senha.html", force=force)

        if len(nova_senha) < 6:
            flash("A nova senha deve ter ao menos 6 caracteres.", "danger")
            return render_template("auth/trocar_senha.html", force=force)

        if nova_senha != confirmar:
            flash("As senhas não coincidem.", "danger")
            return render_template("auth/trocar_senha.html", force=force)

        if nova_senha == SENHA_PADRAO:
            flash("Escolha uma senha diferente da senha padrão.", "danger")
            return render_template("auth/trocar_senha.html", force=force)

        current_user.set_password(nova_senha)
        db.session.commit()
        session.pop("force_password_change", None)
        flash("Senha alterada com sucesso! 🎉", "success")
        return redirect(_dashboard_url())

    return render_template("auth/trocar_senha.html", force=force)
