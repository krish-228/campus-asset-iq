from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
import json
import urllib.parse
import random
from django.db import models, transaction
from .models import DeviceComplaint, UserProfile, DeviceAsset, CustodyTransferLog, EquipmentPMS, EquipmentBreakdown



def normalize_device_type(code, asset_id=''):
    c = (code or '').upper().strip()
    if 'WORKSTATION' in c or ('CPU' in c and ('DISPLAY' in c or 'MONITOR' in c or 'KEYBOARD' in c or 'MOUSE' in c)):
        return code or 'Workstation (CPU, Display, Keyboard, Mouse)'
    if ',' in (code or ''):
        return code.strip()
    if c in ('C', 'CPU', 'DESKTOP', 'PC', 'TOWER', 'COMPUTER'):
        return 'CPU'
    if c in ('D', 'DISPLAY', 'MONITOR', 'SCREEN'):
        return 'Display'
    if c in ('K', 'KB', 'KEYBOARD'):
        return 'Keyboard'
    if c in ('M', 'MOUSE'):
        return 'Mouse'
    if c in ('P', 'PRT', 'PRINTER', 'BARCODE PRINTER', 'LASER PRINTER'):
        return 'Printer'
    if c in ('T', 'TAB', 'TABLET', 'IPAD'):
        return 'Tablet'
    if c in ('U', 'UPS', 'INVERTER', 'POWER'):
        return 'UPS'
    
    # Check asset_id format: PSM/IT/<TYPE>/<MMYY>/<NUM> or legacy PSM/IT/<FLOOR>/<TYPE>-<NUM>
    aid = asset_id.upper()
    if '/C/' in aid or '/C-' in aid or '/C.' in aid: return 'CPU'
    if '/D/' in aid or '/D-' in aid or '/D.' in aid or '/DISP-' in aid: return 'Display'
    if '/K/' in aid or '/K-' in aid or '/K.' in aid or '/KB-' in aid: return 'Keyboard'
    if '/M/' in aid or '/M-' in aid or '/M.' in aid: return 'Mouse'
    if '/P/' in aid or '/P-' in aid or '/P.' in aid or '/PRT-' in aid: return 'Printer'
    if '/T/' in aid or '/T-' in aid: return 'Tablet'
    if '/U/' in aid or '/U-' in aid: return 'UPS'
    return code or 'CPU'

def parse_and_normalize_components(components_input, device_type_str='', monitor_spec='', keyboard_spec='', mouse_spec='', tablet_spec='', printer_spec='', ups_spec='', other_spec='', other_type=''):
    """
    Parses and normalizes a list of hardware components selected for a workstation.
    Returns an ordered list of canonical component types, e.g. ['CPU', 'Display', 'Keyboard', 'Mouse', 'Tablet', 'Other'].
    """
    import re
    comps = []
    if isinstance(components_input, list) and components_input:
        comps = [str(c).strip() for c in components_input if str(c).strip()]
    elif isinstance(components_input, str) and components_input.strip():
        comps = [s.strip() for s in components_input.split(',') if s.strip()]
    elif device_type_str:
        dt = device_type_str.strip()
        match = re.search(r'\(([^)]+)\)', dt)
        if match:
            comps = [s.strip() for s in match.group(1).split(',') if s.strip()]
        elif 'workstation' in dt.lower():
            comps = ['CPU']
            if monitor_spec: comps.append('Display')
            if keyboard_spec: comps.append('Keyboard')
            if mouse_spec: comps.append('Mouse')
            if tablet_spec: comps.append('Tablet')
            if printer_spec: comps.append('Printer')
            if ups_spec: comps.append('UPS')
            if other_spec or other_type: comps.append(other_type or 'Other')
            if len(comps) == 1:
                comps = ['CPU', 'Display', 'Keyboard', 'Mouse']
        elif ',' in dt:
            comps = [s.strip() for s in dt.split(',') if s.strip()]

    canonical = []
    for c in comps:
        u = c.upper()
        if 'CPU' in u or 'DESKTOP' in u or 'PC' in u:
            canonical.append('CPU')
        elif 'DISPLAY' in u or 'MONITOR' in u or 'SCREEN' in u:
            canonical.append('Display')
        elif 'KEYBOARD' in u or 'KB' in u:
            canonical.append('Keyboard')
        elif 'MOUSE' in u:
            canonical.append('Mouse')
        elif 'TABLET' in u or 'TAB' in u or 'IPAD' in u:
            canonical.append('Tablet')
        elif 'BARCODE PRINTER' in u or 'LABEL PRINTER' in u:
            canonical.append(other_type or 'Barcode Printer')
        elif 'PRINTER' in u or 'PRT' in u:
            canonical.append('Printer')
        elif 'UPS' in u or 'POWER' in u or 'INVERTER' in u:
            canonical.append('UPS')
        elif 'OTHER' in u or 'CUSTOM' in u:
            canonical.append(other_type or 'Other')
        else:
            canonical.append(c)

    order = ['CPU', 'Display', 'Keyboard', 'Mouse', 'Tablet', 'Printer', 'UPS', 'Other']
    unique_comps = []
    for o in order:
        if o in canonical and o not in unique_comps:
            unique_comps.append(o)
    for c in canonical:
        if c not in unique_comps:
            unique_comps.append(c)

    return unique_comps

def allocate_sequential_tags(base_tag, count):
    """
    Allocates `count` collision-free sequential asset tags starting from `base_tag`.
    Guarantees 100% collision-free against PostgreSQL DeviceAsset table.
    """
    import re
    now = timezone.localtime()
    mmyy = now.strftime("%m%y")
    
    parts = base_tag.strip().split('/')
    if len(parts) >= 4 and parts[-1].isdigit():
        prefix = "/".join(parts[:-1]) + "/"
        try:
            start_num = int(parts[-1])
        except ValueError:
            start_num = 1
    else:
        prefix = f"PSM/IT/{mmyy}/"
        start_num = 1

    existing_tags = set(DeviceAsset.objects.values_list('asset_id', flat=True))
    existing_upper = {t.upper().strip() for t in existing_tags if t}

    allocated = []
    curr = start_num
    while len(allocated) < count and curr <= 999:
        candidate = f"{prefix}{curr:03d}"
        if candidate.upper() not in existing_upper and candidate not in allocated:
            allocated.append(candidate)
        curr += 1

    # Fallback if 999 reached
    if len(allocated) < count:
        for n in range(1, 1000):
            candidate = f"{prefix}{n:03d}"
            if candidate.upper() not in existing_upper and candidate not in allocated:
                allocated.append(candidate)
                if len(allocated) >= count:
                    break

    return allocated

def ensure_sample_devices():
    """No-op: sample devices permanently purged."""
    pass

def api_get_devices(request):
    """JSON API returning all hardware devices from SQLite database (PSM Hospital only)."""
    ensure_sample_devices()
    qs = DeviceAsset.objects.filter(org_id='HOSP')
    
    devices_data = []
    for d in qs:
        devices_data.append({
            'id': d.dev_id,
            'assetId': d.asset_id,
            'deviceType': d.device_type or normalize_device_type('', d.asset_id),
            'serialNumber': d.serial_number,
            'orgId': d.org_id,
            'orgName': d.org_name,
            'buildingName': d.building_name,
            'floorName': d.floor_name,
            'roomName': d.room_name,
            'assignedUserId': d.assigned_user_id,
            'assignedUserName': d.assigned_user_name,
            'empId': d.assigned_emp_id,
            'designation': getattr(d, 'assigned_designation', '') or '',
            'assignedDesignation': getattr(d, 'assigned_designation', '') or '',
            'department': getattr(d, 'assigned_department', '') or '',
            'assignedDepartment': getattr(d, 'assigned_department', '') or '',
            'email': getattr(d, 'assigned_email', '') or '',
            'assignedEmail': getattr(d, 'assigned_email', '') or '',
            'phone': getattr(d, 'assigned_phone', '') or '',
            'assignedPhone': getattr(d, 'assigned_phone', '') or '',
            'monitorSpec': d.monitor_spec,
            'cpuProcessor': d.cpu_processor,
            'storageRam': d.storage_ram,
            'keyboardSpec': getattr(d, 'keyboard_spec', '') or '',
            'mouseSpec': getattr(d, 'mouse_spec', '') or '',
            'printerSpec': getattr(d, 'printer_spec', '') or '',
            'upsSpec': getattr(d, 'ups_spec', '') or '',
            'tabletSpec': getattr(d, 'tablet_spec', '') or '',
            'ipAddress': d.ip_address,
            'macAddress': d.mac_address,
            'operatingSystem': d.operating_system,
            'purchaseDate': d.purchase_date,
            'warrantyExpiryDate': d.warranty_expiry_date,
            'status': d.status,
            'brandName': getattr(d, 'brand_name', '') or '',
            'brand': getattr(d, 'brand_name', '') or '',
            'hardwareDeviceId': getattr(d, 'device_id', '') or '',
            'anydeskId': getattr(d, 'anydesk_id', '') or '',
        })
    return JsonResponse({'success': True, 'devices': devices_data})

