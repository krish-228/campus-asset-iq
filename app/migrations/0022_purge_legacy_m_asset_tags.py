import re
from django.db import migrations

def purge_legacy_m_tags(apps, schema_editor):
    DeviceAsset = apps.get_model('app', 'DeviceAsset')
    CustodyTransferLog = apps.get_model('app', 'CustodyTransferLog')
    UserProfile = apps.get_model('app', 'UserProfile')
    DeviceComplaint = apps.get_model('app', 'DeviceComplaint')
    EquipmentPMS = apps.get_model('app', 'EquipmentPMS')
    EquipmentBreakdown = apps.get_model('app', 'EquipmentBreakdown')

    # 1. DeviceAsset
    for dev in DeviceAsset.objects.all():
        if dev.asset_id and ('/M/' in dev.asset_id or '/m/' in dev.asset_id or re.match(r'^PSM/IT/[A-Za-z]/', dev.asset_id)):
            new_tag = re.sub(r'^PSM/IT/[A-Za-z]/', 'PSM/IT/', dev.asset_id, flags=re.IGNORECASE).replace('/M/', '/').replace('/m/', '/')
            dev.asset_id = new_tag
            dev.save(update_fields=['asset_id'])

    # 2. CustodyTransferLog
    for log in CustodyTransferLog.objects.all():
        if log.device_asset_id and ('/M/' in log.device_asset_id or '/m/' in log.device_asset_id or re.match(r'^PSM/IT/[A-Za-z]/', log.device_asset_id)):
            log.device_asset_id = re.sub(r'^PSM/IT/[A-Za-z]/', 'PSM/IT/', log.device_asset_id, flags=re.IGNORECASE).replace('/M/', '/').replace('/m/', '/')
            log.save(update_fields=['device_asset_id'])

    # 3. UserProfile assigned_asset_id
    for u in UserProfile.objects.all():
        if u.assigned_asset_id and ('/M/' in u.assigned_asset_id or '/m/' in u.assigned_asset_id or re.match(r'^PSM/IT/[A-Za-z]/', u.assigned_asset_id)):
            u.assigned_asset_id = re.sub(r'^PSM/IT/[A-Za-z]/', 'PSM/IT/', u.assigned_asset_id, flags=re.IGNORECASE).replace('/M/', '/').replace('/m/', '/')
            u.save(update_fields=['assigned_asset_id'])

    # 4. DeviceComplaint
    for c in DeviceComplaint.objects.all():
        if hasattr(c, 'device_asset_id') and c.device_asset_id and ('/M/' in c.device_asset_id or '/m/' in c.device_asset_id or re.match(r'^PSM/IT/[A-Za-z]/', c.device_asset_id)):
            c.device_asset_id = re.sub(r'^PSM/IT/[A-Za-z]/', 'PSM/IT/', c.device_asset_id, flags=re.IGNORECASE).replace('/M/', '/').replace('/m/', '/')
            c.save(update_fields=['device_asset_id'])

    # 5. EquipmentBreakdown
    for b in EquipmentBreakdown.objects.all():
        if hasattr(b, 'asset_id') and b.asset_id and ('/M/' in b.asset_id or '/m/' in b.asset_id or re.match(r'^PSM/IT/[A-Za-z]/', b.asset_id)):
            b.asset_id = re.sub(r'^PSM/IT/[A-Za-z]/', 'PSM/IT/', b.asset_id, flags=re.IGNORECASE).replace('/M/', '/').replace('/m/', '/')
            b.save(update_fields=['asset_id'])

    # 6. EquipmentPMS
    for pms in EquipmentPMS.objects.all():
        if hasattr(pms, 'asset_id') and pms.asset_id and ('/M/' in pms.asset_id or '/m/' in pms.asset_id or re.match(r'^PSM/IT/[A-Za-z]/', pms.asset_id)):
            pms.asset_id = re.sub(r'^PSM/IT/[A-Za-z]/', 'PSM/IT/', pms.asset_id, flags=re.IGNORECASE).replace('/M/', '/').replace('/m/', '/')
            pms.save(update_fields=['asset_id'])

class Migration(migrations.Migration):

    dependencies = [
        ('app', '0021_cleanup_dummy_specs'),
    ]

    operations = [
        migrations.RunPython(purge_legacy_m_tags, reverse_code=migrations.RunPython.noop),
    ]
