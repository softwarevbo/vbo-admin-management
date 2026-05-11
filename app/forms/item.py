from flask_wtf import FlaskForm
from wtforms import BooleanField, DecimalField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import NumberRange, Optional, Length


class ItemMasterForm(FlaskForm):
    item_code = StringField("Item code", validators=[Optional(), Length(max=64)])
    item_name = StringField("Item name", validators=[Optional(), Length(max=255)])
    category_id = SelectField("Category", coerce=int, validators=[Optional()])
    description = TextAreaField("Description", validators=[Optional()])
    default_unit = StringField("Unit", validators=[Optional()], default="Nos")
    default_gst_percentage = DecimalField("Default GST %", validators=[Optional()], default=18)
    minimum_stock_alert = DecimalField(
        "Minimum stock alert", validators=[Optional(), NumberRange(min=0)], default=0
    )
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save")


class CategoryForm(FlaskForm):
    name = StringField("Category name", validators=[Optional(), Length(max=120)])
    description = TextAreaField("Description", validators=[Optional()])
    submit = SubmitField("Save")
