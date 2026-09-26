from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import (
    DeviceAsset,
    CustodyTransferLog,
    DeviceComplaint,
    EquipmentPMS,
    EquipmentBreakdown,
    UserProfile,
)

class Command(BaseCommand):
    help = "Permanently wipes all devices, complaints, breakdown records, PMS schedules, and test users from the database."

    def add_arguments(self, parser):
        parser.add_argument(
            '--yes',
            action='store_true',
            help='Bypass confirmation prompt and proceed immediately with deletion.',
        )

    def handle(self, *args, **options):
        if not options.get('yes'):
            self.stdout.write(self.style.WARNING(
                "WARNING: This will permanently delete ALL hardware assets, complaints, "
                "breakdown records, PMS logs, and test staff from the database."
            ))
            confirm = input("Type 'CONFIRM' to proceed: ")
            if confirm.strip() != 'CONFIRM':
                self.stdout.write(self.style.ERROR("Aborted. No data was deleted."))
                return

        dev_count = DeviceAsset.objects.count()
        trans_count = CustodyTransferLog.objects.count()
        comp_count = DeviceComplaint.objects.count()
        pms_count = EquipmentPMS.objects.count()
        bd_count = EquipmentBreakdown.objects.count()

        DeviceAsset.objects.all().delete()
        CustodyTransferLog.objects.all().delete()
        DeviceComplaint.objects.all().delete()
        EquipmentPMS.objects.all().delete()
        EquipmentBreakdown.objects.all().delete()

        # Delete non-admin test profiles & users, preserving system administrators
        prof_count = UserProfile.objects.filter(user__is_staff=False, user__is_superuser=False).count()
        UserProfile.objects.filter(user__is_staff=False, user__is_superuser=False).delete()
        user_count = User.objects.filter(is_staff=False, is_superuser=False).count()
        User.objects.filter(is_staff=False, is_superuser=False).delete()

        self.stdout.write(self.style.SUCCESS(
            f"Successfully purged database to a 100% clean slate:\n"
            f" - Deleted {dev_count} DeviceAsset records\n"
            f" - Deleted {trans_count} CustodyTransferLog records\n"
            f" - Deleted {comp_count} DeviceComplaint records\n"
            f" - Deleted {pms_count} EquipmentPMS records\n"
            f" - Deleted {bd_count} EquipmentBreakdown records\n"
            f" - Deleted {prof_count} test UserProfile records\n"
            f" - Deleted {user_count} test User records\n"
            f"Admin accounts preserved. Database is 100% clean!"
        ))
