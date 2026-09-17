from django.contrib import admin
from .models import UserProfile, DeviceComplaint, DeviceAsset, CustodyTransferLog, EquipmentPMS, EquipmentBreakdown


@admin.register(EquipmentBreakdown)
class EquipmentBreakdownAdmin(admin.ModelAdmin):
    list_display = ('id', 'breakdown_date', 'asset_id', 'device_name', 'equipment_type', 'breakdown_cause', 'tat_duration', 'status')
    search_fields = ('asset_id', 'device_name', 'breakdown_cause', 'dept_hod_name', 'it_staff_name')
    list_filter = ('equipment_type', 'device_name', 'status')


@admin.register(EquipmentPMS)
class EquipmentPMSAdmin(admin.ModelAdmin):
    list_display = ('asset_code', 'equipment_name', 'company_name', 'maintenance_frequency', 'pms1_done_date', 'pms4_due_date', 'status')
    search_fields = ('asset_code', 'equipment_name', 'company_name', 'department_location')
    list_filter = ('maintenance_frequency', 'company_name', 'status')


@admin.register(DeviceAsset)
class DeviceAssetAdmin(admin.ModelAdmin):
    list_display = ('asset_id', 'device_type', 'org_id', 'room_name', 'assigned_user_name', 'status', 'ip_address')
    search_fields = ('asset_id', 'device_type', 'assigned_user_name', 'room_name', 'serial_number')
    list_filter = ('device_type', 'org_id', 'status', 'building_name')


@admin.register(CustodyTransferLog)
class CustodyTransferLogAdmin(admin.ModelAdmin):
    list_display = ('device_asset_id', 'from_user_name', 'to_user_name', 'handover_date', 'assigned_by')
    search_fields = ('device_asset_id', 'from_user_name', 'to_user_name')
    list_filter = ('handover_date',)


@admin.register(DeviceComplaint)
class DeviceComplaintAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'device_asset_id', 'user_full_name', 'issue_category', 'priority', 'status', 'created_at')
    search_fields = ('ticket_id', 'device_asset_id', 'user_full_name', 'subject')
    list_filter = ('status', 'priority', 'org_id', 'issue_category')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('emp_id', 'full_name', 'password', 'org_id', 'department', 'assigned_asset_id')
    search_fields = ('emp_id', 'full_name', 'department', 'assigned_asset_id')
    list_filter = ('org_id', 'department')
