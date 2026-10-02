from django.db import migrations
from django.db.models import Q
import uuid

def deduplicate_hitakshi_workstation(apps, schema_editor):
    DeviceAsset = apps.get_model('app', 'DeviceAsset')
    CustodyTransferLog = apps.get_model('app', 'CustodyTransferLog')
    DeviceComplaint = apps.get_model('app', 'DeviceComplaint')
    UserProfile = apps.get_model('app', 'UserProfile')

    TARGET_TAG = 'PSM/IT/0926/076'
    OLD_TAG = 'PSM/IT/0826/008'

    # -------------------------------------------------------------------------
    # 1. GATHER BEST SPECS FOR HITAKSHI NAYAK'S 5 WORKSTATION COMPONENTS
    # -------------------------------------------------------------------------
    hitakshi_q = Q(assigned_user_name__icontains='Hitakshi') | Q(assigned_emp_id__in=['68050', '60050'])
    hitakshi_devs = list(DeviceAsset.objects.filter(hitakshi_q | Q(asset_id__iexact=TARGET_TAG) | Q(asset_id__icontains='076') | Q(asset_id__icontains='008')))

    # Component definitions with real physical hardware specifications
    COMP_DEFS = {
        'CPU': {
            'device_type': 'CPU',
            'brand_name': 'Intex',
            'cpu_processor': 'Intel Core i3-8100',
            'storage_ram': '8GB RAM / 256GB SSD',
            'operating_system': 'Windows 11 Home',
            'ip_address': '192.168.31.209',
            'mac_address': '00-E0-27-40-41-DB',
            'default_sn': '2115019697260787576',
        },
        'Display': {
            'device_type': 'Display',
            'brand_name': 'Zebronics',
            'cpu_processor': 'Zeb-PA129 54.6cm LED Monitor',
            'monitor_spec': 'Zeb-PA129 54.6cm LED Monitor',
            'storage_ram': '',
            'operating_system': '',
            'ip_address': '-',
            'mac_address': '-',
            'default_sn': 'ZAA32FX00404',
        },
        'Keyboard': {
            'device_type': 'Keyboard',
            'brand_name': 'HP',
            'cpu_processor': 'HP KM160 Wired Keyboard',
            'keyboard_spec': 'HP KM160 Wired Keyboard',
            'storage_ram': '',
            'operating_system': '',
            'ip_address': '-',
            'mac_address': '-',
            'default_sn': 'KM160240833659',
        },
        'Mouse': {
            'device_type': 'Mouse',
            'brand_name': 'HP',
            'cpu_processor': 'HP KM160 Wired Mouse',
            'mouse_spec': 'HP KM160 Wired Mouse',
            'storage_ram': '',
            'operating_system': '',
            'ip_address': '-',
            'mac_address': '-',
            'default_sn': 'KM160240833659',
        },
        'Printer': {
            'device_type': 'Printer',
            'brand_name': 'Canon',
            'cpu_processor': 'Canon LBP6030 Laser Printer',
            'printer_spec': 'Canon LBP6030 Laser Printer',
            'storage_ram': '',
            'operating_system': '',
            'ip_address': '-',
            'mac_address': '-',
            'default_sn': 'NTNA855874',
        },
    }

    preserved_ids = set()

    # Find or update exactly one row per component type under TARGET_TAG
    for comp_type, defs in COMP_DEFS.items():
        # Look for existing candidate for this component type
        candidates = [
            d for d in hitakshi_devs 
            if d.device_type and d.device_type.upper() == comp_type.upper()
        ]
        
        # Pick the best candidate (prefer one with real non-placeholder serial number)
        best_dev = None
        for c in candidates:
            if c.serial_number and not c.serial_number.startswith('SN-PSM-') and c.serial_number.upper() not in ('NA', 'N/A', '-'):
                best_dev = c
                break
        if not best_dev and candidates:
            best_dev = candidates[0]

        best_sn = defs['default_sn']
        if best_dev and best_dev.serial_number and not best_dev.serial_number.startswith('SN-PSM-') and best_dev.serial_number.upper() not in ('NA', 'N/A', '-'):
            best_sn = best_dev.serial_number

        if best_dev:
            best_dev.asset_id = TARGET_TAG
            best_dev.device_type = defs['device_type']
            best_dev.brand_name = defs['brand_name']
            best_dev.serial_number = best_sn
            best_dev.cpu_processor = defs.get('cpu_processor', '')
            best_dev.storage_ram = defs.get('storage_ram', '')
            best_dev.operating_system = defs.get('operating_system', '')
            best_dev.ip_address = defs.get('ip_address', '-')
            best_dev.mac_address = defs.get('mac_address', '-')
            if 'monitor_spec' in defs: best_dev.monitor_spec = defs['monitor_spec']
            if 'keyboard_spec' in defs: best_dev.keyboard_spec = defs['keyboard_spec']
            if 'mouse_spec' in defs: best_dev.mouse_spec = defs['mouse_spec']
            if 'printer_spec' in defs: best_dev.printer_spec = defs['printer_spec']
            best_dev.building_name = 'PSM Hospital'
            best_dev.floor_name = 'Ground Floor'
            best_dev.room_name = 'Cardiology OPD / 03'
            best_dev.assigned_user_name = 'Hitakshi Nayak'
            best_dev.assigned_emp_id = '68050'
            best_dev.assigned_designation = 'Nursing Staff'
            best_dev.assigned_department = 'Cardiology OPD'
            best_dev.status = 'Active'
            best_dev.org_id = 'HOSP'
            best_dev.org_name = 'PSM Hospital'
            best_dev.save()
            preserved_ids.add(best_dev.id)
        else:
            new_row = DeviceAsset.objects.create(
                dev_id=f"dev-{uuid.uuid4().hex[:8]}",
                asset_id=TARGET_TAG,
                device_type=defs['device_type'],
                brand_name=defs['brand_name'],
                serial_number=best_sn,
                cpu_processor=defs.get('cpu_processor', ''),
                storage_ram=defs.get('storage_ram', ''),
                operating_system=defs.get('operating_system', ''),
                ip_address=defs.get('ip_address', '-'),
                mac_address=defs.get('mac_address', '-'),
                monitor_spec=defs.get('monitor_spec', ''),
                keyboard_spec=defs.get('keyboard_spec', ''),
                mouse_spec=defs.get('mouse_spec', ''),
                printer_spec=defs.get('printer_spec', ''),
                building_name='PSM Hospital',
                floor_name='Ground Floor',
                room_name='Cardiology OPD / 03',
                assigned_user_name='Hitakshi Nayak',
                assigned_emp_id='68050',
                assigned_designation='Nursing Staff',
                assigned_department='Cardiology OPD',
                status='Active',
                org_id='HOSP',
                org_name='PSM Hospital'
            )
            preserved_ids.add(new_row.id)

    # -------------------------------------------------------------------------
    # 2. DELETE ALL EXTRA / DUPLICATE RECORDS FOR HITAKSHI NAYAK
    # -------------------------------------------------------------------------
    for d in hitakshi_devs:
        if d.id not in preserved_ids:
            d.delete()

    # Also delete any other remaining records with tag 008
    DeviceAsset.objects.filter(asset_id__iexact=OLD_TAG).delete()

    # -------------------------------------------------------------------------
    # 3. GLOBAL DEDUPLICATION: ENSURE NO OTHER ASSET_ID HAS DUPLICATE HARDWARE
    # -------------------------------------------------------------------------
    all_tags = set(DeviceAsset.objects.values_list('asset_id', flat=True))
    for tag in all_tags:
        if not tag: continue
        tag_devs = list(DeviceAsset.objects.filter(asset_id__iexact=tag))
        type_seen = {}
        for dev in tag_devs:
            dt = (dev.device_type or 'CPU').strip().upper()
            if dt not in type_seen:
                type_seen[dt] = dev
            else:
                # Duplicate found for same asset_id and component type!
                existing = type_seen[dt]
                # Keep the one with real serial number and delete the other
                has_real_sn = dev.serial_number and not dev.serial_number.startswith('SN-PSM-') and dev.serial_number.upper() not in ('NA', 'N/A', '-')
                exist_has_real = existing.serial_number and not existing.serial_number.startswith('SN-PSM-') and existing.serial_number.upper() not in ('NA', 'N/A', '-')
                if has_real_sn and not exist_has_real:
                    existing.delete()
                    type_seen[dt] = dev
                else:
                    dev.delete()

    # -------------------------------------------------------------------------
    # 4. UPDATE CUSTODY LOGS, COMPLAINTS, AND USER PROFILES
    # -------------------------------------------------------------------------
    CustodyTransferLog.objects.filter(
        Q(to_user_name__icontains='Hitakshi') | Q(to_emp_id__in=['68050', '60050']) | Q(device_asset_id__icontains='008')
    ).update(device_asset_id=TARGET_TAG, to_user_name='Hitakshi Nayak', to_emp_id='68050')

    DeviceComplaint.objects.filter(
        Q(user_full_name__icontains='Hitakshi') | Q(emp_id__in=['68050', '60050']) | Q(device_asset_id__icontains='008')
    ).update(device_asset_id=TARGET_TAG, user_full_name='Hitakshi Nayak', emp_id='68050')

    UserProfile.objects.filter(
        Q(emp_id__in=['68050', '60050']) | Q(full_name__icontains='Hitakshi')
    ).update(assigned_asset_id=TARGET_TAG, full_name='Hitakshi Nayak', emp_id='68050', designation='Nursing Staff', department='Cardiology OPD')


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0025_reassign_077_peripherals_to_016'),
    ]

    operations = [
        migrations.RunPython(deduplicate_hitakshi_workstation, reverse_noop),
    ]
