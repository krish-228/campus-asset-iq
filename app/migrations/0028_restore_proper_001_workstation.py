from django.db import migrations
from django.db.models import Q
import uuid

def restore_proper_001_workstation(apps, schema_editor):
    DeviceAsset = apps.get_model('app', 'DeviceAsset')
    UserProfile = apps.get_model('app', 'UserProfile')
    User = apps.get_model('auth', 'User')
    CustodyTransferLog = apps.get_model('app', 'CustodyTransferLog')

    TAG = 'PSM/IT/0826/001'

    # Purge any dummy placeholder devices with SN-PSM-DIS-9580
    DeviceAsset.objects.filter(serial_number='SN-PSM-DIS-9580').delete()

    # Clean up test users and test transfer logs
    UserProfile.objects.filter(emp_id__in=['EMP-TEST-99', 'EMP-TEST-001']).delete()
    CustodyTransferLog.objects.filter(device_asset_id=TAG).delete()

    # Ensure User and UserProfile for Radhe Shyam
    u = User.objects.filter(username='radheshyam').first()
    if not u:
        u = User.objects.create(
            username='radheshyam',
            email='radhe.shyam@psmhospital.org',
            first_name='Radhe',
            last_name='Shyam',
            is_active=True
        )
        u.set_password('radhe@1234')
        u.save()

    prof = UserProfile.objects.filter(user=u).first()
    if not prof:
        prof = UserProfile.objects.filter(emp_id='1001').first()
    if not prof:
        prof = UserProfile(user=u)

    prof.user = u
    prof.emp_id = '1001'
    prof.full_name = 'Radhe Shyam'
    prof.department = 'Cardiology'
    prof.designation = 'Senior Consultant'
    prof.phone = '+91 98250 12345'
    prof.org_id = 'HOSP'
    prof.assigned_asset_id = TAG
    prof.save()

    CUSTODIAN_NAME = 'Radhe Shyam'
    CUSTODIAN_EMP = '1001'
    CUSTODIAN_DESIG = 'Senior Consultant'
    CUSTODIAN_DEPT = 'Cardiology'
    CUSTODIAN_EMAIL = 'radhe.shyam@psmhospital.org'
    CUSTODIAN_PHONE = '+91 98250 12345'

    # 1. Ensure CPU exists and has proper specs
    cpu = DeviceAsset.objects.filter(asset_id=TAG, device_type='CPU').first()
    if not cpu:
        cpu = DeviceAsset.objects.filter(id=21).first()
    if cpu:
        cpu.asset_id = TAG
        cpu.device_type = 'CPU'
        cpu.brand_name = 'HP'
        cpu.serial_number = 'SN-HP-PD600-001'
        cpu.cpu_processor = 'Intel Core i5-10500 (6 cores, 3.10 GHz)'
        cpu.storage_ram = '16GB RAM / 512GB NVMe SSD'
        cpu.monitor_spec = '24" FHD IPS Display'
        cpu.operating_system = 'Windows 11 Pro'
        cpu.ip_address = '192.168.20.101'
        cpu.mac_address = 'B4-2E-99-20-01-FA'
        cpu.anydesk_id = '928 341 001'
        cpu.building_name = 'PSM Hospital'
        cpu.floor_name = '2nd Floor'
        cpu.room_name = 'Room 201'
        cpu.assigned_department = CUSTODIAN_DEPT
        cpu.assigned_designation = CUSTODIAN_DESIG
        cpu.assigned_user_name = CUSTODIAN_NAME
        cpu.assigned_emp_id = CUSTODIAN_EMP
        cpu.assigned_email = CUSTODIAN_EMAIL
        cpu.assigned_phone = CUSTODIAN_PHONE
        cpu.status = 'Active'
        cpu.purchase_date = '28-Sep-2026'
        cpu.warranty_expiry_date = '27-Sep-2029'
        cpu.save()
    else:
        DeviceAsset.objects.create(
            dev_id=f"dev-{uuid.uuid4().hex[:8]}",
            asset_id=TAG,
            device_type='CPU',
            brand_name='HP',
            serial_number='SN-HP-PD600-001',
            org_id='HOSP',
            org_name='PSM Hospital',
            building_name='PSM Hospital',
            floor_name='2nd Floor',
            room_name='Room 201',
            assigned_department=CUSTODIAN_DEPT,
            assigned_designation=CUSTODIAN_DESIG,
            assigned_user_name=CUSTODIAN_NAME,
            assigned_emp_id=CUSTODIAN_EMP,
            assigned_email=CUSTODIAN_EMAIL,
            assigned_phone=CUSTODIAN_PHONE,
            cpu_processor='Intel Core i5-10500 (6 cores, 3.10 GHz)',
            storage_ram='16GB RAM / 512GB NVMe SSD',
            monitor_spec='24" FHD IPS Display',
            operating_system='Windows 11 Pro',
            ip_address='192.168.20.101',
            mac_address='B4-2E-99-20-01-FA',
            anydesk_id='928 341 001',
            status='Active',
            purchase_date='28-Sep-2026',
            warranty_expiry_date='27-Sep-2029'
        )

    # 2. Ensure Display exists and has proper specs
    disp = DeviceAsset.objects.filter(asset_id=TAG, device_type='Display').first()
    if not disp:
        disp = DeviceAsset.objects.filter(id=20).first()
    if disp:
        disp.asset_id = TAG
        disp.device_type = 'Display'
        disp.brand_name = 'Dell'
        disp.serial_number = 'SN-DELL-P24-001'
        disp.monitor_spec = '24" FHD IPS (1920x1080) Anti-Glare Display'
        disp.cpu_processor = '24" FHD IPS Display'
        disp.storage_ram = ''
        disp.operating_system = 'Hardware Display'
        disp.ip_address = '-'
        disp.mac_address = '-'
        disp.building_name = 'PSM Hospital'
        disp.floor_name = '2nd Floor'
        disp.room_name = 'Room 201'
        disp.assigned_department = CUSTODIAN_DEPT
        disp.assigned_designation = CUSTODIAN_DESIG
        disp.assigned_user_name = CUSTODIAN_NAME
        disp.assigned_emp_id = CUSTODIAN_EMP
        disp.assigned_email = CUSTODIAN_EMAIL
        disp.assigned_phone = CUSTODIAN_PHONE
        disp.status = 'Active'
        disp.purchase_date = '28-Sep-2026'
        disp.warranty_expiry_date = '27-Sep-2029'
        disp.save()
    else:
        DeviceAsset.objects.create(
            dev_id=f"dev-{uuid.uuid4().hex[:8]}",
            asset_id=TAG,
            device_type='Display',
            brand_name='Dell',
            serial_number='SN-DELL-P24-001',
            org_id='HOSP',
            org_name='PSM Hospital',
            building_name='PSM Hospital',
            floor_name='2nd Floor',
            room_name='Room 201',
            assigned_department=CUSTODIAN_DEPT,
            assigned_designation=CUSTODIAN_DESIG,
            assigned_user_name=CUSTODIAN_NAME,
            assigned_emp_id=CUSTODIAN_EMP,
            assigned_email=CUSTODIAN_EMAIL,
            assigned_phone=CUSTODIAN_PHONE,
            monitor_spec='24" FHD IPS (1920x1080) Anti-Glare Display',
            cpu_processor='24" FHD IPS Display',
            operating_system='Hardware Display',
            ip_address='-',
            mac_address='-',
            status='Active',
            purchase_date='28-Sep-2026',
            warranty_expiry_date='27-Sep-2029'
        )

    # 3. Ensure Keyboard exists and has proper specs
    kb = DeviceAsset.objects.filter(asset_id=TAG, device_type='Keyboard').first()
    if not kb:
        kb = DeviceAsset.objects.filter(id=178).first()
    if kb:
        kb.asset_id = TAG
        kb.device_type = 'Keyboard'
        kb.brand_name = 'HP'
        kb.serial_number = 'SN-HP-KB-001'
        kb.keyboard_spec = 'HP Business Slim USB Wired Keyboard'
        kb.cpu_processor = 'HP Business Slim USB Wired Keyboard'
        kb.storage_ram = ''
        kb.operating_system = 'Hardware Peripheral'
        kb.ip_address = '-'
        kb.mac_address = '-'
        kb.building_name = 'PSM Hospital'
        kb.floor_name = '2nd Floor'
        kb.room_name = 'Room 201'
        kb.assigned_department = CUSTODIAN_DEPT
        kb.assigned_designation = CUSTODIAN_DESIG
        kb.assigned_user_name = CUSTODIAN_NAME
        kb.assigned_emp_id = CUSTODIAN_EMP
        kb.assigned_email = CUSTODIAN_EMAIL
        kb.assigned_phone = CUSTODIAN_PHONE
        kb.status = 'Active'
        kb.purchase_date = '28-Sep-2026'
        kb.warranty_expiry_date = '27-Sep-2029'
        kb.save()
    else:
        DeviceAsset.objects.create(
            dev_id=f"dev-{uuid.uuid4().hex[:8]}",
            asset_id=TAG,
            device_type='Keyboard',
            brand_name='HP',
            serial_number='SN-HP-KB-001',
            org_id='HOSP',
            org_name='PSM Hospital',
            building_name='PSM Hospital',
            floor_name='2nd Floor',
            room_name='Room 201',
            assigned_department=CUSTODIAN_DEPT,
            assigned_designation=CUSTODIAN_DESIG,
            assigned_user_name=CUSTODIAN_NAME,
            assigned_emp_id=CUSTODIAN_EMP,
            assigned_email=CUSTODIAN_EMAIL,
            assigned_phone=CUSTODIAN_PHONE,
            keyboard_spec='HP Business Slim USB Wired Keyboard',
            cpu_processor='HP Business Slim USB Wired Keyboard',
            operating_system='Hardware Peripheral',
            ip_address='-',
            mac_address='-',
            status='Active',
            purchase_date='28-Sep-2026',
            warranty_expiry_date='27-Sep-2029'
        )

    # 4. Ensure Mouse exists and has proper specs
    ms = DeviceAsset.objects.filter(asset_id=TAG, device_type='Mouse').first()
    if not ms:
        ms = DeviceAsset.objects.filter(id=179).first()
    if ms:
        ms.asset_id = TAG
        ms.device_type = 'Mouse'
        ms.brand_name = 'HP'
        ms.serial_number = 'SN-HP-MS-001'
        ms.mouse_spec = 'HP Optical 1000 DPI USB Wired Mouse'
        ms.cpu_processor = 'HP Optical 1000 DPI USB Wired Mouse'
        ms.storage_ram = ''
        ms.operating_system = 'Hardware Peripheral'
        ms.ip_address = '-'
        ms.mac_address = '-'
        ms.building_name = 'PSM Hospital'
        ms.floor_name = '2nd Floor'
        ms.room_name = 'Room 201'
        ms.assigned_department = CUSTODIAN_DEPT
        ms.assigned_designation = CUSTODIAN_DESIG
        ms.assigned_user_name = CUSTODIAN_NAME
        ms.assigned_emp_id = CUSTODIAN_EMP
        ms.assigned_email = CUSTODIAN_EMAIL
        ms.assigned_phone = CUSTODIAN_PHONE
        ms.status = 'Active'
        ms.purchase_date = '28-Sep-2026'
        ms.warranty_expiry_date = '27-Sep-2029'
        ms.save()
    else:
        DeviceAsset.objects.create(
            dev_id=f"dev-{uuid.uuid4().hex[:8]}",
            asset_id=TAG,
            device_type='Mouse',
            brand_name='HP',
            serial_number='SN-HP-MS-001',
            org_id='HOSP',
            org_name='PSM Hospital',
            building_name='PSM Hospital',
            floor_name='2nd Floor',
            room_name='Room 201',
            assigned_department=CUSTODIAN_DEPT,
            assigned_designation=CUSTODIAN_DESIG,
            assigned_user_name=CUSTODIAN_NAME,
            assigned_emp_id=CUSTODIAN_EMP,
            assigned_email=CUSTODIAN_EMAIL,
            assigned_phone=CUSTODIAN_PHONE,
            mouse_spec='HP Optical 1000 DPI USB Wired Mouse',
            cpu_processor='HP Optical 1000 DPI USB Wired Mouse',
            operating_system='Hardware Peripheral',
            ip_address='-',
            mac_address='-',
            status='Active',
            purchase_date='28-Sep-2026',
            warranty_expiry_date='27-Sep-2029'
        )

def reverse_noop(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('app', '0027_purge_078_blood_reception_assets'),
    ]

    operations = [
        migrations.RunPython(restore_proper_001_workstation, reverse_noop),
    ]
