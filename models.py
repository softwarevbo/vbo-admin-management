from django.db import models
from django.db.models import Sum
from decimal import Decimal

class Employee(models.Model):
    employee_id = models.CharField(max_length=50, primary_key=True, help_text="Unique Employee ID")
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15)
    designation = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.employee_id})"

class VendorBankAccount(models.Model):
    vendor_name = models.CharField(max_length=150, unique=True)
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    branch = models.CharField(max_length=100)
    ifsc_code = models.CharField(max_length=20)
    
    # Optional Contact and Information fields
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.vendor_name} - {self.bank_name} ({self.account_number[-4:] if len(self.account_number) > 4 else self.account_number})"

class AdminBillInventory(models.Model):
    sl_no = models.AutoField(primary_key=True)
    vendor = models.ForeignKey(VendorBankAccount, on_delete=models.CASCADE, related_name="bills")
    vendor_bill_no = models.CharField(max_length=100)
    vendor_bill_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Total sum of all items (auto-calculated if items exist, or manually entered)")
    div_section = models.CharField(max_length=100, help_text="Division or Section")
    indent_end_user = models.CharField(max_length=100, help_text="Indent End User")
    received_date = models.DateField()
    bill_received_date = models.DateField()
    processed_date = models.DateField(null=True, blank=True)

    def recalculate_total(self):
        # Calculate sum of all associated item amounts if items exist
        if self.items.exists():
            total = self.items.aggregate(total_sum=Sum('amount'))['total_sum'] or Decimal('0.00')
            if self.amount != total:
                self.amount = total
                # Use save(update_fields=...) or standard save to avoid infinite recursion if signals are used
                AdminBillInventory.objects.filter(pk=self.pk).update(amount=total)
            return total
        return self.amount

    def __str__(self):
        return f"Bill {self.vendor_bill_no} ({self.vendor.vendor_name})"

class ItemManagement(models.Model):
    STATUS_CHOICES = [
        ('IN_STOCK', 'In Stock'),
        ('ISSUED', 'Issued'),
    ]

    bill = models.ForeignKey(AdminBillInventory, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1)
    gst = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('18.00'), help_text="GST percentage")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    
    # Issue details
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name="issued_items")
    issue_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_STOCK')
    issue_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Calculation: amount = quantity * unit_price * (1 + gst / 100)
        subtotal = Decimal(str(self.quantity)) * self.unit_price
        gst_amount = subtotal * (self.gst / Decimal('100.00'))
        self.amount = subtotal + gst_amount
        
        super().save(*args, **kwargs)
        
        # Trigger bill total recalculation
        if self.bill:
            self.bill.recalculate_total()

    def delete(self, *args, **kwargs):
        bill = self.bill
        super().delete(*args, **kwargs)
        if bill:
            bill.recalculate_total()

    def __str__(self):
        return f"{self.name} ({self.quantity} x {self.unit_price})"

class SystemLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ]

    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.CharField(max_length=150, default="System")
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100)
    record_name = models.CharField(max_length=255)
    changed_fields = models.TextField(blank=True, help_text="JSON list of changes")

    def __str__(self):
        return f"{self.timestamp} - {self.action} on {self.model_name} (ID: {self.record_id})"
