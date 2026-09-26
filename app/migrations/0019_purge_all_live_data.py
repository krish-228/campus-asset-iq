from django.db import migrations


def purge_all_live_data(apps, schema_editor):
    DeviceAsset = apps.get_model('app', 'DeviceAsset')
    CustodyTransferLog = apps.get_model('app', 'CustodyTransferLog')
    DeviceComplaint = apps.get_model('app', 'DeviceComplaint')
    EquipmentPMS = apps.get_model('app', 'EquipmentPMS')
    EquipmentBreakdown = apps.get_model('app', 'EquipmentBreakdown')
    UserProfile = apps.get_model('app', 'UserProfile')
    User = apps.get_model('auth', 'User')

    # Purge all hardware assets, custody logs, tickets, PMS, and breakdown history
    DeviceAsset.objects.all().delete()
    CustodyTransferLog.objects.all().delete()
    DeviceComplaint.objects.all().delete()
    EquipmentPMS.objects.all().delete()
    EquipmentBreakdown.objects.all().delete()

    # Purge non-admin test users while preserving system administrators
    UserProfile.objects.filter(user__is_staff=False, user__is_superuser=False).delete()
    User.objects.filter(is_staff=False, is_superuser=False).delete()


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0018_unify_workstation_asset_ids'),
    ]

    operations = [
        migrations.RunPython(purge_all_live_data, reverse_noop),
    ]
