# Generated migration to restore Hitakshi Nayak's workstation from phantom tag PSM/IT/0926/076 back to canonical tag PSM/IT/0826/008

from django.db import migrations
from django.db.models import Q


def restore_workstation_008(apps, schema_editor):
    DeviceAsset = apps.get_model('app', 'DeviceAsset')
    CustodyTransferLog = apps.get_model('app', 'CustodyTransferLog')
    DeviceComplaint = apps.get_model('app', 'DeviceComplaint')
    UserProfile = apps.get_model('app', 'UserProfile')

    OLD_TAG = 'PSM/IT/0926/076'
    RESTORED_TAG = 'PSM/IT/0826/008'

    # Update all DeviceAsset records under 076 to 008
    DeviceAsset.objects.filter(
        Q(asset_id__iexact=OLD_TAG) | Q(asset_id__iendswith='/076') | Q(asset_id__icontains='076')
    ).update(
        asset_id=RESTORED_TAG,
        room_name='Cardiology OPD / 03',
        floor_name='Ground Floor',
        building_name='PSM Hospital',
        assigned_user_name='Hitakshi Nayak',
        assigned_emp_id='68050',
        assigned_designation='Nursing Staff',
        assigned_department='Cardiology OPD',
        status='Active',
        org_id='HOSP',
        org_name='PSM Hospital'
    )

    # Also update any transfer logs, complaints, and user profiles
    CustodyTransferLog.objects.filter(
        Q(device_asset_id__iexact=OLD_TAG) | Q(device_asset_id__icontains='076')
    ).update(
        device_asset_id=RESTORED_TAG,
        to_user_name='Hitakshi Nayak',
        to_emp_id='68050'
    )

    DeviceComplaint.objects.filter(
        Q(device_asset_id__iexact=OLD_TAG) | Q(device_asset_id__icontains='076')
    ).update(
        device_asset_id=RESTORED_TAG,
        user_full_name='Hitakshi Nayak',
        emp_id='68050'
    )

    UserProfile.objects.filter(
        Q(assigned_asset_id__iexact=OLD_TAG) | Q(assigned_asset_id__icontains='076')
    ).update(
        assigned_asset_id=RESTORED_TAG
    )

    # Safety purge any residual phantom tags above 075 if any exist
    DeviceAsset.objects.filter(asset_id__in=['PSM/IT/0826/077', 'PSM/IT/0826/078', 'PSM/IT/1026/078']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0034_purge_dummy_tablets'),
    ]

    operations = [
        migrations.RunPython(restore_workstation_008, reverse_code=migrations.RunPython.noop),
    ]
