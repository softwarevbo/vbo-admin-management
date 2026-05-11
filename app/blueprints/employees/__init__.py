from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.field_definitions import MODULE_EMPLOYEE
from app.constants import ROLE_ADMIN, ROLE_INVENTORY_MANAGER, ROLE_SUPER_ADMIN
from app.extensions import db
from app.forms.employee import EmployeeForm
from app.models.employee import Department, Employee
from app.services import audit_service
from app.services.duplicate_check_service import employee_duplicate_errors
from app.services.field_rules_service import get_field_view, get_rules_for_module
from app.utils.decorators import role_required
from app.utils.dynamic_forms import apply_rules_to_form, validate_submission

bp = Blueprint("employees", __name__)


@bp.before_request
@login_required
def _auth():
    pass


def _can_edit():
    return current_user.role.name in (
        ROLE_SUPER_ADMIN,
        ROLE_ADMIN,
        ROLE_INVENTORY_MANAGER,
    )


@bp.route("/")
def list_employees():
    q = Employee.query.filter(Employee.deleted_at.is_(None)).order_by(Employee.employee_name)
    if request.args.get("dept"):
        q = q.filter(Employee.department.ilike(f"%{request.args.get('dept')}%"))
    if request.args.get("q"):
        like = f"%{request.args.get('q')}%"
        q = q.filter((Employee.employee_name.ilike(like)) | (Employee.employee_code.ilike(like)))
    rows = q.limit(500).all()
    return render_template("employees/list.html", rows=rows, args=request.args, can_edit=_can_edit())


@bp.route("/new", methods=["GET", "POST"])
@role_required(ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_INVENTORY_MANAGER)
def new_employee():
    form = EmployeeForm()
    form.department_id.choices = [(0, "—")] + [
        (d.id, d.name) for d in Department.query.order_by(Department.name).all()
    ]
    rules = get_rules_for_module(MODULE_EMPLOYEE)
    apply_rules_to_form(form, rules)
    for row in get_field_view(MODULE_EMPLOYEE):
        if row.get("label") and hasattr(form, row["key"]):
            getattr(form, row["key"]).label.text = row["label"]
    if validate_submission(
        form,
        MODULE_EMPLOYEE,
        "employee_create",
        duplicate_checker=lambda: employee_duplicate_errors(form, exclude_employee_id=None),
    ):
        e = Employee()
        form.populate_obj(e)
        e.employee_code = form.employee_code.data.strip() if form.employee_code.data else ""
        e.employee_name = form.employee_name.data.strip() if form.employee_name.data else ""
        if form.department_id.data == 0:
            e.department_id = None
        db.session.add(e)
        db.session.commit()
        audit_service.log_action("employee_create", entity_type="employee", entity_id=e.id)
        db.session.commit()
        flash("Employee saved successfully.", "success")
        return redirect(url_for("employees.list_employees"))
    return render_template(
        "employees/form.html",
        form=form,
        employee=None,
        field_rules=rules,
        module=MODULE_EMPLOYEE,
        field_view=get_field_view(MODULE_EMPLOYEE),
    )


@bp.route("/<int:eid>/edit", methods=["GET", "POST"])
def edit_employee(eid):
    if not _can_edit():
        flash("Permission denied.", "danger")
        return redirect(url_for("employees.list_employees"))
    employee = Employee.query.filter_by(id=eid, deleted_at=None).first_or_404()
    form = EmployeeForm(obj=employee)
    form.department_id.choices = [(0, "—")] + [
        (d.id, d.name) for d in Department.query.order_by(Department.name).all()
    ]
    rules = get_rules_for_module(MODULE_EMPLOYEE)
    apply_rules_to_form(form, rules)
    for row in get_field_view(MODULE_EMPLOYEE):
        if row.get("label") and hasattr(form, row["key"]):
            getattr(form, row["key"]).label.text = row["label"]
    if validate_submission(
        form,
        MODULE_EMPLOYEE,
        "employee_update",
        duplicate_checker=lambda: employee_duplicate_errors(
            form, exclude_employee_id=employee.id
        ),
    ):
        form.populate_obj(employee)
        employee.employee_code = (
            form.employee_code.data.strip() if form.employee_code.data else ""
        )
        employee.employee_name = (
            form.employee_name.data.strip() if form.employee_name.data else ""
        )
        if form.department_id.data == 0:
            employee.department_id = None
        db.session.commit()
        flash("Employee updated successfully.", "success")
        return redirect(url_for("employees.list_employees"))
    return render_template(
        "employees/form.html",
        form=form,
        employee=employee,
        field_rules=rules,
        module=MODULE_EMPLOYEE,
        field_view=get_field_view(MODULE_EMPLOYEE),
    )


@bp.route("/<int:eid>/delete", methods=["POST"])
@role_required(ROLE_SUPER_ADMIN, ROLE_ADMIN)
def delete_employee(eid):
    e = Employee.query.get_or_404(eid)
    e.deleted_at = datetime.now(timezone.utc)
    db.session.commit()
    flash("Employee archived.", "info")
    return redirect(url_for("employees.list_employees"))
