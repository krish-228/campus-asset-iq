from django.db import migrations


def clean_non_tablet_specs(apps, schema_editor):
    DeviceAsset = apps.get_model('app', 'DeviceAsset')
    # 1. Non-tablet devices should never have tablet_spec
    DeviceAsset.objects.exclude(device_type__iexact='Tablet').update(tablet_spec='')
    # 2. Non-printer devices should never have printer_spec
    DeviceAsset.objects.exclude(device_type__iexact='Printer').update(printer_spec='')
    # 3. Non-UPS devices should never have ups_spec
    DeviceAsset.objects.exclude(device_type__iexact='UPS').update(ups_spec='')


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0032_seed_hospital_clinical_tablets'),
    ]

    operations = [
        migrations.RunPython(clean_non_tablet_specs, migrations.RunPython.noop),
    ]
