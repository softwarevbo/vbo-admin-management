from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    DateField,
    DecimalField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import NumberRange, Optional


class VendorBillForm(FlaskForm):
    vendor_id = SelectField("Vendor", coerce=int, validators=[Optional()])
    vendor_bill_no = StringField("Vendor bill number", validators=[Optional()])
    vendor_bill_date = DateField("Vendor bill date", validators=[Optional()])
    bill_received_date = DateField("Received date", validators=[Optional()])
    division_section = StringField("Division / Section", validators=[Optional()])
    indenter_end_user = StringField("Indenter / End user", validators=[Optional()])
    purchase_order_no = StringField("PO number", validators=[Optional()])
    remarks = TextAreaField("Remarks", validators=[Optional()])
    invoice_file = FileField(
        "Invoice scan (PDF/Image)",
        validators=[Optional(), FileAllowed(["pdf", "png", "jpg", "jpeg"], "Allowed: pdf, png, jpg")],
    )
    submit = SubmitField("Save draft")


class BillLineForm(FlaskForm):
    item_master_id = SelectField("Item", coerce=int, validators=[Optional()])
    description = TextAreaField("Description", validators=[Optional()])
    quantity = DecimalField("Quantity", validators=[Optional(), NumberRange(min=0)])
    unit = StringField("Unit", validators=[Optional()])
    unit_price = DecimalField("Unit price", validators=[Optional(), NumberRange(min=0)])
    discount = DecimalField("Discount (amount)", validators=[Optional()], default=0)
    gst_percentage = DecimalField("GST %", validators=[Optional()], default=18)


class BillWorkflowForm(FlaskForm):
    comments = TextAreaField("Comments", validators=[Optional()])
    submit_review = SubmitField("Submit for review")
    approve = SubmitField("Approve")
    reject = SubmitField("Reject")
    mark_paid = SubmitField("Mark as paid")
    payment_date = DateField("Payment date", validators=[Optional()])


class BillApprovalLevelForm(FlaskForm):
    approval_level_required = IntegerField(
        "Approval levels required", validators=[Optional(), NumberRange(min=1, max=5)]
    )
    submit = SubmitField("Update")