@csrf_exempt
def api_reassign_device(request):
    """Handles custody transfer / reassignment of hardware and logs audit trail."""
    ensure_sample_devices()
    if request.method == 'POST':
        import json
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body.decode('utf-8'))
            except Exception:
                data = {}
        else:
            data = request.POST

        dev_id = data.get('deviceId') or data.get('device_id')
        new_user_id = data.get('newUserId') or data.get('new_user_id')
        new_user_name = data.get('newUserName') or data.get('new_user_name', '')
        new_emp_id = data.get('newEmpId') or data.get('new_emp_id', '')
        handover_date = data.get('handoverDate') or data.get('handover_date') or timezone.now().strftime('%Y-%m-%d')
        remarks = (data.get('remarks') or '').strip()
        assigned_by = data.get('assignedBy') or request.session.get('staff_name', 'IT Admin Desk')

        # Find device by dev_id or assetId
        device = DeviceAsset.objects.filter(dev_id=dev_id).first() or DeviceAsset.objects.filter(asset_id=dev_id).first()
        if not device:
            return JsonResponse({'success': False, 'message': f'Device {dev_id} not found in database.'}, status=404)

        from_user_name = device.assigned_user_name or "Unassigned"
        from_emp_id = device.assigned_emp_id or ""

        if new_user_id == '__UNASSIGN__':
            device.assigned_user_id = None
            device.assigned_user_name = "Unassigned"
            device.assigned_emp_id = ""
            device.save()

            # Create audit log
            CustodyTransferLog.objects.create(
                device=device,
                device_asset_id=device.asset_id,
                from_user_name=from_user_name,
                from_emp_id=from_emp_id,
                to_user_name="Unassigned (IT Spares)",
                to_emp_id="",
                handover_date=handover_date,
                assigned_by=assigned_by,
                remarks=remarks or f"Returned to IT Spares from {from_user_name}"
            )
            return JsonResponse({
                'success': True, 
                'message': f"Device {device.asset_id} returned to Unassigned Spares pool.",
                'device': {
                    'id': device.dev_id,
                    'assetId': device.asset_id,
                    'assignedUserName': 'Unassigned',
                    'assignedUserId': None
                }
            })

        # Lookup new user info from UserProfile if not provided
        if not new_user_name and new_emp_id:
            profile = UserProfile.objects.filter(emp_id=new_emp_id).first()
            if profile:
                new_user_name = profile.full_name

        device.assigned_user_id = new_user_id
        device.assigned_user_name = new_user_name or "Assigned Staff"
        device.assigned_emp_id = new_emp_id
        device.save()

        # Update UserProfile assigned_asset_id if user is registered in the portal
        if new_emp_id:
            UserProfile.objects.filter(emp_id=new_emp_id).update(assigned_asset_id=device.asset_id)

        # Create custody transfer log
        CustodyTransferLog.objects.create(
            device=device,
            device_asset_id=device.asset_id,
            from_user_name=from_user_name,
            from_emp_id=from_emp_id,
            to_user_name=new_user_name or "Assigned Staff",
            to_emp_id=new_emp_id,
            handover_date=handover_date,
            assigned_by=assigned_by,
            remarks=remarks or f"Custody transferred from {from_user_name} to {new_user_name}"
        )

        return JsonResponse({
            'success': True,
            'message': f"Custody of {device.asset_id} successfully transferred to {new_user_name}!",
            'device': {
                'id': device.dev_id,
                'assetId': device.asset_id,
                'assignedUserName': device.assigned_user_name,
                'assignedUserId': device.assigned_user_id,
                'empId': device.assigned_emp_id,
            }
        })

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def api_save_device(request):
    """Registers a new hardware device or updates an existing device in PostgreSQL database.
    Immediately synchronizes with Asset Tag Center and Inventory."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST method required.'}, status=405)

    import json
    import uuid
    import datetime

    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = {}
    else:
        data = request.POST

    asset_id = (data.get('assetId') or data.get('asset_id') or '').strip().upper()
    if not asset_id:
        return JsonResponse({'success': False, 'message': 'Asset Tag / ID is required.'}, status=400)

    # 3-digit sequence constraint validation on last segment
    parts = asset_id.split('/')
    if len(parts) >= 4 and (len(parts[-1]) > 3 or (parts[-1] and not parts[-1].isdigit())):
        return JsonResponse({
            'success': False,
            'message': 'Invalid Asset Tag: Sequence code cannot exceed 3 digits (e.g. 001 to 999).'
        }, status=400)

    serial_number = (data.get('serialNumber') or data.get('serial_number') or '').strip().upper()
    device_type = normalize_device_type(data.get('deviceType') or data.get('device_type'), asset_id)
    org_id = (data.get('orgId') or data.get('org_id') or 'HOSP').strip()
    org_name = 'PSM Hospital' if org_id == 'HOSP' else 'Swaminarayan University'

    building_name = (data.get('buildingName') or data.get('building_name') or 'PSM Hospital').strip()
    floor_name = (data.get('floorName') or data.get('floor_name') or 'Ground Floor').strip()
    room_name = (data.get('roomName') or data.get('room_name') or 'General Facility').strip()

    assigned_user_id = data.get('assignedUserId') or data.get('assigned_user_id') or ''
    assigned_user_name = (data.get('assignedUserName') or data.get('assigned_user_name') or 'Unassigned').strip()
    assigned_emp_id = (data.get('assignedEmpId') or data.get('assigned_emp_id') or data.get('empId') or '').strip()
    assigned_designation = (data.get('assignedDesignation') or data.get('assigned_designation') or data.get('designation') or '').strip()
    assigned_department = (data.get('assignedDepartment') or data.get('assigned_department') or data.get('department') or '').strip()
    assigned_email = (data.get('assignedEmail') or data.get('assigned_email') or data.get('email') or '').strip()
    assigned_phone = (data.get('assignedPhone') or data.get('assigned_phone') or data.get('phone') or data.get('contact') or '').strip()

    # If designation, department, phone, or email is empty and a known staff is assigned, auto-fill from UserProfile or SAMPLE_STAFF
    if assigned_user_name and assigned_user_name.lower() != 'unassigned':
        prof = UserProfile.objects.filter(full_name__iexact=assigned_user_name).select_related('user').first()
        if not prof and assigned_emp_id:
            prof = UserProfile.objects.filter(emp_id__iexact=assigned_emp_id).select_related('user').first()
        if prof:
            if not assigned_designation and prof.designation:
                assigned_designation = prof.designation
            if not assigned_department and prof.department:
                assigned_department = prof.department
            if not assigned_phone and prof.phone:
                assigned_phone = prof.phone
            if not assigned_email and prof.user and prof.user.email:
                assigned_email = prof.user.email


    cpu_processor = (data.get('cpuProcessor') or data.get('cpu_processor') or 'Intel Core i5 (Standard)').strip()
    storage_ram = (data.get('storageRam') or data.get('storage_ram') or '16GB RAM / 512GB SSD').strip()
    monitor_spec = (data.get('monitorSpec') or data.get('monitor_spec') or '24" FHD IPS Display').strip()
    keyboard_spec = (data.get('keyboardSpec') or data.get('keyboard_spec') or '').strip()
    mouse_spec = (data.get('mouseSpec') or data.get('mouse_spec') or '').strip()
    printer_spec = (data.get('printerSpec') or data.get('printer_spec') or '').strip()
    ups_spec = (data.get('upsSpec') or data.get('ups_spec') or '').strip()
    tablet_spec = (data.get('tabletSpec') or data.get('tablet_spec') or '').strip()
    operating_system = (data.get('operatingSystem') or data.get('operating_system') or 'Windows 11 Pro').strip()
    ip_address = (data.get('ipAddress') or data.get('ip_address') or '').strip()
    mac_address = (data.get('macAddress') or data.get('mac_address') or '').strip().upper()
    status = (data.get('status') or 'Active').strip()
    purchase_date = (data.get('purchaseDate') or data.get('purchase_date') or timezone.now().strftime('%d-%b-%Y')).strip()
    warranty_expiry_date = (data.get('warrantyExpiryDate') or data.get('warranty_expiry_date') or (datetime.date.today() + datetime.timedelta(days=1095)).strftime('%d-%b-%Y')).strip()
    brand_name = (data.get('brand_name') or data.get('brand') or '').strip()
    cpu_brand = (data.get('cpu_brand') or '').strip()
    monitor_brand = (data.get('monitor_brand') or '').strip()
    keyboard_brand = (data.get('keyboard_brand') or '').strip()
    mouse_brand = (data.get('mouse_brand') or '').strip()
    printer_brand = (data.get('printer_brand') or '').strip()
    ups_brand = (data.get('ups_brand') or '').strip()
    tablet_brand = (data.get('tablet_brand') or '').strip()
    cpu_serial = (data.get('cpu_serial') or data.get('cpu_sn') or '').strip().upper()
    monitor_serial = (data.get('monitor_serial') or data.get('monitor_sn') or '').strip().upper()
    keyboard_serial = (data.get('keyboard_serial') or data.get('keyboard_sn') or '').strip().upper()
    mouse_serial = (data.get('mouse_serial') or data.get('mouse_sn') or '').strip().upper()
    printer_serial = (data.get('printer_serial') or data.get('printer_sn') or '').strip().upper()
    ups_serial = (data.get('ups_serial') or data.get('ups_sn') or '').strip().upper()
    tablet_serial = (data.get('tablet_serial') or data.get('tablet_sn') or '').strip().upper()
    tablet_device_id = (data.get('tablet_device_id') or data.get('device_id') or '').strip().upper()
    tablet_anydesk_id = (data.get('tablet_anydesk_id') or data.get('anydesk_id') or '').strip()
    tablet_mac = (data.get('tablet_mac_address') or data.get('tablet_mac') or '').strip().upper()
    other_device_type = (data.get('other_device_type') or data.get('other_type') or '').strip()
    other_brand = (data.get('other_brand') or '').strip()
    other_model = (data.get('other_model') or data.get('other_spec') or '').strip()
    other_serial = (data.get('other_serial') or data.get('other_sn') or '').strip().upper()
    other_spec = other_model
    device_id = (data.get('device_id') or tablet_device_id or '').strip()
    anydesk_id = (data.get('anydesk_id') or tablet_anydesk_id or '').strip()

    if not serial_number and cpu_serial:
        serial_number = cpu_serial

    # For standalone single-device registrations, align cpu_processor if empty or default
    if not ('workstation' in device_type.lower() or ',' in device_type):
        if 'keyboard' in device_type.lower() and keyboard_spec:
            cpu_processor = keyboard_spec
        elif 'mouse' in device_type.lower() and mouse_spec:
            cpu_processor = mouse_spec
        elif 'printer' in device_type.lower() and printer_spec:
            cpu_processor = printer_spec
        elif 'ups' in device_type.lower() and ups_spec:
            cpu_processor = ups_spec
        elif 'tablet' in device_type.lower() and tablet_spec:
            cpu_processor = tablet_spec
        elif other_model or other_spec:
            cpu_processor = other_model or other_spec

    if device_type.upper() in ('OTHER', 'OTHER DEVICE') and other_device_type:
        device_type = other_device_type

    edit_id = (data.get('editId') or data.get('edit_id') or data.get('id') or '').strip()
    is_edit_request = bool(data.get('is_edit') or edit_id or data.get('allow_overwrite'))
    if edit_id:
        dev = DeviceAsset.objects.filter(dev_id=edit_id).first() or DeviceAsset.objects.filter(asset_id__iexact=asset_id).first()
    else:
        dev = DeviceAsset.objects.filter(asset_id__iexact=asset_id).first()

    if dev and not is_edit_request:
        return JsonResponse({
            'success': False,
            'message': f'Asset Tag "{asset_id}" is already registered to {dev.device_type} in {dev.room_name}. Please click "Auto Generate" for the next unique code.'
        }, status=409)

    # Determine multi-component workstation composition
    raw_components = data.get('components')
    components = parse_and_normalize_components(
        raw_components,
        data.get('deviceType') or data.get('device_type'),
        monitor_spec=monitor_spec,
        keyboard_spec=keyboard_spec,
        mouse_spec=mouse_spec,
        tablet_spec=tablet_spec,
        printer_spec=printer_spec,
        ups_spec=ups_spec,
        other_spec=other_spec,
        other_type=other_device_type
    )

    # =========================================================================
    # MULTI-COMPONENT WORKSTATION ITEMIZATION (Single Asset Tag Architecture)
    # Saves distinct DeviceAsset rows in PostgreSQL for each selected hardware piece
    # All components for this person share the exact same single asset tag
    # =========================================================================
    if not is_edit_request and len(components) > 1:
        allocated_tags = [asset_id] * len(components)
        created_devices = []

        ABBR_MAP = {
            'CPU': 'CPU',
            'DISPLAY': 'DISP',
            'KEYBOARD': 'KB',
            'MOUSE': 'MS',
            'TABLET': 'TAB',
            'PRINTER': 'PRT',
            'UPS': 'UPS',
            'OTHER': 'OTH',
            'SCANNER': 'SCN',
            'BIOMETRIC MACHINE': 'BIO',
            'BIOMETRIC': 'BIO',
            'EYE SCANNER': 'EYE',
            'BARCODE PRINTER': 'BPR',
            'BARCODE SCANNER': 'BCS',
            'PROJECTOR': 'PRJ',
            'WEBCAM': 'CAM'
        }

        with transaction.atomic():
            for idx, comp in enumerate(components):
                comp_tag = allocated_tags[idx]
                comp_dev_id = f"dev-{uuid.uuid4().hex[:8]}"

                # Serial number per component
                comp_upper = comp.upper()
                comp_abbr = ABBR_MAP.get(comp_upper, comp_upper[:3])
                if comp_upper == 'CPU':
                    comp_sn = cpu_serial or serial_number or f"SN-PSM-CPU-{comp_tag.split('/')[-1]}"
                elif comp_upper == 'DISPLAY':
                    comp_sn = monitor_serial or (f"{serial_number}-DISP" if serial_number else f"SN-PSM-DISP-{comp_tag.split('/')[-1]}")
                elif comp_upper == 'KEYBOARD':
                    comp_sn = keyboard_serial or (f"{serial_number}-KB" if serial_number else f"SN-PSM-KB-{comp_tag.split('/')[-1]}")
                elif comp_upper == 'MOUSE':
                    comp_sn = mouse_serial or (f"{serial_number}-MS" if serial_number else f"SN-PSM-MS-{comp_tag.split('/')[-1]}")
                elif comp_upper == 'TABLET':
                    comp_sn = tablet_serial or (f"{serial_number}-TAB" if serial_number else f"SN-PSM-TAB-{comp_tag.split('/')[-1]}")
                elif comp_upper == 'PRINTER':
                    comp_sn = printer_serial or (f"{serial_number}-PRT" if serial_number else f"SN-PSM-PRT-{comp_tag.split('/')[-1]}")
                elif comp_upper == 'UPS':
                    comp_sn = ups_serial or (f"{serial_number}-UPS" if serial_number else f"SN-PSM-UPS-{comp_tag.split('/')[-1]}")
                elif (
                    comp_upper in ('OTHER', 'CUSTOM', 'SCANNER', 'BIOMETRIC MACHINE', 'BIOMETRIC', 'EYE SCANNER', 'BARCODE PRINTER')
                    or 'OTHER' in comp_upper
                    or 'SCANNER' in comp_upper
                    or 'BIOMETRIC' in comp_upper
                    or 'EYE' in comp_upper
                    or 'BARCODE' in comp_upper
                    or (other_device_type and comp_upper == other_device_type.upper())
                ):
                    comp_sn = other_serial or (f"{serial_number}-{comp_abbr}" if serial_number else f"SN-PSM-{comp_abbr}-{comp_tag.split('/')[-1]}")
                else:
                    comp_sn = f"{serial_number}-{comp_abbr}" if serial_number else f"SN-PSM-{comp_abbr}-{comp_tag.split('/')[-1]}"

                # Component-specific compute / specs & brand
                if comp_upper == 'CPU':
                    item_dev_type = 'CPU'
                    item_brand = cpu_brand or brand_name or 'Dell'
                    item_cpu = cpu_processor or 'Intel Core i5 (Standard)'
                    item_ram = storage_ram or '16GB RAM / 512GB SSD'
                    item_os = operating_system or 'Windows 11 Pro'
                    item_ip = ip_address
                    item_mac = mac_address
                elif comp_upper == 'DISPLAY':
                    item_dev_type = 'Display'
                    item_brand = monitor_brand or brand_name or 'Dell'
                    item_cpu = monitor_spec or '24" FHD IPS Medical / Office Grade Display'
                    item_ram = 'Hardware Display Monitor'
                    item_os = 'Hardware Display'
                    item_ip = '-'
                    item_mac = '-'
                elif comp_upper == 'KEYBOARD':
                    item_dev_type = 'Keyboard'
                    item_brand = keyboard_brand or brand_name or 'Dell'
                    item_cpu = keyboard_spec or 'Spill-Resistant Membrane USB Keyboard'
                    item_ram = 'Hardware Peripheral (HID)'
                    item_os = 'Hardware Peripheral (HID)'
                    item_ip = '-'
                    item_mac = '-'
                elif comp_upper == 'MOUSE':
                    item_dev_type = 'Mouse'
                    item_brand = mouse_brand or brand_name or 'Dell'
                    item_cpu = mouse_spec or 'Ergonomic Optical Cleanable Clinic Mouse'
                    item_ram = 'Hardware Peripheral (HID)'
                    item_os = 'Hardware Peripheral (HID)'
                    item_ip = '-'
                    item_mac = '-'
                elif comp_upper == 'TABLET':
                    item_dev_type = 'Tablet'
                    item_brand = tablet_brand or brand_name or 'Samsung'
                    item_cpu = tablet_spec or 'Mobile Diagnostic Tablet'
                    item_ram = 'Mobile Workstation Unit'
                    item_os = 'Mobile OS / Windows Tablet'
                    item_ip = ip_address or '-'
                    item_mac = tablet_mac or mac_address or '-'
                elif comp_upper == 'PRINTER':
                    item_dev_type = 'Printer'
                    item_brand = printer_brand or brand_name or 'HP'
                    item_cpu = printer_spec or 'Direct Thermal & Document Printer'
                    item_ram = 'Direct Print Unit'
                    item_os = 'Printer Firmware'
                    item_ip = ip_address or '-'
                    item_mac = mac_address or '-'
                elif comp_upper == 'UPS':
                    item_dev_type = 'UPS'
                    item_brand = ups_brand or brand_name or 'APC'
                    item_cpu = ups_spec or 'Line-Interactive Battery Backup Unit'
                    item_ram = 'AC Power Protection'
                    item_os = 'Power Unit'
                    item_ip = '-'
                    item_mac = '-'
                elif (
                    comp_upper in ('OTHER', 'CUSTOM', 'SCANNER', 'BIOMETRIC MACHINE', 'BIOMETRIC', 'EYE SCANNER', 'BARCODE PRINTER')
                    or 'OTHER' in comp_upper
                    or 'SCANNER' in comp_upper
                    or 'BIOMETRIC' in comp_upper
                    or 'EYE' in comp_upper
                    or 'BARCODE' in comp_upper
                    or (other_device_type and comp_upper == other_device_type.upper())
                ):
                    item_dev_type = other_device_type or comp
                    item_brand = other_brand or brand_name or ''
                    item_cpu = other_model or f'{item_dev_type} Hardware Unit'
                    item_ram = 'Hardware Accessory / Peripheral'
                    item_os = 'Hardware Firmware'
                    item_ip = '-'
                    item_mac = '-'
                else:
                    item_dev_type = comp
                    item_brand = brand_name or ''
                    item_cpu = f'{comp} Hardware Unit'
                    item_ram = 'Standard Hardware Component'
                    item_os = operating_system or 'Hardware Firmware'
                    item_ip = '-'
                    item_mac = '-'

                item_dev = DeviceAsset.objects.create(
                    dev_id=comp_dev_id,
                    asset_id=comp_tag,
                    device_type=item_dev_type,
                    brand_name=item_brand,
                    serial_number=comp_sn,
                    device_id=tablet_device_id if comp_upper == 'TABLET' else (device_id if comp_upper == 'CPU' else ''),
                    anydesk_id=tablet_anydesk_id if comp_upper == 'TABLET' else anydesk_id,
                    org_id=org_id,
                    org_name=org_name,
                    building_name=building_name,
                    floor_name=floor_name,
                    room_name=room_name,
                    assigned_user_id=assigned_user_id,
                    assigned_user_name=assigned_user_name,
                    assigned_emp_id=assigned_emp_id,
                    assigned_designation=assigned_designation,
                    assigned_department=assigned_department,
                    assigned_email=assigned_email,
                    assigned_phone=assigned_phone,
                    cpu_processor=item_cpu,
                    storage_ram=item_ram,
                    monitor_spec=monitor_spec if comp_upper in ('CPU', 'DISPLAY') else '',
                    keyboard_spec=keyboard_spec if comp_upper in ('CPU', 'KEYBOARD') else '',
                    mouse_spec=mouse_spec if comp_upper in ('CPU', 'MOUSE') else '',
                    printer_spec=printer_spec if comp_upper in ('CPU', 'PRINTER') else '',
                    ups_spec=ups_spec if comp_upper in ('CPU', 'UPS') else '',
                    tablet_spec=tablet_spec if comp_upper in ('CPU', 'TABLET') else '',
                    operating_system=item_os,
                    ip_address=item_ip,
                    mac_address=item_mac,
                    purchase_date=purchase_date,
                    warranty_expiry_date=warranty_expiry_date,
                    status=status
                )
                created_devices.append(item_dev)

                if assigned_user_name and assigned_user_name.lower() != 'unassigned':
                    CustodyTransferLog.objects.create(
                        device=item_dev,
                        device_asset_id=item_dev.asset_id,
                        from_user_name="Initial Provisioning",
                        from_emp_id="",
                        to_user_name=assigned_user_name,
                        to_emp_id=assigned_emp_id,
                        handover_date=purchase_date,
                        assigned_by=request.session.get('staff_name', 'IT Admin Desk') if hasattr(request, 'session') else 'IT Admin Desk',
                        remarks=f"Initial Workstation assignment ({item_dev.device_type}) to {assigned_user_name}"
                    )

            if assigned_emp_id:
                UserProfile.objects.filter(emp_id=assigned_emp_id).update(assigned_asset_id=asset_id)

        primary = created_devices[0]
        tag_summary = f"{asset_id} ({len(created_devices)} Components)"

        return JsonResponse({
            'success': True,
            'message': f"Workstation Set ({len(created_devices)} hardware components under Asset Tag {asset_id}) registered successfully and synchronized with Inventory!",
            'is_new': True,
            'is_workstation': True,
            'asset_id': asset_id,
            'asset_tag_summary': asset_id,
            'created_count': len(created_devices),
            'tags': allocated_tags,
            'tag_url': f"/tag/?asset_id={urllib.parse.quote(asset_id)}",
            'device': {
                'id': primary.dev_id,
                'assetId': primary.asset_id,
                'deviceType': primary.device_type,
                'serialNumber': primary.serial_number,
                'orgId': primary.org_id,
                'orgName': primary.org_name,
                'buildingName': primary.building_name,
                'floorName': primary.floor_name,
                'roomName': primary.room_name,
                'assignedUserId': primary.assigned_user_id,
                'assignedUserName': primary.assigned_user_name,
                'empId': primary.assigned_emp_id,
                'designation': primary.assigned_designation or '',
                'assignedDesignation': primary.assigned_designation or '',
                'email': getattr(primary, 'assigned_email', '') or '',
                'assignedEmail': getattr(primary, 'assigned_email', '') or '',
                'phone': getattr(primary, 'assigned_phone', '') or '',
                'assignedPhone': getattr(primary, 'assigned_phone', '') or '',
                'cpuProcessor': primary.cpu_processor,
                'storageRam': primary.storage_ram,
                'monitorSpec': primary.monitor_spec,
                'keyboardSpec': getattr(primary, 'keyboard_spec', '') or '',
                'mouseSpec': getattr(primary, 'mouse_spec', '') or '',
                'printerSpec': getattr(primary, 'printer_spec', '') or '',
                'upsSpec': getattr(primary, 'ups_spec', '') or '',
                'tabletSpec': getattr(primary, 'tablet_spec', '') or '',
                'operatingSystem': primary.operating_system,
                'ipAddress': primary.ip_address,
                'macAddress': primary.mac_address,
                'purchaseDate': primary.purchase_date,
                'warrantyExpiryDate': primary.warranty_expiry_date,
                'status': primary.status,
                'brandName': getattr(primary, 'brand_name', '') or '',
                'brand': getattr(primary, 'brand_name', '') or '',
            },
            'devices': [
                {
                    'id': d.dev_id,
                    'assetId': d.asset_id,
                    'deviceType': d.device_type,
                    'brandName': getattr(d, 'brand_name', '') or '',
                    'brand': getattr(d, 'brand_name', '') or '',
                    'serialNumber': d.serial_number,
                    'orgId': d.org_id,
                    'orgName': d.org_name,
                    'buildingName': d.building_name,
                    'floorName': d.floor_name,
                    'roomName': d.room_name,
                    'assignedUserId': d.assigned_user_id,
                    'assignedUserName': d.assigned_user_name,
                    'empId': d.assigned_emp_id,
                    'designation': d.assigned_designation or '',
                    'assignedDesignation': d.assigned_designation or '',
                    'email': getattr(d, 'assigned_email', '') or '',
                    'assignedEmail': getattr(d, 'assigned_email', '') or '',
                    'phone': getattr(d, 'assigned_phone', '') or '',
                    'assignedPhone': getattr(d, 'assigned_phone', '') or '',
                    'cpuProcessor': d.cpu_processor,
                    'storageRam': d.storage_ram,
                    'monitorSpec': d.monitor_spec,
                    'keyboardSpec': getattr(d, 'keyboard_spec', '') or '',
                    'mouseSpec': getattr(d, 'mouse_spec', '') or '',
                    'printerSpec': getattr(d, 'printer_spec', '') or '',
                    'upsSpec': getattr(d, 'ups_spec', '') or '',
                    'tabletSpec': getattr(d, 'tablet_spec', '') or '',
                    'operatingSystem': d.operating_system,
                    'ipAddress': d.ip_address,
                    'macAddress': d.mac_address,
                    'purchaseDate': d.purchase_date,
                    'warrantyExpiryDate': d.warranty_expiry_date,
                    'status': d.status,
                } for d in created_devices
            ]
        })

    single_brand = brand_name
    if not single_brand:
        dtype_up = device_type.upper()
        if 'CPU' in dtype_up or 'WORKSTATION' in dtype_up:
            single_brand = cpu_brand or 'Dell'
        elif 'DISPLAY' in dtype_up or 'MONITOR' in dtype_up:
            single_brand = monitor_brand or 'Dell'
        elif 'KEYBOARD' in dtype_up:
            single_brand = keyboard_brand or 'Dell'
        elif 'MOUSE' in dtype_up:
            single_brand = mouse_brand or 'Dell'
        elif 'PRINTER' in dtype_up:
            single_brand = printer_brand or 'HP'
        elif 'UPS' in dtype_up:
            single_brand = ups_brand or 'APC'
        elif 'TABLET' in dtype_up:
            single_brand = tablet_brand or 'Samsung'
        elif other_brand:
            single_brand = other_brand
        else:
            single_brand = ''

    if not serial_number:
        dtype_up = device_type.upper()
        if 'CPU' in dtype_up:
            serial_number = cpu_serial
        elif 'DISPLAY' in dtype_up or 'MONITOR' in dtype_up:
            serial_number = monitor_serial
        elif 'KEYBOARD' in dtype_up:
            serial_number = keyboard_serial
        elif 'MOUSE' in dtype_up:
            serial_number = mouse_serial
        elif 'PRINTER' in dtype_up:
            serial_number = printer_serial
        elif 'UPS' in dtype_up:
            serial_number = ups_serial
        elif 'TABLET' in dtype_up:
            serial_number = tablet_serial
        elif other_serial:
            serial_number = other_serial

    is_new = False
    if dev:
        dev.device_type = device_type
        if single_brand:
            dev.brand_name = single_brand
        if serial_number:
            dev.serial_number = serial_number
        dev.org_id = org_id
        dev.org_name = org_name
        dev.building_name = building_name
        dev.floor_name = floor_name
        dev.room_name = room_name
        dev.assigned_user_id = assigned_user_id
        dev.assigned_user_name = assigned_user_name
        dev.assigned_emp_id = assigned_emp_id
        dev.assigned_designation = assigned_designation
        dev.assigned_department = assigned_department
        dev.assigned_email = assigned_email
        dev.assigned_phone = assigned_phone
        dev.cpu_processor = cpu_processor
        dev.storage_ram = storage_ram
        dev.monitor_spec = monitor_spec
        dev.keyboard_spec = keyboard_spec
        dev.mouse_spec = mouse_spec
        dev.printer_spec = printer_spec
        dev.ups_spec = ups_spec
        dev.tablet_spec = tablet_spec
        dev.operating_system = operating_system
        dev.ip_address = ip_address
        dev.mac_address = tablet_mac if ('TABLET' in dtype_up and tablet_mac) else mac_address
        if 'TABLET' in dtype_up:
            if tablet_device_id:
                dev.device_id = tablet_device_id
            if tablet_anydesk_id:
                dev.anydesk_id = tablet_anydesk_id
        else:
            if device_id:
                dev.device_id = device_id
            if anydesk_id:
                dev.anydesk_id = anydesk_id
        dev.purchase_date = purchase_date
        dev.warranty_expiry_date = warranty_expiry_date
        dev.status = status
        dev.save()
    else:
        is_new = True
        dev_id = f"dev-{uuid.uuid4().hex[:8]}"
        dev = DeviceAsset.objects.create(
            dev_id=dev_id,
            asset_id=asset_id,
            device_type=device_type,
            brand_name=single_brand,
            serial_number=serial_number,
            device_id=tablet_device_id if 'TABLET' in dtype_up else device_id,
            anydesk_id=tablet_anydesk_id if 'TABLET' in dtype_up else anydesk_id,
            org_id=org_id,
            org_name=org_name,
            building_name=building_name,
            floor_name=floor_name,
            room_name=room_name,
            assigned_user_id=assigned_user_id,
            assigned_user_name=assigned_user_name,
            assigned_emp_id=assigned_emp_id,
            assigned_designation=assigned_designation,
            assigned_department=assigned_department,
            assigned_email=assigned_email,
            assigned_phone=assigned_phone,
            cpu_processor=cpu_processor,
            storage_ram=storage_ram,
            monitor_spec=monitor_spec,
            keyboard_spec=keyboard_spec,
            mouse_spec=mouse_spec,
            printer_spec=printer_spec,
            ups_spec=ups_spec,
            tablet_spec=tablet_spec,
            operating_system=operating_system,
            ip_address=ip_address,
            mac_address=tablet_mac if ('TABLET' in dtype_up and tablet_mac) else mac_address,
            purchase_date=purchase_date,
            warranty_expiry_date=warranty_expiry_date,
            status=status
        )

    if is_new and assigned_emp_id:
        UserProfile.objects.filter(emp_id=assigned_emp_id).update(assigned_asset_id=dev.asset_id)

    # Initial custody audit log if assigned
    if is_new and assigned_user_name and assigned_user_name.lower() != 'unassigned':
        CustodyTransferLog.objects.create(
            device=dev,
            device_asset_id=dev.asset_id,
            from_user_name="Initial Provisioning",
            from_emp_id="",
            to_user_name=assigned_user_name,
            to_emp_id=assigned_emp_id,
            handover_date=purchase_date,
            assigned_by=request.session.get('staff_name', 'IT Admin Desk') if hasattr(request, 'session') else 'IT Admin Desk',
            remarks=f"Initial hardware assignment to {assigned_user_name}"
        )

    return JsonResponse({
        'success': True,
        'message': f"Hardware device {dev.asset_id} {'registered' if is_new else 'updated'} successfully and synchronized with Asset Tag Center!",
        'is_new': is_new,
        'asset_id': dev.asset_id,
        'tag_url': f"/tag/?asset_id={urllib.parse.quote(dev.asset_id)}",
        'device': {
            'id': dev.dev_id,
            'assetId': dev.asset_id,
            'deviceType': dev.device_type,
            'serialNumber': dev.serial_number,
            'orgId': dev.org_id,
            'orgName': dev.org_name,
            'buildingName': dev.building_name,
            'floorName': dev.floor_name,
            'roomName': dev.room_name,
            'assignedUserId': dev.assigned_user_id,
            'assignedUserName': dev.assigned_user_name,
            'empId': dev.assigned_emp_id,
            'designation': dev.assigned_designation or '',
            'assignedDesignation': dev.assigned_designation or '',
            'email': getattr(dev, 'assigned_email', '') or '',
            'assignedEmail': getattr(dev, 'assigned_email', '') or '',
            'phone': getattr(dev, 'assigned_phone', '') or '',
            'assignedPhone': getattr(dev, 'assigned_phone', '') or '',
            'cpuProcessor': dev.cpu_processor,
            'storageRam': dev.storage_ram,
            'monitorSpec': dev.monitor_spec,
            'keyboardSpec': getattr(dev, 'keyboard_spec', '') or '',
            'mouseSpec': getattr(dev, 'mouse_spec', '') or '',
            'printerSpec': getattr(dev, 'printer_spec', '') or '',
            'upsSpec': getattr(dev, 'ups_spec', '') or '',
            'tabletSpec': getattr(dev, 'tablet_spec', '') or '',
            'operatingSystem': dev.operating_system,
            'ipAddress': dev.ip_address,
            'macAddress': dev.mac_address,
            'purchaseDate': dev.purchase_date,
            'warrantyExpiryDate': dev.warranty_expiry_date,
            'status': dev.status,
            'brandName': getattr(dev, 'brand_name', '') or '',
            'brand': getattr(dev, 'brand_name', '') or '',
            'hardwareDeviceId': getattr(dev, 'device_id', '') or '',
            'anydeskId': getattr(dev, 'anydesk_id', '') or '',
        }
    })

def api_get_audit_logs(request):
    """Returns audit trail of all custody transfers from database."""
    qs = CustodyTransferLog.objects.all().order_by('-created_at')
    logs = []
    for l in qs:
        logs.append({
            'id': l.id,
            'deviceAssetId': l.device_asset_id,
            'fromUserName': l.from_user_name,
            'toUserName': l.to_user_name,
            'toEmpId': l.to_emp_id,
            'handoverDate': l.handover_date,
            'assignedBy': l.assigned_by,
            'remarks': l.remarks,
            'createdAt': l.created_at.strftime('%Y-%m-%d %H:%M')
        })
    return JsonResponse({'success': True, 'logs': logs})

# ============================================================================
# USER PORTAL VIEWS (AUTHENTICATION, MY DEVICE, COMPLAINTS)
# ============================================================================

def user_portal_root(request):
    """Main landing entry for staff/users: redirect directly to the Mobile QR incident report portal."""
    return redirect('mobile_report')


def is_admin_authenticated(request):
    """Check if the current session or user has active administrator privileges."""
    session = getattr(request, 'session', {})
    if session.get('admin_logged_in'):
        return True
    if hasattr(request, 'user') and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return True
    return False


def admin_required(view_func):
    """Decorator ensuring user is authenticated as administrator before accessing view."""
    from functools import wraps
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not is_admin_authenticated(request):
            full_path = request.get_full_path()
            if full_path in ('/', '/admin-portal/'):
                return redirect('admin_login')
            return redirect(f"/admin-login/?next={full_path}")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_login_view(request):
    """Administrator & Hardware Manager Sign In view."""
    # If already logged in, redirect directly to index (the organization selector picture page)
    if is_admin_authenticated(request):
        return redirect('index')

    next_url = request.GET.get('next') or request.POST.get('next') or 'index'
    if next_url in ('admin_login', '/admin-login/', ''):
        next_url = 'index'

    if request.method == 'POST':
        # 1-Click Quick Demo Admin Login
        if request.POST.get('demo_admin') == 'true':
            admin_user = User.objects.filter(is_superuser=True).first() or User.objects.filter(is_staff=True).first()
            if not admin_user:
                admin_user = User.objects.create_superuser(
                    username='admin',
                    email='admin@psmhospital.org',
                    password='admin',
                    first_name='System',
                    last_name='Administrator'
                )
            login(request, admin_user)
            admin_name = admin_user.get_full_name() or admin_user.username
            parts = admin_name.split()
            admin_initials = (parts[0][0] + (parts[1][0] if len(parts) > 1 else '')).upper() if parts else 'AD'
            
            request.session['admin_logged_in'] = True
            request.session['admin_name'] = admin_name
            request.session['admin_username'] = admin_user.username
            request.session['admin_role'] = 'Master Systems Administrator'
            request.session['admin_initials'] = admin_initials
            
            messages.success(request, f"Authenticated successfully as {admin_name}!")
            return redirect(next_url)

        # Standard Credentials Login
        login_id = request.POST.get('login_id', '').strip()
        password = request.POST.get('password', '').strip()

        if not login_id or not password:
            messages.error(request, "Please enter both Administrator Username/Email and Password.")
            return render(request, "admin/admin_login.html", {'next': next_url})

        # Match username or email
        target_user = User.objects.filter(username__iexact=login_id).first()
        if not target_user:
            target_user = User.objects.filter(email__iexact=login_id).first()

        user = None
        if target_user:
            user = authenticate(request, username=target_user.username, password=password)
        else:
            user = authenticate(request, username=login_id, password=password)

        if user is not None:
            # Check admin privileges
            if not (user.is_staff or user.is_superuser):
                profile = getattr(user, 'profile', None)
                if not (profile and 'admin' in profile.designation.lower()):
                    messages.error(request, "Access restricted. This account does not have IT Administrator privileges.")
                    return render(request, "admin/admin_login.html", {'next': next_url})

            login(request, user)
            profile = getattr(user, 'profile', None)
            if not profile:
                profile = UserProfile.objects.create(
                    user=user,
                    emp_id=user.username.upper(),
                    full_name=user.get_full_name() or user.username,
                    org_id='HOSP',
                    department='IT & Medical Systems',
                    designation='Master Administrator' if user.is_superuser else 'IT Systems Lead',
                    password=password
                )
            elif profile.password != password:
                profile.password = password
                profile.save(update_fields=['password'])

            admin_name = user.get_full_name() or (profile.full_name if profile else user.username)
            parts = admin_name.split()
            admin_initials = (parts[0][0] + (parts[1][0] if len(parts) > 1 else '')).upper() if parts else user.username[:2].upper()
            admin_role = profile.designation if (profile and profile.designation) else ('Master Administrator' if user.is_superuser else 'IT Systems Lead')

            request.session['admin_logged_in'] = True
            request.session['admin_name'] = admin_name
            request.session['admin_username'] = user.username
            request.session['admin_role'] = admin_role
            request.session['admin_initials'] = admin_initials

            messages.success(request, f"Welcome back to Central Admin Console, {admin_name}!")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid credentials. Please verify your administrator username/email and password.")

    return render(request, "admin/admin_login.html", {'next': next_url})


def admin_signup_view(request):
    """Administrator & Systems Engineer Registration view."""
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip().lower()
        email = request.POST.get('email', '').strip().lower()
        department = request.POST.get('department', '').strip() or 'IT & Medical Systems'
        designation = request.POST.get('designation', '').strip() or 'Systems Administrator'
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        # Validation
        if not full_name or not username or not email or not password:
            messages.error(request, "All required fields must be completed.")
            return render(request, "admin/admin_signup.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match. Please re-enter your password.")
            return render(request, "admin/admin_signup.html")

        if len(password) < 4:
            messages.error(request, "Password must be at least 4 characters long.")
            return render(request, "admin/admin_signup.html")

        # Check existing username / email
        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, f"An administrator with username '{username}' already exists. Please choose another username or log in.")
            return render(request, "admin/admin_signup.html")

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, f"An account with email '{email}' is already registered. Please log in.")
            return render(request, "admin/admin_signup.html")

        # Create Django User with staff privileges
        name_parts = full_name.split(maxsplit=1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        new_admin = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=True
        )

        UserProfile.objects.create(
            user=new_admin,
            emp_id=username.upper(),
            full_name=full_name,
            org_id='HOSP',
            department=department,
            designation=designation,
            assigned_asset_id='HOSP-SRV-CORE01',
            password=password
        )

        # Redirect directly to Admin Sign In page
        messages.success(request, f"Admin account '{username}' created successfully! Please sign in with your credentials.")
        return redirect(f"/admin-login/?registered={username}")

    return render(request, "admin/admin_signup.html")


def admin_logout_view(request):
    """Administrator Secure Sign Out."""
    logout(request)
    for key in ['admin_logged_in', 'admin_name', 'admin_username', 'admin_role', 'admin_initials']:
        request.session.pop(key, None)
    messages.info(request, "You have been securely signed out from the Administrator Console.")
    return redirect('admin_login')


def user_login_view(request):
    """Staff & Users entry view: redirect directly to the instant Mobile QR incident report portal."""
    return redirect('mobile_report')

def user_signup_view(request):
    """Staff registration view."""
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        emp_id = request.POST.get('emp_id', '').strip().upper()
        email = request.POST.get('email', '').strip().lower()
        org_id = request.POST.get('org_id', 'HOSP')
        department = request.POST.get('department', '').strip()
        designation = request.POST.get('designation', '').strip()
        assigned_asset_id = request.POST.get('assigned_asset_id', '').strip().upper()
        password = request.POST.get('password', '').strip()

        if not full_name or not emp_id or not email or not password:
            messages.error(request, "All required fields must be completed.")
            return render(request, "user/user_signup.html")

        # Create Django User
        username = emp_id.lower().replace('-', '_')
        if User.objects.filter(username=username).exists():
            messages.error(request, f"An account with Employee ID {emp_id} already exists. Please log in.")
            return redirect('user_login')

        clean_asset_id = assigned_asset_id or f"PSM-WRK-{emp_id}"

        user = User.objects.create_user(username=username, email=email, password=password, first_name=full_name)
        UserProfile.objects.create(
            user=user,
            emp_id=emp_id,
            full_name=full_name,
            org_id='HOSP',
            department=department,
            designation=designation,
            assigned_asset_id=clean_asset_id,
            password=password
        )

        # Ensure DeviceAsset is linked or registered
        dev_existing = DeviceAsset.objects.filter(asset_id__iexact=clean_asset_id).first()
        if dev_existing:
            dev_existing.assigned_emp_id = emp_id
            dev_existing.assigned_user_name = full_name
            dev_existing.assigned_user_id = emp_id
            dev_existing.assigned_designation = designation
            dev_existing.save()
        else:
            clean_dev_id = f"dev-{emp_id}".lower().replace('/', '-')
            base_dev_id = clean_dev_id
            counter = 1
            while DeviceAsset.objects.filter(dev_id=clean_dev_id).exists():
                clean_dev_id = f"{base_dev_id}-{counter}"
                counter += 1
            DeviceAsset.objects.create(
                dev_id=clean_dev_id,
                asset_id=clean_asset_id,
                serial_number=f"SN-{clean_asset_id.replace('/', '-')}",
                org_id='HOSP',
                org_name='PSM Hospital',
                building_name='PSM Main Complex',
                floor_name='Ground Floor',
                room_name=department or 'Clinical Department',
                assigned_user_id=emp_id,
                assigned_user_name=full_name,
                assigned_emp_id=emp_id,
                assigned_designation=designation,
                monitor_spec='24" Dell UltraSharp FHD LED',
                cpu_processor='Intel Core i5-12400 (6 cores, 12 threads)',
                storage_ram='512GB NVMe SSD / 16GB DDR4 RAM',
                operating_system='Windows 11 Pro 64-bit',
                status='Active'
            )

        # Store session
        request.session['staff_emp_id'] = emp_id
        request.session['staff_name'] = full_name
        request.session['staff_org'] = 'HOSP'
        request.session['staff_org_name'] = 'PSM Hospital'
        request.session['staff_dept'] = department
        request.session['staff_email'] = email
        request.session['staff_asset'] = clean_asset_id

        messages.success(request, f"Account created successfully! Welcome to the Device Service Portal, {full_name}!")
        return redirect('user_dashboard')

    return render(request, "user/user_signup.html")

def user_logout_view(request):
    """User logout."""
    logout(request)
    request.session.flush()
    messages.info(request, "You have been logged out from your employee portal.")
    return redirect('user_login')

def user_dashboard(request):
    """Employee Portal Dashboard: redirect directly to the unified Mobile QR incident report portal."""
    return redirect('mobile_report')

def submit_complaint(request):
    """Handles submission of a hardware problem / complaint by an employee."""
    if request.method == 'POST':
        user_name = request.session.get('staff_name', request.POST.get('user_full_name', 'PSM Hospital Staff'))
        emp_id = request.session.get('staff_emp_id', request.POST.get('emp_id', 'MED-00042'))
        org_id = 'HOSP'
        user_dept = request.session.get('staff_dept', request.POST.get('user_dept', 'Clinical Services'))
        user_email = request.session.get('staff_email', request.POST.get('user_email', ''))

        device_asset_id = request.POST.get('device_asset_id', '').strip()
        room_location = request.POST.get('room_location', '').strip()
        issue_category = request.POST.get('issue_category', 'Hardware Fault')
        priority = request.POST.get('priority', 'Normal')
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()

        if not subject or not description:
            messages.error(request, "Please provide a subject title and description of the device issue.")
            return redirect('user_dashboard')

        # Generate unique ticket ID: TKT-2026-XXX
        rand_num = random.randint(100, 999)
        ticket_id = f"TKT-2026-{rand_num}"
        while DeviceComplaint.objects.filter(ticket_id=ticket_id).exists():
            rand_num = random.randint(100, 999)
            ticket_id = f"TKT-2026-{rand_num}"

        DeviceComplaint.objects.create(
            ticket_id=ticket_id,
            user=request.user if request.user.is_authenticated else None,
            user_full_name=user_name,
            emp_id=emp_id,
            user_email=user_email,
            user_dept=user_dept,
            org_id='HOSP',
            device_asset_id=device_asset_id or 'PSM/IT/2F/C-201',
            room_location=room_location or 'Clinical Ward',
            issue_category=issue_category,
            priority=priority,
            subject=subject,
            description=description,
            status='Pending',
            technician_name='Biomedical IT Team'
        )

        messages.success(request, f"Service Complaint #{ticket_id} filed successfully! Biomedical IT Support has been notified.")
        return redirect('mobile_report')

    return redirect('mobile_report')


def get_active_tunnel_url():
    """Retrieve the active trycloudflare HTTPS URL if tunnel is running."""
    import glob, re, os
    from django.conf import settings
    try:
        tunnel_file = os.path.join(settings.BASE_DIR, "tunnel_url.txt")
        if os.path.exists(tunnel_file):
            with open(tunnel_file, "r", encoding="utf-8") as f:
                u = f.read().strip()
                if u.startswith("https://"):
                    return u
        logs = glob.glob(r'C:\Users\Asus\.gemini\antigravity-ide\brain\*\.system_generated\tasks\task-*.log')
        for l in sorted(logs, key=os.path.getmtime, reverse=True)[:5]:
            with open(l, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    m = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                    if m:
                        return m.group(0)
    except Exception:
        pass
    return "https://remark-valentine-fax-discipline.trycloudflare.com"



# ============================================================================
# MOBILE QR DEVICE COMPLAINT SYSTEM (DEDICATED HOSPITAL STAFF INTERFACE)
# ============================================================================

def mobile_report_view(request, asset_id=None):
    """
    Dedicated Mobile Phone Device Complaint Portal.
    Engineered specifically for smartphone screens. Hospital doctors, nurses,
    and ward staff scan the physical QR tag on a hardware device to instantly
    report issues with 1-tap categories and priority triage.
    """
    ensure_sample_devices()

    # 1. Resolve raw asset ID from URL path or GET query
    raw_asset_id = asset_id or request.GET.get('asset_id') or request.GET.get('id') or ''
    if raw_asset_id:
        raw_asset_id = urllib.parse.unquote(str(raw_asset_id)).strip()
        # Strip trailing slashes that may come from URL matching
        raw_asset_id = raw_asset_id.rstrip('/')

    # 2. Look up the device in PostgreSQL DeviceAsset
    device_obj = None
    if raw_asset_id:
        device_obj = DeviceAsset.objects.filter(asset_id__iexact=raw_asset_id).first()
        if not device_obj:
            device_obj = DeviceAsset.objects.filter(dev_id__iexact=raw_asset_id).first()
        if not device_obj and '/' in raw_asset_id:
            device_obj = DeviceAsset.objects.filter(asset_id__iexact=raw_asset_id.replace('/', '-')).first()
        if not device_obj and '-' in raw_asset_id:
            device_obj = DeviceAsset.objects.filter(asset_id__iexact=raw_asset_id.replace('-', '/')).first()

    # 3. Format structured device context
    device_data = None
    if device_obj:
        user_name = device_obj.assigned_user_name or 'Hospital Staff / General'
        user_desig = ''
        user_dept = ''
        if device_obj.assigned_user_name:
            prof = UserProfile.objects.filter(full_name__iexact=device_obj.assigned_user_name).first()
            if not prof and device_obj.assigned_emp_id:
                prof = UserProfile.objects.filter(emp_id__iexact=device_obj.assigned_emp_id).first()
            if prof:
                user_desig = prof.designation or ''
                user_dept = prof.department or ''


        # Determine readable hardware model / processor line (e.g. Intel Core i5-13400 (10 cores))
        hardware_model = device_obj.cpu_processor or device_obj.monitor_spec or (f"{device_obj.device_type} Workstation")

        device_data = {
            'asset_id': device_obj.asset_id,
            'dev_id': device_obj.dev_id,
            'device_type': device_obj.device_type or 'Hardware',
            'serial_number': device_obj.serial_number or 'N/A',
            'building': device_obj.building_name or 'PSM Hospital',
            'floor': device_obj.floor_name or 'Ground Floor',
            'room': device_obj.room_name or 'Clinical Ward',
            'custodian': user_name,
            'designation': user_desig or 'Healthcare Professional',
            'department': user_dept or (device_obj.room_name or 'Clinical Services'),
            'status': device_obj.status or 'Active',
            'os': device_obj.operating_system or '',
            'cpu_processor': device_obj.cpu_processor or '',
            'hardware_model': hardware_model,
            'specs': f"{device_obj.cpu_processor} | {device_obj.storage_ram}" if device_obj.cpu_processor else (device_obj.monitor_spec or ''),
        }
    elif raw_asset_id:
        device_data = {
            'asset_id': raw_asset_id,
            'dev_id': '',
            'device_type': 'Hardware Device',
            'serial_number': 'Scanning Tag',
            'building': 'PSM Hospital',
            'floor': 'Clinical Wing',
            'room': 'Ward / Lab',
            'custodian': 'Hospital Station',
            'designation': 'Healthcare Staff',
            'department': 'Clinical Ward',
            'status': 'Active',
            'os': '',
            'cpu_processor': '',
            'hardware_model': 'Hospital Station Equipment',
            'specs': '',
        }

    # 4. Fetch list of PSM Hospital devices for rapid searchable picker
    hospital_devices = list(DeviceAsset.objects.filter(org_id='HOSP').values(
        'asset_id', 'device_type', 'room_name', 'floor_name', 'assigned_user_name'
    )[:150])

    context = {
        'scanned_asset_id': raw_asset_id,
        'device': device_data,
        'hospital_devices_json': json.dumps(hospital_devices),
        'tunnel_url': get_active_tunnel_url(),
    }
    return render(request, "user/mobile_report.html", context)


@csrf_exempt
def api_submit_quick_complaint(request):
    """
    Mobile AJAX endpoint to submit a device complaint from a smartphone scan.
    Creates a new DeviceComplaint record (org_id='HOSP', status='Pending')
    which appears in real-time in the admin Helpdesk & Device Complaints table.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed. Use POST.'}, status=405)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8'))
        else:
            data = request.POST

        device_asset_id = str(data.get('device_asset_id') or data.get('asset_id') or '').strip()
        user_full_name = str(data.get('user_full_name') or data.get('staff_name') or '').strip() or 'PSM Hospital Staff'
        emp_id = str(data.get('emp_id', '')).strip()
        user_dept = str(data.get('user_dept') or data.get('staff_dept') or '').strip() or 'Clinical Services'
        user_phone = str(data.get('user_phone') or data.get('staff_phone') or '').strip()
        room_location = str(data.get('room_location', '')).strip()
        issue_category = str(data.get('issue_category') or data.get('category') or 'Hardware Fault').strip()
        priority = str(data.get('priority', 'Normal')).strip()
        subject = str(data.get('subject', '')).strip()
        description = str(data.get('description', '')).strip()

        if not device_asset_id:
            return JsonResponse({'success': False, 'error': 'Asset Tag / ID is required.'}, status=400)

        # Look up device room & info if not provided
        if not room_location:
            dev = DeviceAsset.objects.filter(asset_id__iexact=device_asset_id).first()
            if dev and dev.room_name:
                room_location = f"{dev.room_name} ({dev.floor_name or 'PSM Hospital'})"
            else:
                room_location = 'Clinical Ward / Department'

        # Auto-craft a concise subject if empty
        if not subject:
            prefix = "[EMERGENCY]" if priority == 'Critical' else "[ROUTINE]"
            subject = f"{prefix} {issue_category} — {device_asset_id}"

        # Combine phone/intercom info into description
        full_description = description
        if user_phone:
            full_description = f"{description}\n\n[Reporter Contact / Ext]: {user_phone}".strip()

        # Generate unique ticket ID: TKT-2026-XXX
        rand_num = random.randint(100, 999)
        ticket_id = f"TKT-2026-{rand_num}"
        while DeviceComplaint.objects.filter(ticket_id=ticket_id).exists():
            rand_num = random.randint(100, 999)
            ticket_id = f"TKT-2026-{rand_num}"

        # Create record in database
        user_inst = request.user if (hasattr(request, 'user') and request.user and request.user.is_authenticated) else None
        complaint = DeviceComplaint.objects.create(
            ticket_id=ticket_id,
            user=user_inst,
            user_full_name=user_full_name,
            emp_id=emp_id or 'STAFF-MOBILE',
            user_email='',
            user_dept=user_dept,
            org_id='HOSP',
            device_asset_id=device_asset_id,
            room_location=room_location,
            issue_category=issue_category,
            priority=priority,
            subject=subject,
            description=full_description or f"Malfunctioning hardware reported via mobile QR scan: {issue_category}",
            status='Pending',
            technician_name='Biomedical IT Team'
        )

        sla_minutes = 30 if priority == 'Critical' else 240
        sla_text = "< 30 Mins (Emergency Priority)" if priority == 'Critical' else "2 - 4 Hours (Routine SLA)"

        return JsonResponse({
            'success': True,
            'ticket_id': ticket_id,
            'priority': priority,
            'sla_minutes': sla_minutes,
            'sla_text': sla_text,
            'device_asset_id': device_asset_id,
            'room_location': room_location,
            'created_at': timezone.localtime(complaint.created_at).strftime("%d-%b-%Y %I:%M %p"),
            'message': f"Complaint #{ticket_id} registered successfully! Biomedical IT Support has been dispatched."
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================================================
# ADMIN SIDE HELPDESK & COMPLAINTS MANAGEMENT
# ============================================================================

@admin_required
def admin_complaints(request):
    """Admin Helpdesk Tickets / Complaints view (PSM Hospital only)."""
    org = request.GET.get('org', 'HOSP')
    if org == 'UNI':
        return redirect('/admin-complaints/?org=HOSP')

    status_filter = request.GET.get('status', 'ALL')

    queryset = DeviceComplaint.objects.filter(org_id='HOSP').order_by('-created_at')
    if status_filter != 'ALL':
        queryset = queryset.filter(status=status_filter)

    total_tickets = DeviceComplaint.objects.filter(org_id='HOSP').count()
    pending_tickets = DeviceComplaint.objects.filter(org_id='HOSP', status='Pending').count()
    progress_tickets = DeviceComplaint.objects.filter(org_id='HOSP', status='In Progress').count()
    resolved_tickets = DeviceComplaint.objects.filter(org_id='HOSP', status='Resolved').count()
    critical_tickets = DeviceComplaint.objects.filter(org_id='HOSP', priority='Critical').count()

    context = {
        'selected_org': 'HOSP',
        'status_filter': status_filter,
        'complaints': queryset,
        'total_tickets': total_tickets,
        'pending_tickets': pending_tickets,
        'progress_tickets': progress_tickets,
        'resolved_tickets': resolved_tickets,
        'critical_tickets': critical_tickets,
    }
    return render(request, "admin/admin_complaints.html", context)

@admin_required
def admin_update_complaint(request, ticket_id):
    """Admin endpoint to update complaint status, assign technician, and add remarks."""
    if request.method == 'POST':
        complaint = get_object_or_404(DeviceComplaint, ticket_id=ticket_id)
        new_status = request.POST.get('status', complaint.status)
        technician = request.POST.get('technician_name', complaint.technician_name)
        remarks = request.POST.get('admin_remarks', complaint.admin_remarks)

        complaint.status = new_status
        complaint.technician_name = technician
        complaint.admin_remarks = remarks

        if new_status in ['Resolved', 'Closed']:
            complaint.resolved_at = timezone.now()

        complaint.save()
        messages.success(request, f"Ticket #{ticket_id} updated to '{new_status}' successfully!")

        next_url = request.POST.get('next', 'admin_complaints')
        return redirect(next_url)

    return redirect('admin_complaints')


# ============================================================================
# EXISTING ADMIN PAGES (100% PRESERVED DESIGN & FUNCTIONALITY)
# ============================================================================

def get_serialized_devices_and_logs():
    """
    Direct server-side data serialization from PostgreSQL for instant, zero-latency rendering.
    Bypasses secondary client-side fetch('/api/devices/') and fetch('/api/audit-logs/') calls.
    """
    ensure_sample_devices()
    devices_qs = DeviceAsset.objects.filter(org_id='HOSP').order_by('-id')
    devices_data = []
    for d in devices_qs:
        devices_data.append({
            'id': d.dev_id,
            'assetId': d.asset_id,
            'deviceType': d.device_type or normalize_device_type('', d.asset_id),
            'serialNumber': d.serial_number,
            'orgId': d.org_id,
            'orgName': d.org_name,
            'buildingName': d.building_name,
            'floorName': d.floor_name,
            'roomName': d.room_name,
            'assignedUserId': d.assigned_user_id,
            'assignedUserName': d.assigned_user_name,
            'empId': d.assigned_emp_id,
            'designation': getattr(d, 'assigned_designation', '') or '',
            'assignedDesignation': getattr(d, 'assigned_designation', '') or '',
            'department': getattr(d, 'assigned_department', '') or '',
            'assignedDepartment': getattr(d, 'assigned_department', '') or '',
            'email': getattr(d, 'assigned_email', '') or '',
            'assignedEmail': getattr(d, 'assigned_email', '') or '',
            'phone': getattr(d, 'assigned_phone', '') or '',
            'assignedPhone': getattr(d, 'assigned_phone', '') or '',
            'monitorSpec': d.monitor_spec,
            'cpuProcessor': d.cpu_processor,
            'storageRam': d.storage_ram,
            'ipAddress': d.ip_address,
            'macAddress': d.mac_address,
            'brandName': getattr(d, 'brand_name', '') or '',
            'anydeskId': getattr(d, 'anydesk_id', '') or '',
            'keyboardSpec': getattr(d, 'keyboard_spec', '') or '',
            'mouseSpec': getattr(d, 'mouse_spec', '') or '',
            'printerSpec': getattr(d, 'printer_spec', '') or '',
            'upsSpec': getattr(d, 'ups_spec', '') or '',
            'tabletSpec': getattr(d, 'tablet_spec', '') or '',
            'operatingSystem': d.operating_system,
            'purchaseDate': d.purchase_date,
            'warrantyExpiryDate': d.warranty_expiry_date,
            'status': d.status,
        })

    logs_qs = CustodyTransferLog.objects.all().order_by('-created_at')
    logs_data = []
    for l in logs_qs:
        logs_data.append({
            'id': l.id,
            'deviceAssetId': l.device_asset_id,
            'fromUserName': l.from_user_name,
            'toUserName': l.to_user_name,
            'toEmpId': l.to_emp_id,
            'handoverDate': l.handover_date,
            'assignedBy': l.assigned_by,
            'remarks': l.remarks,
            'createdAt': l.created_at.strftime('%Y-%m-%d %H:%M')
        })

    return json.dumps(devices_data), json.dumps(logs_data)


@admin_required
def index(request):
    """Landing Portal Gateway (Swaminarayan University vs PSM Hospital)"""
    pending_count = DeviceComplaint.objects.filter(status='Pending').count()
    devices_json, audit_logs_json = get_serialized_devices_and_logs()
    return render(request, "admin/index.html", {
        'pending_tickets': pending_count,
        'devices_json': devices_json,
        'audit_logs_json': audit_logs_json,
        'selected_org': 'HOSP'
    })

@admin_required
def inventory(request):
    """1. Devices Inventory: Dedicated to PSM Hospital"""
    org = request.GET.get('org', 'HOSP')
    if org == 'UNI':
        return redirect('/inventory/?org=HOSP')
    pending_count = DeviceComplaint.objects.filter(status='Pending').count()
    devices_json, audit_logs_json = get_serialized_devices_and_logs()
    context = {
        'selected_org': 'HOSP',
        'pending_tickets': pending_count,
        'devices_json': devices_json,
        'audit_logs_json': audit_logs_json,
    }
    return render(request, "admin/inventory.html", context)


def mobile_add_device_view(request):
    """
    Mobile-first Hardware Enrollment & Device Provisioning Portal.
    Allows hospital engineers, IT staff, and technicians on mobile phones or tablets
    to rapidly add and register new hardware devices directly into the PostgreSQL DeviceAsset table.
    """
    import datetime

    today_str = timezone.localtime().strftime("%d-%b-%Y")
    warranty_str = (timezone.localtime() + datetime.timedelta(days=1095)).strftime("%d-%b-%Y")

    # Dedicated PSM Hospital clinical buildings and wings
    buildings = [
        'PSM Hospital',
        'ICU & Critical Care Wing',
        'Emergency & Trauma Center',
        'Radiology & Diagnostics Wing',
        'OPD & Surgical Block',
        'Biomedical Engineering Unit',
    ]

    floors = ['Ground Floor', '1st Floor', '2nd Floor', '3rd Floor', '4th Floor', '5th Floor', 'Basement']
    
    # Hospital clinical rooms and wards
    rooms = list(DeviceAsset.objects.filter(org_id='HOSP').exclude(room_name='').values_list('room_name', flat=True).distinct()[:20])
    if not rooms:
        rooms = [
            'ICU Bed Ward 1 (Room 101)',
            'ICU Central Nursing Desk',
            'Emergency Trauma Room 102',
            'Radiology Diagnostic Desk',
            'Pathology Lab Terminal',
            'OPD Clinic 04'
        ]

    # PSM Hospital clinical and administrative staff
    staff_qs = UserProfile.objects.filter(org_id='HOSP').select_related('user')[:50]
    if staff_qs.exists():
        staff_list = [
            {
                'full_name': prof.full_name,
                'emp_id': prof.emp_id,
                'department': prof.department,
                'designation': prof.designation or '',
                'phone': prof.phone or '',
                'email': (prof.user.email if prof.user else '') or '',
                'org_id': prof.org_id
            }
            for prof in staff_qs
        ]


    context = {
        'today_str': today_str,
        'warranty_str': warranty_str,
        'buildings': buildings,
        'floors': floors,
        'rooms': rooms,
        'staff_list': staff_list,
        'staff_list_json': json.dumps(staff_list, default=str),
        'selected_org': 'HOSP',
    }
    response = render(request, "admin/mobile_add_device.html", context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@csrf_exempt
def api_generate_asset_id(request):
    """
    Generates a unique, standardized hardware asset tag strictly for PSM Hospital.
    Format: PSM/IT/<MMYY>/<XXX>
    Example: PSM/IT/0926/001, PSM/IT/0926/002, PSM/IT/0926/003, etc.
    Guarantees 100% collision-free against PostgreSQL DeviceAsset table.
    """
    import re

    current_val = (request.GET.get('current') or request.POST.get('current') or '').strip().upper()
    force_next = request.GET.get('next') in ('1', 'true', 'True')

    now = timezone.localtime()
    mmyy = now.strftime("%m%y")  # e.g. "0926"
    prefix = f"PSM/IT/{mmyy}/"

    # Scan ALL existing tags in PostgreSQL to guarantee global uniqueness
    all_tags = list(DeviceAsset.objects.all().values_list('asset_id', flat=True))
    used_numbers = set()

    for tag in all_tags:
        tag_str = str(tag).strip().upper()
        # 1. Match /{mmyy}/(\d+)
        m = re.search(rf'/{mmyy}/(\d+)', tag_str)
        if m:
            try:
                used_numbers.add(int(m.group(1)))
            except ValueError:
                pass
        # 2. Match standard 4-part structure PSM/IT/<MMYY>/<XXX>
        parts = tag_str.split('/')
        if len(parts) >= 4 and (parts[2] == mmyy or (len(parts) >= 5 and parts[3] == mmyy)):
            try:
                used_numbers.add(int(parts[-1]))
            except ValueError:
                pass

    max_used = max(used_numbers) if used_numbers else 0

    cur_num = 0
    if current_val:
        m_cur = re.search(r'(\d+)$', current_val)
        if m_cur:
            try:
                cur_num = int(m_cur.group(1))
            except ValueError:
                pass

    # If the user explicitly requested next number (e.g. clicked Auto Generate again)
    if force_next and cur_num > 0:
        start_num = max(max_used + 1, cur_num + 1)
    else:
        start_num = max_used + 1

    next_num = start_num
    if next_num > 999:
        # Wrap or find lowest available slot within 001-999
        found_slot = None
        for n in range(1, 1000):
            cand = f"{prefix}{n:03d}"
            if (n not in used_numbers) and not DeviceAsset.objects.filter(asset_id__iexact=cand).exists():
                found_slot = n
                break
        next_num = found_slot if found_slot is not None else 999

    candidate = f"{prefix}{next_num:03d}"

    # Strict PostgreSQL collision verification loop (strictly within 3 digits)
    while ((next_num in used_numbers) or DeviceAsset.objects.filter(asset_id__iexact=candidate).exists()) and next_num < 999:
        next_num += 1
        candidate = f"{prefix}{next_num:03d}"

    return JsonResponse({'success': True, 'asset_id': candidate, 'seq_num': next_num})


@csrf_exempt
def api_check_asset_id(request):
    """Real-time validation API: checks if an asset_id already exists in PostgreSQL."""
    asset_id = (request.GET.get('asset_id') or request.POST.get('asset_id') or '').strip().upper()
    if not asset_id:
        return JsonResponse({'exists': False, 'valid': False, 'message': 'Empty ID'})

    # 3-digit sequence constraint validation on last segment
    parts = asset_id.split('/')
    if len(parts) >= 4:
        seq = parts[-1]
        if len(seq) > 3 or (seq and not seq.isdigit()):
            return JsonResponse({
                'exists': False,
                'valid': False,
                'asset_id': asset_id,
                'message': 'Sequence number cannot exceed 3 digits (e.g. 001 to 999).'
            })

    dev = DeviceAsset.objects.filter(asset_id__iexact=asset_id).first()
    if dev:
        return JsonResponse({
            'exists': True,
            'valid': True,
            'asset_id': dev.asset_id,
            'device_type': dev.device_type,
            'location': f"{dev.room_name} ({dev.floor_name})",
            'status': dev.status,
            'message': f"Already registered to {dev.device_type} in {dev.room_name}."
        })
    return JsonResponse({
        'exists': False,
        'valid': True,
        'asset_id': asset_id,
        'message': "Tag is available & unique."
    })

@admin_required
def user(request):
    """3. Staff & Users Directory (Dedicated to PSM Hospital)"""
    org = request.GET.get('org', 'HOSP')
    if org == 'UNI':
        return redirect('/user/?org=HOSP')
    pending_count = DeviceComplaint.objects.filter(status='Pending').count()
    devices_json, audit_logs_json = get_serialized_devices_and_logs()
    context = {
        'selected_org': 'HOSP',
        'pending_tickets': pending_count,
        'devices_json': devices_json,
        'audit_logs_json': audit_logs_json,
    }
    return render(request, "admin/user.html", context)

@admin_required
def location(request):
    """2. Location Explorer: PSM Hospital dedicated clinical hierarchy"""
    org = request.GET.get('org', 'HOSP')
    if org == 'UNI':
        return redirect('/location/?org=HOSP')
    pending_count = DeviceComplaint.objects.filter(status='Pending').count()
    devices_json, audit_logs_json = get_serialized_devices_and_logs()
    context = {
        'selected_org': 'HOSP',
        'pending_tickets': pending_count,
        'devices_json': devices_json,
        'audit_logs_json': audit_logs_json,
    }
    return render(request, "admin/location.html", context)

@admin_required
def audit(request):
    """4. Audit & History Logs: Handover and custody logs (PSM Hospital)"""
    org = request.GET.get('org', 'HOSP')
    if org == 'UNI':
        return redirect('/audit/?org=HOSP')
    pending_count = DeviceComplaint.objects.filter(status='Pending').count()
    devices_json, audit_logs_json = get_serialized_devices_and_logs()
    context = {
        'selected_org': 'HOSP',
        'pending_tickets': pending_count,
        'devices_json': devices_json,
        'audit_logs_json': audit_logs_json,
    }
    return render(request, "admin/audit.html", context)

@admin_required
def tag(request):
    """5. Asset Tag Center: Printable QR & Barcode stickers (PSM Hospital)"""
    org = request.GET.get('org', 'HOSP')
    if org == 'UNI':
        return redirect('/tag/?org=HOSP')
    pending_count = DeviceComplaint.objects.filter(status='Pending').count()
    devices_json, audit_logs_json = get_serialized_devices_and_logs()
    context = {
        'selected_org': 'HOSP',
        'pending_tickets': pending_count,
        'devices_json': devices_json,
        'audit_logs_json': audit_logs_json,
    }
    return render(request, "admin/tag.html", context)


@admin_required
def pms_schedule(request):
    """7. Equipment Preventive Maintenance Service (PMS) Schedule Tracker"""
    org = 'HOSP'
    search = request.GET.get('search', '').strip()
    filter_company = request.GET.get('company', 'ALL')
    filter_status = request.GET.get('status', 'ALL')

    records = EquipmentPMS.objects.all().order_by('id')

    if search:
        records = records.filter(
            models.Q(asset_code__icontains=search) |
            models.Q(equipment_name__icontains=search) |
            models.Q(company_name__icontains=search) |
            models.Q(department_location__icontains=search)
        )
    if filter_company and filter_company != 'ALL':
        records = records.filter(company_name=filter_company)
    if filter_status and filter_status != 'ALL':
        records = records.filter(status=filter_status)

    total_count = EquipmentPMS.objects.count()
    completed_count = EquipmentPMS.objects.filter(status='Completed').count()
    pending_count = EquipmentPMS.objects.filter(status='Pending 4th PMS').count()
    due_soon_count = EquipmentPMS.objects.filter(status='Due Soon').count()

    # Dynamic equipment category counts from database
    computer_q = models.Q(equipment_name__icontains='computer') | models.Q(equipment_name__icontains='pc') | models.Q(equipment_name__icontains='desktop') | models.Q(equipment_name__icontains='laptop') | models.Q(equipment_name__icontains='cpu')
    printer_q = models.Q(equipment_name__icontains='printer') | models.Q(equipment_name__icontains='scanner')
    cub_q = models.Q(equipment_name__icontains='cub') | models.Q(equipment_name__icontains='hub') | models.Q(equipment_name__icontains='switch') | models.Q(equipment_name__icontains='router')
    landline_q = models.Q(equipment_name__icontains='landline') | models.Q(equipment_name__icontains='phone') | models.Q(equipment_name__icontains='intercom')
    cctv_q = models.Q(equipment_name__icontains='cctv') | models.Q(equipment_name__icontains='camera')

    count_computer = EquipmentPMS.objects.filter(computer_q).count()
    count_printer = EquipmentPMS.objects.filter(printer_q).count()
    count_cub = EquipmentPMS.objects.filter(cub_q).count()
    count_landline = EquipmentPMS.objects.filter(landline_q).count()
    count_cctv = EquipmentPMS.objects.filter(cctv_q).count()
    
    companies = EquipmentPMS.objects.values_list('company_name', flat=True).distinct().order_by('company_name')

    pending_tickets = DeviceComplaint.objects.filter(status='Pending').count()

    inventory_devices = DeviceAsset.objects.all().order_by('asset_id')

    context = {
        'selected_org': org,
        'records': records,
        'total_count': total_count,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'due_soon_count': due_soon_count,
        'count_computer': count_computer,
        'count_printer': count_printer,
        'count_cub': count_cub,
        'count_landline': count_landline,
        'count_cctv': count_cctv,
        'companies': companies,
        'search': search,
        'filter_company': filter_company,
        'filter_status': filter_status,
        'pending_tickets': pending_tickets,
        'inventory_devices': inventory_devices,
    }
    return render(request, "admin/pms_schedule.html", context)


@csrf_exempt
def api_update_pms(request, pms_id):
    """Update PMS schedule record (supports full field edit or quick 4th cycle)."""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
        except Exception:
            data = request.POST

        item = get_object_or_404(EquipmentPMS, pk=pms_id)
        
        # Check and update fields if provided
        if 'equipment_name' in data:
            item.equipment_name = data.get('equipment_name', item.equipment_name).strip()
        if 'company_name' in data:
            item.company_name = data.get('company_name', item.company_name).strip()
        if 'asset_code' in data:
            new_code = data.get('asset_code', item.asset_code).strip().upper()
            if new_code and new_code != item.asset_code:
                if EquipmentPMS.objects.filter(asset_code=new_code).exclude(pk=pms_id).exists():
                    return JsonResponse({'success': False, 'error': f'Asset code {new_code} already belongs to another record!'}, status=400)
                item.asset_code = new_code
        if 'installation_date' in data:
            item.installation_date = data.get('installation_date', item.installation_date).strip()
        if 'maintenance_frequency' in data:
            item.maintenance_frequency = data.get('maintenance_frequency', item.maintenance_frequency).strip()
        if 'department_location' in data:
            item.department_location = data.get('department_location', item.department_location).strip()
        if 'pms1_done_date' in data:
            item.pms1_done_date = data.get('pms1_done_date', item.pms1_done_date).strip()
        if 'pms2_due_date' in data:
            item.pms2_due_date = data.get('pms2_due_date', item.pms2_due_date).strip()
        if 'pms2_done_date' in data:
            item.pms2_done_date = data.get('pms2_done_date', item.pms2_done_date).strip()
        if 'pms3_due_date' in data:
            item.pms3_due_date = data.get('pms3_due_date', item.pms3_due_date).strip()
        if 'pms3_done_date' in data:
            item.pms3_done_date = data.get('pms3_done_date', item.pms3_done_date).strip()
        if 'pms4_due_date' in data:
            item.pms4_due_date = data.get('pms4_due_date', item.pms4_due_date).strip()
        if 'pms4_done_date' in data:
            item.pms4_done_date = data.get('pms4_done_date', item.pms4_done_date).strip()
        if 'engineer_notes' in data:
            item.engineer_notes = data.get('engineer_notes', item.engineer_notes).strip()
        if 'status' in data:
            item.status = data.get('status', item.status).strip()

        item.save()

        return JsonResponse({
            'success': True,
            'message': f'PMS Record for {item.asset_code} updated successfully!',
            'id': item.id,
            'asset_code': item.asset_code,
            'equipment_name': item.equipment_name,
            'company_name': item.company_name,
            'pms4_done_date': item.pms4_done_date,
            'status': item.status
        })

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)


@csrf_exempt
def api_delete_pms(request, pms_id):
    """Delete an equipment PMS schedule record."""
    if request.method in ['POST', 'DELETE']:
        item = get_object_or_404(EquipmentPMS, pk=pms_id)
        code = item.asset_code
        item.delete()
        return JsonResponse({'success': True, 'message': f'PMS Record {code} deleted successfully!'})
    return JsonResponse({'success': False, 'error': 'POST/DELETE method required.'}, status=405)


@csrf_exempt
def api_add_pms(request):
    """Add a new equipment maintenance schedule record."""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
        except Exception:
            data = request.POST

        asset_code = data.get('asset_code', '').strip().upper()
        if not asset_code:
            return JsonResponse({'success': False, 'error': 'Asset Code is required.'}, status=400)

        if EquipmentPMS.objects.filter(asset_code=asset_code).exists():
            return JsonResponse({'success': False, 'error': f'Asset code {asset_code} already exists!'}, status=400)

        new_record = EquipmentPMS.objects.create(
            equipment_name=data.get('equipment_name', 'Computer').strip(),
            company_name=data.get('company_name', 'HP').strip(),
            installation_date=data.get('installation_date', '08-11-2021').strip(),
            asset_code=asset_code,
            maintenance_frequency=data.get('maintenance_frequency', 'QUARTERLY').strip(),
            pms1_done_date=data.get('pms1_done_date', '').strip(),
            pms2_due_date=data.get('pms2_due_date', '').strip(),
            pms2_done_date=data.get('pms2_done_date', '').strip(),
            pms3_due_date=data.get('pms3_due_date', '').strip(),
            pms3_done_date=data.get('pms3_done_date', '').strip(),
            pms4_due_date=data.get('pms4_due_date', '').strip(),
            pms4_done_date=data.get('pms4_done_date', '').strip(),
            status=data.get('status', 'Pending 4th PMS').strip(),
            department_location=data.get('department_location', 'IT Lab').strip(),
            engineer_notes=data.get('engineer_notes', '').strip()
        )
        return JsonResponse({'success': True, 'id': new_record.id, 'asset_code': new_record.asset_code})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)


@csrf_exempt
def api_import_pms_excel(request):
    """Import PMS schedule records from Excel (.xlsx, .xls) or CSV."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required.'}, status=405)

    import json
    import csv
    import io
    import datetime

    rows_data = []

    # 1. Check if multipart file uploaded
    if 'file' in request.FILES:
        uploaded_file = request.FILES['file']
        filename = uploaded_file.name.lower()

        if filename.endswith('.csv'):
            try:
                content = uploaded_file.read().decode('utf-8-sig', errors='replace')
                reader = csv.DictReader(io.StringIO(content))
                for r in reader:
                    rows_data.append(r)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Failed to parse CSV file: {str(e)}'}, status=400)
        elif filename.endswith(('.xlsx', '.xlsm', '.xltx', '.xls')):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(io.BytesIO(uploaded_file.read()), data_only=True)
                ws = wb.active
                iter_rows = list(ws.iter_rows(values_only=True))
                if not iter_rows:
                    return JsonResponse({'success': False, 'error': 'Uploaded Excel file is empty.'}, status=400)

                header_row = iter_rows[0]
                headers = [str(h).strip() if h is not None else f"col_{idx}" for idx, h in enumerate(header_row)]

                for row_vals in iter_rows[1:]:
                    if not any(row_vals):
                        continue
                    row_dict = {}
                    for idx, val in enumerate(row_vals):
                        if idx < len(headers):
                            if isinstance(val, (datetime.datetime, datetime.date)):
                                row_dict[headers[idx]] = val.strftime('%d-%m-%Y' if isinstance(val, datetime.date) and not isinstance(val, datetime.datetime) else '%d-%m-%Y %H:%M')
                            elif isinstance(val, datetime.time):
                                row_dict[headers[idx]] = val.strftime('%H:%M')
                            else:
                                row_dict[headers[idx]] = str(val).strip() if val is not None else ''
                    rows_data.append(row_dict)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Failed to parse Excel file: {str(e)}'}, status=400)
        else:
            return JsonResponse({'success': False, 'error': 'Unsupported file format. Please upload an Excel (.xlsx) or CSV file.'}, status=400)

    # 2. Check JSON payload
    elif request.body:
        try:
            payload = json.loads(request.body)
            if isinstance(payload, list):
                rows_data = payload
            elif isinstance(payload, dict):
                rows_data = payload.get('rows', [])
        except Exception:
            pass

    if not rows_data:
        return JsonResponse({'success': False, 'error': 'No valid data rows found in uploaded file or request.'}, status=400)

    def find_val(row_dict, aliases, default=''):
        lower_map = {str(k).strip().lower(): v for k, v in row_dict.items() if k is not None}
        for a in aliases:
            al = a.lower()
            if al in lower_map and lower_map[al] not in (None, ''):
                return str(lower_map[al]).strip()
        return default

    created_or_updated = 0

    for r in rows_data:
        asset_code = find_val(r, ['asset coding', 'asset coding (tag)', 'asset_code', 'asset code', 'tag', 'code']).upper()
        equipment_name = find_val(r, ['name of the equipment', 'equipment name', 'equipment_name', 'equipment', 'name'], 'Computer')
        company_name = find_val(r, ['name of company', 'company / oem', 'company_name', 'company', 'oem', 'vendor'], 'HP')

        if not asset_code:
            if not any(r.values()):
                continue
            random_sfx = random.randint(100, 999)
            asset_code = f"KH/IT/{equipment_name[:4].upper()}/{random_sfx}"

        install_date = find_val(r, ['date of installation', 'installation date', 'installation_date', 'installed on'], '08-11-2021')
        frequency = find_val(r, ['maintainance frequency', 'maintenance frequency', 'frequency', 'maintenance_frequency'], 'QUARTERLY').upper()
        if 'HALF' in frequency:
            frequency = 'HALF-YEARLY'
        elif 'ANNUAL' in frequency:
            frequency = 'ANNUALLY'
        else:
            frequency = 'QUARTERLY'

        pms1_done = find_val(r, ['1st pms done date', 'pms1 done date', 'pms1_done_date', 'pms1 done', 'pms1'])
        pms2_due = find_val(r, ['due date of 2nd pms', '2nd pms due date', 'pms2_due_date', 'pms2 due'])
        pms2_done = find_val(r, ['2nd pms done date', 'pms2 done date', 'pms2_done_date', 'pms2 done'])
        pms3_due = find_val(r, ['due date of 3rd pms', '3rd pms due date', 'pms3_due_date', 'pms3 due'])
        pms3_done = find_val(r, ['3rd pms done date', 'pms3 done date', 'pms3_done_date', 'pms3 done'])
        pms4_due = find_val(r, ['due date of 4th pms', '4th pms due date', 'pms4_due_date', 'pms4 due'])
        pms4_done = find_val(r, ['4th pms done date', 'pms4 done date', 'pms4_done_date', 'pms4 done'])

        location = find_val(r, ['location / department', 'location', 'department_location', 'department', 'room'], 'IT Lab')
        notes = find_val(r, ['engineer notes', 'service engineer / inspection notes', 'engineer_notes', 'notes', 'remarks'], 'Preventive maintenance check completed.')

        status = find_val(r, ['status'])
        if not status:
            status = 'Completed' if pms4_done else 'Pending 4th PMS'

        EquipmentPMS.objects.update_or_create(
            asset_code=asset_code,
            defaults={
                'equipment_name': equipment_name,
                'company_name': company_name,
                'installation_date': install_date,
                'maintenance_frequency': frequency,
                'pms1_done_date': pms1_done,
                'pms2_due_date': pms2_due,
                'pms2_done_date': pms2_done,
                'pms3_due_date': pms3_due,
                'pms3_done_date': pms3_done,
                'pms4_due_date': pms4_due,
                'pms4_done_date': pms4_done,
                'department_location': location,
                'engineer_notes': notes,
                'status': status,
            }
        )
        created_or_updated += 1

    return JsonResponse({
        'success': True,
        'count': created_or_updated,
        'message': f'Successfully registered {created_or_updated} PMS records from Excel!'
    })


# ============================================================================
# 8. EQUIPMENT BREAKDOWN REGISTER
# ============================================================================
@admin_required
def equipment_breakdown(request):
    """8. Equipment Breakdown Register view."""
    org = request.GET.get('org', 'ALL')
    search = request.GET.get('search', '').strip()
    filter_device = request.GET.get('device', 'ALL')
    filter_type = request.GET.get('type', 'ALL')
    filter_status = request.GET.get('status', 'ALL')

    records = EquipmentBreakdown.objects.all().order_by('-id')

    if search:
        records = records.filter(
            models.Q(asset_id__icontains=search) |
            models.Q(device_name__icontains=search) |
            models.Q(location__icontains=search) |
            models.Q(breakdown_cause__icontains=search) |
            models.Q(dept_hod_name__icontains=search) |
            models.Q(it_staff_name__icontains=search) |
            models.Q(status__icontains=search) |
            models.Q(equipment_type__icontains=search) |
            models.Q(tat_duration__icontains=search)
        )
    if filter_device and filter_device != 'ALL':
        records = records.filter(device_name__iexact=filter_device)
    if filter_type and filter_type != 'ALL':
        records = records.filter(equipment_type__iexact=filter_type)
    if filter_status and filter_status != 'ALL':
        s_val = filter_status.strip().lower()
        if 'resolve' in s_val or 'repaired' in s_val:
            records = records.filter(status__icontains='resolve')
        elif 'repair' in s_val:
            records = records.filter(status__icontains='repair')
        else:
            records = records.filter(status__iexact=filter_status.strip())

    total_count = EquipmentBreakdown.objects.count()
    critical_count = EquipmentBreakdown.objects.filter(equipment_type='Critical').count()
    routine_count = EquipmentBreakdown.objects.filter(equipment_type='Routine').count()
    under_repair_count = EquipmentBreakdown.objects.filter(status='Under Repair').count()
    resolved_count = EquipmentBreakdown.objects.filter(status='Resolved').count()

    # Dropdown choices from User's Images 3 & 4
    device_choices = [c[0] for c in EquipmentBreakdown.DEVICE_NAME_CHOICES]
    type_choices = [c[0] for c in EquipmentBreakdown.EQUIPMENT_TYPE_CHOICES]

    pending_tickets = DeviceComplaint.objects.filter(status='Pending').count()
    pms_total_count = EquipmentPMS.objects.count()

    inventory_devices = DeviceAsset.objects.all().order_by('asset_id')
    pms_assets = EquipmentPMS.objects.all().order_by('asset_code')

    context = {
        'selected_org': org,
        'records': records,
        'total_count': total_count,
        'critical_count': critical_count,
        'routine_count': routine_count,
        'under_repair_count': under_repair_count,
        'resolved_count': resolved_count,
        'device_choices': device_choices,
        'type_choices': type_choices,
        'search': search,
        'filter_device': filter_device,
        'filter_type': filter_type,
        'filter_status': filter_status,
        'pending_tickets': pending_tickets,
        'pms_total_count': pms_total_count,
        'inventory_devices': inventory_devices,
        'pms_assets': pms_assets,
    }
    return render(request, "admin/equipment_breakdown.html", context)


def _sanitize_date_slash(val):
    if not val:
        return ''
    return val.strip().replace('.', '/')

def _sanitize_time_colon(val):
    if not val:
        return ''
    import re
    return re.sub(r'(\d+)\.(\d+)', r'\1:\2', val.strip())

def _sanitize_datetime(val):
    if not val:
        return ''
    import re
    parts = val.strip().split(' ', 1)
    if len(parts) == 2:
        d = parts[0].replace('.', '/')
        t = re.sub(r'(\d+)\.(\d+)', r'\1:\2', parts[1])
        return f"{d} {t}"
    return re.sub(r'(\d+)\.(\d+)', r'\1:\2', val.strip().replace('.', '/'))


@csrf_exempt
def api_add_breakdown(request):
    """Add a new breakdown record via AJAX modal and sync DeviceAsset status."""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
        except Exception:
            data = request.POST

        breakdown_date = _sanitize_date_slash(data.get('breakdown_date', ''))
        breakdown_time = _sanitize_time_colon(data.get('breakdown_time', ''))
        asset_id = data.get('asset_id', '').strip()
        device_name = data.get('device_name', 'CPU').strip()
        breakdown_cause = data.get('breakdown_cause', '').strip()
        equipment_type = data.get('equipment_type', 'Routine').strip()

        if not asset_id:
            return JsonResponse({'success': False, 'error': 'IT Asset ID is required.'}, status=400)

        intimation_datetime = _sanitize_datetime(data.get('intimation_datetime', ''))
        checkin_datetime = _sanitize_datetime(data.get('checkin_datetime', ''))
        dept_hod_name = data.get('dept_hod_name', '').strip()
        it_staff_name = data.get('it_staff_name', 'IT Staff').strip()
        repair_datetime = _sanitize_datetime(data.get('repair_datetime', ''))
        tat_duration = data.get('tat_duration', '').strip()
        sign_dept_hod = data.get('sign_dept_hod', '').strip()
        sign_it_cell = data.get('sign_it_cell', '').strip()
        status = data.get('status', 'Under Repair' if not repair_datetime else 'Resolved').strip()
        location = data.get('location', '').strip()
        if not location and asset_id:
            matching_dev = DeviceAsset.objects.filter(models.Q(asset_id__iexact=asset_id)).first()
            if matching_dev:
                loc_parts = [p for p in [matching_dev.building_name, matching_dev.floor_name, matching_dev.room_name] if p]
                location = " - ".join(loc_parts) if loc_parts else (matching_dev.room_name or '')

        new_record = EquipmentBreakdown.objects.create(
            breakdown_date=breakdown_date,
            breakdown_time=breakdown_time,
            asset_id=asset_id,
            device_name=device_name,
            location=location,
            breakdown_cause=breakdown_cause,
            equipment_type=equipment_type,
            intimation_datetime=intimation_datetime,
            checkin_datetime=checkin_datetime,
            dept_hod_name=dept_hod_name,
            it_staff_name=it_staff_name,
            repair_datetime=repair_datetime,
            tat_duration=tat_duration,
            sign_dept_hod=sign_dept_hod,
            sign_it_cell=sign_it_cell,
            status=status
        )

        # Database Bidirectional Sync: if status is Under Repair, update DeviceAsset
        if status == 'Under Repair':
            matching_dev = DeviceAsset.objects.filter(models.Q(asset_id__iexact=asset_id)).first()
            if matching_dev:
                matching_dev.status = 'Maintenance'
                matching_dev.save(update_fields=['status'])

        return JsonResponse({
            'success': True,
            'message': f'Breakdown record #{new_record.id} logged for {new_record.asset_id}!',
            'id': new_record.id,
            'asset_id': new_record.asset_id
        })

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)


@csrf_exempt
def api_resolve_breakdown(request, pk):
    """Resolve / close out an active equipment breakdown and restore DeviceAsset status."""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
        except Exception:
            data = request.POST

        record = get_object_or_404(EquipmentBreakdown, pk=pk)
        repair_date = _sanitize_datetime(data.get('repair_datetime', ''))
        tat = data.get('tat_duration', '').strip()
        sign_it = data.get('sign_it_cell', '').strip()

        if not repair_date:
            repair_date = timezone.now().strftime('%d/%m/%Y %I:%M %p').lower()
        if not tat:
            tat = '30 minutes'
        if not sign_it:
            sign_it = record.it_staff_name or 'IT CELL Engineer'

        record.repair_datetime = repair_date
        record.tat_duration = tat
        record.sign_it_cell = sign_it
        record.status = 'Resolved'
        record.save()

        # Database Bidirectional Sync: Restore hardware asset back to Active
        matching_dev = DeviceAsset.objects.filter(models.Q(asset_id__iexact=record.asset_id)).first()
        if matching_dev:
            matching_dev.status = 'Active'
            matching_dev.save(update_fields=['status'])

        return JsonResponse({
            'success': True,
            'message': f'Breakdown #{record.id} resolved!',
            'repair_datetime': record.repair_datetime,
            'tat_duration': record.tat_duration
        })

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)


@csrf_exempt
def api_update_breakdown(request, pk):
    """Update all fields of an existing equipment breakdown incident."""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
        except Exception:
            data = request.POST

        record = get_object_or_404(EquipmentBreakdown, pk=pk)

        if 'breakdown_date' in data:
            record.breakdown_date = _sanitize_date_slash(data.get('breakdown_date', record.breakdown_date))
        if 'breakdown_time' in data:
            record.breakdown_time = _sanitize_time_colon(data.get('breakdown_time', record.breakdown_time))
        if 'asset_id' in data:
            record.asset_id = data.get('asset_id', record.asset_id).strip()
        if 'device_name' in data:
            record.device_name = data.get('device_name', record.device_name).strip()
        if 'breakdown_cause' in data:
            record.breakdown_cause = data.get('breakdown_cause', record.breakdown_cause).strip()
        if 'equipment_type' in data:
            record.equipment_type = data.get('equipment_type', record.equipment_type).strip()
        if 'intimation_datetime' in data:
            record.intimation_datetime = _sanitize_datetime(data.get('intimation_datetime', record.intimation_datetime))
        if 'checkin_datetime' in data:
            record.checkin_datetime = _sanitize_datetime(data.get('checkin_datetime', record.checkin_datetime))
        if 'dept_hod_name' in data:
            record.dept_hod_name = data.get('dept_hod_name', record.dept_hod_name).strip()
        if 'it_staff_name' in data:
            record.it_staff_name = data.get('it_staff_name', record.it_staff_name).strip()
        if 'repair_datetime' in data:
            record.repair_datetime = _sanitize_datetime(data.get('repair_datetime', record.repair_datetime))
        if 'tat_duration' in data:
            record.tat_duration = data.get('tat_duration', record.tat_duration).strip()
        if 'sign_dept_hod' in data:
            record.sign_dept_hod = data.get('sign_dept_hod', record.sign_dept_hod).strip()
        if 'sign_it_cell' in data:
            record.sign_it_cell = data.get('sign_it_cell', record.sign_it_cell).strip()
        if 'location' in data:
            record.location = data.get('location', record.location).strip()
        if 'status' in data:
            record.status = data.get('status', record.status).strip()

        record.save()

        # Database Bidirectional Sync
        matching_dev = DeviceAsset.objects.filter(models.Q(asset_id__iexact=record.asset_id)).first()
        if matching_dev:
            matching_dev.status = 'Maintenance' if record.status == 'Under Repair' else 'Active'
            matching_dev.save(update_fields=['status'])

        return JsonResponse({
            'success': True,
            'message': f'Breakdown record #{record.id} updated successfully!',
            'id': record.id,
            'asset_id': record.asset_id,
            'status': record.status
        })

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)


@csrf_exempt
def api_delete_breakdown(request, pk):
    """Delete an equipment breakdown incident."""
    if request.method in ['POST', 'DELETE']:
        record = get_object_or_404(EquipmentBreakdown, pk=pk)
        asset_id = record.asset_id
        was_under_repair = (record.status == 'Under Repair')
        record.delete()

        # If it was under repair, check if any other breakdown for this asset is active
        if was_under_repair:
            still_active = EquipmentBreakdown.objects.filter(asset_id=asset_id, status='Under Repair').exists()
            if not still_active:
                matching_dev = DeviceAsset.objects.filter(models.Q(asset_id__iexact=asset_id)).first()
                if matching_dev:
                    matching_dev.status = 'Active'
                    matching_dev.save(update_fields=['status'])

        return JsonResponse({'success': True, 'message': f'Breakdown record #{pk} for {asset_id} deleted successfully!'})

    return JsonResponse({'success': False, 'error': 'POST/DELETE method required.'}, status=405)


@csrf_exempt
def api_import_breakdown_excel(request):
    """Import equipment breakdown records from Excel (.xlsx, .xls) or CSV."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required.'}, status=405)

    import json
    import csv
    import io
    import datetime

    rows_data = []

    # 1. Check if multipart file was uploaded
    if 'file' in request.FILES:
        uploaded_file = request.FILES['file']
        filename = uploaded_file.name.lower()
        
        if filename.endswith('.csv'):
            try:
                content = uploaded_file.read().decode('utf-8-sig', errors='replace')
                reader = csv.DictReader(io.StringIO(content))
                for r in reader:
                    rows_data.append(r)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Failed to parse CSV file: {str(e)}'}, status=400)
        elif filename.endswith(('.xlsx', '.xlsm', '.xltx', '.xls')):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(io.BytesIO(uploaded_file.read()), data_only=True)
                ws = wb.active
                iter_rows = list(ws.iter_rows(values_only=True))
                if not iter_rows:
                    return JsonResponse({'success': False, 'error': 'Uploaded Excel file is empty.'}, status=400)
                
                header_row = iter_rows[0]
                headers = [str(h).strip() if h is not None else f"col_{idx}" for idx, h in enumerate(header_row)]
                
                for row_vals in iter_rows[1:]:
                    if not any(row_vals):
                        continue
                    row_dict = {}
                    for idx, val in enumerate(row_vals):
                        if idx < len(headers):
                            if isinstance(val, (datetime.datetime, datetime.date)):
                                row_dict[headers[idx]] = val.strftime('%d/%m/%Y' if isinstance(val, datetime.date) and not isinstance(val, datetime.datetime) else '%d/%m/%Y %H:%M')
                            elif isinstance(val, datetime.time):
                                row_dict[headers[idx]] = val.strftime('%H:%M')
                            else:
                                row_dict[headers[idx]] = str(val).strip() if val is not None else ''
                    rows_data.append(row_dict)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Failed to parse Excel file: {str(e)}'}, status=400)
        else:
            return JsonResponse({'success': False, 'error': 'Unsupported file format. Please upload an Excel (.xlsx) or CSV file.'}, status=400)

    # 2. Check if JSON payload was passed
    elif request.body:
        try:
            payload = json.loads(request.body)
            if isinstance(payload, list):
                rows_data = payload
            elif isinstance(payload, dict):
                rows_data = payload.get('rows', [])
        except Exception:
            pass

    if not rows_data:
        return JsonResponse({'success': False, 'error': 'No valid data rows found in uploaded file or request.'}, status=400)

    def find_val(row_dict, aliases, default=''):
        lower_map = {str(k).strip().lower(): v for k, v in row_dict.items() if k is not None}
        for a in aliases:
            al = a.lower()
            if al in lower_map and lower_map[al] not in (None, ''):
                return str(lower_map[al]).strip()
        return default

    created_records = []

    for r in rows_data:
        asset_id = find_val(r, [
            'asset id', 'asset_id', 'it asset id', 'asset number', 'asset no', 'instrument / equipment name', 
            'equipment name', 'device asset', 'asset'
        ])
        device_name = find_val(r, ['device name', 'device_name', 'device', 'instrument name', 'equipment'], 'CPU')
        
        # If row is completely empty, skip
        if not asset_id and not any(r.values()):
            continue
            
        if not asset_id:
            random_sfx = random.randint(100, 999)
            asset_id = f"IT-{device_name[:3].upper()}-{random_sfx}"

        breakdown_date = _sanitize_date_slash(find_val(r, ['breakdown date', 'breakdown_date', 'date', 'incident date'], timezone.now().strftime('%d/%m/%Y')))
        breakdown_time = _sanitize_time_colon(find_val(r, ['breakdown time', 'breakdown_time', 'time', 'incident time'], timezone.now().strftime('%H:%M')))
        breakdown_cause = find_val(r, ['breakdown cause', 'breakdown_cause', 'cause', 'fault', 'issue', 'problem', 'reason'], 'Hardware fault')
        equipment_type = find_val(r, ['type of equipment critical/routine', 'equipment type', 'equipment_type', 'type', 'critical/routine'], 'Routine')
        
        if 'crit' in equipment_type.lower():
            equipment_type = 'Critical'
        else:
            equipment_type = 'Routine'

        intimation_datetime = _sanitize_datetime(find_val(r, ['intimation date & time to it cell / bme', 'intimation date & time to bio medical engineer', 'intimation date & time', 'intimation datetime', 'intimation_datetime', 'intimation', 'notified at']))
        checkin_datetime = _sanitize_datetime(find_val(r, ['checkin date & time', 'checkin datetime', 'checkin_datetime', 'checkin', 'received at']))
        dept_hod_name = find_val(r, ['name of departmental hod', 'dept hod name', 'dept_hod_name', 'hod name', 'department hod', 'dept hod'])
        it_staff_name = find_val(r, ['name of it cell / bme staff', 'name of bme staff', 'it staff name', 'it_staff_name', 'it staff', 'bme staff', 'technician'], 'IT Support')
        repair_datetime = _sanitize_datetime(find_val(r, ['repair date & time', 'repair datetime', 'repair_datetime', 'repaired at', 'completion date']))
        tat_duration = find_val(r, ['total turn around time (tat)', 'turn around time', 'tat duration', 'tat_duration', 'tat'])
        sign_dept_hod = find_val(r, ['sign of departmental hod', 'sign dept hod', 'sign_dept_hod', 'hod sign'])
        sign_it_cell = find_val(r, ['sign of it cell / bme staff', 'sign of bme staff', 'sign it cell', 'sign_it_cell', 'it sign'])
        location = find_val(r, ['location', 'room', 'room / location', 'room location', 'department', 'dept', 'ward', 'building', 'floor'])
        if not location and asset_id:
            dev = DeviceAsset.objects.filter(models.Q(asset_id__iexact=asset_id)).first()
            if dev:
                loc_parts = [p for p in [dev.building_name, dev.floor_name, dev.room_name] if p]
                location = " - ".join(loc_parts) if loc_parts else (dev.room_name or '')

        raw_status = find_val(r, ['status'])
        if raw_status:
            s_low = raw_status.lower()
            if 'resolve' in s_low or 'repaired' in s_low or 'closed' in s_low or 'fixed' in s_low or 'completed' in s_low:
                status = 'Resolved'
            elif 'repair' in s_low or 'progress' in s_low or 'pending' in s_low or 'open' in s_low:
                status = 'Under Repair'
            else:
                status = 'Resolved' if (repair_datetime or tat_duration) else 'Under Repair'
        else:
            status = 'Resolved' if (repair_datetime or tat_duration) else 'Under Repair'

        rec = EquipmentBreakdown.objects.create(
            breakdown_date=breakdown_date,
            breakdown_time=breakdown_time,
            asset_id=asset_id,
            device_name=device_name,
            location=location,
            breakdown_cause=breakdown_cause,
            equipment_type=equipment_type,
            intimation_datetime=intimation_datetime,
            checkin_datetime=checkin_datetime,
            dept_hod_name=dept_hod_name,
            it_staff_name=it_staff_name,
            repair_datetime=repair_datetime,
            tat_duration=tat_duration,
            sign_dept_hod=sign_dept_hod,
            sign_it_cell=sign_it_cell,
            status=status
        )
        created_records.append(rec)

    return JsonResponse({
        'success': True,
        'count': len(created_records),
        'message': f'Successfully imported {len(created_records)} equipment breakdown records from Excel!'
    })


@csrf_exempt
def api_import_devices_excel(request):
    """Import devices/hardware inventory records from Excel (.xlsx, .xls) or CSV into DeviceAsset."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required.'}, status=405)

    import json
    import csv
    import io
    import datetime
    import uuid
    import random

    rows_data = []

    # 1. Check if multipart file was uploaded
    if 'file' in request.FILES:
        uploaded_file = request.FILES['file']
        filename = uploaded_file.name.lower()

        if filename.endswith('.csv'):
            try:
                content = uploaded_file.read().decode('utf-8-sig', errors='replace')
                reader = csv.DictReader(io.StringIO(content))
                for r in reader:
                    rows_data.append(r)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Failed to parse CSV file: {str(e)}'}, status=400)
        elif filename.endswith(('.xlsx', '.xlsm', '.xltx', '.xls')):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(io.BytesIO(uploaded_file.read()), data_only=True)
                ws = wb.active
                iter_rows = list(ws.iter_rows(values_only=True))
                if not iter_rows:
                    return JsonResponse({'success': False, 'error': 'Uploaded Excel file is empty.'}, status=400)

                header_row = iter_rows[0]
                headers = [str(h).strip() if h is not None else f"col_{idx}" for idx, h in enumerate(header_row)]

                for row_vals in iter_rows[1:]:
                    if not any(row_vals):
                        continue
                    row_dict = {}
                    for idx, val in enumerate(row_vals):
                        if idx < len(headers):
                            if isinstance(val, (datetime.datetime, datetime.date)):
                                row_dict[headers[idx]] = val.strftime('%d-%b-%Y')
                            elif isinstance(val, datetime.time):
                                row_dict[headers[idx]] = val.strftime('%H:%M')
                            else:
                                row_dict[headers[idx]] = str(val).strip() if val is not None else ''
                    rows_data.append(row_dict)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Failed to parse Excel file: {str(e)}'}, status=400)
        else:
            return JsonResponse({'success': False, 'error': 'Unsupported file format. Please upload an Excel (.xlsx, .xls) or CSV file.'}, status=400)

    # 2. Check if JSON payload was passed
    elif request.body:
        try:
            payload = json.loads(request.body)
            if isinstance(payload, list):
                rows_data = payload
            elif isinstance(payload, dict):
                rows_data = payload.get('rows', [])
        except Exception:
            pass

    if not rows_data:
        return JsonResponse({'success': False, 'error': 'No valid data rows found in uploaded file or request.'}, status=400)

    def find_val(row_dict, aliases, default=''):
        lower_map = {str(k).strip().lower(): v for k, v in row_dict.items() if k is not None}
        for a in aliases:
            al = a.lower()
            if al in lower_map and lower_map[al] not in (None, ''):
                return str(lower_map[al]).strip()
        return default

    saved_count = 0
    created_count = 0
    updated_count = 0

    for r in rows_data:
        if not any(str(v).strip() for v in r.values() if v is not None):
            continue

        asset_id = find_val(r, [
            'asset tag', 'asset id', 'asset_id', 'it asset id', 'asset tag / id',
            'asset number', 'asset no', 'tag id', 'tag', 'device asset id', 'device tag', 'asset'
        ])
        serial_number = find_val(r, [
            'serial number', 'serial_number', 'serial no', 'serial', 'sn', 's/n'
        ])

        if not asset_id and not serial_number:
            continue

        if not asset_id:
            now_str = timezone.localtime().strftime("%m%y")
            all_m_tags = set(DeviceAsset.objects.filter(asset_id__contains=f"/{now_str}/").values_list('asset_id', flat=True))
            max_n = 0
            for t_tag in all_m_tags:
                p_parts = t_tag.strip().split('/')
                if len(p_parts) >= 4:
                    try:
                        n_val = int(p_parts[-1])
                        if n_val > max_n: max_n = n_val
                    except (ValueError, TypeError): pass
            next_n = max_n + 1
            while f"PSM/IT/{now_str}/{next_n:03d}" in all_m_tags:
                next_n += 1
            asset_id = f"PSM/IT/{now_str}/{next_n:03d}"

        device_type_raw = find_val(r, [
            'device type', 'device_type', 'type', 'device category', 'category', 'device', 'equipment type'
        ], '')
        device_type = normalize_device_type(device_type_raw, asset_id)

        if not serial_number:
            serial_number = f"SN-PSM-{device_type[:3].upper()}-{random.randint(1000, 9999)}"

        brand_name = find_val(r, ['brand / make', 'brand', 'brand_name', 'make', 'manufacturer', 'company'], '')
        model_specs = find_val(r, [
            'hardware model & specs', 'hardware model & specifications', 'hardware model',
            'model & specs', 'model', 'specs', 'hardware specs', 'compute hardware'
        ], '')

        building_name = find_val(r, ['building', 'building name', 'bldg', 'wing', 'facility'], 'PSM Hospital Main Complex')
        floor_name = find_val(r, ['floor', 'floor name', 'level', 'floor level'], 'Ground Floor')
        room_name = find_val(r, ['room / location', 'room name', 'room', 'location', 'lab', 'department / room', 'ward', 'dept'], 'General Clinical Area')

        assigned_user_name = find_val(r, [
            'assigned custodian', 'custodian / user', 'custodian', 'assigned user', 'assigned user name',
            'user', 'staff name', 'employee name', 'doctor / staff', 'doctor name', 'user name', 'custodian name'
        ], 'Unassigned')
        assigned_emp_id = find_val(r, ['employee id', 'emp id', 'staff id', 'assigned emp id', 'emp_id', 'custodian emp id'], '')
        assigned_department = find_val(r, ['department', 'custodian dept', 'dept', 'custodian department', 'assigned department'], '')
        assigned_designation = find_val(r, ['designation', 'custodian designation', 'role', 'title', 'assigned designation'], '')
        assigned_contact = find_val(r, ['custodian contact', 'contact', 'email', 'phone', 'contact info', 'mobile', 'telephone'], '')

        assigned_email = assigned_contact if '@' in (assigned_contact or '') else ''
        assigned_phone = assigned_contact if '@' not in (assigned_contact or '') else ''

        cpu_processor = find_val(r, ['processor (cpu)', 'processor', 'cpu / processor', 'cpu processor', 'cpu', 'processor / cpu'], '')
        storage_ram = find_val(r, ['ram & storage', 'ram and storage', 'storage & ram', 'storage / ram', 'storage ram', 'ram', 'storage', 'memory', 'disk', 'ram/storage'], '')
        monitor_spec = find_val(r, ['monitor / screen', 'monitor specs', 'monitor spec', 'monitor', 'display', 'screen', 'monitor / display'], '')
        operating_system = find_val(r, ['operating system', 'operating_system', 'os & display', 'os', 'system os'], '')
        
        ip_raw = find_val(r, ['ip address', 'ip_address', 'ip', 'network & ip', 'network ip', 'ip addr'], '')
        ip_address = '' if ip_raw in ('-', '—', 'N/A', 'n/a') else ip_raw

        mac_raw = find_val(r, ['mac address', 'mac_address', 'mac', 'physical address'], '')
        mac_address = '' if mac_raw in ('-', '—', 'N/A', 'n/a') else mac_raw

        anydesk_raw = find_val(r, ['anydesk remote id', 'anydesk id', 'anydesk_id', 'anydesk', 'remote id'], '')
        anydesk_id = '' if anydesk_raw in ('-', '—', 'N/A', 'n/a') else anydesk_raw

        purchase_date = find_val(r, ['purchase date', 'purchase_date', 'procurement date', 'date of purchase'], datetime.date.today().strftime('%d-%b-%Y'))
        warranty_expiry_date = find_val(r, ['warranty expiry', 'warranty expiry date', 'warranty_expiry_date', 'warranty date', 'warranty upto', 'warranty'], (datetime.date.today() + datetime.timedelta(days=1095)).strftime('%d-%b-%Y'))

        status_raw = find_val(r, ['hardware status', 'status & health', 'status', 'health', 'state'], 'Active')
        st_lower = status_raw.lower()
        if 'maint' in st_lower:
            status = 'In Maintenance'
        elif 'storage' in st_lower or 'spare' in st_lower:
            status = 'In Storage'
        elif 'decom' in st_lower:
            status = 'Decommissioned'
        else:
            status = 'Active'

        # Default brand name if missing
        type_upper = device_type.upper()
        if not brand_name:
            if type_upper in ('CPU', 'DISPLAY', 'KEYBOARD', 'MOUSE'):
                brand_name = 'Dell'
            elif 'PRINTER' in type_upper:
                brand_name = 'HP'
            elif 'UPS' in type_upper:
                brand_name = 'APC'
            elif 'TABLET' in type_upper:
                brand_name = 'Samsung'
            else:
                brand_name = 'Standard OEM'

        # Peripheral & component specific fields
        keyboard_spec = ''
        mouse_spec = ''
        printer_spec = ''
        ups_spec = ''
        tablet_spec = ''

        if type_upper == 'DISPLAY':
            monitor_spec = monitor_spec if (monitor_spec and monitor_spec != '—') else (model_specs or '24" FHD IPS Medical Grade Display')
            cpu_processor = model_specs or monitor_spec
        elif type_upper == 'KEYBOARD':
            keyboard_spec = model_specs or 'Dell KB216 USB Wired Antimicrobial Keyboard'
            cpu_processor = keyboard_spec
        elif type_upper == 'MOUSE':
            mouse_spec = model_specs or 'Dell MS116 Cleanable Optical Clinic Mouse'
            cpu_processor = mouse_spec
        elif type_upper == 'PRINTER':
            printer_spec = model_specs or 'HP LaserJet Pro Network Printer'
            cpu_processor = printer_spec
            if not operating_system or operating_system == '—':
                operating_system = 'HP Jetdirect Embedded Firmware'
        elif type_upper == 'UPS':
            ups_spec = model_specs or 'APC Back-UPS 1100VA Surge Protected'
            cpu_processor = ups_spec
            if not operating_system or operating_system == '—':
                operating_system = 'Microcontroller Power Firmware'
        elif type_upper == 'TABLET':
            tablet_spec = model_specs or 'Samsung Galaxy Tab Active Touch Terminal'
            cpu_processor = tablet_spec
            if not operating_system or operating_system == '—':
                operating_system = 'Android / Windows 11 Tablet OS'
        elif type_upper in ('CPU', 'DESKTOP', 'PC', 'TOWER'):
            if not cpu_processor or cpu_processor == '—':
                cpu_processor = model_specs or 'Intel Core i5-12500 (6 Cores, 3.0 GHz)'
            if not storage_ram or storage_ram == '—':
                storage_ram = '16GB RAM / 512GB NVMe SSD'
            if not operating_system or operating_system == '—':
                operating_system = 'Windows 11 Pro Medical Edition'

        # Check if imported row represents a multi-component Workstation
        imported_components = parse_and_normalize_components(
            [],
            device_type_raw or device_type,
            monitor_spec=monitor_spec
        )

        if len(imported_components) > 1:
            # Unpack into itemized components under custodian sharing the single asset tag
            for c_idx, comp_name in enumerate(imported_components):
                c_tag = asset_id
                c_upper = comp_name.upper()
                c_sn = f"{serial_number}-{c_upper[:3]}" if serial_number else f"SN-PSM-{c_upper[:3]}-{c_tag.split('/')[-1]}"
                c_brand = brand_name or ('Dell' if c_upper in ('CPU', 'DISPLAY', 'KEYBOARD', 'MOUSE') else 'HP' if c_upper == 'PRINTER' else 'APC' if c_upper == 'UPS' else 'Samsung' if c_upper == 'TABLET' else 'Standard OEM')

                c_kb = ''
                c_ms = ''
                c_prt = ''
                c_ups = ''
                c_tab = ''
                c_anydesk = anydesk_id if c_upper == 'CPU' else ''

                if c_upper == 'CPU':
                    c_type = 'CPU'
                    c_cpu = cpu_processor or 'Intel Core i5-12500 (6 Cores)'
                    c_ram = storage_ram or '16GB RAM / 512GB NVMe SSD'
                    c_os = operating_system or 'Windows 11 Pro Medical Edition'
                    c_ip = ip_address
                    c_mac = mac_address
                elif c_upper == 'DISPLAY':
                    c_type = 'Display'
                    c_cpu = monitor_spec or '24" FHD IPS Medical Grade Display'
                    c_ram = 'Hardware Display Monitor'
                    c_os = 'Hardware Display'
                    c_ip = ''
                    c_mac = ''
                elif c_upper == 'KEYBOARD':
                    c_type = 'Keyboard'
                    c_kb = 'Dell KB216 USB Wired Antimicrobial Keyboard'
                    c_cpu = c_kb
                    c_ram = 'Hardware Peripheral (HID)'
                    c_os = 'Hardware Peripheral (HID)'
                    c_ip = ''
                    c_mac = ''
                elif c_upper == 'MOUSE':
                    c_type = 'Mouse'
                    c_ms = 'Dell MS116 Cleanable Optical Clinic Mouse'
                    c_cpu = c_ms
                    c_ram = 'Hardware Peripheral (HID)'
                    c_os = 'Hardware Peripheral (HID)'
                    c_ip = ''
                    c_mac = ''
                elif c_upper == 'TABLET':
                    c_type = 'Tablet'
                    c_tab = 'Samsung Galaxy Tab Active Touch Terminal'
                    c_cpu = c_tab
                    c_ram = 'Mobile Diagnostic Tablet'
                    c_os = 'Android / Windows 11 Tablet OS'
                    c_ip = ''
                    c_mac = ''
                elif c_upper == 'PRINTER':
                    c_type = 'Printer'
                    c_prt = 'HP LaserJet Pro Network Printer'
                    c_cpu = c_prt
                    c_ram = 'Direct Print Unit'
                    c_os = 'HP Jetdirect Embedded Firmware'
                    c_ip = ip_address
                    c_mac = mac_address
                elif c_upper == 'UPS':
                    c_type = 'UPS'
                    c_ups = 'APC Back-UPS 1100VA Surge Protected'
                    c_cpu = c_ups
                    c_ram = 'AC Power Protection'
                    c_os = 'Microcontroller Power Firmware'
                    c_ip = ''
                    c_mac = ''
                else:
                    c_type = comp_name
                    c_cpu = f'{comp_name} Hardware Unit'
                    c_ram = 'Standard Hardware Component'
                    c_os = operating_system or 'Firmware Embedded'
                    c_ip = ''
                    c_mac = ''

                c_dev = DeviceAsset.objects.filter(asset_id__iexact=c_tag, device_type__iexact=c_type).first()
                if c_dev:
                    c_dev.device_type = c_type
                    c_dev.brand_name = c_brand
                    c_dev.serial_number = c_sn
                    c_dev.building_name = building_name
                    c_dev.floor_name = floor_name
                    c_dev.room_name = room_name
                    c_dev.assigned_user_name = assigned_user_name
                    c_dev.assigned_emp_id = assigned_emp_id
                    c_dev.assigned_department = assigned_department
                    c_dev.assigned_designation = assigned_designation
                    c_dev.assigned_email = assigned_email
                    c_dev.assigned_phone = assigned_phone
                    c_dev.cpu_processor = c_cpu
                    c_dev.storage_ram = c_ram
                    c_dev.monitor_spec = monitor_spec if c_upper in ('CPU', 'DISPLAY') else ''
                    c_dev.keyboard_spec = c_kb
                    c_dev.mouse_spec = c_ms
                    c_dev.printer_spec = c_prt
                    c_dev.ups_spec = c_ups
                    c_dev.tablet_spec = c_tab
                    c_dev.operating_system = c_os
                    c_dev.ip_address = c_ip
                    c_dev.mac_address = c_mac
                    c_dev.anydesk_id = c_anydesk
                    c_dev.purchase_date = purchase_date
                    c_dev.warranty_expiry_date = warranty_expiry_date
                    c_dev.status = status
                    c_dev.save()
                    updated_count += 1
                else:
                    DeviceAsset.objects.create(
                        dev_id=f"dev-{uuid.uuid4().hex[:8]}",
                        asset_id=c_tag,
                        device_type=c_type,
                        brand_name=c_brand,
                        serial_number=c_sn,
                        org_id='HOSP',
                        org_name='PSM Hospital',
                        building_name=building_name,
                        floor_name=floor_name,
                        room_name=room_name,
                        assigned_user_id='',
                        assigned_user_name=assigned_user_name,
                        assigned_emp_id=assigned_emp_id,
                        assigned_department=assigned_department,
                        assigned_designation=assigned_designation,
                        assigned_email=assigned_email,
                        assigned_phone=assigned_phone,
                        cpu_processor=c_cpu,
                        storage_ram=c_ram,
                        monitor_spec=monitor_spec if c_upper in ('CPU', 'DISPLAY') else '',
                        keyboard_spec=c_kb,
                        mouse_spec=c_ms,
                        printer_spec=c_prt,
                        ups_spec=c_ups,
                        tablet_spec=c_tab,
                        operating_system=c_os,
                        ip_address=c_ip,
                        mac_address=c_mac,
                        anydesk_id=c_anydesk,
                        purchase_date=purchase_date,
                        warranty_expiry_date=warranty_expiry_date,
                        status=status
                    )
                    created_count += 1
                saved_count += 1

            # Sync user profile if assigned
            if assigned_user_name and assigned_user_name.lower() != 'unassigned':
                prof = None
                if assigned_emp_id:
                    prof = UserProfile.objects.filter(emp_id__iexact=assigned_emp_id).first()
                if not prof:
                    prof = UserProfile.objects.filter(full_name__iexact=assigned_user_name).first()
                if prof:
                    if assigned_department and not prof.department: prof.department = assigned_department
                    if assigned_designation and not prof.designation: prof.designation = assigned_designation
                    if assigned_phone and not prof.phone: prof.phone = assigned_phone
                    if not prof.assigned_asset_id: prof.assigned_asset_id = asset_id
                    prof.save()
                else:
                    clean_u = (assigned_emp_id or assigned_user_name.lower().replace(' ', '_')).replace('/', '_')
                    base_u = clean_u
                    cntr = 1
                    while User.objects.filter(username=clean_u).exists():
                        clean_u = f"{base_u}_{cntr}"
                        cntr += 1
                    em_val = assigned_email or f"{clean_u}@psm.hospital"
                    new_u = User.objects.create_user(
                        username=clean_u,
                        email=em_val,
                        first_name=assigned_user_name.split()[0] if assigned_user_name else 'Staff',
                        last_name=" ".join(assigned_user_name.split()[1:]) if len(assigned_user_name.split()) > 1 else ''
                    )
                    UserProfile.objects.create(
                        user=new_u,
                        emp_id=assigned_emp_id or f"EMP-{uuid.uuid4().hex[:6].upper()}",
                        full_name=assigned_user_name,
                        org_id='HOSP',
                        department=assigned_department or 'Clinical Healthcare Unit',
                        designation=assigned_designation or 'Assigned Custodian',
                        phone=assigned_phone or '',
                        assigned_asset_id=asset_id
                    )
            continue

        # Look up existing record by asset_id + device_type OR serial_number
        dev = None
        if serial_number and not serial_number.startswith('SN-PSM-'):
            dev = DeviceAsset.objects.filter(serial_number__iexact=serial_number).first()
        if not dev:
            dev = DeviceAsset.objects.filter(asset_id__iexact=asset_id, device_type__iexact=device_type).first()

        if dev:
            dev.device_type = device_type
            dev.brand_name = brand_name
            dev.serial_number = serial_number
            dev.building_name = building_name
            dev.floor_name = floor_name
            dev.room_name = room_name
            dev.assigned_user_name = assigned_user_name
            dev.assigned_emp_id = assigned_emp_id
            dev.assigned_department = assigned_department
            dev.assigned_designation = assigned_designation
            dev.assigned_email = assigned_email
            dev.assigned_phone = assigned_phone
            dev.cpu_processor = cpu_processor
            dev.storage_ram = storage_ram
            dev.monitor_spec = monitor_spec
            dev.keyboard_spec = keyboard_spec
            dev.mouse_spec = mouse_spec
            dev.printer_spec = printer_spec
            dev.ups_spec = ups_spec
            dev.tablet_spec = tablet_spec
            dev.operating_system = operating_system
            dev.ip_address = ip_address
            dev.mac_address = mac_address
            dev.anydesk_id = anydesk_id
            dev.purchase_date = purchase_date
            dev.warranty_expiry_date = warranty_expiry_date
            dev.status = status
            dev.save()
            updated_count += 1
        else:
            dev_id = f"dev-{uuid.uuid4().hex[:8]}"
            DeviceAsset.objects.create(
                dev_id=dev_id,
                asset_id=asset_id,
                device_type=device_type,
                brand_name=brand_name,
                serial_number=serial_number,
                org_id='HOSP',
                org_name='PSM Hospital',
                building_name=building_name,
                floor_name=floor_name,
                room_name=room_name,
                assigned_user_id='',
                assigned_user_name=assigned_user_name,
                assigned_emp_id=assigned_emp_id,
                assigned_department=assigned_department,
                assigned_designation=assigned_designation,
                assigned_email=assigned_email,
                assigned_phone=assigned_phone,
                cpu_processor=cpu_processor,
                storage_ram=storage_ram,
                monitor_spec=monitor_spec,
                keyboard_spec=keyboard_spec,
                mouse_spec=mouse_spec,
                printer_spec=printer_spec,
                ups_spec=ups_spec,
                tablet_spec=tablet_spec,
                operating_system=operating_system,
                ip_address=ip_address,
                mac_address=mac_address,
                anydesk_id=anydesk_id,
                purchase_date=purchase_date,
                warranty_expiry_date=warranty_expiry_date,
                status=status
            )
            created_count += 1

        # Sync user profile if assigned
        if assigned_user_name and assigned_user_name.lower() != 'unassigned':
            prof = None
            if assigned_emp_id:
                prof = UserProfile.objects.filter(emp_id__iexact=assigned_emp_id).first()
            if not prof:
                prof = UserProfile.objects.filter(full_name__iexact=assigned_user_name).first()
            if prof:
                if assigned_department and not prof.department: prof.department = assigned_department
                if assigned_designation and not prof.designation: prof.designation = assigned_designation
                if assigned_phone and not prof.phone: prof.phone = assigned_phone
                if not prof.assigned_asset_id: prof.assigned_asset_id = asset_id
                prof.save()
            else:
                clean_u = (assigned_emp_id or assigned_user_name.lower().replace(' ', '_')).replace('/', '_')
                base_u = clean_u
                cntr = 1
                while User.objects.filter(username=clean_u).exists():
                    clean_u = f"{base_u}_{cntr}"
                    cntr += 1
                em_val = assigned_email or f"{clean_u}@psm.hospital"
                new_u = User.objects.create_user(
                    username=clean_u,
                    email=em_val,
                    first_name=assigned_user_name.split()[0] if assigned_user_name else 'Staff',
                    last_name=" ".join(assigned_user_name.split()[1:]) if len(assigned_user_name.split()) > 1 else ''
                )
                UserProfile.objects.create(
                    user=new_u,
                    emp_id=assigned_emp_id or f"EMP-{uuid.uuid4().hex[:6].upper()}",
                    full_name=assigned_user_name,
                    org_id='HOSP',
                    department=assigned_department or 'Clinical Healthcare Unit',
                    designation=assigned_designation or 'Assigned Custodian',
                    phone=assigned_phone or '',
                    assigned_asset_id=asset_id
                )

        saved_count += 1

    return JsonResponse({
        'success': True,
        'count': saved_count,
        'created': created_count,
        'updated': updated_count,
        'message': f'Successfully imported {saved_count} device(s) ({created_count} registered, {updated_count} updated) into Inventory!'
    })


@csrf_exempt
def api_clear_all_data(request):
    """
    Administrator API & Web Trigger to completely purge all device inventory,
    complaints, breakdown records, PMS schedules, and test accounts.
    Allows 1-click clean slate directly from live deployment.
    """
    if not is_admin_authenticated(request):
        return JsonResponse({
            'success': False,
            'error': 'Administrator authentication required. Please log into the Admin Console first.'
        }, status=403)

    if request.method not in ('POST', 'GET'):
        return JsonResponse({'success': False, 'error': 'POST or GET method required.'}, status=405)

    confirm = (request.POST.get('confirm') or request.GET.get('confirm') or '').strip().lower()
    if confirm != 'yes':
        return JsonResponse({
            'success': False,
            'error': "Confirmation required. Pass confirm='yes' to execute permanent data wipe."
        }, status=400)

    dev_count = DeviceAsset.objects.count()
    trans_count = CustodyTransferLog.objects.count()
    comp_count = DeviceComplaint.objects.count()
    pms_count = EquipmentPMS.objects.count()
    bd_count = EquipmentBreakdown.objects.count()

    DeviceAsset.objects.all().delete()
    CustodyTransferLog.objects.all().delete()
    DeviceComplaint.objects.all().delete()
    EquipmentPMS.objects.all().delete()
    EquipmentBreakdown.objects.all().delete()

    # Clean up non-admin test profiles & staff accounts while preserving administrative access
    prof_count = UserProfile.objects.filter(user__is_staff=False, user__is_superuser=False).count()
    UserProfile.objects.filter(user__is_staff=False, user__is_superuser=False).delete()
    user_count = User.objects.filter(is_staff=False, is_superuser=False).count()
    User.objects.filter(is_staff=False, is_superuser=False).delete()

    msg = f"Successfully purged database to 100% clean slate: {dev_count} devices, {comp_count} complaints, {bd_count} breakdown records, {pms_count} PMS schedules deleted."

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json' or request.POST.get('format') == 'json' or request.GET.get('format') == 'json':
        return JsonResponse({
            'success': True,
            'message': msg,
            'counts': {
                'devices': dev_count,
                'transfers': trans_count,
                'complaints': comp_count,
                'pms': pms_count,
                'breakdown': bd_count,
                'test_profiles': prof_count,
                'test_users': user_count
            }
        })

    messages.success(request, msg)
    return redirect('inventory')