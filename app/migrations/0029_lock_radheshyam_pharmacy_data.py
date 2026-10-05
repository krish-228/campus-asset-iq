from django.db import migrations
from django.contrib.auth.hashers import make_password

def lock_radheshyam_pharmacy_data(apps, schema_editor):
    DeviceAsset = apps.get_model('app', 'DeviceAsset')
    UserProfile = apps.get_model('app', 'UserProfile')
    User = apps.get_model('auth', 'User')

    TAG = 'PSM/IT/0826/001'
    CUSTODIAN_NAME = 'Radhe Shyam'
    CUSTODIAN_EMP = '0000'
    CUSTODIAN_DESIG = 'Pharmacy Incharge'
    CUSTODIAN_DEPT = 'Pharmacy'
    CUSTODIAN_EMAIL = 'radherajpurohit9928@gmail.com'
    CUSTODIAN_PHONE = '7229938069'
    BUILDING_NAME = 'PSM Hospital Main Complex'
    FLOOR_NAME = 'Ground Floor'
    ROOM_NAME = 'Pharmacy 01'

    # Purge any dummy 1001 user profiles
    UserProfile.objects.filter(emp_id='1001').delete()

    # Ensure auth_user
    u = User.objects.filter(username='radheshyam').first()
    if not u:
        u = User.objects.filter(email=CUSTODIAN_EMAIL).first()
    if not u:
        u = User.objects.create(
            username='radheshyam',
            email=CUSTODIAN_EMAIL,
            first_name='Radhe',
            last_name='Shyam',
            password=make_password('radhe@1234'),
            is_active=True
        )
    else:
        u.email = CUSTODIAN_EMAIL
        u.first_name = 'Radhe'
        u.last_name = 'Shyam'
        if not u.password:
            u.password = make_password('radhe@1234')
        u.save()

    # Ensure UserProfile
    prof = UserProfile.objects.filter(user=u).first()
    if not prof:
        prof = UserProfile.objects.filter(emp_id=CUSTODIAN_EMP).first()
    if not prof:
        prof = UserProfile(user=u)

    prof.user = u
    prof.emp_id = CUSTODIAN_EMP
    prof.full_name = CUSTODIAN_NAME
    prof.department = CUSTODIAN_DEPT
    prof.designation = CUSTODIAN_DESIG
    prof.phone = CUSTODIAN_PHONE
    prof.org_id = 'HOSP'
    prof.assigned_asset_id = TAG
    prof.save()

    # Update all DeviceAsset rows with tag PSM/IT/0826/001
    DeviceAsset.objects.filter(asset_id=TAG).update(
        assigned_user_name=CUSTODIAN_NAME,
        assigned_emp_id=CUSTODIAN_EMP,
        assigned_designation=CUSTODIAN_DESIG,
        assigned_department=CUSTODIAN_DEPT,
        assigned_email=CUSTODIAN_EMAIL,
        assigned_phone=CUSTODIAN_PHONE,
        building_name=BUILDING_NAME,
        floor_name=FLOOR_NAME,
        room_name=ROOM_NAME,
        org_id='HOSP',
        org_name='PSM Hospital',
        status='Active'
    )

def reverse_noop(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('app', '0028_restore_proper_001_workstation'),
    ]

    operations = [
        migrations.RunPython(lock_radheshyam_pharmacy_data, reverse_noop),
    ]
