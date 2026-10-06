from django.db import models
from app.models import DeviceComplaint, EquipmentPMS, EquipmentBreakdown, DeviceAsset

def admin_nav_counts(request):
    """Provides dynamic live count badges for the unified admin left sidebar across all views."""
    try:
        # Detect technician user
        is_technician = request.session.get('is_technician', False)
        tech_name = request.session.get('technician_name', '')
        
        if not is_technician and hasattr(request, 'user') and request.user.is_authenticated:
            uname = request.user.username.lower()
            if uname == 'sunil':
                is_technician = True
                tech_name = 'Sunil'
            elif uname == 'sahil':
                is_technician = True
                tech_name = 'Sahil'

        if is_technician and tech_name:
            first_name = tech_name.split()[0]
            pending_count = DeviceComplaint.objects.filter(
                models.Q(technician_name__icontains=tech_name) | models.Q(technician_name__icontains=first_name),
                status__in=['Pending', 'In Progress']
            ).count()
            breakdown_count = EquipmentBreakdown.objects.filter(
                models.Q(it_staff_name__icontains=tech_name) | models.Q(it_staff_name__icontains=first_name),
                status__in=['Under Repair', 'Pending Review', 'Pending', 'In Progress']
            ).count()
        else:
            pending_count = DeviceComplaint.objects.filter(status='Pending').count()
            breakdown_count = EquipmentBreakdown.objects.count()

        pms_count = EquipmentPMS.objects.count()
        device_count = DeviceAsset.objects.count()

        # Admin Session details
        admin_name = request.session.get('admin_name')
        admin_initials = request.session.get('admin_initials')
        admin_role = request.session.get('admin_role')
        
        if not admin_name and hasattr(request, 'user') and request.user.is_authenticated:
            admin_name = request.user.get_full_name() or request.user.username
            parts = admin_name.split()
            admin_initials = (parts[0][0] + (parts[1][0] if len(parts) > 1 else '')).upper() if parts else 'AD'
            if is_technician:
                admin_role = 'Field Hardware Technician'
            else:
                admin_role = 'Master Administrator' if request.user.is_superuser else 'IT Systems Lead'

        return {
            'nav_pending_tickets': pending_count,
            'nav_pms_count': pms_count,
            'nav_breakdown_count': breakdown_count,
            'nav_device_count': device_count,
            'current_admin_name': admin_name or 'PSM Administrator',
            'current_admin_initials': admin_initials or 'AD',
            'current_admin_role': admin_role or 'Systems Administrator',
            'is_technician_session': is_technician,
            'is_admin_logged_in': request.session.get('admin_logged_in', False) or (hasattr(request, 'user') and request.user.is_authenticated and request.user.is_staff),
        }
    except Exception:
        return {
            'nav_pending_tickets': 0,
            'nav_pms_count': 0,
            'nav_breakdown_count': 0,
            'nav_device_count': 0,
            'current_admin_name': 'PSM Administrator',
            'current_admin_initials': 'AD',
            'current_admin_role': 'Systems Administrator',
            'is_admin_logged_in': False,
        }
