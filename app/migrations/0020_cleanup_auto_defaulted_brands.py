from django.db import migrations

def cleanup_auto_defaulted_brands(apps, schema_editor):
    DeviceAsset = apps.get_model('app', 'DeviceAsset')
    for dev in DeviceAsset.objects.all():
        b_up = (dev.brand_name or '').strip().upper()
        m_up = (dev.cpu_processor or dev.monitor_spec or dev.keyboard_spec or dev.mouse_spec or '').upper()

        if b_up in ('STANDARD OEM', '—', '-', 'N/A', 'NONE', 'UNKNOWN', 'NULL', 'UNASSIGNED'):
            dev.brand_name = ''
            dev.save(update_fields=['brand_name'])

class Migration(migrations.Migration):

    dependencies = [
        ('app', '0019_purge_all_live_data'),
    ]

    operations = [
        migrations.RunPython(cleanup_auto_defaulted_brands, reverse_code=migrations.RunPython.noop),
    ]
