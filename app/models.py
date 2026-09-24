from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    emp_id = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=150)
    org_id = models.CharField(max_length=20, choices=[('UNI', 'Swaminarayan University'), ('HOSP', 'PSM Hospital')], default='UNI')
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    assigned_asset_id = models.CharField(max_length=50, blank=True, help_text="e.g. IT-PC-00125 or HOSP-ICU-00042")
    password = models.CharField(max_length=150, blank=True, default='', help_text="Staff portal account password")

    def __str__(self):
        return f"{self.full_name} ({self.emp_id}) - {self.org_id}"


class DeviceComplaint(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending Review'),
        ('In Progress', 'In Progress / Assigned'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('Normal', 'Normal'),
        ('High', 'High Priority'),
        ('Critical', 'Critical / Emergency'),
    ]

    ISSUE_CHOICES = [
        ('Hardware Fault', 'Hardware Fault (CPU / Motherboard / RAM / PSU)'),
        ('Display & Screen', 'Display / Monitor Flickering / No Signal'),
        ('Network & Internet', 'Network Drop / Ethernet / Wi-Fi Disconnect'),
        ('OS & Software Crash', 'Operating System Crash / Blue Screen / Freezing'),
        ('Peripherals Damage', 'Damaged Keyboard / Mouse / Accessories'),
        ('Location Relocation', 'Request Physical Shift to Another Lab/Ward'),
        ('Other Issue', 'Other Technical Issue'),
    ]

    ticket_id = models.CharField(max_length=30, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints')
    user_full_name = models.CharField(max_length=150)
    emp_id = models.CharField(max_length=50, blank=True)
    user_email = models.CharField(max_length=150, blank=True)
    user_dept = models.CharField(max_length=100, blank=True)
    org_id = models.CharField(max_length=20, choices=[('UNI', 'Swaminarayan University'), ('HOSP', 'PSM Hospital')], default='UNI')
    
    device_asset_id = models.CharField(max_length=50)
    room_location = models.CharField(max_length=100, blank=True)
    
    issue_category = models.CharField(max_length=100, choices=ISSUE_CHOICES, default='Hardware Fault')
    priority = models.CharField(max_length=30, choices=PRIORITY_CHOICES, default='Normal')
    subject = models.CharField(max_length=200)
    description = models.TextField()
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pending')
    admin_remarks = models.TextField(blank=True, default='')
    technician_name = models.CharField(max_length=100, blank=True, default='IT Desk Team')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.ticket_id}] {self.device_asset_id} - {self.status}"


class DeviceAsset(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('In Maintenance', 'In Maintenance'),
        ('Decommissioned', 'Decommissioned'),
    ]

    dev_id = models.CharField(max_length=50, unique=True, help_text="e.g. dev-01")
    asset_id = models.CharField(max_length=50, db_index=True, help_text="e.g. IT-PC-00125")
    device_type = models.CharField(max_length=100, blank=True, default='CPU', help_text="e.g. CPU, Display, Keyboard, Mouse, Printer")
    brand_name = models.CharField(max_length=100, blank=True, default="", help_text="e.g. Dell, HP, Lenovo, Logitech, Zebra, APC, Samsung")
    serial_number = models.CharField(max_length=100, blank=True)
    org_id = models.CharField(max_length=20, choices=[('UNI', 'Swaminarayan University'), ('HOSP', 'PSM Hospital')], default='UNI')
    org_name = models.CharField(max_length=100, blank=True)
    building_name = models.CharField(max_length=100, blank=True)
    floor_name = models.CharField(max_length=100, blank=True)
    room_name = models.CharField(max_length=100, blank=True)
    
    assigned_user_id = models.CharField(max_length=50, blank=True, null=True)
    assigned_user_name = models.CharField(max_length=150, blank=True, default="Unassigned")
    assigned_emp_id = models.CharField(max_length=50, blank=True)
    assigned_designation = models.CharField(max_length=150, blank=True, default="")
    assigned_department = models.CharField(max_length=150, blank=True, default="")
    assigned_email = models.CharField(max_length=150, blank=True, default="")
    assigned_phone = models.CharField(max_length=50, blank=True, default="")
    
    monitor_spec = models.CharField(max_length=255, blank=True)
    cpu_processor = models.CharField(max_length=255, blank=True)
    storage_ram = models.CharField(max_length=255, blank=True)
    keyboard_spec = models.CharField(max_length=255, blank=True, default="")
    mouse_spec = models.CharField(max_length=255, blank=True, default="")
    printer_spec = models.CharField(max_length=255, blank=True, default="")
    ups_spec = models.CharField(max_length=255, blank=True, default="")
    tablet_spec = models.CharField(max_length=255, blank=True, default="")
    ip_address = models.CharField(max_length=50, blank=True)
    mac_address = models.CharField(max_length=50, blank=True)
    device_id = models.CharField(max_length=100, blank=True, default="", help_text="Hardware / Tablet Device ID")
    anydesk_id = models.CharField(max_length=100, blank=True, default="", help_text="AnyDesk Remote ID")
    operating_system = models.CharField(max_length=100, blank=True)
    purchase_date = models.CharField(max_length=50, blank=True)
    warranty_expiry_date = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Active')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['asset_id']

    def __str__(self):
        return f"{self.asset_id} - {self.assigned_user_name}"


