from app.models import DeviceComplaint, EquipmentPMS, EquipmentBreakdown, DeviceAsset

def admin_nav_counts(request):
    """Provides dynamic live count badges for the unified admin left sidebar across all views."""
    try:
        pending_count = DeviceComplaint.objects.filter(status='Pending').count()
        pms_count = EquipmentPMS.objects.count()
        breakdown_count = EquipmentBreakdown.objects.count()
        device_count = DeviceAsset.objects.count()
        # Admin Session details
        admin_name = request.session.get('admin_name')
        admin_initials = request.session.get('admin_initials')
        admin_role = request.session.get('admin_role')
        
        if not admin_name and hasattr(request, 'user') and request.user.is_authenticated:
            admin_name = request.user.get_full_name() or request.user.username
            parts = admin_name.split()
            admin_initials = (parts[0][0] + (parts[1][0] if len(parts) > 1 else '')).upper() if parts else 'AD'
            admin_role = 'Master Administrator' if request.user.is_superuser else 'IT Systems Lead'

        return {
            'nav_pending_tickets': pending_count,
            'nav_pms_count': pms_count,
            'nav_breakdown_count': breakdown_count,
            'nav_device_count': device_count,
            'current_admin_name': admin_name or 'PSM Administrator',
            'current_admin_initials': admin_initials or 'AD',
            'current_admin_role': admin_role or 'Systems Administrator',
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
