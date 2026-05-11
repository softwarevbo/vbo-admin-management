from datetime import datetime, timedelta, timezone

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user

from app.extensions import db
from app.forms.auth import ForgotPasswordForm, LoginForm, ResetPasswordForm
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.services import audit_service
from app.utils.security import generate_token, hash_token

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user and user.is_active and user.check_password(form.password.data):
            session.permanent = True
            login_user(user, remember=form.remember.data)
            user.last_login_at = datetime.now(timezone.utc)
            audit_service.log_action("login", entity_type="user", entity_id=user.id)
            db.session.commit()
            next_url = request.args.get("next") or url_for("main.dashboard")
            return redirect(next_url)
        flash("Invalid username or password.", "danger")
    return render_template("auth/login.html", form=form)


@bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        audit_service.log_action("logout", entity_type="user", entity_id=current_user.id)
        db.session.commit()
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@bp.route("/forgot", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user:
            raw = generate_token()
            row = PasswordResetToken(
                user_id=user.id,
                token_hash=hash_token(raw),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
            )
            db.session.add(row)
            db.session.commit()
            link = url_for("auth.reset_password", token=raw, _external=True)
            flash(
                f"If the account exists, a reset link was generated. "
                f"Development link: {link}",
                "warning",
            )
        else:
            flash("If the account exists, you will receive reset instructions.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot.html", form=form)


@bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    form = ResetPasswordForm()
    th = hash_token(token)
    row = PasswordResetToken.query.filter_by(token_hash=th).first()
    if (
        not row
        or row.used_at
        or row.expires_at < datetime.now(timezone.utc)
    ):
        flash("Invalid or expired reset link.", "danger")
        return redirect(url_for("auth.login"))
    if form.validate_on_submit():
        user = User.query.get(row.user_id)
        user.set_password(form.password.data)
        row.used_at = datetime.now(timezone.utc)
        db.session.commit()
        flash("Password updated. Please sign in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset.html", form=form)
