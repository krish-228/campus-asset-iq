from django.db import migrations

def cleanup_dummy_specs(apps, schema_editor):
    DeviceAsset = apps.get_model('app', 'DeviceAsset')
    dummy_phrases = [
        'HARDWARE DISPLAY MONITOR',
        'CONNECTED DISPLAY MONITOR',
        'HARDWARE DISPLAY',
        'HARDWARE PERIPHERAL (HID)',
        'HARDWARE PERIPHERAL',
        'HARDWARE ACCESSORY / PERIPHERAL',
        'HARDWARE ACCESSORY',
        'STANDARD HARDWARE COMPONENT',
        'CAMPUS CLINICAL HARDWARE UNIT',
        'DIRECT PRINT UNIT',
        'PRINTER FIRMWARE',
        'MOBILE WORKSTATION UNIT',
        'MOBILE OS',
        'AC POWER PROTECTION',
        'POWER UNIT',
        'MICROCONTROLLER POWER FIRMWARE',
        'HARDWARE FIRMWARE',
        'FIRMWARE EMBEDDED',
        'WORKSTATION OS',
        'WORKSTATION PROCESSOR UNIT',
        'WORKSTATION COMPUTE ENGINE',
        'STANDARD RAM & STORAGE',
        'SYSTEM RAM & NVME STORAGE',
    ]

    for dev in DeviceAsset.objects.all():
        updated = False
        ram_up = (dev.storage_ram or '').strip().upper()
        os_up = (dev.operating_system or '').strip().upper()

        for phrase in dummy_phrases:
            if phrase in ram_up:
                dev.storage_ram = ''
                updated = True
                break

        for phrase in dummy_phrases:
            if phrase in os_up:
                dev.operating_system = ''
                updated = True
                break

        if updated:
            dev.save(update_fields=['storage_ram', 'operating_system'])

class Migration(migrations.Migration):

    dependencies = [
        ('app', '0020_cleanup_auto_defaulted_brands'),
    ]

    operations = [
        migrations.RunPython(cleanup_dummy_specs, reverse_code=migrations.RunPython.noop),
    ]
