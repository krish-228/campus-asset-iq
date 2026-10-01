from django.db import migrations
from django.db.models import Q

def purge_079_and_lalshing(apps, schema_editor):
    DeviceAsset = apps.get_model('app', 'DeviceAsset')
    UserProfile = apps.get_model('app', 'UserProfile')
    CustodyTransferLog = apps.get_model('app', 'CustodyTransferLog')
    DeviceComplaint = apps.get_model('app', 'DeviceComplaint')

    # 1. Purge matching devices from DeviceAsset
    dev_query = (
        Q(asset_id__icontains='079') |
        Q(asset_id__icontains='PSM/IT/0926/079') |
        Q(assigned_user_name__icontains='Lal') |
        Q(assigned_emp_id__in=['68127', '860127']) |
        Q(serial_number__icontains='079') |
        Q(serial_number__icontains='CN-0W41TY')
    )
    deleted_devs, _ = DeviceAsset.objects.filter(dev_query).delete()

    # 2. Purge user profiles
    prof_query = (
        Q(full_name__icontains='Lal') |
        Q(emp_id__in=['68127', '860127'])
    )
    UserProfile.objects.filter(prof_query).delete()

    # 3. Purge custody transfer logs
    log_query = (
        Q(device_asset_id__icontains='079') |
        Q(to_user_name__icontains='Lal') |
        Q(from_user_name__icontains='Lal')
    )
    CustodyTransferLog.objects.filter(log_query).delete()

    # 4. Purge complaints
    comp_query = (
        Q(device_asset_id__icontains='079') |
        Q(user_full_name__icontains='Lal') |
        Q(emp_id__in=['68127', '860127'])
    )
    DeviceComplaint.objects.filter(comp_query).delete()


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0023_deduplicate_device_assets'),
    ]

    operations = [
        migrations.RunPython(purge_079_and_lalshing, reverse_noop),
    ]
