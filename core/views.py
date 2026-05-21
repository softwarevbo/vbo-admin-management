import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from decimal import Decimal
from datetime import datetime
from .models import Employee, VendorBankAccount, AdminBillInventory, ItemManagement, SystemLog

# Render Main Dashboard Page
def index(request):
    return render(request, 'core/index.html')

# Helper to parse decimal & date fields safely
def parse_decimal(val, default=0.0):
    try:
        return Decimal(str(val))
    except (ValueError, TypeError):
        return Decimal(str(default))

def parse_int(val, default=0):
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

def parse_date(val):
    if not val:
        return None
    try:
        return datetime.strptime(val, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

# API - Stats Summary for Dashboard Charts and Widgets
def get_stats(request):
    total_bills = AdminBillInventory.objects.count()
    total_amount = AdminBillInventory.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_employees = Employee.objects.count()
    total_vendors = VendorBankAccount.objects.count()
    total_items = ItemManagement.objects.count()
    issued_items = ItemManagement.objects.filter(issue_status='ISSUED').count()
    in_stock_items = ItemManagement.objects.filter(issue_status='IN_STOCK').count()

    # Division distribution
    divs = AdminBillInventory.objects.values('div_section').annotate(total=Sum('amount')).order_by('-total')
    division_data = {item['div_section']: float(item['total'] or 0) for item in divs if item['div_section']}

    # Monthly expenditure trend
    monthly_costs = (
        AdminBillInventory.objects
        .annotate(month=TruncMonth('vendor_bill_date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    
    monthly_data = {
        item['month'].strftime("%b %Y") if item['month'] else "Unknown": float(item['total'] or 0)
        for item in monthly_costs
    }

    return JsonResponse({
        'total_bills': total_bills,
        'total_amount': float(total_amount),
        'total_employees': total_employees,
        'total_vendors': total_vendors,
        'total_items': total_items,
        'issued_items': issued_items,
        'in_stock_items': in_stock_items,
        'division_data': division_data,
        'monthly_data': monthly_data
    })


# API - CRUD: Employee
@csrf_exempt
def employee_list(request):
    if request.method == 'GET':
        employees = list(Employee.objects.all().values())
        return JsonResponse(employees, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            emp = Employee.objects.create(
                employee_id=data.get('employee_id'),
                name=data.get('name'),
                email=data.get('email'),
                mobile=data.get('mobile'),
                designation=data.get('designation')
            )
            return JsonResponse({'status': 'success', 'message': 'Employee created', 'id': emp.employee_id}, status=201)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def employee_detail(request, pk):
    try:
        emp = Employee.objects.get(pk=pk)
    except Employee.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Employee not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse({
            'employee_id': emp.employee_id,
            'name': emp.name,
            'email': emp.email,
            'mobile': emp.mobile,
            'designation': emp.designation
        })
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            emp.name = data.get('name', emp.name)
            emp.email = data.get('email', emp.email)
            emp.mobile = data.get('mobile', emp.mobile)
            emp.designation = data.get('designation', emp.designation)
            emp.save()
            return JsonResponse({'status': 'success', 'message': 'Employee updated'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    elif request.method == 'DELETE':
        emp.delete()
        return JsonResponse({'status': 'success', 'message': 'Employee deleted'})


# API - CRUD: VendorBankAccount
@csrf_exempt
def vendor_list(request):
    if request.method == 'GET':
        vendors = list(VendorBankAccount.objects.all().values())
        return JsonResponse(vendors, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            vendor = VendorBankAccount.objects.create(
                vendor_name=data.get('vendor_name'),
                bank_name=data.get('bank_name'),
                account_number=data.get('account_number'),
                branch=data.get('branch'),
                ifsc_code=data.get('ifsc_code')
            )
            return JsonResponse({'status': 'success', 'message': 'Vendor details created', 'id': vendor.id}, status=201)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def vendor_detail(request, pk):
    try:
        vendor = VendorBankAccount.objects.get(pk=pk)
    except VendorBankAccount.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Vendor not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse({
            'id': vendor.id,
            'vendor_name': vendor.vendor_name,
            'bank_name': vendor.bank_name,
            'account_number': vendor.account_number,
            'branch': vendor.branch,
            'ifsc_code': vendor.ifsc_code
        })
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            vendor.vendor_name = data.get('vendor_name', vendor.vendor_name)
            vendor.bank_name = data.get('bank_name', vendor.bank_name)
            vendor.account_number = data.get('account_number', vendor.account_number)
            vendor.branch = data.get('branch', vendor.branch)
            vendor.ifsc_code = data.get('ifsc_code', vendor.ifsc_code)
            vendor.save()
            return JsonResponse({'status': 'success', 'message': 'Vendor details updated'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    elif request.method == 'DELETE':
        vendor.delete()
        return JsonResponse({'status': 'success', 'message': 'Vendor deleted'})


# API - CRUD: AdminBillInventory
@csrf_exempt
def bill_list(request):
    if request.method == 'GET':
        bills = []
        for bill in AdminBillInventory.objects.all().select_related('vendor'):
            bills.append({
                'sl_no': bill.sl_no,
                'vendor_id': bill.vendor.id,
                'vendor_name': bill.vendor.vendor_name,
                'vendor_bill_no': bill.vendor_bill_no,
                'vendor_bill_date': bill.vendor_bill_date.isoformat(),
                'amount': float(bill.amount),
                'div_section': bill.div_section,
                'indent_end_user': bill.indent_end_user,
                'received_date': bill.received_date.isoformat(),
                'bill_received_date': bill.bill_received_date.isoformat(),
                'processed_date': bill.processed_date.isoformat() if bill.processed_date else None,
            })
        return JsonResponse(bills, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            vendor_id = data.get('vendor_id')
            vendor = VendorBankAccount.objects.get(pk=vendor_id)
            
            bill = AdminBillInventory.objects.create(
                vendor=vendor,
                vendor_bill_no=data.get('vendor_bill_no'),
                vendor_bill_date=parse_date(data.get('vendor_bill_date')),
                div_section=data.get('div_section'),
                indent_end_user=data.get('indent_end_user'),
                received_date=parse_date(data.get('received_date')),
                bill_received_date=parse_date(data.get('bill_received_date')),
                processed_date=parse_date(data.get('processed_date')),
                amount=Decimal('0.00')  # initially 0, updated by items
            )
            return JsonResponse({'status': 'success', 'message': 'Bill created', 'sl_no': bill.sl_no}, status=201)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def bill_detail(request, pk):
    try:
        bill = AdminBillInventory.objects.get(pk=pk)
    except AdminBillInventory.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Bill not found'}, status=404)

    if request.method == 'GET':
        items = list(bill.items.values(
            'id', 'name', 'description', 'quantity', 'gst', 'unit_price', 'amount', 
            'employee_id', 'employee__name', 'issue_status', 'issue_date'
        ))
        return JsonResponse({
            'sl_no': bill.sl_no,
            'vendor_id': bill.vendor.id,
            'vendor_name': bill.vendor.vendor_name,
            'vendor_bill_no': bill.vendor_bill_no,
            'vendor_bill_date': bill.vendor_bill_date.isoformat(),
            'amount': float(bill.amount),
            'div_section': bill.div_section,
            'indent_end_user': bill.indent_end_user,
            'received_date': bill.received_date.isoformat(),
            'bill_received_date': bill.bill_received_date.isoformat(),
            'processed_date': bill.processed_date.isoformat() if bill.processed_date else None,
            'items': items
        })
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            if 'vendor_id' in data:
                bill.vendor = VendorBankAccount.objects.get(pk=data['vendor_id'])
            bill.vendor_bill_no = data.get('vendor_bill_no', bill.vendor_bill_no)
            bill.vendor_bill_date = parse_date(data.get('vendor_bill_date')) or bill.vendor_bill_date
            bill.div_section = data.get('div_section', bill.div_section)
            bill.indent_end_user = data.get('indent_end_user', bill.indent_end_user)
            bill.received_date = parse_date(data.get('received_date')) or bill.received_date
            bill.bill_received_date = parse_date(data.get('bill_received_date')) or bill.bill_received_date
            bill.processed_date = parse_date(data.get('processed_date')) if 'processed_date' in data else bill.processed_date
            bill.save()
            bill.recalculate_total()
            return JsonResponse({'status': 'success', 'message': 'Bill updated'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    elif request.method == 'DELETE':
        bill.delete()
        return JsonResponse({'status': 'success', 'message': 'Bill deleted'})


# API - CRUD: ItemManagement
@csrf_exempt
def item_list(request):
    if request.method == 'GET':
        items = []
        for item in ItemManagement.objects.all().select_related('bill', 'employee'):
            items.append({
                'id': item.id,
                'bill_id': item.bill.sl_no,
                'bill_no': item.bill.vendor_bill_no,
                'name': item.name,
                'description': item.description,
                'quantity': item.quantity,
                'gst': float(item.gst),
                'unit_price': float(item.unit_price),
                'amount': float(item.amount),
                'employee_id': item.employee.employee_id if item.employee else None,
                'employee_name': item.employee.name if item.employee else None,
                'issue_status': item.issue_status,
                'issue_date': item.issue_date.isoformat() if item.issue_date else None,
            })
        return JsonResponse(items, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            bill_id = data.get('bill_id')
            bill = AdminBillInventory.objects.get(pk=bill_id)
            
            emp_id = data.get('employee_id')
            employee = None
            if emp_id:
                employee = Employee.objects.get(pk=emp_id)

            item = ItemManagement.objects.create(
                bill=bill,
                name=data.get('name'),
                description=data.get('description', ''),
                quantity=parse_int(data.get('quantity'), 1),
                gst=parse_decimal(data.get('gst'), 18.00),
                unit_price=parse_decimal(data.get('unit_price'), 0.0),
                employee=employee,
                issue_status=data.get('issue_status', 'IN_STOCK'),
                issue_date=parse_date(data.get('issue_date'))
            )
            return JsonResponse({'status': 'success', 'message': 'Item added to bill', 'id': item.id}, status=201)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def item_detail(request, pk):
    try:
        item = ItemManagement.objects.get(pk=pk)
    except ItemManagement.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse({
            'id': item.id,
            'bill_id': item.bill.sl_no,
            'name': item.name,
            'description': item.description,
            'quantity': item.quantity,
            'gst': float(item.gst),
            'unit_price': float(item.unit_price),
            'amount': float(item.amount),
            'employee_id': item.employee.employee_id if item.employee else None,
            'issue_status': item.issue_status,
            'issue_date': item.issue_date.isoformat() if item.issue_date else None,
        })
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            if 'bill_id' in data:
                item.bill = AdminBillInventory.objects.get(pk=data['bill_id'])
            
            item.name = data.get('name', item.name)
            item.description = data.get('description', item.description)
            item.quantity = parse_int(data.get('quantity'), item.quantity)
            item.gst = parse_decimal(data.get('gst'), item.gst)
            item.unit_price = parse_decimal(data.get('unit_price'), item.unit_price)
            
            # Issue updates
            if 'employee_id' in data:
                emp_id = data['employee_id']
                item.employee = Employee.objects.get(pk=emp_id) if emp_id else None
            
            item.issue_status = data.get('issue_status', item.issue_status)
            item.issue_date = parse_date(data.get('issue_date')) if 'issue_date' in data else item.issue_date
            
            item.save()
            return JsonResponse({'status': 'success', 'message': 'Item updated'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    elif request.method == 'DELETE':
        item.delete()
        return JsonResponse({'status': 'success', 'message': 'Item deleted'})


# API - System Logs View
def log_list(request):
    logs = []
    # get 100 latest logs
    for log in SystemLog.objects.all().order_by('-timestamp')[:100]:
        logs.append({
            'id': log.id,
            'timestamp': log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            'user': log.user,
            'action': log.action,
            'model_name': log.model_name,
            'record_id': log.record_id,
            'record_name': log.record_name,
            'changed_fields': log.changed_fields
        })
    return JsonResponse(logs, safe=False)


# API - Grouped Stock Inventory Summary
def stock_summary(request):
    from django.db.models import Q
    stock_data = (
        ItemManagement.objects.values('name')
        .annotate(
            total_purchased=Sum('quantity'),
            total_issued=Sum('quantity', filter=Q(issue_status='ISSUED')),
            total_in_stock=Sum('quantity', filter=Q(issue_status='IN_STOCK')),
            total_value=Sum('amount', filter=Q(issue_status='IN_STOCK'))
        )
        .order_by('name')
    )
    
    summary = []
    for item in stock_data:
        summary.append({
            'name': item['name'],
            'total_purchased': item['total_purchased'] or 0,
            'total_issued': item['total_issued'] or 0,
            'total_in_stock': item['total_in_stock'] or 0,
            'total_value': float(item['total_value'] or 0.0)
        })
        
    return JsonResponse(summary, safe=False)
