import json
from django.test import TestCase
from decimal import Decimal
from datetime import date
from .models import Employee, VendorBankAccount, AdminBillInventory, ItemManagement, SystemLog

class AdminManagementSystemTests(TestCase):
    
    def setUp(self):
        # Create standard employee
        self.employee = Employee.objects.create(
            employee_id="EMP101",
            name="Kei",
            email="kei@company.com",
            mobile="9876543210",
            designation="System Admin"
        )
        # Create standard vendor bank account
        self.vendor = VendorBankAccount.objects.create(
            vendor_name="Global Vendor Ltd",
            bank_name="Test Bank",
            account_number="123456789",
            branch="City Branch",
            ifsc_code="TEST000123"
        )
        # Create standard bill
        self.bill = AdminBillInventory.objects.create(
            vendor=self.vendor,
            vendor_bill_no="INV-001",
            vendor_bill_date=date(2026, 5, 21),
            div_section="IT division",
            indent_end_user="Technical Office",
            received_date=date(2026, 5, 21),
            bill_received_date=date(2026, 5, 21)
        )

    def test_item_amount_calculation(self):
        """Test that item amount is calculated as qty * unit_price + GST correctly"""
        item = ItemManagement.objects.create(
            bill=self.bill,
            name="Monitor",
            quantity=2,
            unit_price=Decimal("10000.00"),
            gst=Decimal("18.00") # 18% GST
        )
        # Expected total: 2 * 10000 * 1.18 = 23600.00
        self.assertEqual(item.amount, Decimal("23600.00"))

    def test_bill_recalculate_total(self):
        """Test that adding/updating/deleting items automatically updates the bill total"""
        # Initially amount is 0.00
        self.assertEqual(self.bill.amount, Decimal("0.00"))
        
        # Add item 1
        item1 = ItemManagement.objects.create(
            bill=self.bill,
            name="Mouse",
            quantity=5,
            unit_price=Decimal("100.00"),
            gst=Decimal("12.00") # 12% GST
        )
        # Expected: 5 * 100 * 1.12 = 560.00
        self.bill.refresh_from_db()
        self.assertEqual(self.bill.amount, Decimal("560.00"))
        
        # Add item 2
        item2 = ItemManagement.objects.create(
            bill=self.bill,
            name="Keyboard",
            quantity=2,
            unit_price=Decimal("200.00"),
            gst=Decimal("5.00") # 5% GST
        )
        # Expected: 2 * 200 * 1.05 = 420.00
        # Total bill expected: 560 + 420 = 980.00
        self.bill.refresh_from_db()
        self.assertEqual(self.bill.amount, Decimal("980.00"))

        # Update item 1 quantity
        item1.quantity = 10
        item1.save()
        # Expected: 10 * 100 * 1.12 = 1120.00
        # Total bill expected: 1120 + 420 = 1540.00
        self.bill.refresh_from_db()
        self.assertEqual(self.bill.amount, Decimal("1540.00"))

        # Delete item 2
        item2.delete()
        # Total bill expected: 1120.00
        self.bill.refresh_from_db()
        self.assertEqual(self.bill.amount, Decimal("1120.00"))

    def test_system_log_signals(self):
        """Test that database modifications create audit entries in SystemLog"""
        # Clear existing logs created during setUp
        SystemLog.objects.all().delete()
        
        # Create a new Employee and check create log
        emp = Employee.objects.create(
            employee_id="EMP999",
            name="New Employee",
            email="new@company.com",
            mobile="1111122222",
            designation="Intern"
        )
        create_log = SystemLog.objects.filter(model_name="Employee", action="CREATE", record_id="EMP999").first()
        self.assertIsNotNone(create_log)
        changes = json.loads(create_log.changed_fields)
        self.assertEqual(changes["name"]["new"], "New Employee")
        self.assertEqual(changes["designation"]["new"], "Intern")

        # Update the Employee and check update log
        emp.designation = "Associate"
        emp.save()
        update_log = SystemLog.objects.filter(model_name="Employee", action="UPDATE", record_id="EMP999").first()
        self.assertIsNotNone(update_log)
        changes = json.loads(update_log.changed_fields)
        self.assertEqual(changes["designation"]["old"], "Intern")
        self.assertEqual(changes["designation"]["new"], "Associate")

        # Delete Employee and check delete log
        emp.delete()
        delete_log = SystemLog.objects.filter(model_name="Employee", action="DELETE", record_id="EMP999").first()
        self.assertIsNotNone(delete_log)
        changes = json.loads(delete_log.changed_fields)
        self.assertEqual(changes["name"]["old"], "New Employee")

    def test_stock_summary_api(self):
        """Test the stock summary API aggregates quantities and stock values properly"""
        # Create stock items
        ItemManagement.objects.create(
            bill=self.bill, name="Chair", quantity=10, unit_price=Decimal("1000.00"), gst=Decimal("18.00"),
            issue_status="IN_STOCK"
        )
        ItemManagement.objects.create(
            bill=self.bill, name="Chair", quantity=5, unit_price=Decimal("1000.00"), gst=Decimal("18.00"),
            issue_status="ISSUED", employee=self.employee, issue_date=date(2026, 5, 21)
        )
        
        response = self.client.get('/api/stock/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify Chair results
        chair_info = next((item for item in data if item['name'] == 'Chair'), None)
        self.assertIsNotNone(chair_info)
        self.assertEqual(chair_info['total_purchased'], 15)
        self.assertEqual(chair_info['total_issued'], 5)
        self.assertEqual(chair_info['total_in_stock'], 10)
        # 10 in stock * 1000 * 1.18 = 11800.00
        self.assertEqual(chair_info['total_value'], 11800.00)

