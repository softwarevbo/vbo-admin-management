"""Employees and departments."""
from datetime import datetime, timezone

from app.extensions import db


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    division = db.Column(db.String(120))
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    employees = db.relationship("Employee", back_populates="department_rel")


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    employee_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    employee_name = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(120))
    mobile_number = db.Column(db.String(20))
    designation = db.Column(db.String(120))
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    department = db.Column(db.String(120))
    division_section = db.Column(db.String(120))
    office_location = db.Column(db.String(120))
    joining_date = db.Column(db.Date)
    employment_status = db.Column(db.String(40), default="active")
    profile_photo = db.Column(db.String(255))
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(160))
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at = db.Column(db.DateTime)

    department_rel = db.relationship("Department", back_populates="employees")
    issues = db.relationship("ItemIssue", back_populates="employee")
