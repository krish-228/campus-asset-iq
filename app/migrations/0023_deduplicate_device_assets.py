from collections import defaultdict
from django.db import migrations

def deduplicate_device_assets(apps, schema_editor):
    DeviceAsset = apps.get_model('app', 'DeviceAsset')
    to_delete_ids = set()

    # 1. Duplicate devices within the exact same asset_id
    by_asset = defaultdict(list)
    for dev in DeviceAsset.objects.all().order_by('id'):
        tag = (dev.asset_id or '').strip().upper()
        if tag:
            by_asset[tag].append(dev)

    for tag, devs in by_asset.items():
        by_type = defaultdict(list)
        for d in devs:
            dt = (d.device_type or '').strip().upper()
            by_type[dt].append(d)

        for dt, type_devs in by_type.items():
            if len(type_devs) > 1:
                # Group by serial number
                by_sn = defaultdict(list)
                for td in type_devs:
                    sn = (td.serial_number or '').strip().upper()
                    by_sn[sn].append(td)

                for sn, sn_devs in by_sn.items():
                    if len(sn_devs) > 1:
                        sorted_sn = sorted(sn_devs, key=lambda x: (x.updated_at or x.created_at, x.id), reverse=True)
                        keep = sorted_sn[0]
                        for rem in sorted_sn[1:]:
                            to_delete_ids.add(rem.id)

                # Special CPU check: if one CPU has auto-generated SN-PSM-CPU- and another has genuine hardware SN
                if dt == 'CPU' and len(type_devs) > 1:
                    real_cpus = [d for d in type_devs if d.serial_number and not d.serial_number.startswith('SN-PSM-') and d.serial_number.upper() not in ('NA', 'N/A', '-')]
                    dummy_cpus = [d for d in type_devs if not d.serial_number or d.serial_number.startswith('SN-PSM-') or d.serial_number.upper() in ('NA', 'N/A', '-')]
                    if real_cpus and dummy_cpus:
                        for dc in dummy_cpus:
                            to_delete_ids.add(dc.id)

    # 2. Duplicate workstation sets for the same custodian
    by_custodian = defaultdict(list)
    for dev in DeviceAsset.objects.exclude(assigned_user_name__in=['', 'Unassigned']).order_by('id'):
        if dev.id in to_delete_ids:
            continue
        cust = (dev.assigned_user_name or '').strip().lower()
        if cust:
            by_custodian[cust].append(dev)

    for cust, devs in by_custodian.items():
        by_component = defaultdict(list)
        for d in devs:
            dt_clean = d.device_type.strip().upper() if d.device_type else 'OTHER'
            sn_clean = (d.serial_number or '').strip().upper()
            by_component[(dt_clean, sn_clean)].append(d)

        for (dt_clean, sn_clean), c_devs in by_component.items():
            if len(c_devs) > 1:
                sorted_c = sorted(c_devs, key=lambda x: (x.updated_at or x.created_at, x.id), reverse=True)
                keep = sorted_c[0]
                for rem in sorted_c[1:]:
                    to_delete_ids.add(rem.id)

        # Check if custodian has 2 CPUs (one real, one placeholder)
        cust_cpus = [d for d in devs if (d.device_type or '').strip().upper() == 'CPU' and d.id not in to_delete_ids]
        if len(cust_cpus) > 1:
            real_cpus = [d for d in cust_cpus if d.serial_number and not d.serial_number.startswith('SN-PSM-') and d.serial_number.upper() not in ('NA', 'N/A', '-')]
            dummy_cpus = [d for d in cust_cpus if not d.serial_number or d.serial_number.startswith('SN-PSM-') or d.serial_number.upper() in ('NA', 'N/A', '-')]
            if real_cpus and dummy_cpus:
                for dc in dummy_cpus:
                    to_delete_ids.add(dc.id)

    # 3. Check generic peripherals (Display NA, Keyboard NA, etc.) for same custodian
    for cust, devs in by_custodian.items():
        for comp_type in ['DISPLAY', 'KEYBOARD', 'MOUSE', 'UPS']:
            type_rows = [d for d in devs if (d.device_type or '').strip().upper() == comp_type and d.id not in to_delete_ids]
            if len(type_rows) > 1:
                na_rows = [d for d in type_rows if not d.serial_number or d.serial_number.upper() in ('NA', 'N/A', '-', '')]
                if len(na_rows) > 1:
                    sorted_na = sorted(na_rows, key=lambda x: (x.updated_at or x.created_at, x.id), reverse=True)
                    for rem in sorted_na[1:]:
                        to_delete_ids.add(rem.id)

    if to_delete_ids:
        DeviceAsset.objects.filter(id__in=to_delete_ids).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('app', '0022_purge_legacy_m_asset_tags'),
    ]

    operations = [
        migrations.RunPython(deduplicate_device_assets, reverse_code=migrations.RunPython.noop),
    ]
