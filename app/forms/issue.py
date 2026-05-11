from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, SubmitField, TextAreaField
from wtforms.validators import Optional


class ItemIssueForm(FlaskForm):
    employee_id = SelectField("Employee", coerce=int, validators=[Optional()])
    issue_date = DateField("Issue date", validators=[Optional()])
    remarks = TextAreaField("Remarks", validators=[Optional()])
    submit = SubmitField("Issue items")


class ItemReturnForm(FlaskForm):
    submit = SubmitField("Process return")
