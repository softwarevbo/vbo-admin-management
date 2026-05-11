from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SubmitField, TextAreaField
from wtforms.validators import Email, Length, Optional, ValidationError

from app.utils.validation import is_valid_gstin, is_valid_ifsc


class VendorForm(FlaskForm):
    vendor_code = StringField("Vendor code", validators=[Optional(), Length(max=32)])
    vendor_name = StringField("Vendor name", validators=[Optional(), Length(max=255)])
    vendor_company_name = StringField("Company name", validators=[Optional(), Length(max=255)])
    contact_person = StringField("Contact person", validators=[Optional(), Length(max=120)])
    mobile_number = StringField("Mobile", validators=[Optional(), Length(max=20)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=120)])
    gstin_number = StringField("GSTIN", validators=[Optional(), Length(max=20)])
    pan_number = StringField("PAN", validators=[Optional(), Length(max=20)])
    address = TextAreaField("Address", validators=[Optional()])
    city = StringField("City", validators=[Optional(), Length(max=80)])
    state = StringField("State", validators=[Optional(), Length(max=80)])
    pincode = StringField("PIN", validators=[Optional(), Length(max=12)])
    country = StringField("Country", validators=[Optional(), Length(max=80)])
    bank_name = StringField("Bank name", validators=[Optional(), Length(max=120)])
    branch_name = StringField("Branch", validators=[Optional(), Length(max=120)])
    account_holder_name = StringField("Account holder", validators=[Optional(), Length(max=120)])
    account_number = StringField("Account number", validators=[Optional(), Length(max=40)])
    ifsc_code = StringField("IFSC", validators=[Optional(), Length(max=20)])
    swift_code = StringField("SWIFT", validators=[Optional(), Length(max=20)])
    account_type = StringField("Account type", validators=[Optional(), Length(max=40)])
    upi_id = StringField("UPI ID", validators=[Optional(), Length(max=80)])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save")

    def validate_gstin_number(self, field):
        if field.data and not is_valid_gstin(field.data):
            raise ValidationError("GSTIN format appears invalid.")

    def validate_ifsc_code(self, field):
        if field.data and not is_valid_ifsc(field.data):
            raise ValidationError("IFSC format appears invalid.")
