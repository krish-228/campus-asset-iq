from django.db import migrations
from django.db.models import Q

def reassign_077_and_clean(apps, schema_editor):
    DeviceAsset = apps.get_model('app', 'DeviceAsset')
    CustodyTransferLog = apps.get_model('app', 'CustodyTransferLog')
    DeviceComplaint = apps.get_model('app', 'DeviceComplaint')
    UserProfile = apps.get_model('app', 'UserProfile')

    TARGET_WORKSTATION_TAG = 'PSM/IT/0826/016'

    # 1. Any Gunjan device (emp_id 60278 or name Gunjan) that has tag 077 must be unified under PSM/IT/0826/016
    gunjan_077_devs = DeviceAsset.objects.filter(
        Q(assigned_emp_id='60278') | Q(assigned_user_name__icontains='Gunjan'),
        asset_id__icontains='077'
    )
    for dev in gunjan_077_devs:
        dev.asset_id = TARGET_WORKSTATION_TAG
        dev.save()

    # 2. Also ensure any Gunjan device not yet matching 016 is unified under 016
    gunjan_other_devs = DeviceAsset.objects.filter(
        Q(assigned_emp_id='60278') | Q(assigned_user_name__icontains='Gunjan')
    ).exclude(asset_id=TARGET_WORKSTATION_TAG)
    for dev in gunjan_other_devs:
        dev.asset_id = TARGET_WORKSTATION_TAG
        dev.save()

    # 3. Purge/delete any remaining device asset with tag 077 so 077 is 100% free and fresh
    DeviceAsset.objects.filter(
        Q(asset_id__icontains='077') |
        Q(asset_id__icontains='PSM/IT/0926/077') |
        Q(asset_id__icontains='PSM/IT/0826/077')
    ).delete()

    # 4. In CustodyTransferLog, update any Gunjan logs referencing 077 to 016, and delete any leftover 077 logs
    CustodyTransferLog.objects.filter(
        Q(to_user_name__icontains='Gunjan') | Q(to_emp_id='60278'),
        device_asset_id__icontains='077'
    ).update(device_asset_id=TARGET_WORKSTATION_TAG)

    CustodyTransferLog.objects.filter(device_asset_id__icontains='077').delete()

    # 5. In DeviceComplaint, update any Gunjan complaints referencing 077 to 016, and delete any leftover 077 complaints
    DeviceComplaint.objects.filter(
        Q(user_full_name__icontains='Gunjan') | Q(emp_id='60278'),
        device_asset_id__icontains='077'
    ).update(device_asset_id=TARGET_WORKSTATION_TAG)

    DeviceComplaint.objects.filter(device_asset_id__icontains='077').delete()

    # 6. Ensure Gunjan's UserProfile has assigned_asset_id = PSM/IT/0826/016
    UserProfile.objects.filter(
        Q(emp_id='60278') | Q(full_name__icontains='Gunjan')
    ).update(assigned_asset_id=TARGET_WORKSTATION_TAG)


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0024_purge_079_lalshing_assets'),
    ]

    operations = [
        migrations.RunPython(reassign_077_and_clean, reverse_noop),
    ]
