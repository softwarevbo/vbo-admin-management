from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/stats/', views.get_stats, name='api_stats'),
    path('api/employees/', views.employee_list, name='api_employees'),
    path('api/employees/<str:pk>/', views.employee_detail, name='api_employee_detail'),
    path('api/vendors/', views.vendor_list, name='api_vendors'),
    path('api/vendors/<int:pk>/', views.vendor_detail, name='api_vendor_detail'),
    path('api/bills/', views.bill_list, name='api_bills'),
    path('api/bills/<int:pk>/', views.bill_detail, name='api_bill_detail'),
    path('api/items/', views.item_list, name='api_items'),
    path('api/items/<int:pk>/', views.item_detail, name='api_item_detail'),
    path('api/logs/', views.log_list, name='api_logs'),
    path('api/stock/', views.stock_summary, name='api_stock'),
]
