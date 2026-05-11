from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import Email, Optional, Length


class EmployeeForm(FlaskForm):
    employee_code = StringField("Employee code", validators=[Optional(), Length(max=32)])
    employee_name = StringField("Name", validators=[Optional(), Length(max=160)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=120)])
    mobile_number = StringField("Mobile", validators=[Optional(), Length(max=20)])
    designation = StringField("Designation", validators=[Optional(), Length(max=120)])
    department_id = SelectField("Department", coerce=int, validators=[Optional()])
    department = StringField("Department (text)", validators=[Optional(), Length(max=120)])
    division_section = StringField("Division / Section", validators=[Optional(), Length(max=120)])
    office_location = StringField("Office location", validators=[Optional(), Length(max=120)])
    joining_date = DateField("Joining date", validators=[Optional()])
    employment_status = SelectField(
        "Status",
        choices=[("active", "Active"), ("inactive", "Inactive")],
        validators=[Optional()],
    )
    address = TextAreaField("Address", validators=[Optional()])
    emergency_contact = StringField("Emergency contact", validators=[Optional(), Length(max=160)])
    submit = SubmitField("Save")
