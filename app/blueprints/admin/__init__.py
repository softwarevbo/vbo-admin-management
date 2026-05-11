from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.field_definitions import ALL_MODULES, FIELD_REGISTRY, MODULE_LABELS
from app.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN
from app.extensions import db
from app.models.audit import AuditLog
from app.models.form_field_rule import ValidationLog
from app.models.user import Role, User
from app.services import audit_service
from app.services.field_rules_service import get_field_view, get_rules_for_module, save_rules_from_form
from app.utils.decorators import role_required
from wtforms import PasswordField, SelectField, StringField, SubmitField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, Length, Optional


class UserAdminForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    role_id = SelectField("Role", coerce=int, validators=[DataRequired()])
    password = PasswordField("Password", validators=[Optional(), Length(min=8)])
    submit = SubmitField("Save user")


bp = Blueprint("admin", __name__)


@bp.before_request
@login_required
def _auth():
    pass


@bp.route("/users")
@role_required(ROLE_SUPER_ADMIN, ROLE_ADMIN)
def users():
    rows = User.query.filter(User.deleted_at.is_(None)).order_by(User.username).all()
    return render_template("admin/users.html", rows=rows)


@bp.route("/users/new", methods=["GET", "POST"])
@role_required(ROLE_SUPER_ADMIN, ROLE_ADMIN)
def new_user():
    form = UserAdminForm()
    form.role_id.choices = [(r.id, r.name) for r in Role.query.order_by(Role.name).all()]
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data.strip()).first():
            flash("Username exists.", "danger")
        else:
            u = User(
                username=form.username.data.strip(),
                email=form.email.data.strip().lower(),
                full_name=form.full_name.data.strip(),
                role_id=form.role_id.data,
                is_active=True,
            )
            pwd = form.password.data or "ChangeMe123!"
            u.set_password(pwd)
            db.session.add(u)
            db.session.commit()
            audit_service.log_action("user_create", entity_type="user", entity_id=u.id)
            db.session.commit()
            flash("User created.", "success")
            return redirect(url_for("admin.users"))
    return render_template("admin/user_form.html", form=form)


@bp.route("/audit")
@role_required(ROLE_SUPER_ADMIN, ROLE_ADMIN)
def audit():
    q = AuditLog.query.order_by(AuditLog.created_at.desc())
    if request.args.get("user_id"):
        q = q.filter(AuditLog.user_id == int(request.args.get("user_id")))
    rows = q.limit(500).all()
    return render_template("admin/audit.html", rows=rows, args=request.args)


@bp.route("/field-settings", methods=["GET", "POST"])
@role_required(ROLE_SUPER_ADMIN, ROLE_ADMIN)
def field_settings():
    if request.method == "POST":
        module = request.form.get("module", "").strip()
        if module in ALL_MODULES:
            save_rules_from_form(module, request.form)
            flash(f"Mandatory / uniqueness rules saved for “{MODULE_LABELS.get(module, module)}”.", "success")
        return redirect(url_for("admin.field_settings", module=module or None))
    active = request.args.get("module") or ALL_MODULES[0]
    if active not in ALL_MODULES:
        active = ALL_MODULES[0]
    tables = {}
    for mod in ALL_MODULES:
        rules = get_rules_for_module(mod)
        tables[mod] = []
        for fm in FIELD_REGISTRY.get(mod, []):
            key = fm["key"]
            tables[mod].append(
                {
                    "key": key,
                    "label": fm["label"],
                    "label_override": rules.get(key, {}).get("label"),
                    "order": rules.get(key, {}).get("order", 0),
                    "visible": rules.get(key, {}).get("visible", True),
                    "required": rules.get(key, {}).get("required", False),
                    "unique": rules.get(key, {}).get("unique", False),
                }
            )
    return render_template(
        "admin/field_settings.html",
        all_modules=ALL_MODULES,
        module_labels=MODULE_LABELS,
        active_module=active,
        tables=tables,
    )


@bp.route("/validation-logs")
@role_required(ROLE_SUPER_ADMIN, ROLE_ADMIN)
def validation_logs():
    q = ValidationLog.query.order_by(ValidationLog.created_at.desc())
    if request.args.get("module"):
        q = q.filter(ValidationLog.module == request.args.get("module"))
    rows = q.limit(500).all()
    return render_template(
        "admin/validation_logs.html",
        rows=rows,
        modules=ALL_MODULES,
        args=request.args,
    )
