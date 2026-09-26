"""
URL configuration for tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from app import views

urlpatterns = [
    path('favicon.ico', lambda request: HttpResponse(b"", content_type="image/x-icon")),
    path('admin/', admin.site.urls),
    
    # Landing Portal Gateway (Swaminarayan University vs PSM Hospital)
    path('', views.index, name='index'),
    path('admin-portal/', views.index, name='admin_portal'),

    # Admin Authentication Routes (IT Systems, Hardware Managers, Superusers)
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('admin-signup/', views.admin_signup_view, name='admin_signup'),
    path('admin-logout/', views.admin_logout_view, name='admin_logout'),

    # User Portal Routes (Employee Entry, Auth, Dashboard, Complaint Service)
    path('portal/entry/', views.user_portal_root, name='user_portal_root'),
    path('portal/', views.user_dashboard, name='user_dashboard'),
    path('portal/login/', views.user_login_view, name='user_login'),
    path('portal/signup/', views.user_signup_view, name='user_signup'),
    path('portal/logout/', views.user_logout_view, name='user_logout'),
    path('portal/complaint/submit/', views.submit_complaint, name='submit_complaint'),

    # Mobile QR Quick Complaint Routes (Hospital Staff Direct Device Reporting)
    path('report/', views.mobile_report_view, name='mobile_report'),
    path('report/<path:asset_id>/', views.mobile_report_view, name='mobile_report_asset'),
    path('qr/<path:asset_id>/', views.mobile_report_view, name='qr_report_asset'),
    path('scan/', views.mobile_report_view, name='mobile_scan'),
    path('scan/<path:asset_id>/', views.mobile_report_view, name='mobile_scan_asset'),
    path('api/complaint/quick-submit/', views.api_submit_quick_complaint, name='api_submit_quick_complaint'),

    # Admin Portal & Helpdesk Routes
    path('admin-complaints/', views.admin_complaints, name='admin_complaints'),
    path('admin-complaints/update/<str:ticket_id>/', views.admin_update_complaint, name='admin_update_complaint'),

    # Existing Admin Hardware Lifecycle Routes
    path('inventory/', views.inventory, name='inventory'),
    path('inventory/add/', views.mobile_add_device_view, name='mobile_add_device'),
    path('api/devices/quick-generate-id/', views.api_generate_asset_id, name='api_generate_asset_id'),
    path('api/devices/check-asset-id/', views.api_check_asset_id, name='api_check_asset_id'),
    path('user/', views.user, name='user'),
    path('location/', views.location, name='location'),
    path('audit/', views.audit, name='audit'),
    path('tag/', views.tag, name='tag'),

    # Preventive Maintenance Service (PMS) Schedule
    path('pms-schedule/', views.pms_schedule, name='pms_schedule'),
    path('api/pms/update/<int:pms_id>/', views.api_update_pms, name='api_update_pms'),
    path('api/pms/add/', views.api_add_pms, name='api_add_pms'),
    path('api/pms/delete/<int:pms_id>/', views.api_delete_pms, name='api_delete_pms'),
    path('api/pms/import-excel/', views.api_import_pms_excel, name='api_import_pms_excel'),

    # Equipment Breakdown Register
    path('breakdown-register/', views.equipment_breakdown, name='equipment_breakdown'),
    path('api/breakdown/add/', views.api_add_breakdown, name='api_add_breakdown'),
    path('api/breakdown/resolve/<int:pk>/', views.api_resolve_breakdown, name='api_resolve_breakdown'),
    path('api/breakdown/update/<int:pk>/', views.api_update_breakdown, name='api_update_breakdown'),
    path('api/breakdown/delete/<int:pk>/', views.api_delete_breakdown, name='api_delete_breakdown'),
    path('api/breakdown/import-excel/', views.api_import_breakdown_excel, name='api_import_breakdown_excel'),

    # Central Database Synchronization & Admin Maintenance APIs
    path('api/devices/', views.api_get_devices, name='api_get_devices'),
    path('api/devices/import-excel/', views.api_import_devices_excel, name='api_import_devices_excel'),
    path('api/devices/reassign/', views.api_reassign_device, name='api_reassign_device'),
    path('api/devices/save/', views.api_save_device, name='api_save_device'),
    path('api/audit-logs/', views.api_get_audit_logs, name='api_get_audit_logs'),
]

