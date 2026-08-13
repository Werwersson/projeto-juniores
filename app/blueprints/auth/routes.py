from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.blueprints.auth import auth_bp
from app.models.user import User, UserRole
from app.models.audit import log as audit_log, LogAction
from app import db
import time

SENHA_PADRAO = "juniores2025"
MAX_ATTEMPTS = 5

def _get_ip() -> str:
    return request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()

def _dashboard_url() -> str:
    """Retorna a URL do dashboard correto, robusto a String e Enum no role."""
    role = current_user.role
    role_str = role.value if hasattr(role, "value") else str(role).lower()
    if "supervisor" in role_str:
        return url_for("supervisor.dashboard")
    if "lider" in role_str:
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

    ip = _get_ip()
    
    # 1. Recupera as falhas da sessão do navegador (funciona perfeitamente no Vercel)
    tentativas = session.get("failed_attempts", 0)
    bloqueado = tentativas >= MAX_ATTEMPTS

    # 2. Verifica se já está bloqueado ANTES de tentar fazer o login
    if bloqueado and request.method == "GET":
        flash("Acesso bloqueado por segurança. Fale com o líder do seu PGM para recuperar o acesso.", "danger")
        return render_template("auth/login.html", bloqueado=True)

    if request.method == "POST":
        if bloqueado:
            flash("Acesso bloqueado por segurança. Fale com o líder do seu PGM para recuperar o acesso.", "danger")
            return render_template("auth/login.html", bloqueado=True)

        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar_one_or_none()

        if user and user.check_password(password):
            # SUCESSO: Zera as falhas salvas na sessão
            session.pop("failed_attempts", None)
            
            login_user(user, remember=remember)
            audit_log(LogAction.LOGIN_OK,
                      f"{user.name} ({user.email}) fez login",
                      actor=user, ip=ip)
            db.session.commit()

            if password == SENHA_PADRAO:
                session["force_password_change"] = True
                flash("Por segurança, defina uma nova senha antes de continuar.", "warning")
                return redirect(url_for("auth.trocar_senha"))

            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(_dashboard_url())

        # FALHA: Registra o erro na sessão
        tentativas += 1
        session["failed_attempts"] = tentativas
        
        audit_log(LogAction.LOGIN_FAIL,
                  f"Tentativa de login falhou para '{email}'",
                  actor=None, ip=ip)
        db.session.commit()

        # Calcula quantas tentativas restam
        restantes = max(0, MAX_ATTEMPTS - tentativas)
        
        # 3. Exibe a mensagem correta baseada nas tentativas restantes
        if restantes == 0:
            flash("Acesso bloqueado por segurança. Fale com o líder do seu PGM para recuperar o acesso.", "danger")
            return render_template("auth/login.html", bloqueado=True)
        else:
            flash(f"E-mail ou senha incorretos. {restantes} tentativa(s) restante(s).", "danger")

    return render_template("auth/login.html", bloqueado=bloqueado)


@auth_bp.route("/logout")
@login_required
def logout():
    audit_log(LogAction.LOGOUT, f"{current_user.name} saiu do sistema",
              actor=current_user)
    db.session.commit()
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
        audit_log(LogAction.SENHA_TROCADA,
                  f"{current_user.name} alterou a própria senha",
                  actor=current_user)
        db.session.commit()
        session.pop("force_password_change", None)
        flash("Senha alterada com sucesso! 🎉", "success")
        return redirect(_dashboard_url())

    return render_template("auth/trocar_senha.html", force=force)


@auth_bp.route("/redefinir/<token>", methods=["GET", "POST"])
def redefinir_senha(token: str):
    user = db.session.execute(
        db.select(User).where(User.reset_token == token)
    ).scalar_one_or_none()

    if not user or not user.reset_token_valid:
        flash("Este link é inválido ou já expirou. Peça ao seu líder para gerar um novo.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        nova_senha = request.form.get("nova_senha", "")
        confirmar  = request.form.get("confirmar", "")

        if len(nova_senha) < 6:
            flash("A senha deve ter ao menos 6 caracteres.", "danger")
            return render_template("auth/redefinir_senha.html", token=token, user=user)
        if nova_senha != confirmar:
            flash("As senhas não coincidem.", "danger")
            return render_template("auth/redefinir_senha.html", token=token, user=user)
        if nova_senha == SENHA_PADRAO:
            flash("Escolha uma senha diferente da senha padrão.", "danger")
            return render_template("auth/redefinir_senha.html", token=token, user=user)

        user.set_password(nova_senha)
        user.clear_reset_token()
        audit_log(LogAction.SENHA_REDEFINIDA,
                  f"Senha de {user.name} redefinida via link de recuperação",
                  actor=user, ip=_get_ip())
        db.session.commit()
        login_user(user)
        flash(f"Senha redefinida! Bem-vindo(a), {user.name}! 🎉", "success")
        return redirect(_dashboard_url())

    return render_template("auth/redefinir_senha.html", token=token, user=user)


@auth_bp.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    if request.method == "POST":
        name  = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()

        errors = []
        if not name:
            errors.append("Nome é obrigatório.")
        if not email:
            errors.append("E-mail é obrigatório.")

        if email and db.session.execute(
            db.select(User).where(User.email == email, User.id != current_user.id)
        ).scalar_one_or_none():
            errors.append("Este e-mail já está cadastrado para outro usuário.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("auth/perfil.html")

        old_email = current_user.email
        current_user.name  = name
        current_user.email = email
        audit_log(LogAction.PERFIL_EDITADO,
                  f"{name} editou o próprio perfil (email: {old_email} → {email})",
                  actor=current_user)
        db.session.commit()
        flash("Perfil atualizado com sucesso!", "success")
        return redirect(url_for("auth.perfil"))

    return render_template("auth/perfil.html")