class CustodyTransferLog(models.Model):
    device = models.ForeignKey(DeviceAsset, on_delete=models.CASCADE, related_name='custody_logs', null=True, blank=True)
    device_asset_id = models.CharField(max_length=50)
    from_user_name = models.CharField(max_length=150, default="Unassigned")
    from_emp_id = models.CharField(max_length=50, blank=True)
    to_user_name = models.CharField(max_length=150)
    to_emp_id = models.CharField(max_length=50, blank=True)
    handover_date = models.CharField(max_length=50)
    assigned_by = models.CharField(max_length=100, default="IT Admin Desk")
    remarks = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.device_asset_id}: {self.from_user_name} -> {self.to_user_name} ({self.handover_date})"


class EquipmentPMS(models.Model):
    FREQUENCY_CHOICES = [
        ('QUARTERLY', 'Quarterly (Every 3 Months)'),
        ('HALF-YEARLY', 'Half-Yearly (Every 6 Months)'),
        ('ANNUALLY', 'Annually (Once a Year)'),
        ('MONTHLY', 'Monthly (Every Month)'),
    ]

    STATUS_CHOICES = [
        ('Completed', 'All Cycles Completed'),
        ('Pending 4th PMS', 'Pending 4th PMS'),
        ('Due Soon', 'Upcoming Due'),
        ('Overdue', 'Service Overdue'),
    ]

    equipment_name = models.CharField(max_length=150, default='Computer', help_text="e.g. Computer, ICU Monitor, Laptop")
    company_name = models.CharField(max_length=100, default='HP', help_text="e.g. HP, Dell, Lenovo, GE Healthcare")
    installation_date = models.CharField(max_length=50, default='08-11-2021', help_text="Installation Date (DD-MM-YYYY)")
    asset_code = models.CharField(max_length=100, unique=True, help_text="e.g. KH/IT/COMPUTER/1")
    maintenance_frequency = models.CharField(max_length=50, choices=FREQUENCY_CHOICES, default='QUARTERLY')
    
    # 1st Cycle
    pms1_done_date = models.CharField(max_length=50, default='08-08-2022', help_text="1st PMS Done Date")
    
    # 2nd Cycle
    pms2_due_date = models.CharField(max_length=50, default='08-11-2022', help_text="Due Date of 2nd PMS")
    pms2_done_date = models.CharField(max_length=50, default='09-11-2022', help_text="2nd PMS Done Date")
    
    # 3rd Cycle
    pms3_due_date = models.CharField(max_length=50, default='09-02-2023', help_text="Due Date of 3rd PMS")
    pms3_done_date = models.CharField(max_length=50, default='09-02-2023', help_text="3rd PMS Done Date")
    
    # 4th Cycle
    pms4_due_date = models.CharField(max_length=50, default='09-05-2023', help_text="Due Date of 4th PMS")
    pms4_done_date = models.CharField(max_length=50, blank=True, default='', help_text="4th PMS Done Date (if completed)")

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending 4th PMS')
    department_location = models.CharField(max_length=150, blank=True, default='IT Lab 101')
    engineer_notes = models.TextField(blank=True, default='Quarterly system fan blow-out, thermal paste check, power supply testing and OS health diagnostic completed.')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Equipment PMS Record'
        verbose_name_plural = 'Equipment PMS Records'

    def __str__(self):
        return f"{self.asset_code} - {self.equipment_name} ({self.company_name})"


