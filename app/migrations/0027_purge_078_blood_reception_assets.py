from django.db import migrations
from django.db.models import Q

def purge_078_assets(apps, schema_editor):
    DeviceAsset = apps.get_model('app', 'DeviceAsset')
    CustodyTransferLog = apps.get_model('app', 'CustodyTransferLog')
    DeviceComplaint = apps.get_model('app', 'DeviceComplaint')

    # 1. Purge matching devices from DeviceAsset
    dev_query = (
        Q(asset_id__icontains='078') |
        Q(asset_id__iendswith='/078') |
        Q(serial_number__in=['SN-PSM-CPU-9183', 'SN-PSM-DIS-1619'])
    )
    DeviceAsset.objects.filter(dev_query).delete()

    # 2. Purge custody transfer logs
    log_query = Q(device_asset_id__icontains='078')
    CustodyTransferLog.objects.filter(log_query).delete()

    # 3. Purge complaints
    comp_query = Q(device_asset_id__icontains='078')
    DeviceComplaint.objects.filter(comp_query).delete()


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0026_deduplicate_hitakshi_workstation'),
    ]

    operations = [
        migrations.RunPython(purge_078_assets, reverse_noop),
    ]
