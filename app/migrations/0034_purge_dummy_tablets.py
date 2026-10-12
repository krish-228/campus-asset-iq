# Generated migration for purging seeded dummy clinical tablets

from django.db import migrations


def purge_dummy_hospital_tablets(apps, schema_editor):
    DeviceAsset = apps.get_model('app', 'DeviceAsset')
    CustodyTransferLog = apps.get_model('app', 'CustodyTransferLog')

    dummy_dev_ids = [
        'dev-tab-0771',
        'dev-tab-0782',
        'dev-tab-0793',
        'dev-tab-0804',
        'dev-tab-0815',
        'dev-tab-0826'
    ]

    # Delete any transfer logs related to these dummy tablets
    CustodyTransferLog.objects.filter(device__dev_id__in=dummy_dev_ids).delete()
    CustodyTransferLog.objects.filter(device_asset_id__in=[
        'PSM/IT/0826/077',
        'PSM/IT/0826/078',
        'PSM/IT/0826/079',
        'PSM/IT/0826/080',
        'PSM/IT/0826/081',
        'PSM/IT/0826/082'
    ], remarks__icontains='Tablet').delete()

    # Delete the dummy tablet devices
    DeviceAsset.objects.filter(dev_id__in=dummy_dev_ids).delete()
    DeviceAsset.objects.filter(dev_id__startswith='dev-tab-').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0033_clean_cpu_tablet_specs'),
    ]

    operations = [
        migrations.RunPython(purge_dummy_hospital_tablets, reverse_code=migrations.RunPython.noop),
    ]