class EquipmentBreakdown(models.Model):
    DEVICE_NAME_CHOICES = [
        ('Monitor', 'Monitor'),
        ('CPU', 'CPU'),
        ('Keyboard', 'Keyboard'),
        ('Mouse', 'Mouse'),
        ('UPS', 'UPS'),
        ('Laser Printer', 'Laser Printer'),
        ('Barcode Printer', 'Barcode Printer'),
        ('Scanner', 'Scanner'),
        ('Other', 'Other'),
    ]

    EQUIPMENT_TYPE_CHOICES = [
        ('Critical', 'Critical'),
        ('Routine', 'Routine'),
    ]

    STATUS_CHOICES = [
        ('Resolved', 'Resolved (Repaired)'),
        ('Under Repair', 'Under Active Repair'),
        ('Pending Review', 'Pending Department Review'),
    ]

    breakdown_date = models.CharField(max_length=50, default='26/07/2022', help_text="e.g. 26/07/2022 or 02/09/2026")
    breakdown_time = models.CharField(max_length=50, default='2:00 pm', help_text="e.g. 2:00 pm or 14:30")
    asset_id = models.CharField(max_length=100, default='IT-PC-00101', help_text="e.g. IT-PC-00101 or Asset Code")
    device_name = models.CharField(max_length=100, choices=DEVICE_NAME_CHOICES, default='CPU', help_text="IT Device Name")
    breakdown_cause = models.TextField(default='Hardware malfunction', help_text="Breakdown Cause / Issue description")
    equipment_type = models.CharField(max_length=50, choices=EQUIPMENT_TYPE_CHOICES, default='Routine', help_text="Critical or Routine")
    intimation_datetime = models.CharField(max_length=100, default='26/07/2022 2:10 pm', help_text="Intimation date & time to IT CELL")
    checkin_datetime = models.CharField(max_length=100, default='26/07/2022 2:20 pm', help_text="IT CELL Checkin Date & Time")
    dept_hod_name = models.CharField(max_length=150, blank=True, default='Dr. Rajesh Sharma', help_text="Name of Departmental HOD")
    it_staff_name = models.CharField(max_length=150, blank=True, default='Er. Amit Verma (IT CELL)', help_text="Name of IT CELL / BME staff")
    repair_datetime = models.CharField(max_length=100, blank=True, default='26/07/2022 2:35 pm', help_text="Repair Date & Time")
    tat_duration = models.CharField(max_length=100, blank=True, default='35 minutes', help_text="Total Turn Around Time (TAT)")
    sign_dept_hod = models.CharField(max_length=150, blank=True, default='Dr. Rajesh Sharma (Verified)', help_text="Sign of Departmental HOD")
    sign_it_cell = models.CharField(max_length=150, blank=True, default='Er. Amit Verma (IT CELL)', help_text="Sign of IT CELL")
    location = models.CharField(max_length=150, blank=True, default='', help_text="Department / Room / Location")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Resolved')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Equipment Breakdown'
        verbose_name_plural = 'Equipment Breakdowns'

    def __str__(self):
        return f"#{self.id} - {self.asset_id} ({self.device_name}) - {self.equipment_type}"

    @property
    def display_breakdown_date(self):
        """Format date with / instead of ."""
        val = (self.breakdown_date or '').strip()
        return val.replace('.', '/')

    @property
    def display_breakdown_time(self):
        """Format time with : instead of ."""
        import re
        val = (self.breakdown_time or '').strip()
        return re.sub(r'(\d+)\.(\d+)', r'\1:\2', val)

    @property
    def display_intimation_datetime(self):
        """Format intimation datetime with / for date and : for time."""
        import re
        val = (self.intimation_datetime or '').strip()
        parts = val.split(' ', 1)
        if len(parts) == 2:
            d_part = parts[0].replace('.', '/')
            t_part = re.sub(r'(\d+)\.(\d+)', r'\1:\2', parts[1])
            return f"{d_part} {t_part}"
        return re.sub(r'(\d+)\.(\d+)', r'\1:\2', val.replace('.', '/'))

    @property
    def display_checkin_datetime(self):
        """Format checkin datetime with / for date and : for time."""
        import re
        val = (self.checkin_datetime or '').strip()
        parts = val.split(' ', 1)
        if len(parts) == 2:
            d_part = parts[0].replace('.', '/')
            t_part = re.sub(r'(\d+)\.(\d+)', r'\1:\2', parts[1])
            return f"{d_part} {t_part}"
        return re.sub(r'(\d+)\.(\d+)', r'\1:\2', val.replace('.', '/'))

    @property
    def display_repair_datetime(self):
        """Format repair datetime with / for date and : for time."""
        val = (self.repair_datetime or '').strip()
        if not val:
            return ''
        import re
        parts = val.split(' ', 1)
        if len(parts) == 2:
            d_part = parts[0].replace('.', '/')
            t_part = re.sub(r'(\d+)\.(\d+)', r'\1:\2', parts[1])
            return f"{d_part} {t_part}"
        return re.sub(r'(\d+)\.(\d+)', r'\1:\2', val.replace('.', '/'))




