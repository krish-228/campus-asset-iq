from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
import json
import urllib.parse
import random
from django.db import models
from .models import DeviceComplaint, UserProfile, DeviceAsset, CustodyTransferLog, EquipmentPMS, EquipmentBreakdown

# ============================================================================
# REALISTIC CAMPUS HARDWARE & STAFF CATALOG
# ============================================================================

SAMPLE_STAFF = [
    {
        'id': 'usr-dr-sharma',
        'empId': 'MED-00042',
        'username': 'dr_sharma',
        'fullName': 'Dr. Vikram Sharma',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'department': 'Emergency & Critical Care',
        'designation': 'Chief Intensivist / HOD',
        'email': 'vikram.sharma@hospital.org',
        'phone': '9811223344',
        'assignedAssetId': 'PSM/IT/2F/C-201'
    },
    {
        'id': 'usr-nurse-kavita',
        'empId': 'MED-00115',
        'username': 'kavita',
        'fullName': 'Kavita Nair',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'department': 'ICU Nursing',
        'designation': 'Senior Nursing Officer',
        'email': 'kavita.nair@hospital.org',
        'phone': '9877001122',
        'assignedAssetId': 'PSM/IT/2F/C-203'
    },
    {
        'id': 'usr-dr-mehta',
        'empId': 'MED-00078',
        'username': 'dr_mehta',
        'fullName': 'Dr. Aarti Mehta',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'department': 'Radiology',
        'designation': 'Consultant Radiologist',
        'email': 'aarti.mehta@hospital.org',
        'phone': '9900112233',
        'assignedAssetId': 'PSM/IT/GF/C-003'
    },
    {
        'id': 'usr-triage-nurse',
        'empId': 'MED-00142',
        'username': 'rekha',
        'fullName': 'Staff Nurse Rekha',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'department': 'Emergency & Trauma Care',
        'designation': 'Emergency Triage Officer',
        'email': 'rekha.menon@hospital.org',
        'phone': '9811442200',
        'assignedAssetId': 'PSM/IT/GF/C-001'
    },
    {
        'id': 'usr-bill-exec',
        'empId': 'MED-00205',
        'username': 'ramesh',
        'fullName': 'Ramesh Patel',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'department': 'Patient Billing & Registration',
        'designation': 'Senior Billing Executive',
        'email': 'ramesh.patel@hospital.org',
        'phone': '9866554433',
        'assignedAssetId': 'PSM/IT/1F/C-102'
    },
    {
        'id': 'usr-xray-tech',
        'empId': 'MED-00188',
        'username': 'suresh',
        'fullName': 'Suresh Verma',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'department': 'Radiology & Imaging',
        'designation': 'Chief Radiographer',
        'email': 'suresh.verma@hospital.org',
        'phone': '9877889900',
        'assignedAssetId': 'PSM/IT/GF/C-004'
    },
    {
        'id': 'usr-path-lead',
        'empId': 'MED-00064',
        'username': 'pooja',
        'fullName': 'Dr. Pooja Iyer',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'department': 'Central Pathology',
        'designation': 'Chief Clinical Pathologist',
        'email': 'pooja.iyer@hospital.org',
        'phone': '9822334455',
        'assignedAssetId': 'PSM/IT/5F/C-501'
    },
    {
        'id': 'usr-biomed-lead',
        'empId': 'MED-00030',
        'username': 'rajesh_bme',
        'fullName': 'Er. Rajesh Kulkarni',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'department': 'Biomedical Engineering',
        'designation': 'Chief Biomedical Engineer',
        'email': 'rajesh.bme@hospital.org',
        'phone': '9844001122',
        'assignedAssetId': 'PSM/IT/B/C-0.01'
    },
    {
        'id': 'usr-dr-joshi',
        'empId': 'MED-00055',
        'username': 'ananya_joshi',
        'fullName': 'Dr. Ananya Joshi',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'department': 'Surgical Sciences & OT',
        'designation': 'Senior Consultant Surgeon / OT Incharge',
        'email': 'ananya.joshi@hospital.org',
        'phone': '9833445566',
        'assignedAssetId': 'PSM/IT/3F/C-301'
    },
    {
        'id': 'usr-ward-nurse',
        'empId': 'MED-00164',
        'username': 'priya_ward',
        'fullName': 'Sister Priya Nair',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'department': 'Inpatient Care & Deluxe Wards',
        'designation': 'Senior Ward Incharge',
        'email': 'priya.ward@hospital.org',
        'phone': '9844556677',
        'assignedAssetId': 'PSM/IT/4F/C-401'
    }
]

SAMPLE_DEVICES = [
    # BASEMENT (Level -1) — Code: 0.01
    {
        'id': 'dev-bme-01',
        'assetId': 'PSM/IT/B/C-0.01',
        'deviceType': 'C',
        'serialNumber': 'SN-HP-DL380-15',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': 'Basement Floor',
        'roomName': 'Biomedical Engineering Workshop',
        'assignedUserId': 'usr-biomed-lead',
        'assignedUserName': 'Er. Rajesh Kulkarni',
        'empId': 'MED-00030',
        'monitorSpec': 'HP 24" Cleanable Industrial Console',
        'cpuProcessor': 'Intel Xeon E-2388G (8 cores, 5.1 GHz)',
        'storageRam': '2TB Enterprise NVMe / 64GB ECC RAM',
        'ipAddress': '10.20.0.15',
        'macAddress': 'A0-36-9F-12-88-01',
        'operatingSystem': 'Windows Server 2022 Datacenter',
        'purchaseDate': '10-Feb-2024',
        'warrantyExpiryDate': '09-Feb-2029',
        'status': 'Active'
    },
    {
        'id': 'dev-bme-m01',
        'assetId': 'PSM/IT/B/M-0.01',
        'deviceType': 'M',
        'serialNumber': 'SN-LOGI-BME-01',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': 'Basement Floor',
        'roomName': 'Biomedical Engineering Workshop',
        'assignedUserId': 'usr-biomed-lead',
        'assignedUserName': 'Er. Rajesh Kulkarni',
        'empId': 'MED-00030',
        'monitorSpec': 'N/A - Peripherals',
        'cpuProcessor': 'Logitech Optical Sensor (1000 DPI)',
        'storageRam': 'USB Plug-and-Play / 1.8m Shielded Cable',
        'ipAddress': '10.20.0.16',
        'macAddress': 'A0-36-9F-12-88-02',
        'operatingSystem': 'Hardware Peripheral (HID)',
        'purchaseDate': '10-Feb-2024',
        'warrantyExpiryDate': '09-Feb-2027',
        'status': 'Active'
    },
    {
        'id': 'dev-bme-k01',
        'assetId': 'PSM/IT/B/K-0.01',
        'deviceType': 'K',
        'serialNumber': 'SN-SEAL-KB-01',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': 'Basement Floor',
        'roomName': 'Biomedical Engineering Workshop',
        'assignedUserId': 'usr-biomed-lead',
        'assignedUserName': 'Er. Rajesh Kulkarni',
        'empId': 'MED-00030',
        'monitorSpec': 'N/A - Peripherals',
        'cpuProcessor': 'IP68 Waterproof Silicone Membrane Controller',
        'storageRam': 'USB Cleanable Keyboard / Antimicrobial',
        'ipAddress': '10.20.0.17',
        'macAddress': 'A0-36-9F-12-88-03',
        'operatingSystem': 'Hardware Peripheral (HID)',
        'purchaseDate': '10-Feb-2024',
        'warrantyExpiryDate': '09-Feb-2027',
        'status': 'Active'
    },
    {
        'id': 'dev-bme-p01',
        'assetId': 'PSM/IT/B/P-0.01',
        'deviceType': 'P',
        'serialNumber': 'SN-ZEBRA-ZD421-B1',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': 'Basement Floor',
        'roomName': 'Hospital IT Server & Telemetry Hub',
        'assignedUserId': 'usr-biomed-lead',
        'assignedUserName': 'Er. Rajesh Kulkarni',
        'empId': 'MED-00030',
        'monitorSpec': 'LED Status Matrix Panel',
        'cpuProcessor': 'ARM Cortex-A7 32-bit RISC Engine',
        'storageRam': '512GB Flash / 256MB SDRAM / Direct Thermal 203 DPI',
        'ipAddress': '10.20.0.18',
        'macAddress': 'A0-36-9F-12-88-04',
        'operatingSystem': 'Link-OS Enterprise',
        'purchaseDate': '10-Feb-2024',
        'warrantyExpiryDate': '09-Feb-2029',
        'status': 'Active'
    },
    # GROUND FLOOR (Level 0) — Code: 001..004
    {
        'id': 'dev-22',
        'assetId': 'PSM/IT/GF/C-001',
        'deviceType': 'C',
        'serialNumber': 'SN-HP-ED800-11',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': 'Ground Floor',
        'roomName': 'Emergency & Trauma Triage Desk 01',
        'assignedUserId': 'usr-triage-nurse',
        'assignedUserName': 'Staff Nurse Rekha',
        'empId': 'MED-00142',
        'monitorSpec': 'HP Healthcare Edition HC241 24" Cleanable',
        'cpuProcessor': 'Intel Core i5-10500 (6 cores, 3.1 GHz)',
        'storageRam': '512GB SSD / 16GB DDR4',
        'ipAddress': '10.20.10.11',
        'macAddress': 'B4-2E-99-12-34-56',
        'operatingSystem': 'Windows 11 Pro Medical Edition',
        'purchaseDate': '12-May-2024',
        'warrantyExpiryDate': '11-May-2027',
        'status': 'Active'
    },
    {
        'id': 'dev-23',
        'assetId': 'PSM/IT/GF/C-002',
        'deviceType': 'C',
        'serialNumber': 'SN-ZEBRA-TC52-01',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': 'Ground Floor',
        'roomName': 'Emergency & Trauma Triage Desk 01',
        'assignedUserId': '',
        'assignedUserName': 'Unassigned (Triage Pool)',
        'empId': '',
        'monitorSpec': '5.0" HD Antimicrobial Glove-Touch Display',
        'cpuProcessor': 'Qualcomm Snapdragon 660 Octa-Core 2.2 GHz',
        'storageRam': '64GB Flash / 4GB RAM',
        'ipAddress': '10.20.10.12',
        'macAddress': 'B4-2E-99-12-34-57',
        'operatingSystem': 'Android 13 Enterprise',
        'purchaseDate': '12-May-2024',
        'warrantyExpiryDate': '11-May-2026',
        'status': 'Active'
    },
    {
        'id': 'dev-08',
        'assetId': 'PSM/IT/GF/C-003',
        'deviceType': 'C',
        'serialNumber': 'SN-GE-MED-4410',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': 'Ground Floor',
        'roomName': 'CT / MRI Diagnostic Console 01',
        'assignedUserId': 'usr-dr-mehta',
        'assignedUserName': 'Dr. Aarti Mehta',
        'empId': 'MED-00078',
        'monitorSpec': 'Barco Coronis 3MP Diagnostic Grayscale Dual',
        'cpuProcessor': 'Intel Xeon W-2245 (8 cores, 4.5 GHz)',
        'storageRam': '4TB NVMe RAID / 64GB ECC DDR4',
        'ipAddress': '10.20.30.18',
        'macAddress': '70-85-C2-91-88-00',
        'operatingSystem': 'Windows 10 Enterprise LTSC',
        'purchaseDate': '10-Aug-2023',
        'warrantyExpiryDate': '09-Aug-2028',
        'status': 'Active'
    },
    {
        'id': 'dev-27',
        'assetId': 'PSM/IT/GF/C-004',
        'deviceType': 'C',
        'serialNumber': 'SN-PHIL-XR-22',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': 'Ground Floor',
        'roomName': 'Digital X-Ray Diagnostic Station',
        'assignedUserId': 'usr-xray-tech',
        'assignedUserName': 'Suresh Verma',
        'empId': 'MED-00188',
        'monitorSpec': 'Eizo Radiforce 3MP Grayscale Medical Diagnostic',
        'cpuProcessor': 'Intel Core i7-11700 (8 cores, 4.9 GHz)',
        'storageRam': '1TB NVMe SSD + 2TB PACS Local / 32GB DDR4',
        'ipAddress': '10.20.30.22',
        'macAddress': '70-85-C2-91-88-22',
        'operatingSystem': 'Windows 10 Enterprise LTSC',
        'purchaseDate': '15-Jul-2023',
        'warrantyExpiryDate': '14-Jul-2028',
        'status': 'Active'
    },
    {
        'id': 'dev-emg-m01',
        'assetId': 'PSM/IT/GF/M-001',
        'deviceType': 'M',
        'serialNumber': 'SN-LOGI-EMG-01',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': 'Ground Floor',
        'roomName': 'Emergency & Trauma Triage Desk 01',
        'assignedUserId': 'usr-triage-nurse',
        'assignedUserName': 'Staff Nurse Rekha',
        'empId': 'MED-00142',
        'monitorSpec': 'N/A - Peripherals',
        'cpuProcessor': 'Antimicrobial Optical Sensor (1200 DPI)',
        'storageRam': 'USB Cleanable Wired Mouse',
        'ipAddress': '10.20.10.13',
        'macAddress': 'B4-2E-99-12-34-60',
        'operatingSystem': 'Hardware Peripheral (HID)',
        'purchaseDate': '12-May-2024',
        'warrantyExpiryDate': '11-May-2027',
        'status': 'Active'
    },
    {
        'id': 'dev-emg-k01',
        'assetId': 'PSM/IT/GF/K-001',
        'deviceType': 'K',
        'serialNumber': 'SN-SEAL-EMG-01',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': 'Ground Floor',
        'roomName': 'Emergency & Trauma Triage Desk 01',
        'assignedUserId': 'usr-triage-nurse',
        'assignedUserName': 'Staff Nurse Rekha',
        'empId': 'MED-00142',
        'monitorSpec': 'N/A - Peripherals',
        'cpuProcessor': 'Silicone Sealed Membrane Keyboard',
        'storageRam': 'USB Disinfectable Hospital Keyboard',
        'ipAddress': '10.20.10.14',
        'macAddress': 'B4-2E-99-12-34-61',
        'operatingSystem': 'Hardware Peripheral (HID)',
        'purchaseDate': '12-May-2024',
        'warrantyExpiryDate': '11-May-2027',
        'status': 'Active'
    },
    {
        'id': 'dev-emg-p01',
        'assetId': 'PSM/IT/GF/P-001',
        'deviceType': 'P',
        'serialNumber': 'SN-ZEBRA-HC100-G1',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': 'Ground Floor',
        'roomName': 'Emergency & Trauma Triage Desk 01',
        'assignedUserId': 'usr-triage-nurse',
        'assignedUserName': 'Staff Nurse Rekha',
        'empId': 'MED-00142',
        'monitorSpec': 'Cartridge Status Display',
        'cpuProcessor': 'Zebra ZPL-II Thermal Core Processor',
        'storageRam': 'Patient ID Wristband 300 DPI Thermal Direct',
        'ipAddress': '10.20.10.15',
        'macAddress': 'B4-2E-99-12-34-62',
        'operatingSystem': 'Link-OS Enterprise',
        'purchaseDate': '12-May-2024',
        'warrantyExpiryDate': '11-May-2027',
        'status': 'Active'
    },
    # 1ST FLOOR (Level 1 - OPD & Pharmacy) — Code: 101..102
    {
        'id': 'dev-09',
        'assetId': 'PSM/IT/1F/C-101',
        'deviceType': 'C',
        'serialNumber': 'SN-DELL-OPD-104',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '1st Floor',
        'roomName': 'OPD Consultation Room 104',
        'assignedUserId': 'usr-dr-sharma',
        'assignedUserName': 'Dr. Vikram Sharma',
        'empId': 'MED-00042',
        'monitorSpec': 'HP 23.8" All-In-One FHD Display',
        'cpuProcessor': 'Intel Core i3-13100 (4 cores, 4.5 GHz)',
        'storageRam': '256GB SSD / 8GB DDR4',
        'ipAddress': '10.20.20.67',
        'macAddress': '90-B1-1C-54-32-11',
        'operatingSystem': 'Windows 11 Pro',
        'purchaseDate': '18-Oct-2024',
        'warrantyExpiryDate': '17-Oct-2027',
        'status': 'Active'
    },
    {
        'id': 'dev-26',
        'assetId': 'PSM/IT/1F/C-102',
        'deviceType': 'C',
        'serialNumber': 'SN-LEN-NEO50-81',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '1st Floor',
        'roomName': 'OPD Registration & Billing 02',
        'assignedUserId': 'usr-bill-exec',
        'assignedUserName': 'Ramesh Patel',
        'empId': 'MED-00205',
        'monitorSpec': 'Dual 21.5" Countertop Display + Thermal Receipt Unit',
        'cpuProcessor': 'Intel Core i5-12400 (6 cores, 4.4 GHz)',
        'storageRam': '512GB SSD / 16GB DDR4',
        'ipAddress': '10.20.20.81',
        'macAddress': '90-B1-1C-54-32-81',
        'operatingSystem': 'Windows 11 Pro',
        'purchaseDate': '20-Sep-2024',
        'warrantyExpiryDate': '19-Sep-2027',
        'status': 'Active'
    },
    {
        'id': 'dev-opd-m01',
        'assetId': 'PSM/IT/1F/M-101',
        'deviceType': 'M',
        'serialNumber': 'SN-DELL-MS116-101',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '1st Floor',
        'roomName': 'OPD Consultation Room 104',
        'assignedUserId': 'usr-dr-sharma',
        'assignedUserName': 'Dr. Vikram Sharma',
        'empId': 'MED-00042',
        'monitorSpec': 'N/A - Peripherals',
        'cpuProcessor': 'Dell Optical LED Tracking (1000 DPI)',
        'storageRam': 'USB Wired Standard Clinic Mouse',
        'ipAddress': '10.20.20.68',
        'macAddress': '90-B1-1C-54-32-12',
        'operatingSystem': 'Hardware Peripheral (HID)',
        'purchaseDate': '18-Oct-2024',
        'warrantyExpiryDate': '17-Oct-2027',
        'status': 'Active'
    },
    {
        'id': 'dev-opd-k01',
        'assetId': 'PSM/IT/1F/K-101',
        'deviceType': 'K',
        'serialNumber': 'SN-DELL-KB216-101',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '1st Floor',
        'roomName': 'OPD Consultation Room 104',
        'assignedUserId': 'usr-dr-sharma',
        'assignedUserName': 'Dr. Vikram Sharma',
        'empId': 'MED-00042',
        'monitorSpec': 'N/A - Peripherals',
        'cpuProcessor': 'Dell Multimedia Chiclet Keyboard',
        'storageRam': 'USB Wired Full-Size English Layout',
        'ipAddress': '10.20.20.69',
        'macAddress': '90-B1-1C-54-32-13',
        'operatingSystem': 'Hardware Peripheral (HID)',
        'purchaseDate': '18-Oct-2024',
        'warrantyExpiryDate': '17-Oct-2027',
        'status': 'Active'
    },
    {
        'id': 'dev-opd-p01',
        'assetId': 'PSM/IT/1F/P-101',
        'deviceType': 'P',
        'serialNumber': 'SN-EPSON-TM88-101',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '1st Floor',
        'roomName': 'Central Hospital Pharmacy Counter',
        'assignedUserId': 'usr-bill-exec',
        'assignedUserName': 'Ramesh Patel',
        'empId': 'MED-00205',
        'monitorSpec': 'Receipt Status LED Indicator',
        'cpuProcessor': 'Epson ESC/POS High-Speed Thermal Controller',
        'storageRam': '350mm/sec High-Speed Thermal Prescription Printer',
        'ipAddress': '10.20.20.95',
        'macAddress': '90-B1-1C-54-32-95',
        'operatingSystem': 'ESC/POS Medical Network Print Server',
        'purchaseDate': '20-Sep-2024',
        'warrantyExpiryDate': '19-Sep-2027',
        'status': 'Active'
    },
    # 2ND FLOOR (Level 2 - ICU & Critical Care) — Code: 201..204
    {
        'id': 'dev-06',
        'assetId': 'PSM/IT/2F/C-201',
        'deviceType': 'C',
        'serialNumber': 'SN-MED-99321',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '2nd Floor',
        'roomName': 'ICU Bedside Monitoring Pod A',
        'assignedUserId': 'usr-dr-sharma',
        'assignedUserName': 'Dr. Vikram Sharma',
        'empId': 'MED-00042',
        'monitorSpec': 'Medical Grade Antimicrobial 24" Touch Display',
        'cpuProcessor': 'Intel Core i5-12500E (Fanless Medical Grade)',
        'storageRam': '512GB M.2 SSD / 16GB ECC RAM',
        'ipAddress': '10.20.10.42',
        'macAddress': 'E4-54-E8-71-22-31',
        'operatingSystem': 'Windows 11 Pro Medical Edition',
        'purchaseDate': '05-Jan-2025',
        'warrantyExpiryDate': '04-Jan-2030',
        'status': 'Active'
    },
    {
        'id': 'dev-24',
        'assetId': 'PSM/IT/2F/C-202',
        'deviceType': 'C',
        'serialNumber': 'SN-MR-BV-45',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '2nd Floor',
        'roomName': 'ICU Bedside Monitoring Pod A',
        'assignedUserId': '',
        'assignedUserName': 'Unassigned (ICU Bed Pool)',
        'empId': '',
        'monitorSpec': 'Mindray 12.1" Touch Multi-parameter Medical Screen',
        'cpuProcessor': 'Embedded Quad-Core Medical Grade SoC',
        'storageRam': '128GB eMMC / 8GB RAM',
        'ipAddress': '10.20.10.45',
        'macAddress': 'E4-54-E8-71-22-35',
        'operatingSystem': 'Embedded Medical OS',
        'purchaseDate': '05-Jan-2025',
        'warrantyExpiryDate': '04-Jan-2030',
        'status': 'Active'
    },
    {
        'id': 'dev-07',
        'assetId': 'PSM/IT/2F/C-203',
        'deviceType': 'C',
        'serialNumber': 'SN-MED-99322',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '2nd Floor',
        'roomName': 'ICU Central Nursing Telemetry Station',
        'assignedUserId': 'usr-nurse-kavita',
        'assignedUserName': 'Kavita Nair',
        'empId': 'MED-00115',
        'monitorSpec': 'Dual 24" Dell Medical Display',
        'cpuProcessor': 'Intel Core i5-13400 (10 cores)',
        'storageRam': '512GB SSD / 16GB DDR4',
        'ipAddress': '10.20.10.43',
        'macAddress': 'E4-54-E8-71-22-32',
        'operatingSystem': 'Windows 11 Pro',
        'purchaseDate': '05-Jan-2025',
        'warrantyExpiryDate': '04-Jan-2028',
        'status': 'Active'
    },
    {
        'id': 'dev-25',
        'assetId': 'PSM/IT/2F/C-204',
        'deviceType': 'C',
        'serialNumber': 'SN-ADV-POC-49',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '2nd Floor',
        'roomName': 'ICU Central Nursing Telemetry Station',
        'assignedUserId': 'usr-nurse-kavita',
        'assignedUserName': 'Kavita Nair',
        'empId': 'MED-00115',
        'monitorSpec': 'Advantech 24" Antimicrobial Touch with Dual Battery',
        'cpuProcessor': 'Intel Core i7-1185G7E (Fanless Medical Grade)',
        'storageRam': '512GB Industrial NVMe / 32GB RAM',
        'ipAddress': '10.20.10.49',
        'macAddress': 'E4-54-E8-71-22-39',
        'operatingSystem': 'Windows 11 IoT Enterprise',
        'purchaseDate': '08-Feb-2025',
        'warrantyExpiryDate': '07-Feb-2030',
        'status': 'Active'
    },
    {
        'id': 'dev-icu-m01',
        'assetId': 'PSM/IT/2F/M-201',
        'deviceType': 'M',
        'serialNumber': 'SN-MED-MSE-201',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '2nd Floor',
        'roomName': 'ICU Central Nursing Telemetry Station',
        'assignedUserId': 'usr-nurse-kavita',
        'assignedUserName': 'Kavita Nair',
        'empId': 'MED-00115',
        'monitorSpec': 'N/A - Peripherals',
        'cpuProcessor': 'IP68 Fully Sealed Washable Optical Sensor',
        'storageRam': 'Silicone Sealed Clinical Mouse',
        'ipAddress': '10.20.10.44',
        'macAddress': 'E4-54-E8-71-22-44',
        'operatingSystem': 'Hardware Peripheral (HID)',
        'purchaseDate': '05-Jan-2025',
        'warrantyExpiryDate': '04-Jan-2028',
        'status': 'Active'
    },
    {
        'id': 'dev-icu-k01',
        'assetId': 'PSM/IT/2F/K-201',
        'deviceType': 'K',
        'serialNumber': 'SN-MED-KBD-201',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '2nd Floor',
        'roomName': 'ICU Central Nursing Telemetry Station',
        'assignedUserId': 'usr-nurse-kavita',
        'assignedUserName': 'Kavita Nair',
        'empId': 'MED-00115',
        'monitorSpec': 'N/A - Peripherals',
        'cpuProcessor': 'Antimicrobial Sealed Backlit Keyboard Controller',
        'storageRam': 'Washable Medical Grade Keyboard',
        'ipAddress': '10.20.10.46',
        'macAddress': 'E4-54-E8-71-22-46',
        'operatingSystem': 'Hardware Peripheral (HID)',
        'purchaseDate': '05-Jan-2025',
        'warrantyExpiryDate': '04-Jan-2028',
        'status': 'Active'
    },
    {
        'id': 'dev-icu-p01',
        'assetId': 'PSM/IT/2F/P-201',
        'deviceType': 'P',
        'serialNumber': 'SN-HP-LJ404-201',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '2nd Floor',
        'roomName': 'ICU Central Nursing Telemetry Station',
        'assignedUserId': 'usr-nurse-kavita',
        'assignedUserName': 'Kavita Nair',
        'empId': 'MED-00115',
        'monitorSpec': '2-Line Backlit LCD Display',
        'cpuProcessor': 'HP 1200MHz Dual-Core Clinical Print Engine',
        'storageRam': '40 ppm Duplex Laser Telemetry Chart Printer',
        'ipAddress': '10.20.10.48',
        'macAddress': 'E4-54-E8-71-22-48',
        'operatingSystem': 'HP FutureSmart Firmware',
        'purchaseDate': '05-Jan-2025',
        'warrantyExpiryDate': '04-Jan-2028',
        'status': 'Active'
    },
    # 3RD FLOOR (Level 3 - Operation Theatres) — Code: 301
    {
        'id': 'dev-ot-01',
        'assetId': 'PSM/IT/3F/C-301',
        'deviceType': 'C',
        'serialNumber': 'SN-MIN-ANESTH-55',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '3rd Floor',
        'roomName': 'Modular Operation Theatre OT-1',
        'assignedUserId': 'usr-dr-joshi',
        'assignedUserName': 'Dr. Ananya Joshi',
        'empId': 'MED-00055',
        'monitorSpec': 'Mindray 19" High-Res Surgical Touch Display',
        'cpuProcessor': 'Intel Core i7-11700E (Fanless Medical Controller)',
        'storageRam': '512GB Industrial SSD / 32GB ECC RAM',
        'ipAddress': '10.20.50.55',
        'macAddress': '00-1B-21-99-44-55',
        'operatingSystem': 'Windows 11 IoT Enterprise Medical',
        'purchaseDate': '14-Mar-2024',
        'warrantyExpiryDate': '13-Mar-2029',
        'status': 'Active'
    },
    {
        'id': 'dev-ot-m01',
        'assetId': 'PSM/IT/3F/M-301',
        'deviceType': 'M',
        'serialNumber': 'SN-SURG-MSE-301',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '3rd Floor',
        'roomName': 'Modular Operation Theatre OT-1',
        'assignedUserId': 'usr-dr-joshi',
        'assignedUserName': 'Dr. Ananya Joshi',
        'empId': 'MED-00055',
        'monitorSpec': 'N/A - Peripherals',
        'cpuProcessor': 'Hermetically Sealed Autoclavable Optical Sensor',
        'storageRam': 'IP68 Sterilizable Surgical Mouse',
        'ipAddress': '10.20.50.56',
        'macAddress': '00-1B-21-99-44-56',
        'operatingSystem': 'Hardware Peripheral (HID)',
        'purchaseDate': '14-Mar-2024',
        'warrantyExpiryDate': '13-Mar-2029',
        'status': 'Active'
    },
    {
        'id': 'dev-ot-k01',
        'assetId': 'PSM/IT/3F/K-301',
        'deviceType': 'K',
        'serialNumber': 'SN-SURG-KBD-301',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '3rd Floor',
        'roomName': 'Modular Operation Theatre OT-1',
        'assignedUserId': 'usr-dr-joshi',
        'assignedUserName': 'Dr. Ananya Joshi',
        'empId': 'MED-00055',
        'monitorSpec': 'N/A - Peripherals',
        'cpuProcessor': 'Integrated Touchpad Silicone Controller',
        'storageRam': 'Autoclavable Medical Keyboard with Integrated Touchpad',
        'ipAddress': '10.20.50.57',
        'macAddress': '00-1B-21-99-44-57',
        'operatingSystem': 'Hardware Peripheral (HID)',
        'purchaseDate': '14-Mar-2024',
        'warrantyExpiryDate': '13-Mar-2029',
        'status': 'Active'
    },
    {
        'id': 'dev-ot-p01',
        'assetId': 'PSM/IT/3F/P-301',
        'deviceType': 'P',
        'serialNumber': 'SN-SONY-UPDR80-301',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '3rd Floor',
        'roomName': 'PACU Post-Anesthesia Recovery Hub',
        'assignedUserId': 'usr-dr-joshi',
        'assignedUserName': 'Dr. Ananya Joshi',
        'empId': 'MED-00055',
        'monitorSpec': 'Color Calibration LCD Screen',
        'cpuProcessor': 'Sony Dye-Sublimation High-Definition Imaging Engine',
        'storageRam': '300 DPI Medical Endoscopy Photographic Print Engine',
        'ipAddress': '10.20.50.60',
        'macAddress': '00-1B-21-99-44-60',
        'operatingSystem': 'Medical Imaging Direct Driver',
        'purchaseDate': '14-Mar-2024',
        'warrantyExpiryDate': '13-Mar-2029',
        'status': 'Active'
    },
    # 4TH FLOOR (Level 4 - Inpatient Deluxe Wards) — Code: 401
    {
        'id': 'dev-ward-01',
        'assetId': 'PSM/IT/4F/C-401',
        'deviceType': 'C',
        'serialNumber': 'SN-HP-PD600-72',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '4th Floor',
        'roomName': 'Inpatient Deluxe Ward Station 4A',
        'assignedUserId': 'usr-ward-nurse',
        'assignedUserName': 'Sister Priya Nair',
        'empId': 'MED-00164',
        'monitorSpec': 'HP 23.8" Antimicrobial Cleanable Display',
        'cpuProcessor': 'Intel Core i5-12500 (6 cores, 4.6 GHz)',
        'storageRam': '512GB SSD / 16GB DDR4',
        'ipAddress': '10.20.60.72',
        'macAddress': 'B4-2E-99-44-66-72',
        'operatingSystem': 'Windows 11 Pro',
        'purchaseDate': '18-Aug-2024',
        'warrantyExpiryDate': '17-Aug-2027',
        'status': 'Active'
    },
    {
        'id': 'dev-wrd-m01',
        'assetId': 'PSM/IT/4F/M-401',
        'deviceType': 'M',
        'serialNumber': 'SN-HP-M100-401',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '4th Floor',
        'roomName': 'Inpatient Deluxe Ward Station 4A',
        'assignedUserId': 'usr-ward-nurse',
        'assignedUserName': 'Sister Priya Nair',
        'empId': 'MED-00164',
        'monitorSpec': 'N/A - Peripherals',
        'cpuProcessor': 'HP Ergonomic Optical Tracking (1200 DPI)',
        'storageRam': 'USB Cleanable Clinic Mouse',
        'ipAddress': '10.20.60.73',
        'macAddress': 'B4-2E-99-44-66-73',
        'operatingSystem': 'Hardware Peripheral (HID)',
        'purchaseDate': '18-Aug-2024',
        'warrantyExpiryDate': '17-Aug-2027',
        'status': 'Active'
    },
    {
        'id': 'dev-wrd-k01',
        'assetId': 'PSM/IT/4F/K-401',
        'deviceType': 'K',
        'serialNumber': 'SN-HP-K100-401',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '4th Floor',
        'roomName': 'Inpatient Deluxe Ward Station 4A',
        'assignedUserId': 'usr-ward-nurse',
        'assignedUserName': 'Sister Priya Nair',
        'empId': 'MED-00164',
        'monitorSpec': 'N/A - Peripherals',
        'cpuProcessor': 'HP Healthcare Edition Antimicrobial Keyboard',
        'storageRam': 'Spill-Resistant Membrane USB Keyboard',
        'ipAddress': '10.20.60.74',
        'macAddress': 'B4-2E-99-44-66-74',
        'operatingSystem': 'Hardware Peripheral (HID)',
        'purchaseDate': '18-Aug-2024',
        'warrantyExpiryDate': '17-Aug-2027',
        'status': 'Active'
    },
    {
        'id': 'dev-wrd-p01',
        'assetId': 'PSM/IT/4F/P-401',
        'deviceType': 'P',
        'serialNumber': 'SN-BR-L2350-401',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '4th Floor',
        'roomName': 'Inpatient Deluxe Ward Station 4A',
        'assignedUserId': 'usr-ward-nurse',
        'assignedUserName': 'Sister Priya Nair',
        'empId': 'MED-00164',
        'monitorSpec': 'Status LED Indicator Panel',
        'cpuProcessor': 'Brother High-Efficiency Laser Processor',
        'storageRam': '32 ppm Duplex Ward Discharge Report Laser Printer',
        'ipAddress': '10.20.60.80',
        'macAddress': 'B4-2E-99-44-66-80',
        'operatingSystem': 'Brother Wireless Print Core',
        'purchaseDate': '18-Aug-2024',
        'warrantyExpiryDate': '17-Aug-2027',
        'status': 'Active'
    },
    # 5TH FLOOR (Level 5 - Pathology & Blood Bank) — Code: 501..502
    {
        'id': 'dev-28',
        'assetId': 'PSM/IT/5F/C-501',
        'deviceType': 'C',
        'serialNumber': 'SN-SIEMENS-ATELLICA-31',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '5th Floor',
        'roomName': 'Automated Biochemistry Analyzer Desk',
        'assignedUserId': 'usr-path-lead',
        'assignedUserName': 'Dr. Pooja Iyer',
        'empId': 'MED-00064',
        'monitorSpec': 'Siemens 21.5" Sealed Industrial Touchscreen',
        'cpuProcessor': 'Intel Core i5-11500E (Fanless Industrial Controller)',
        'storageRam': '512GB Industrial M.2 SSD / 16GB ECC DDR4',
        'ipAddress': '10.20.40.31',
        'macAddress': '00-50-56-C0-00-31',
        'operatingSystem': 'Windows 10 IoT LTSC',
        'purchaseDate': '11-Nov-2024',
        'warrantyExpiryDate': '10-Nov-2029',
        'status': 'Active'
    },
    {
        'id': 'dev-blood-01',
        'assetId': 'PSM/IT/5F/C-502',
        'deviceType': 'C',
        'serialNumber': 'SN-DELL-OPT-88',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '5th Floor',
        'roomName': 'Central Blood Bank & Cryo-Storage',
        'assignedUserId': 'usr-path-lead',
        'assignedUserName': 'Dr. Pooja Iyer',
        'empId': 'MED-00064',
        'monitorSpec': 'Dell 24" FHD Barcode-Scanner Integrated Display',
        'cpuProcessor': 'Intel Core i5-13500 (14 cores, 4.8 GHz)',
        'storageRam': '512GB SSD / 16GB DDR5',
        'ipAddress': '10.20.40.88',
        'macAddress': '70-85-C2-44-88-88',
        'operatingSystem': 'Windows 11 Pro',
        'purchaseDate': '22-Oct-2024',
        'warrantyExpiryDate': '21-Oct-2027',
        'status': 'Active'
    },
    {
        'id': 'dev-path-m01',
        'assetId': 'PSM/IT/5F/M-501',
        'deviceType': 'M',
        'serialNumber': 'SN-LOGI-M100-501',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '5th Floor',
        'roomName': 'Automated Biochemistry Analyzer Desk',
        'assignedUserId': 'usr-path-lead',
        'assignedUserName': 'Dr. Pooja Iyer',
        'empId': 'MED-00064',
        'monitorSpec': 'N/A - Peripherals',
        'cpuProcessor': 'Chemical-Resistant Optical Sensor (1000 DPI)',
        'storageRam': 'Bleach-Cleanable Lab Workstation Mouse',
        'ipAddress': '10.20.40.32',
        'macAddress': '00-50-56-C0-00-32',
        'operatingSystem': 'Hardware Peripheral (HID)',
        'purchaseDate': '11-Nov-2024',
        'warrantyExpiryDate': '10-Nov-2029',
        'status': 'Active'
    },
    {
        'id': 'dev-path-k01',
        'assetId': 'PSM/IT/5F/K-501',
        'deviceType': 'K',
        'serialNumber': 'SN-MED-KB-501',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '5th Floor',
        'roomName': 'Automated Biochemistry Analyzer Desk',
        'assignedUserId': 'usr-path-lead',
        'assignedUserName': 'Dr. Pooja Iyer',
        'empId': 'MED-00064',
        'monitorSpec': 'N/A - Peripherals',
        'cpuProcessor': 'IP68 Chemical-Proof Silicone Membrane Keypad',
        'storageRam': 'Sanitizable Pathology Lab Keyboard',
        'ipAddress': '10.20.40.33',
        'macAddress': '00-50-56-C0-00-33',
        'operatingSystem': 'Hardware Peripheral (HID)',
        'purchaseDate': '11-Nov-2024',
        'warrantyExpiryDate': '10-Nov-2029',
        'status': 'Active'
    },
    {
        'id': 'dev-path-p01',
        'assetId': 'PSM/IT/5F/P-501',
        'deviceType': 'P',
        'serialNumber': 'SN-ZEBRA-ZT230-501',
        'orgId': 'HOSP',
        'orgName': 'PSM Hospital',
        'buildingName': 'PSM Hospital',
        'floorName': '5th Floor',
        'roomName': 'Central Blood Bank & Cryo-Storage',
        'assignedUserId': 'usr-path-lead',
        'assignedUserName': 'Dr. Pooja Iyer',
        'empId': 'MED-00064',
        'monitorSpec': 'Multilingual Graphic LCD Display',
        'cpuProcessor': 'Zebra Rugged Thermal Transfer Processing Unit',
        'storageRam': 'Cryo-Resistant Blood Bag Label Printer 300 DPI',
        'ipAddress': '10.20.40.89',
        'macAddress': '70-85-C2-44-88-89',
        'operatingSystem': 'Link-OS Enterprise',
        'purchaseDate': '22-Oct-2024',
        'warrantyExpiryDate': '21-Oct-2029',
        'status': 'Active'
    }
]

def ensure_sample_complaints():
    """Seed initial realistic hospital complaints if empty, and purge any legacy UNI complaints."""
    DeviceComplaint.objects.filter(org_id='UNI').delete()
    if DeviceComplaint.objects.count() == 0:
        DeviceComplaint.objects.create(
            ticket_id="TKT-2026-001",
            user_full_name="Dr. Vikram Sharma",
            emp_id="MED-00042",
            user_email="vikram.sharma@hospital.org",
            user_dept="Emergency & Critical Care",
            org_id="HOSP",
            device_asset_id="PSM/IT/2F/C-201",
            room_location="ICU Bed Ward 1 (Room 101)",
            issue_category="Display & Screen",
            priority="High",
            subject="ICU Monitor Touchscreen Calibration Offset",
            description="The touchscreen interface on Bed Monitor 01 is offset by approximately 2 inches to the right. Calibration utility throws error on touch response.",
            status="Pending",
            technician_name="Biomedical IT Team"
        )
        DeviceComplaint.objects.create(
            ticket_id="TKT-2026-002",
            user_full_name="Kavita Nair",
            emp_id="MED-00115",
            user_email="kavita.nair@hospital.org",
            user_dept="ICU Nursing",
            org_id="HOSP",
            device_asset_id="PSM/IT/2F/C-203",
            room_location="ICU Central Nursing Desk",
            issue_category="OS & Software Crash",
            priority="High",
            subject="Central Nursing Telemetry Station Freeze",
            description="Patient telemetry feed stalls on secondary monitor every 30 minutes. Requires manual service restart.",
            status="In Progress",
            admin_remarks="Assigned to Biomedical IT Engineer. Reinstalling certified medical display telemetry driver.",
            technician_name="Biomedical IT Team"
        )

def normalize_device_type(code, asset_id=''):
    c = (code or '').upper().strip()
    if c in ('C', 'CPU', 'WORKSTATION', 'DESKTOP', 'PC', 'TOWER', 'COMPUTER'):
        return 'CPU'
    if c in ('D', 'DISPLAY', 'MONITOR', 'SCREEN'):
        return 'Display'
    if c in ('K', 'KB', 'KEYBOARD'):
        return 'Keyboard'
    if c in ('M', 'MOUSE'):
        return 'Mouse'
    if c in ('P', 'PRT', 'PRINTER', 'BARCODE PRINTER', 'LASER PRINTER'):
        return 'Printer'
    if c in ('T', 'TAB', 'TABLET', 'IPAD'):
        return 'Tablet'
    if c in ('U', 'UPS', 'INVERTER', 'POWER'):
        return 'UPS'
    
    # Check asset_id format: PSM/IT/<TYPE>/<MMYY>/<NUM> or legacy PSM/IT/<FLOOR>/<TYPE>-<NUM>
    aid = asset_id.upper()
    if '/C/' in aid or '/C-' in aid or '/C.' in aid: return 'CPU'
    if '/D/' in aid or '/D-' in aid or '/D.' in aid or '/DISP-' in aid: return 'Display'
    if '/K/' in aid or '/K-' in aid or '/K.' in aid or '/KB-' in aid: return 'Keyboard'
    if '/M/' in aid or '/M-' in aid or '/M.' in aid: return 'Mouse'
    if '/P/' in aid or '/P-' in aid or '/P.' in aid or '/PRT-' in aid: return 'Printer'
    if '/T/' in aid or '/T-' in aid: return 'Tablet'
    if '/U/' in aid or '/U-' in aid: return 'UPS'
    return code or 'CPU'

def ensure_sample_devices():
    """Seed initial realistic PSM Hospital devices into SQLite database and purge any UNI records."""
    DeviceAsset.objects.filter(org_id='UNI').delete()
    for d in SAMPLE_DEVICES:
        dev_type = normalize_device_type(d.get('deviceType', ''), d.get('assetId', ''))
        assigned_user = d.get('assignedUserName', 'Unassigned')
        desig = d.get('designation', '')
        if not desig and assigned_user and assigned_user.lower() != 'unassigned':
            for s in SAMPLE_STAFF:
                if s.get('fullName', '').lower() == assigned_user.lower():
                    desig = s.get('designation', '')
                    break
        DeviceAsset.objects.update_or_create(
            dev_id=d.get('id', ''),
            defaults={
                'asset_id': d.get('assetId', ''),
                'device_type': dev_type,
                'serial_number': d.get('serialNumber', ''),
                'org_id': 'HOSP',
                'org_name': 'PSM Hospital',
                'building_name': d.get('buildingName', ''),
                'floor_name': d.get('floorName', ''),
                'room_name': d.get('roomName', ''),
                'assigned_user_id': d.get('assignedUserId', ''),
                'assigned_user_name': d.get('assignedUserName', 'Unassigned'),
                'assigned_emp_id': d.get('empId', ''),
                'assigned_designation': desig,
                'monitor_spec': d.get('monitorSpec', ''),
                'cpu_processor': d.get('cpuProcessor', ''),
                'storage_ram': d.get('storageRam', ''),
                'ip_address': d.get('ipAddress', ''),
                'mac_address': d.get('macAddress', ''),
                'operating_system': d.get('operatingSystem', ''),
                'purchase_date': d.get('purchaseDate', ''),
                'warranty_expiry_date': d.get('warrantyExpiryDate', ''),
                'status': d.get('status', 'Active')
            }
        )

def api_get_devices(request):
    """JSON API returning all hardware devices from SQLite database (PSM Hospital only)."""
    ensure_sample_devices()
    qs = DeviceAsset.objects.filter(org_id='HOSP')
    
    devices_data = []
    for d in qs:
        devices_data.append({
            'id': d.dev_id,
            'assetId': d.asset_id,
            'deviceType': d.device_type or normalize_device_type('', d.asset_id),
            'serialNumber': d.serial_number,
            'orgId': d.org_id,
            'orgName': d.org_name,
            'buildingName': d.building_name,
            'floorName': d.floor_name,
            'roomName': d.room_name,
            'assignedUserId': d.assigned_user_id,
            'assignedUserName': d.assigned_user_name,
            'empId': d.assigned_emp_id,
            'designation': d.assigned_designation or '',
            'assignedDesignation': d.assigned_designation or '',
            'monitorSpec': d.monitor_spec,
            'cpuProcessor': d.cpu_processor,
            'storageRam': d.storage_ram,
            'ipAddress': d.ip_address,
            'macAddress': d.mac_address,
            'operatingSystem': d.operating_system,
            'purchaseDate': d.purchase_date,
            'warrantyExpiryDate': d.warranty_expiry_date,
            'status': d.status,
        })
    return JsonResponse({'success': True, 'devices': devices_data})

@csrf_exempt
def api_reassign_device(request):
    """Handles custody transfer / reassignment of hardware and logs audit trail."""
    ensure_sample_devices()
    if request.method == 'POST':
        import json
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body.decode('utf-8'))
            except Exception:
                data = {}
        else:
            data = request.POST

        dev_id = data.get('deviceId') or data.get('device_id')
        new_user_id = data.get('newUserId') or data.get('new_user_id')
        new_user_name = data.get('newUserName') or data.get('new_user_name', '')
        new_emp_id = data.get('newEmpId') or data.get('new_emp_id', '')
        handover_date = data.get('handoverDate') or data.get('handover_date') or timezone.now().strftime('%Y-%m-%d')
        remarks = (data.get('remarks') or '').strip()
        assigned_by = data.get('assignedBy') or request.session.get('staff_name', 'IT Admin Desk')

        # Find device by dev_id or assetId
        device = DeviceAsset.objects.filter(dev_id=dev_id).first() or DeviceAsset.objects.filter(asset_id=dev_id).first()
        if not device:
            return JsonResponse({'success': False, 'message': f'Device {dev_id} not found in database.'}, status=404)

        from_user_name = device.assigned_user_name or "Unassigned"
        from_emp_id = device.assigned_emp_id or ""

        if new_user_id == '__UNASSIGN__':
            device.assigned_user_id = None
            device.assigned_user_name = "Unassigned"
            device.assigned_emp_id = ""
            device.save()

            # Create audit log
            CustodyTransferLog.objects.create(
                device=device,
                device_asset_id=device.asset_id,
                from_user_name=from_user_name,
                from_emp_id=from_emp_id,
                to_user_name="Unassigned (IT Spares)",
                to_emp_id="",
                handover_date=handover_date,
                assigned_by=assigned_by,
                remarks=remarks or f"Returned to IT Spares from {from_user_name}"
            )
            return JsonResponse({
                'success': True, 
                'message': f"Device {device.asset_id} returned to Unassigned Spares pool.",
                'device': {
                    'id': device.dev_id,
                    'assetId': device.asset_id,
                    'assignedUserName': 'Unassigned',
                    'assignedUserId': None
                }
            })

        # Lookup new user info from SAMPLE_STAFF or UserProfile if not provided
        if not new_user_name:
            staff_match = next((s for s in SAMPLE_STAFF if s['id'] == new_user_id or s['empId'] == new_emp_id), None)
            if staff_match:
                new_user_name = staff_match['fullName']
                new_emp_id = staff_match['empId']
            else:
                profile = UserProfile.objects.filter(emp_id=new_emp_id).first()
                if profile:
                    new_user_name = profile.full_name

        device.assigned_user_id = new_user_id
        device.assigned_user_name = new_user_name or "Assigned Staff"
        device.assigned_emp_id = new_emp_id
        device.save()

        # Update UserProfile assigned_asset_id if user is registered in the portal
        if new_emp_id:
            UserProfile.objects.filter(emp_id=new_emp_id).update(assigned_asset_id=device.asset_id)

        # Create custody transfer log
        CustodyTransferLog.objects.create(
            device=device,
            device_asset_id=device.asset_id,
            from_user_name=from_user_name,
            from_emp_id=from_emp_id,
            to_user_name=new_user_name or "Assigned Staff",
            to_emp_id=new_emp_id,
            handover_date=handover_date,
            assigned_by=assigned_by,
            remarks=remarks or f"Custody transferred from {from_user_name} to {new_user_name}"
        )

        return JsonResponse({
            'success': True,
            'message': f"Custody of {device.asset_id} successfully transferred to {new_user_name}!",
            'device': {
                'id': device.dev_id,
                'assetId': device.asset_id,
                'assignedUserName': device.assigned_user_name,
                'assignedUserId': device.assigned_user_id,
                'empId': device.assigned_emp_id,
            }
        })

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def api_save_device(request):
    """Registers a new hardware device or updates an existing device in PostgreSQL database.
    Immediately synchronizes with Asset Tag Center and Inventory."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST method required.'}, status=405)

    import json
    import uuid
    import datetime

    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = {}
    else:
        data = request.POST

    asset_id = (data.get('assetId') or data.get('asset_id') or '').strip().upper()
    if not asset_id:
        return JsonResponse({'success': False, 'message': 'Asset Tag / ID is required.'}, status=400)

    serial_number = (data.get('serialNumber') or data.get('serial_number') or '').strip().upper()
    device_type = normalize_device_type(data.get('deviceType') or data.get('device_type'), asset_id)
    org_id = (data.get('orgId') or data.get('org_id') or 'HOSP').strip()
    org_name = 'PSM Hospital' if org_id == 'HOSP' else 'Swaminarayan University'

    building_name = (data.get('buildingName') or data.get('building_name') or 'PSM Hospital').strip()
    floor_name = (data.get('floorName') or data.get('floor_name') or 'Ground Floor').strip()
    room_name = (data.get('roomName') or data.get('room_name') or 'General Facility').strip()

    assigned_user_id = data.get('assignedUserId') or data.get('assigned_user_id') or ''
    assigned_user_name = (data.get('assignedUserName') or data.get('assigned_user_name') or 'Unassigned').strip()
    assigned_emp_id = (data.get('assignedEmpId') or data.get('assigned_emp_id') or data.get('empId') or '').strip()
    assigned_designation = (data.get('assignedDesignation') or data.get('assigned_designation') or data.get('designation') or '').strip()

    # If designation is empty and a known staff is assigned, auto-fill from UserProfile or SAMPLE_STAFF
    if not assigned_designation and assigned_user_name and assigned_user_name.lower() != 'unassigned':
        prof = UserProfile.objects.filter(full_name__iexact=assigned_user_name).first()
        if not prof and assigned_emp_id:
            prof = UserProfile.objects.filter(emp_id__iexact=assigned_emp_id).first()
        if prof and prof.designation:
            assigned_designation = prof.designation
        else:
            for s in SAMPLE_STAFF:
                if s.get('fullName', '').lower() == assigned_user_name.lower():
                    assigned_designation = s.get('designation', '')
                    break

    cpu_processor = (data.get('cpuProcessor') or data.get('cpu_processor') or 'Intel Core i5 (Standard)').strip()
    storage_ram = (data.get('storageRam') or data.get('storage_ram') or '16GB RAM / 512GB SSD').strip()
    monitor_spec = (data.get('monitorSpec') or data.get('monitor_spec') or '24" FHD IPS Display').strip()
    operating_system = (data.get('operatingSystem') or data.get('operating_system') or 'Windows 11 Pro').strip()
    ip_address = (data.get('ipAddress') or data.get('ip_address') or '').strip()
    mac_address = (data.get('macAddress') or data.get('mac_address') or '').strip().upper()
    status = (data.get('status') or 'Active').strip()
    purchase_date = (data.get('purchaseDate') or data.get('purchase_date') or timezone.now().strftime('%d-%b-%Y')).strip()
    warranty_expiry_date = (data.get('warrantyExpiryDate') or data.get('warranty_expiry_date') or (datetime.date.today() + datetime.timedelta(days=1095)).strftime('%d-%b-%Y')).strip()

    is_edit_request = bool(data.get('is_edit') or data.get('editId') or data.get('edit_id') or data.get('allow_overwrite'))
    dev = DeviceAsset.objects.filter(asset_id__iexact=asset_id).first()

    if dev and not is_edit_request:
        return JsonResponse({
            'success': False,
            'message': f'Asset Tag "{asset_id}" is already registered to {dev.device_type} in {dev.room_name}. Please click "Auto Generate" for the next unique code.'
        }, status=409)

    is_new = False
    if dev:
        dev.device_type = device_type
        if serial_number:
            dev.serial_number = serial_number
        dev.org_id = org_id
        dev.org_name = org_name
        dev.building_name = building_name
        dev.floor_name = floor_name
        dev.room_name = room_name
        dev.assigned_user_id = assigned_user_id
        dev.assigned_user_name = assigned_user_name
        dev.assigned_emp_id = assigned_emp_id
        dev.assigned_designation = assigned_designation
        dev.cpu_processor = cpu_processor
        dev.storage_ram = storage_ram
        dev.monitor_spec = monitor_spec
        dev.operating_system = operating_system
        dev.ip_address = ip_address
        dev.mac_address = mac_address
        dev.purchase_date = purchase_date
        dev.warranty_expiry_date = warranty_expiry_date
        dev.status = status
        dev.save()
    else:
        is_new = True
        dev_id = f"dev-{uuid.uuid4().hex[:8]}"
        dev = DeviceAsset.objects.create(
            dev_id=dev_id,
            asset_id=asset_id,
            device_type=device_type,
            serial_number=serial_number,
            org_id=org_id,
            org_name=org_name,
            building_name=building_name,
            floor_name=floor_name,
            room_name=room_name,
            assigned_user_id=assigned_user_id,
            assigned_user_name=assigned_user_name,
            assigned_emp_id=assigned_emp_id,
            assigned_designation=assigned_designation,
            cpu_processor=cpu_processor,
            storage_ram=storage_ram,
            monitor_spec=monitor_spec,
            operating_system=operating_system,
            ip_address=ip_address,
            mac_address=mac_address,
            purchase_date=purchase_date,
            warranty_expiry_date=warranty_expiry_date,
            status=status
        )

    # Initial custody audit log if assigned
    if is_new and assigned_user_name and assigned_user_name.lower() != 'unassigned':
        CustodyTransferLog.objects.create(
            device=dev,
            device_asset_id=dev.asset_id,
            from_user_name="Initial Provisioning",
            from_emp_id="",
            to_user_name=assigned_user_name,
            to_emp_id=assigned_emp_id,
            handover_date=purchase_date,
            assigned_by=request.session.get('staff_name', 'IT Admin Desk') if hasattr(request, 'session') else 'IT Admin Desk',
            remarks=f"Initial hardware assignment to {assigned_user_name}"
        )

    return JsonResponse({
        'success': True,
        'message': f"Hardware device {dev.asset_id} {'registered' if is_new else 'updated'} successfully and synchronized with Asset Tag Center!",
        'is_new': is_new,
        'asset_id': dev.asset_id,
        'tag_url': f"/tag/?asset_id={urllib.parse.quote(dev.asset_id)}",
        'device': {
            'id': dev.dev_id,
            'assetId': dev.asset_id,
            'deviceType': dev.device_type,
            'serialNumber': dev.serial_number,
            'orgId': dev.org_id,
            'orgName': dev.org_name,
            'buildingName': dev.building_name,
            'floorName': dev.floor_name,
            'roomName': dev.room_name,
            'assignedUserId': dev.assigned_user_id,
            'assignedUserName': dev.assigned_user_name,
            'empId': dev.assigned_emp_id,
            'designation': dev.assigned_designation or '',
            'assignedDesignation': dev.assigned_designation or '',
            'cpuProcessor': dev.cpu_processor,
            'storageRam': dev.storage_ram,
            'monitorSpec': dev.monitor_spec,
            'operatingSystem': dev.operating_system,
            'ipAddress': dev.ip_address,
            'macAddress': dev.mac_address,
            'purchaseDate': dev.purchase_date,
            'warrantyExpiryDate': dev.warranty_expiry_date,
            'status': dev.status,
        }
    })

def api_get_audit_logs(request):
    """Returns audit trail of all custody transfers from database."""
    qs = CustodyTransferLog.objects.all().order_by('-created_at')
    logs = []
    for l in qs:
        logs.append({
            'id': l.id,
            'deviceAssetId': l.device_asset_id,
            'fromUserName': l.from_user_name,
            'toUserName': l.to_user_name,
            'toEmpId': l.to_emp_id,
            'handoverDate': l.handover_date,
            'assignedBy': l.assigned_by,
            'remarks': l.remarks,
            'createdAt': l.created_at.strftime('%Y-%m-%d %H:%M')
        })
    return JsonResponse({'success': True, 'logs': logs})

# ============================================================================
# USER PORTAL VIEWS (AUTHENTICATION, MY DEVICE, COMPLAINTS)
# ============================================================================

def user_portal_root(request):
    """Main landing entry for staff/users: redirect directly to the Mobile QR incident report portal."""
    return redirect('mobile_report')


def is_admin_authenticated(request):
    """Check if the current session or user has active administrator privileges."""
    session = getattr(request, 'session', {})
    if session.get('admin_logged_in'):
        return True
    if hasattr(request, 'user') and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return True
    return False


def admin_required(view_func):
    """Decorator ensuring user is authenticated as administrator before accessing view."""
    from functools import wraps
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not is_admin_authenticated(request):
            full_path = request.get_full_path()
            if full_path in ('/', '/admin-portal/'):
                return redirect('admin_login')
            return redirect(f"/admin-login/?next={full_path}")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_login_view(request):
    """Administrator & Hardware Manager Sign In view."""
    # If already logged in, redirect directly to index (the organization selector picture page)
    if is_admin_authenticated(request):
        return redirect('index')

    next_url = request.GET.get('next') or request.POST.get('next') or 'index'
    if next_url in ('admin_login', '/admin-login/', ''):
        next_url = 'index'

    if request.method == 'POST':
        # 1-Click Quick Demo Admin Login
        if request.POST.get('demo_admin') == 'true':
            admin_user = User.objects.filter(is_superuser=True).first() or User.objects.filter(is_staff=True).first()
            if not admin_user:
                admin_user = User.objects.create_superuser(
                    username='admin',
                    email='admin@psmhospital.org',
                    password='admin',
                    first_name='System',
                    last_name='Administrator'
                )
            login(request, admin_user)
            admin_name = admin_user.get_full_name() or admin_user.username
            parts = admin_name.split()
            admin_initials = (parts[0][0] + (parts[1][0] if len(parts) > 1 else '')).upper() if parts else 'AD'
            
            request.session['admin_logged_in'] = True
            request.session['admin_name'] = admin_name
            request.session['admin_username'] = admin_user.username
            request.session['admin_role'] = 'Master Systems Administrator'
            request.session['admin_initials'] = admin_initials
            
            messages.success(request, f"Authenticated successfully as {admin_name}!")
            return redirect(next_url)

        # Standard Credentials Login
        login_id = request.POST.get('login_id', '').strip()
        password = request.POST.get('password', '').strip()

        if not login_id or not password:
            messages.error(request, "Please enter both Administrator Username/Email and Password.")
            return render(request, "admin/admin_login.html", {'next': next_url})

        # Match username or email
        target_user = User.objects.filter(username__iexact=login_id).first()
        if not target_user:
            target_user = User.objects.filter(email__iexact=login_id).first()

        user = None
        if target_user:
            user = authenticate(request, username=target_user.username, password=password)
        else:
            user = authenticate(request, username=login_id, password=password)

        if user is not None:
            # Check admin privileges
            if not (user.is_staff or user.is_superuser):
                profile = getattr(user, 'profile', None)
                if not (profile and 'admin' in profile.designation.lower()):
                    messages.error(request, "Access restricted. This account does not have IT Administrator privileges.")
                    return render(request, "admin/admin_login.html", {'next': next_url})

            login(request, user)
            profile = getattr(user, 'profile', None)
            if not profile:
                profile = UserProfile.objects.create(
                    user=user,
                    emp_id=user.username.upper(),
                    full_name=user.get_full_name() or user.username,
                    org_id='HOSP',
                    department='IT & Medical Systems',
                    designation='Master Administrator' if user.is_superuser else 'IT Systems Lead',
                    password=password
                )
            elif profile.password != password:
                profile.password = password
                profile.save(update_fields=['password'])

            admin_name = user.get_full_name() or (profile.full_name if profile else user.username)
            parts = admin_name.split()
            admin_initials = (parts[0][0] + (parts[1][0] if len(parts) > 1 else '')).upper() if parts else user.username[:2].upper()
            admin_role = profile.designation if (profile and profile.designation) else ('Master Administrator' if user.is_superuser else 'IT Systems Lead')

            request.session['admin_logged_in'] = True
            request.session['admin_name'] = admin_name
            request.session['admin_username'] = user.username
            request.session['admin_role'] = admin_role
            request.session['admin_initials'] = admin_initials

            messages.success(request, f"Welcome back to Central Admin Console, {admin_name}!")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid credentials. Please verify your administrator username/email and password.")

    return render(request, "admin/admin_login.html", {'next': next_url})


def admin_signup_view(request):
    """Administrator & Systems Engineer Registration view."""
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip().lower()
        email = request.POST.get('email', '').strip().lower()
        department = request.POST.get('department', '').strip() or 'IT & Medical Systems'
        designation = request.POST.get('designation', '').strip() or 'Systems Administrator'
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        # Validation
        if not full_name or not username or not email or not password:
            messages.error(request, "All required fields must be completed.")
            return render(request, "admin/admin_signup.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match. Please re-enter your password.")
            return render(request, "admin/admin_signup.html")

        if len(password) < 4:
            messages.error(request, "Password must be at least 4 characters long.")
            return render(request, "admin/admin_signup.html")

        # Check existing username / email
        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, f"An administrator with username '{username}' already exists. Please choose another username or log in.")
            return render(request, "admin/admin_signup.html")

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, f"An account with email '{email}' is already registered. Please log in.")
            return render(request, "admin/admin_signup.html")

        # Create Django User with staff privileges
        name_parts = full_name.split(maxsplit=1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        new_admin = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=True
        )

        UserProfile.objects.create(
            user=new_admin,
            emp_id=username.upper(),
            full_name=full_name,
            org_id='HOSP',
            department=department,
            designation=designation,
            assigned_asset_id='HOSP-SRV-CORE01',
            password=password
        )

        # Redirect directly to Admin Sign In page
        messages.success(request, f"Admin account '{username}' created successfully! Please sign in with your credentials.")
        return redirect(f"/admin-login/?registered={username}")

    return render(request, "admin/admin_signup.html")


def admin_logout_view(request):
    """Administrator Secure Sign Out."""
    logout(request)
    for key in ['admin_logged_in', 'admin_name', 'admin_username', 'admin_role', 'admin_initials']:
        request.session.pop(key, None)
    messages.info(request, "You have been securely signed out from the Administrator Console.")
    return redirect('admin_login')


def user_login_view(request):
    """Staff & Users entry view: redirect directly to the instant Mobile QR incident report portal."""
    return redirect('mobile_report')

def user_signup_view(request):
    """Staff registration view."""
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        emp_id = request.POST.get('emp_id', '').strip().upper()
        email = request.POST.get('email', '').strip().lower()
        org_id = request.POST.get('org_id', 'HOSP')
        department = request.POST.get('department', '').strip()
        designation = request.POST.get('designation', '').strip()
        assigned_asset_id = request.POST.get('assigned_asset_id', '').strip().upper()
        password = request.POST.get('password', '').strip()

        if not full_name or not emp_id or not email or not password:
            messages.error(request, "All required fields must be completed.")
            return render(request, "user/user_signup.html")

        # Create Django User
        username = emp_id.lower().replace('-', '_')
        if User.objects.filter(username=username).exists():
            messages.error(request, f"An account with Employee ID {emp_id} already exists. Please log in.")
            return redirect('user_login')

        clean_asset_id = assigned_asset_id or f"PSM-WRK-{emp_id}"

        user = User.objects.create_user(username=username, email=email, password=password, first_name=full_name)
        UserProfile.objects.create(
            user=user,
            emp_id=emp_id,
            full_name=full_name,
            org_id='HOSP',
            department=department,
            designation=designation,
            assigned_asset_id=clean_asset_id,
            password=password
        )

        # Ensure DeviceAsset is linked or registered
        dev_existing = DeviceAsset.objects.filter(asset_id__iexact=clean_asset_id).first()
        if dev_existing:
            dev_existing.assigned_emp_id = emp_id
            dev_existing.assigned_user_name = full_name
            dev_existing.assigned_user_id = emp_id
            dev_existing.assigned_designation = designation
            dev_existing.save()
        else:
            clean_dev_id = f"dev-{emp_id}".lower().replace('/', '-')
            base_dev_id = clean_dev_id
            counter = 1
            while DeviceAsset.objects.filter(dev_id=clean_dev_id).exists():
                clean_dev_id = f"{base_dev_id}-{counter}"
                counter += 1
            DeviceAsset.objects.create(
                dev_id=clean_dev_id,
                asset_id=clean_asset_id,
                serial_number=f"SN-{clean_asset_id.replace('/', '-')}",
                org_id='HOSP',
                org_name='PSM Hospital',
                building_name='PSM Main Complex',
                floor_name='Ground Floor',
                room_name=department or 'Clinical Department',
                assigned_user_id=emp_id,
                assigned_user_name=full_name,
                assigned_emp_id=emp_id,
                assigned_designation=designation,
                monitor_spec='24" Dell UltraSharp FHD LED',
                cpu_processor='Intel Core i5-12400 (6 cores, 12 threads)',
                storage_ram='512GB NVMe SSD / 16GB DDR4 RAM',
                operating_system='Windows 11 Pro 64-bit',
                status='Active'
            )

        # Store session
        request.session['staff_emp_id'] = emp_id
        request.session['staff_name'] = full_name
        request.session['staff_org'] = 'HOSP'
        request.session['staff_org_name'] = 'PSM Hospital'
        request.session['staff_dept'] = department
        request.session['staff_email'] = email
        request.session['staff_asset'] = clean_asset_id

        messages.success(request, f"Account created successfully! Welcome to the Device Service Portal, {full_name}!")
        return redirect('user_dashboard')

    return render(request, "user/user_signup.html")

def user_logout_view(request):
    """User logout."""
    logout(request)
    request.session.flush()
    messages.info(request, "You have been logged out from your employee portal.")
    return redirect('user_login')

def user_dashboard(request):
    """Employee Portal Dashboard: redirect directly to the unified Mobile QR incident report portal."""
    return redirect('mobile_report')

def submit_complaint(request):
    """Handles submission of a hardware problem / complaint by an employee."""
    if request.method == 'POST':
        user_name = request.session.get('staff_name', request.POST.get('user_full_name', 'PSM Hospital Staff'))
        emp_id = request.session.get('staff_emp_id', request.POST.get('emp_id', 'MED-00042'))
        org_id = 'HOSP'
        user_dept = request.session.get('staff_dept', request.POST.get('user_dept', 'Clinical Services'))
        user_email = request.session.get('staff_email', request.POST.get('user_email', ''))

        device_asset_id = request.POST.get('device_asset_id', '').strip()
        room_location = request.POST.get('room_location', '').strip()
        issue_category = request.POST.get('issue_category', 'Hardware Fault')
        priority = request.POST.get('priority', 'Normal')
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()

        if not subject or not description:
            messages.error(request, "Please provide a subject title and description of the device issue.")
            return redirect('user_dashboard')

        # Generate unique ticket ID: TKT-2026-XXX
        rand_num = random.randint(100, 999)
        ticket_id = f"TKT-2026-{rand_num}"
        while DeviceComplaint.objects.filter(ticket_id=ticket_id).exists():
            rand_num = random.randint(100, 999)
            ticket_id = f"TKT-2026-{rand_num}"

        DeviceComplaint.objects.create(
            ticket_id=ticket_id,
            user=request.user if request.user.is_authenticated else None,
            user_full_name=user_name,
            emp_id=emp_id,
            user_email=user_email,
            user_dept=user_dept,
            org_id='HOSP',
            device_asset_id=device_asset_id or 'PSM/IT/2F/C-201',
            room_location=room_location or 'Clinical Ward',
            issue_category=issue_category,
            priority=priority,
            subject=subject,
            description=description,
            status='Pending',
            technician_name='Biomedical IT Team'
        )

        messages.success(request, f"Service Complaint #{ticket_id} filed successfully! Biomedical IT Support has been notified.")
        return redirect('mobile_report')

    return redirect('mobile_report')


def get_active_tunnel_url():
    """Retrieve the active trycloudflare HTTPS URL if tunnel is running."""
    import glob, re, os
    from django.conf import settings
    try:
        tunnel_file = os.path.join(settings.BASE_DIR, "tunnel_url.txt")
        if os.path.exists(tunnel_file):
            with open(tunnel_file, "r", encoding="utf-8") as f:
                u = f.read().strip()
                if u.startswith("https://"):
                    return u
        logs = glob.glob(r'C:\Users\Asus\.gemini\antigravity-ide\brain\*\.system_generated\tasks\task-*.log')
        for l in sorted(logs, key=os.path.getmtime, reverse=True)[:5]:
            with open(l, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    m = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                    if m:
                        return m.group(0)
    except Exception:
        pass
    return "https://remark-valentine-fax-discipline.trycloudflare.com"



# ============================================================================
# MOBILE QR DEVICE COMPLAINT SYSTEM (DEDICATED HOSPITAL STAFF INTERFACE)
# ============================================================================

def mobile_report_view(request, asset_id=None):
    """
    Dedicated Mobile Phone Device Complaint Portal.
    Engineered specifically for smartphone screens. Hospital doctors, nurses,
    and ward staff scan the physical QR tag on a hardware device to instantly
    report issues with 1-tap categories and priority triage.
    """
    ensure_sample_devices()

    # 1. Resolve raw asset ID from URL path or GET query
    raw_asset_id = asset_id or request.GET.get('asset_id') or request.GET.get('id') or ''
    if raw_asset_id:
        raw_asset_id = urllib.parse.unquote(str(raw_asset_id)).strip()
        # Strip trailing slashes that may come from URL matching
        raw_asset_id = raw_asset_id.rstrip('/')

    # 2. Look up the device in PostgreSQL DeviceAsset
    device_obj = None
    if raw_asset_id:
        device_obj = DeviceAsset.objects.filter(asset_id__iexact=raw_asset_id).first()
        if not device_obj:
            device_obj = DeviceAsset.objects.filter(dev_id__iexact=raw_asset_id).first()
        if not device_obj and '/' in raw_asset_id:
            device_obj = DeviceAsset.objects.filter(asset_id__iexact=raw_asset_id.replace('/', '-')).first()
        if not device_obj and '-' in raw_asset_id:
            device_obj = DeviceAsset.objects.filter(asset_id__iexact=raw_asset_id.replace('-', '/')).first()

    # 3. Format structured device context
    device_data = None
    if device_obj:
        user_name = device_obj.assigned_user_name or 'Hospital Staff / General'
        user_desig = ''
        user_dept = ''
        if device_obj.assigned_user_name:
            prof = UserProfile.objects.filter(full_name__iexact=device_obj.assigned_user_name).first()
            if not prof and device_obj.assigned_emp_id:
                prof = UserProfile.objects.filter(emp_id__iexact=device_obj.assigned_emp_id).first()
            if prof:
                user_desig = prof.designation or ''
                user_dept = prof.department or ''
            else:
                for s in SAMPLE_STAFF:
                    if s.get('fullName', '').lower() == device_obj.assigned_user_name.lower():
                        user_desig = s.get('designation', '')
                        user_dept = s.get('department', '')
                        break

        # Determine readable hardware model / processor line (e.g. Intel Core i5-13400 (10 cores))
        hardware_model = device_obj.cpu_processor or device_obj.monitor_spec or (f"{device_obj.device_type} Workstation")

        device_data = {
            'asset_id': device_obj.asset_id,
            'dev_id': device_obj.dev_id,
            'device_type': device_obj.device_type or 'Hardware',
            'serial_number': device_obj.serial_number or 'N/A',
            'building': device_obj.building_name or 'PSM Hospital',
            'floor': device_obj.floor_name or 'Ground Floor',
            'room': device_obj.room_name or 'Clinical Ward',
            'custodian': user_name,
            'designation': user_desig or 'Healthcare Professional',
            'department': user_dept or (device_obj.room_name or 'Clinical Services'),
            'status': device_obj.status or 'Active',
            'os': device_obj.operating_system or '',
            'cpu_processor': device_obj.cpu_processor or '',
            'hardware_model': hardware_model,
            'specs': f"{device_obj.cpu_processor} | {device_obj.storage_ram}" if device_obj.cpu_processor else (device_obj.monitor_spec or ''),
        }
    elif raw_asset_id:
        device_data = {
            'asset_id': raw_asset_id,
            'dev_id': '',
            'device_type': 'Hardware Device',
            'serial_number': 'Scanning Tag',
            'building': 'PSM Hospital',
            'floor': 'Clinical Wing',
            'room': 'Ward / Lab',
            'custodian': 'Hospital Station',
            'designation': 'Healthcare Staff',
            'department': 'Clinical Ward',
            'status': 'Active',
            'os': '',
            'cpu_processor': '',
            'hardware_model': 'Hospital Station Equipment',
            'specs': '',
        }

    # 4. Fetch list of PSM Hospital devices for rapid searchable picker
    hospital_devices = list(DeviceAsset.objects.filter(org_id='HOSP').values(
        'asset_id', 'device_type', 'room_name', 'floor_name', 'assigned_user_name'
    )[:150])

    context = {
        'scanned_asset_id': raw_asset_id,
        'device': device_data,
        'hospital_devices_json': json.dumps(hospital_devices),
        'tunnel_url': get_active_tunnel_url(),
    }
    return render(request, "user/mobile_report.html", context)


@csrf_exempt
def api_submit_quick_complaint(request):
    """
    Mobile AJAX endpoint to submit a device complaint from a smartphone scan.
    Creates a new DeviceComplaint record (org_id='HOSP', status='Pending')
    which appears in real-time in the admin Helpdesk & Device Complaints table.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed. Use POST.'}, status=405)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8'))
        else:
            data = request.POST

        device_asset_id = str(data.get('device_asset_id') or data.get('asset_id') or '').strip()
        user_full_name = str(data.get('user_full_name') or data.get('staff_name') or '').strip() or 'PSM Hospital Staff'
        emp_id = str(data.get('emp_id', '')).strip()
        user_dept = str(data.get('user_dept') or data.get('staff_dept') or '').strip() or 'Clinical Services'
        user_phone = str(data.get('user_phone') or data.get('staff_phone') or '').strip()
        room_location = str(data.get('room_location', '')).strip()
        issue_category = str(data.get('issue_category') or data.get('category') or 'Hardware Fault').strip()
        priority = str(data.get('priority', 'Normal')).strip()
        subject = str(data.get('subject', '')).strip()
        description = str(data.get('description', '')).strip()

        if not device_asset_id:
            return JsonResponse({'success': False, 'error': 'Asset Tag / ID is required.'}, status=400)

        # Look up device room & info if not provided
        if not room_location:
            dev = DeviceAsset.objects.filter(asset_id__iexact=device_asset_id).first()
            if dev and dev.room_name:
                room_location = f"{dev.room_name} ({dev.floor_name or 'PSM Hospital'})"
            else:
                room_location = 'Clinical Ward / Department'

        # Auto-craft a concise subject if empty
        if not subject:
            prefix = "[EMERGENCY]" if priority == 'Critical' else "[ROUTINE]"
            subject = f"{prefix} {issue_category} — {device_asset_id}"

        # Combine phone/intercom info into description
        full_description = description
        if user_phone:
            full_description = f"{description}\n\n[Reporter Contact / Ext]: {user_phone}".strip()

        # Generate unique ticket ID: TKT-2026-XXX
        rand_num = random.randint(100, 999)
        ticket_id = f"TKT-2026-{rand_num}"
        while DeviceComplaint.objects.filter(ticket_id=ticket_id).exists():
            rand_num = random.randint(100, 999)
            ticket_id = f"TKT-2026-{rand_num}"

        # Create record in database
        user_inst = request.user if (hasattr(request, 'user') and request.user and request.user.is_authenticated) else None
        complaint = DeviceComplaint.objects.create(
            ticket_id=ticket_id,
            user=user_inst,
            user_full_name=user_full_name,
            emp_id=emp_id or 'STAFF-MOBILE',
            user_email='',
            user_dept=user_dept,
            org_id='HOSP',
            device_asset_id=device_asset_id,
            room_location=room_location,
            issue_category=issue_category,
            priority=priority,
            subject=subject,
            description=full_description or f"Malfunctioning hardware reported via mobile QR scan: {issue_category}",
            status='Pending',
            technician_name='Biomedical IT Team'
        )

        sla_minutes = 30 if priority == 'Critical' else 240
        sla_text = "< 30 Mins (Emergency Priority)" if priority == 'Critical' else "2 - 4 Hours (Routine SLA)"

        return JsonResponse({
            'success': True,
            'ticket_id': ticket_id,
            'priority': priority,
            'sla_minutes': sla_minutes,
            'sla_text': sla_text,
            'device_asset_id': device_asset_id,
            'room_location': room_location,
            'created_at': timezone.localtime(complaint.created_at).strftime("%d-%b-%Y %I:%M %p"),
            'message': f"Complaint #{ticket_id} registered successfully! Biomedical IT Support has been dispatched."
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================================================
# ADMIN SIDE HELPDESK & COMPLAINTS MANAGEMENT
# ============================================================================

@admin_required
def admin_complaints(request):
    """Admin Helpdesk Tickets / Complaints view (PSM Hospital only)."""
    ensure_sample_complaints()

    org = request.GET.get('org', 'HOSP')
    if org == 'UNI':
        return redirect('/admin-complaints/?org=HOSP')

    status_filter = request.GET.get('status', 'ALL')

    queryset = DeviceComplaint.objects.filter(org_id='HOSP').order_by('-created_at')
    if status_filter != 'ALL':
        queryset = queryset.filter(status=status_filter)

    total_tickets = DeviceComplaint.objects.filter(org_id='HOSP').count()
    pending_tickets = DeviceComplaint.objects.filter(org_id='HOSP', status='Pending').count()
    progress_tickets = DeviceComplaint.objects.filter(org_id='HOSP', status='In Progress').count()
    resolved_tickets = DeviceComplaint.objects.filter(org_id='HOSP', status='Resolved').count()
    critical_tickets = DeviceComplaint.objects.filter(org_id='HOSP', priority='Critical').count()

    context = {
        'selected_org': 'HOSP',
        'status_filter': status_filter,
        'complaints': queryset,
        'total_tickets': total_tickets,
        'pending_tickets': pending_tickets,
        'progress_tickets': progress_tickets,
        'resolved_tickets': resolved_tickets,
        'critical_tickets': critical_tickets,
    }
    return render(request, "admin/admin_complaints.html", context)

@admin_required
def admin_update_complaint(request, ticket_id):
    """Admin endpoint to update complaint status, assign technician, and add remarks."""
    if request.method == 'POST':
        complaint = get_object_or_404(DeviceComplaint, ticket_id=ticket_id)
        new_status = request.POST.get('status', complaint.status)
        technician = request.POST.get('technician_name', complaint.technician_name)
        remarks = request.POST.get('admin_remarks', complaint.admin_remarks)

        complaint.status = new_status
        complaint.technician_name = technician
        complaint.admin_remarks = remarks

        if new_status in ['Resolved', 'Closed']:
            complaint.resolved_at = timezone.now()

        complaint.save()
        messages.success(request, f"Ticket #{ticket_id} updated to '{new_status}' successfully!")

        next_url = request.POST.get('next', 'admin_complaints')
        return redirect(next_url)

    return redirect('admin_complaints')


# ============================================================================
# EXISTING ADMIN PAGES (100% PRESERVED DESIGN & FUNCTIONALITY)
# ============================================================================

def get_serialized_devices_and_logs():
    """
    Direct server-side data serialization from PostgreSQL for instant, zero-latency rendering.
    Bypasses secondary client-side fetch('/api/devices/') and fetch('/api/audit-logs/') calls.
    """
    ensure_sample_devices()
    devices_qs = DeviceAsset.objects.filter(org_id='HOSP')
    devices_data = []
    for d in devices_qs:
        devices_data.append({
            'id': d.dev_id,
            'assetId': d.asset_id,
            'deviceType': d.device_type or normalize_device_type('', d.asset_id),
            'serialNumber': d.serial_number,
            'orgId': d.org_id,
            'orgName': d.org_name,
            'buildingName': d.building_name,
            'floorName': d.floor_name,
            'roomName': d.room_name,
            'assignedUserId': d.assigned_user_id,
            'assignedUserName': d.assigned_user_name,
            'empId': d.assigned_emp_id,
            'designation': d.assigned_designation or '',
            'assignedDesignation': d.assigned_designation or '',
            'monitorSpec': d.monitor_spec,
            'cpuProcessor': d.cpu_processor,
            'storageRam': d.storage_ram,
            'ipAddress': d.ip_address,
            'macAddress': d.mac_address,
            'operatingSystem': d.operating_system,
            'purchaseDate': d.purchase_date,
            'warrantyExpiryDate': d.warranty_expiry_date,
            'status': d.status,
        })

    logs_qs = CustodyTransferLog.objects.all().order_by('-created_at')
    logs_data = []
    for l in logs_qs:
        logs_data.append({
            'id': l.id,
            'deviceAssetId': l.device_asset_id,
            'fromUserName': l.from_user_name,
            'toUserName': l.to_user_name,
            'toEmpId': l.to_emp_id,
            'handoverDate': l.handover_date,
            'assignedBy': l.assigned_by,
            'remarks': l.remarks,
            'createdAt': l.created_at.strftime('%Y-%m-%d %H:%M')
        })

    return json.dumps(devices_data), json.dumps(logs_data)


@admin_required
def index(request):
    """Landing Portal Gateway (Swaminarayan University vs PSM Hospital)"""
    pending_count = DeviceComplaint.objects.filter(status='Pending').count()
    devices_json, audit_logs_json = get_serialized_devices_and_logs()
    return render(request, "admin/index.html", {
        'pending_tickets': pending_count,
        'devices_json': devices_json,
        'audit_logs_json': audit_logs_json,
        'selected_org': 'HOSP'
    })

@admin_required
def inventory(request):
    """1. Devices Inventory: Dedicated to PSM Hospital"""
    org = request.GET.get('org', 'HOSP')
    if org == 'UNI':
        return redirect('/inventory/?org=HOSP')
    pending_count = DeviceComplaint.objects.filter(status='Pending').count()
    devices_json, audit_logs_json = get_serialized_devices_and_logs()
    context = {
        'selected_org': 'HOSP',
        'pending_tickets': pending_count,
        'devices_json': devices_json,
        'audit_logs_json': audit_logs_json,
    }
    return render(request, "admin/inventory.html", context)


def mobile_add_device_view(request):
    """
    Mobile-first Hardware Enrollment & Device Provisioning Portal.
    Allows hospital engineers, IT staff, and technicians on mobile phones or tablets
    to rapidly add and register new hardware devices directly into the PostgreSQL DeviceAsset table.
    """
    import datetime

    today_str = timezone.localtime().strftime("%d-%b-%Y")
    warranty_str = (timezone.localtime() + datetime.timedelta(days=1095)).strftime("%d-%b-%Y")

    # Dedicated PSM Hospital clinical buildings and wings
    buildings = [
        'PSM Hospital',
        'ICU & Critical Care Wing',
        'Emergency & Trauma Center',
        'Radiology & Diagnostics Wing',
        'OPD & Surgical Block',
        'Biomedical Engineering Unit',
    ]

    floors = ['Ground Floor', '1st Floor', '2nd Floor', '3rd Floor', '4th Floor', '5th Floor', 'Basement']
    
    # Hospital clinical rooms and wards
    rooms = list(DeviceAsset.objects.filter(org_id='HOSP').exclude(room_name='').values_list('room_name', flat=True).distinct()[:20])
    if not rooms:
        rooms = [
            'ICU Bed Ward 1 (Room 101)',
            'ICU Central Nursing Desk',
            'Emergency Trauma Room 102',
            'Radiology Diagnostic Desk',
            'Pathology Lab Terminal',
            'OPD Clinic 04'
        ]

    # PSM Hospital clinical and administrative staff
    staff_qs = UserProfile.objects.filter(org_id='HOSP').values('full_name', 'emp_id', 'department', 'designation', 'org_id')[:30]
    if staff_qs.exists():
        staff_list = list(staff_qs)
    else:
        staff_list = [
            {
                'full_name': s.get('fullName', ''),
                'emp_id': s.get('empId', ''),
                'department': s.get('department', ''),
                'designation': s.get('designation', ''),
                'org_id': s.get('orgId', 'HOSP')
            }
            for s in SAMPLE_STAFF if s.get('orgId') == 'HOSP'
        ]

    context = {
        'today_str': today_str,
        'warranty_str': warranty_str,
        'buildings': buildings,
        'floors': floors,
        'rooms': rooms,
        'staff_list': staff_list,
        'staff_list_json': json.dumps(staff_list, default=str),
        'selected_org': 'HOSP',
    }
    response = render(request, "admin/mobile_add_device.html", context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@csrf_exempt
def api_generate_asset_id(request):
    """
    Generates a unique, standardized hardware asset tag strictly for PSM Hospital.
    Format: PSM/IT/<TYPE>/<MMYY>/<XXX>
    Example:
      - Mouse:    PSM/IT/M/0926/001 or PSM/IT/M/0926/002
      - CPU:      PSM/IT/C/0926/003
      - Display:  PSM/IT/D/0926/004
      - Printer:  PSM/IT/P/0926/005
      - Keyboard: PSM/IT/K/0926/006
      - Tablet:   PSM/IT/T/0926/007
      - UPS:      PSM/IT/U/0926/008
    Guarantees 100% collision-free against PostgreSQL DeviceAsset table.
    """
    import re

    raw_type = (request.GET.get('type') or request.POST.get('type') or 'CPU').strip().upper()
    current_val = (request.GET.get('current') or request.POST.get('current') or '').strip().upper()
    force_next = request.GET.get('next') in ('1', 'true', 'True')
    
    type_letter_map = {
        'M': 'M', 'MOUSE': 'M',
        'C': 'C', 'CPU': 'C', 'WORKSTATION': 'C', 'DESKTOP': 'C', 'COMPUTER': 'C',
        'D': 'D', 'DISPLAY': 'D', 'MONITOR': 'D', 'SCREEN': 'D',
        'P': 'P', 'PRINTER': 'P', 'PRT': 'P',
        'K': 'K', 'KEYBOARD': 'K', 'KB': 'K',
        'T': 'T', 'TABLET': 'T', 'TAB': 'T', 'IPAD': 'T',
        'U': 'U', 'UPS': 'U', 'INVERTER': 'U', 'POWER': 'U',
    }
    type_letter = type_letter_map.get(raw_type, raw_type[0] if raw_type else 'C')

    now = timezone.localtime()
    mmyy = now.strftime("%m%y")  # e.g. "0926"
    prefix = f"PSM/IT/{type_letter}/{mmyy}/"

    # Scan ALL existing tags in PostgreSQL to guarantee global uniqueness
    all_tags = list(DeviceAsset.objects.all().values_list('asset_id', flat=True))
    used_numbers = set()

    for tag in all_tags:
        tag_str = str(tag).strip().upper()
        # 1. Match /{mmyy}/(\d+)
        m = re.search(rf'/{mmyy}/(\d+)', tag_str)
        if m:
            try:
                used_numbers.add(int(m.group(1)))
            except ValueError:
                pass
        # 2. Match standard 5-part structure
        parts = tag_str.split('/')
        if len(parts) >= 5 and parts[3] == mmyy:
            try:
                used_numbers.add(int(parts[4]))
            except ValueError:
                pass

    max_used = max(used_numbers) if used_numbers else 0

    cur_num = 0
    if current_val:
        m_cur = re.search(r'(\d+)$', current_val)
        if m_cur:
            try:
                cur_num = int(m_cur.group(1))
            except ValueError:
                pass

    # If the user explicitly requested next number (e.g. clicked Auto Generate again)
    if force_next and cur_num > 0:
        start_num = max(max_used + 1, cur_num + 1)
    else:
        start_num = max_used + 1

    next_num = start_num
    candidate = f"{prefix}{next_num:03d}"

    # Strict PostgreSQL collision verification loop
    while (next_num in used_numbers) or DeviceAsset.objects.filter(asset_id__iexact=candidate).exists():
        next_num += 1
        candidate = f"{prefix}{next_num:03d}"

    return JsonResponse({'success': True, 'asset_id': candidate, 'seq_num': next_num})


@csrf_exempt
def api_check_asset_id(request):
    """Real-time validation API: checks if an asset_id already exists in PostgreSQL."""
    asset_id = (request.GET.get('asset_id') or request.POST.get('asset_id') or '').strip().upper()
    if not asset_id:
        return JsonResponse({'exists': False, 'valid': False, 'message': 'Empty ID'})

    dev = DeviceAsset.objects.filter(asset_id__iexact=asset_id).first()
    if dev:
        return JsonResponse({
            'exists': True,
            'valid': True,
            'asset_id': dev.asset_id,
            'device_type': dev.device_type,
            'location': f"{dev.room_name} ({dev.floor_name})",
            'status': dev.status,
            'message': f"Already registered to {dev.device_type} in {dev.room_name}."
        })
    return JsonResponse({
        'exists': False,
        'valid': True,
        'asset_id': asset_id,
        'message': "Tag is available & unique."
    })

@admin_required
def user(request):
    """3. Staff & Users Directory (Dedicated to PSM Hospital)"""
    org = request.GET.get('org', 'HOSP')
    if org == 'UNI':
        return redirect('/user/?org=HOSP')
    pending_count = DeviceComplaint.objects.filter(status='Pending').count()
    devices_json, audit_logs_json = get_serialized_devices_and_logs()
    context = {
        'selected_org': 'HOSP',
        'pending_tickets': pending_count,
        'devices_json': devices_json,
        'audit_logs_json': audit_logs_json,
    }
    return render(request, "admin/user.html", context)

@admin_required
def location(request):
    """2. Location Explorer: PSM Hospital dedicated clinical hierarchy"""
    org = request.GET.get('org', 'HOSP')
    if org == 'UNI':
        return redirect('/location/?org=HOSP')
    pending_count = DeviceComplaint.objects.filter(status='Pending').count()
    devices_json, audit_logs_json = get_serialized_devices_and_logs()
    context = {
        'selected_org': 'HOSP',
        'pending_tickets': pending_count,
        'devices_json': devices_json,
        'audit_logs_json': audit_logs_json,
    }
    return render(request, "admin/location.html", context)

@admin_required
def audit(request):
    """4. Audit & History Logs: Handover and custody logs (PSM Hospital)"""
    org = request.GET.get('org', 'HOSP')
    if org == 'UNI':
        return redirect('/audit/?org=HOSP')
    pending_count = DeviceComplaint.objects.filter(status='Pending').count()
    devices_json, audit_logs_json = get_serialized_devices_and_logs()
    context = {
        'selected_org': 'HOSP',
        'pending_tickets': pending_count,
        'devices_json': devices_json,
        'audit_logs_json': audit_logs_json,
    }
    return render(request, "admin/audit.html", context)

@admin_required
def tag(request):
    """5. Asset Tag Center: Printable QR & Barcode stickers (PSM Hospital)"""
    org = request.GET.get('org', 'HOSP')
    if org == 'UNI':
        return redirect('/tag/?org=HOSP')
    pending_count = DeviceComplaint.objects.filter(status='Pending').count()
    devices_json, audit_logs_json = get_serialized_devices_and_logs()
    context = {
        'selected_org': 'HOSP',
        'pending_tickets': pending_count,
        'devices_json': devices_json,
        'audit_logs_json': audit_logs_json,
    }
    return render(request, "admin/tag.html", context)


@admin_required
def pms_schedule(request):
    """7. Equipment Preventive Maintenance Service (PMS) Schedule Tracker"""
    org = 'HOSP'
    search = request.GET.get('search', '').strip()
    filter_company = request.GET.get('company', 'ALL')
    filter_status = request.GET.get('status', 'ALL')

    records = EquipmentPMS.objects.all().order_by('id')

    if search:
        records = records.filter(
            models.Q(asset_code__icontains=search) |
            models.Q(equipment_name__icontains=search) |
            models.Q(company_name__icontains=search) |
            models.Q(department_location__icontains=search)
        )
    if filter_company and filter_company != 'ALL':
        records = records.filter(company_name=filter_company)
    if filter_status and filter_status != 'ALL':
        records = records.filter(status=filter_status)

    total_count = EquipmentPMS.objects.count()
    completed_count = EquipmentPMS.objects.filter(status='Completed').count()
    pending_count = EquipmentPMS.objects.filter(status='Pending 4th PMS').count()
    due_soon_count = EquipmentPMS.objects.filter(status='Due Soon').count()
    
    companies = EquipmentPMS.objects.values_list('company_name', flat=True).distinct().order_by('company_name')

    pending_tickets = DeviceComplaint.objects.filter(status='Pending').count()

    inventory_devices = DeviceAsset.objects.all().order_by('asset_id')

    context = {
        'selected_org': org,
        'records': records,
        'total_count': total_count,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'due_soon_count': due_soon_count,
        'companies': companies,
        'search': search,
        'filter_company': filter_company,
        'filter_status': filter_status,
        'pending_tickets': pending_tickets,
        'inventory_devices': inventory_devices,
    }
    return render(request, "admin/pms_schedule.html", context)


@csrf_exempt
def api_update_pms(request, pms_id):
    """Update PMS schedule record (supports full field edit or quick 4th cycle)."""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
        except Exception:
            data = request.POST

        item = get_object_or_404(EquipmentPMS, pk=pms_id)
        
        # Check and update fields if provided
        if 'equipment_name' in data:
            item.equipment_name = data.get('equipment_name', item.equipment_name).strip()
        if 'company_name' in data:
            item.company_name = data.get('company_name', item.company_name).strip()
        if 'asset_code' in data:
            new_code = data.get('asset_code', item.asset_code).strip().upper()
            if new_code and new_code != item.asset_code:
                if EquipmentPMS.objects.filter(asset_code=new_code).exclude(pk=pms_id).exists():
                    return JsonResponse({'success': False, 'error': f'Asset code {new_code} already belongs to another record!'}, status=400)
                item.asset_code = new_code
        if 'installation_date' in data:
            item.installation_date = data.get('installation_date', item.installation_date).strip()
        if 'maintenance_frequency' in data:
            item.maintenance_frequency = data.get('maintenance_frequency', item.maintenance_frequency).strip()
        if 'department_location' in data:
            item.department_location = data.get('department_location', item.department_location).strip()
        if 'pms1_done_date' in data:
            item.pms1_done_date = data.get('pms1_done_date', item.pms1_done_date).strip()
        if 'pms2_due_date' in data:
            item.pms2_due_date = data.get('pms2_due_date', item.pms2_due_date).strip()
        if 'pms2_done_date' in data:
            item.pms2_done_date = data.get('pms2_done_date', item.pms2_done_date).strip()
        if 'pms3_due_date' in data:
            item.pms3_due_date = data.get('pms3_due_date', item.pms3_due_date).strip()
        if 'pms3_done_date' in data:
            item.pms3_done_date = data.get('pms3_done_date', item.pms3_done_date).strip()
        if 'pms4_due_date' in data:
            item.pms4_due_date = data.get('pms4_due_date', item.pms4_due_date).strip()
        if 'pms4_done_date' in data:
            item.pms4_done_date = data.get('pms4_done_date', item.pms4_done_date).strip()
        if 'engineer_notes' in data:
            item.engineer_notes = data.get('engineer_notes', item.engineer_notes).strip()
        if 'status' in data:
            item.status = data.get('status', item.status).strip()

        item.save()

        return JsonResponse({
            'success': True,
            'message': f'PMS Record for {item.asset_code} updated successfully!',
            'id': item.id,
            'asset_code': item.asset_code,
            'equipment_name': item.equipment_name,
            'company_name': item.company_name,
            'pms4_done_date': item.pms4_done_date,
            'status': item.status
        })

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)


@csrf_exempt
def api_delete_pms(request, pms_id):
    """Delete an equipment PMS schedule record."""
    if request.method in ['POST', 'DELETE']:
        item = get_object_or_404(EquipmentPMS, pk=pms_id)
        code = item.asset_code
        item.delete()
        return JsonResponse({'success': True, 'message': f'PMS Record {code} deleted successfully!'})
    return JsonResponse({'success': False, 'error': 'POST/DELETE method required.'}, status=405)


@csrf_exempt
def api_add_pms(request):
    """Add a new equipment maintenance schedule record."""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
        except Exception:
            data = request.POST

        asset_code = data.get('asset_code', '').strip().upper()
        if not asset_code:
            return JsonResponse({'success': False, 'error': 'Asset Code is required.'}, status=400)

        if EquipmentPMS.objects.filter(asset_code=asset_code).exists():
            return JsonResponse({'success': False, 'error': f'Asset code {asset_code} already exists!'}, status=400)

        new_record = EquipmentPMS.objects.create(
            equipment_name=data.get('equipment_name', 'Computer').strip(),
            company_name=data.get('company_name', 'HP').strip(),
            installation_date=data.get('installation_date', '08-11-2021').strip(),
            asset_code=asset_code,
            maintenance_frequency=data.get('maintenance_frequency', 'QUARTERLY').strip(),
            pms1_done_date=data.get('pms1_done_date', '').strip(),
            pms2_due_date=data.get('pms2_due_date', '').strip(),
            pms2_done_date=data.get('pms2_done_date', '').strip(),
            pms3_due_date=data.get('pms3_due_date', '').strip(),
            pms3_done_date=data.get('pms3_done_date', '').strip(),
            pms4_due_date=data.get('pms4_due_date', '').strip(),
            pms4_done_date=data.get('pms4_done_date', '').strip(),
            status=data.get('status', 'Pending 4th PMS').strip(),
            department_location=data.get('department_location', 'IT Lab').strip(),
            engineer_notes=data.get('engineer_notes', '').strip()
        )
        return JsonResponse({'success': True, 'id': new_record.id, 'asset_code': new_record.asset_code})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)


@csrf_exempt
def api_import_pms_excel(request):
    """Import PMS schedule records from Excel (.xlsx, .xls) or CSV."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required.'}, status=405)

    import json
    import csv
    import io
    import datetime

    rows_data = []

    # 1. Check if multipart file uploaded
    if 'file' in request.FILES:
        uploaded_file = request.FILES['file']
        filename = uploaded_file.name.lower()

        if filename.endswith('.csv'):
            try:
                content = uploaded_file.read().decode('utf-8-sig', errors='replace')
                reader = csv.DictReader(io.StringIO(content))
                for r in reader:
                    rows_data.append(r)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Failed to parse CSV file: {str(e)}'}, status=400)
        elif filename.endswith(('.xlsx', '.xlsm', '.xltx', '.xls')):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(io.BytesIO(uploaded_file.read()), data_only=True)
                ws = wb.active
                iter_rows = list(ws.iter_rows(values_only=True))
                if not iter_rows:
                    return JsonResponse({'success': False, 'error': 'Uploaded Excel file is empty.'}, status=400)

                header_row = iter_rows[0]
                headers = [str(h).strip() if h is not None else f"col_{idx}" for idx, h in enumerate(header_row)]

                for row_vals in iter_rows[1:]:
                    if not any(row_vals):
                        continue
                    row_dict = {}
                    for idx, val in enumerate(row_vals):
                        if idx < len(headers):
                            if isinstance(val, (datetime.datetime, datetime.date)):
                                row_dict[headers[idx]] = val.strftime('%d-%m-%Y' if isinstance(val, datetime.date) and not isinstance(val, datetime.datetime) else '%d-%m-%Y %H:%M')
                            elif isinstance(val, datetime.time):
                                row_dict[headers[idx]] = val.strftime('%H:%M')
                            else:
                                row_dict[headers[idx]] = str(val).strip() if val is not None else ''
                    rows_data.append(row_dict)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Failed to parse Excel file: {str(e)}'}, status=400)
        else:
            return JsonResponse({'success': False, 'error': 'Unsupported file format. Please upload an Excel (.xlsx) or CSV file.'}, status=400)

    # 2. Check JSON payload
    elif request.body:
        try:
            payload = json.loads(request.body)
            if isinstance(payload, list):
                rows_data = payload
            elif isinstance(payload, dict):
                rows_data = payload.get('rows', [])
        except Exception:
            pass

    if not rows_data:
        return JsonResponse({'success': False, 'error': 'No valid data rows found in uploaded file or request.'}, status=400)

    def find_val(row_dict, aliases, default=''):
        lower_map = {str(k).strip().lower(): v for k, v in row_dict.items() if k is not None}
        for a in aliases:
            al = a.lower()
            if al in lower_map and lower_map[al] not in (None, ''):
                return str(lower_map[al]).strip()
        return default

    created_or_updated = 0

    for r in rows_data:
        asset_code = find_val(r, ['asset coding', 'asset coding (tag)', 'asset_code', 'asset code', 'tag', 'code']).upper()
        equipment_name = find_val(r, ['name of the equipment', 'equipment name', 'equipment_name', 'equipment', 'name'], 'Computer')
        company_name = find_val(r, ['name of company', 'company / oem', 'company_name', 'company', 'oem', 'vendor'], 'HP')

        if not asset_code:
            if not any(r.values()):
                continue
            random_sfx = random.randint(100, 999)
            asset_code = f"KH/IT/{equipment_name[:4].upper()}/{random_sfx}"

        install_date = find_val(r, ['date of installation', 'installation date', 'installation_date', 'installed on'], '08-11-2021')
        frequency = find_val(r, ['maintainance frequency', 'maintenance frequency', 'frequency', 'maintenance_frequency'], 'QUARTERLY').upper()
        if 'HALF' in frequency:
            frequency = 'HALF-YEARLY'
        elif 'ANNUAL' in frequency:
            frequency = 'ANNUALLY'
        else:
            frequency = 'QUARTERLY'

        pms1_done = find_val(r, ['1st pms done date', 'pms1 done date', 'pms1_done_date', 'pms1 done', 'pms1'])
        pms2_due = find_val(r, ['due date of 2nd pms', '2nd pms due date', 'pms2_due_date', 'pms2 due'])
        pms2_done = find_val(r, ['2nd pms done date', 'pms2 done date', 'pms2_done_date', 'pms2 done'])
        pms3_due = find_val(r, ['due date of 3rd pms', '3rd pms due date', 'pms3_due_date', 'pms3 due'])
        pms3_done = find_val(r, ['3rd pms done date', 'pms3 done date', 'pms3_done_date', 'pms3 done'])
        pms4_due = find_val(r, ['due date of 4th pms', '4th pms due date', 'pms4_due_date', 'pms4 due'])
        pms4_done = find_val(r, ['4th pms done date', 'pms4 done date', 'pms4_done_date', 'pms4 done'])

        location = find_val(r, ['location / department', 'location', 'department_location', 'department', 'room'], 'IT Lab')
        notes = find_val(r, ['engineer notes', 'service engineer / inspection notes', 'engineer_notes', 'notes', 'remarks'], 'Preventive maintenance check completed.')

        status = find_val(r, ['status'])
        if not status:
            status = 'Completed' if pms4_done else 'Pending 4th PMS'

        EquipmentPMS.objects.update_or_create(
            asset_code=asset_code,
            defaults={
                'equipment_name': equipment_name,
                'company_name': company_name,
                'installation_date': install_date,
                'maintenance_frequency': frequency,
                'pms1_done_date': pms1_done,
                'pms2_due_date': pms2_due,
                'pms2_done_date': pms2_done,
                'pms3_due_date': pms3_due,
                'pms3_done_date': pms3_done,
                'pms4_due_date': pms4_due,
                'pms4_done_date': pms4_done,
                'department_location': location,
                'engineer_notes': notes,
                'status': status,
            }
        )
        created_or_updated += 1

    return JsonResponse({
        'success': True,
        'count': created_or_updated,
        'message': f'Successfully registered {created_or_updated} PMS records from Excel!'
    })


# ============================================================================
# 8. EQUIPMENT BREAKDOWN REGISTER
# ============================================================================

def ensure_sample_breakdowns():
    """Seed initial breakdown records if table is empty matching User's Image 1."""
    if EquipmentBreakdown.objects.count() == 0:
        samples = [
            {
                'breakdown_date': '26/07/2022',
                'breakdown_time': '2:00 pm',
                'asset_id': 'BME-PUMP-001',
                'device_name': 'Other',
                'location': 'Biomedical Wing, Room 12',
                'breakdown_cause': 'breakage & calibration drop',
                'equipment_type': 'Routine',
                'intimation_datetime': '26/07/2022 2:10 pm',
                'checkin_datetime': '26/07/2022 2:20 pm',
                'dept_hod_name': 'Nam of staff nurse',
                'it_staff_name': 'Name of BME staff',
                'repair_datetime': '26/07/2022 2:35 pm',
                'tat_duration': '35 minutes',
                'sign_dept_hod': 'Sign of Departmental HOD',
                'sign_it_cell': 'Sign of BME staff',
                'status': 'Resolved'
            },
            {
                'breakdown_date': '15/08/2022',
                'breakdown_time': '10:15 am',
                'asset_id': 'KH/IT/COMPUTER/4',
                'device_name': 'CPU',
                'location': 'IT Server Room, 3rd Floor',
                'breakdown_cause': 'RAM failure & continuous beep on boot',
                'equipment_type': 'Critical',
                'intimation_datetime': '15/08/2022 10:20 am',
                'checkin_datetime': '15/08/2022 10:30 am',
                'dept_hod_name': 'Dr. Rajesh Sharma',
                'it_staff_name': 'Er. Amit Verma (IT CELL)',
                'repair_datetime': '15/08/2022 11:15 am',
                'tat_duration': '45 minutes',
                'sign_dept_hod': 'Dr. Rajesh Sharma',
                'sign_it_cell': 'Er. Amit Verma',
                'status': 'Resolved'
            },
            {
                'breakdown_date': '03/09/2022',
                'breakdown_time': '11:45 am',
                'asset_id': 'KH/IT/PRINTER/2',
                'device_name': 'Laser Printer',
                'location': 'Faculty Office, 2nd Floor',
                'breakdown_cause': 'Paper feed roller jammed & toner cartridge error',
                'equipment_type': 'Routine',
                'intimation_datetime': '03/09/2022 11:55 am',
                'checkin_datetime': '03/09/2022 12:05 pm',
                'dept_hod_name': 'Prof. Ananya Sen',
                'it_staff_name': 'Sanjay Rawat (IT Support)',
                'repair_datetime': '03/09/2022 12:40 pm',
                'tat_duration': '35 minutes',
                'sign_dept_hod': 'Prof. Ananya Sen',
                'sign_it_cell': 'Sanjay Rawat',
                'status': 'Resolved'
            },
            {
                'breakdown_date': '20/10/2022',
                'breakdown_time': '03:10 pm',
                'asset_id': 'KH/IT/UPS/1',
                'device_name': 'UPS',
                'location': 'Data Center, Ground Floor',
                'breakdown_cause': 'Backup battery degraded, load tripping under AC failure',
                'equipment_type': 'Critical',
                'intimation_datetime': '20/10/2022 03:15 pm',
                'checkin_datetime': '20/10/2022 03:25 pm',
                'dept_hod_name': 'Dr. Vikram Sharma',
                'it_staff_name': 'Er. Amit Verma (IT CELL)',
                'repair_datetime': '20/10/2022 04:20 pm',
                'tat_duration': '55 minutes',
                'sign_dept_hod': 'Dr. Vikram Sharma',
                'sign_it_cell': 'Er. Amit Verma',
                'status': 'Resolved'
            },
            {
                'breakdown_date': '02/09/2026',
                'breakdown_time': '09:30 am',
                'asset_id': 'KH/IT/COMPUTER/12',
                'device_name': 'Monitor',
                'location': 'Diagnostic Lab, 1st Floor',
                'breakdown_cause': 'Flickering horizontal scanlines & capacitor whistling',
                'equipment_type': 'Critical',
                'intimation_datetime': '02/09/2026 09:35 am',
                'checkin_datetime': '02/09/2026 09:45 am',
                'dept_hod_name': 'Dr. Kavita Nair',
                'it_staff_name': 'Suresh Patil (Hardware Engg)',
                'repair_datetime': '',
                'tat_duration': 'In Progress',
                'sign_dept_hod': 'Pending Verification',
                'sign_it_cell': 'Under Diagnostics',
                'status': 'Under Repair'
            }
        ]
        for item in samples:
            EquipmentBreakdown.objects.create(**item)


@admin_required
def equipment_breakdown(request):
    """8. Equipment Breakdown Register view."""
    ensure_sample_breakdowns()

    org = request.GET.get('org', 'ALL')
    search = request.GET.get('search', '').strip()
    filter_device = request.GET.get('device', 'ALL')
    filter_type = request.GET.get('type', 'ALL')
    filter_status = request.GET.get('status', 'ALL')

    records = EquipmentBreakdown.objects.all().order_by('-id')

    if search:
        records = records.filter(
            models.Q(asset_id__icontains=search) |
            models.Q(device_name__icontains=search) |
            models.Q(location__icontains=search) |
            models.Q(breakdown_cause__icontains=search) |
            models.Q(dept_hod_name__icontains=search) |
            models.Q(it_staff_name__icontains=search) |
            models.Q(status__icontains=search) |
            models.Q(equipment_type__icontains=search) |
            models.Q(tat_duration__icontains=search)
        )
    if filter_device and filter_device != 'ALL':
        records = records.filter(device_name__iexact=filter_device)
    if filter_type and filter_type != 'ALL':
        records = records.filter(equipment_type__iexact=filter_type)
    if filter_status and filter_status != 'ALL':
        s_val = filter_status.strip().lower()
        if 'resolve' in s_val or 'repaired' in s_val:
            records = records.filter(status__icontains='resolve')
        elif 'repair' in s_val:
            records = records.filter(status__icontains='repair')
        else:
            records = records.filter(status__iexact=filter_status.strip())

    total_count = EquipmentBreakdown.objects.count()
    critical_count = EquipmentBreakdown.objects.filter(equipment_type='Critical').count()
    routine_count = EquipmentBreakdown.objects.filter(equipment_type='Routine').count()
    under_repair_count = EquipmentBreakdown.objects.filter(status='Under Repair').count()
    resolved_count = EquipmentBreakdown.objects.filter(status='Resolved').count()

    # Dropdown choices from User's Images 3 & 4
    device_choices = [c[0] for c in EquipmentBreakdown.DEVICE_NAME_CHOICES]
    type_choices = [c[0] for c in EquipmentBreakdown.EQUIPMENT_TYPE_CHOICES]

    pending_tickets = DeviceComplaint.objects.filter(status='Pending').count()
    pms_total_count = EquipmentPMS.objects.count()

    inventory_devices = DeviceAsset.objects.all().order_by('asset_id')
    pms_assets = EquipmentPMS.objects.all().order_by('asset_code')

    context = {
        'selected_org': org,
        'records': records,
        'total_count': total_count,
        'critical_count': critical_count,
        'routine_count': routine_count,
        'under_repair_count': under_repair_count,
        'resolved_count': resolved_count,
        'device_choices': device_choices,
        'type_choices': type_choices,
        'search': search,
        'filter_device': filter_device,
        'filter_type': filter_type,
        'filter_status': filter_status,
        'pending_tickets': pending_tickets,
        'pms_total_count': pms_total_count,
        'inventory_devices': inventory_devices,
        'pms_assets': pms_assets,
    }
    return render(request, "admin/equipment_breakdown.html", context)


def _sanitize_date_slash(val):
    if not val:
        return ''
    return val.strip().replace('.', '/')

def _sanitize_time_colon(val):
    if not val:
        return ''
    import re
    return re.sub(r'(\d+)\.(\d+)', r'\1:\2', val.strip())

def _sanitize_datetime(val):
    if not val:
        return ''
    import re
    parts = val.strip().split(' ', 1)
    if len(parts) == 2:
        d = parts[0].replace('.', '/')
        t = re.sub(r'(\d+)\.(\d+)', r'\1:\2', parts[1])
        return f"{d} {t}"
    return re.sub(r'(\d+)\.(\d+)', r'\1:\2', val.strip().replace('.', '/'))


@csrf_exempt
def api_add_breakdown(request):
    """Add a new breakdown record via AJAX modal and sync DeviceAsset status."""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
        except Exception:
            data = request.POST

        breakdown_date = _sanitize_date_slash(data.get('breakdown_date', ''))
        breakdown_time = _sanitize_time_colon(data.get('breakdown_time', ''))
        asset_id = data.get('asset_id', '').strip()
        device_name = data.get('device_name', 'CPU').strip()
        breakdown_cause = data.get('breakdown_cause', '').strip()
        equipment_type = data.get('equipment_type', 'Routine').strip()

        if not asset_id:
            return JsonResponse({'success': False, 'error': 'IT Asset ID is required.'}, status=400)

        intimation_datetime = _sanitize_datetime(data.get('intimation_datetime', ''))
        checkin_datetime = _sanitize_datetime(data.get('checkin_datetime', ''))
        dept_hod_name = data.get('dept_hod_name', '').strip()
        it_staff_name = data.get('it_staff_name', 'IT Staff').strip()
        repair_datetime = _sanitize_datetime(data.get('repair_datetime', ''))
        tat_duration = data.get('tat_duration', '').strip()
        sign_dept_hod = data.get('sign_dept_hod', '').strip()
        sign_it_cell = data.get('sign_it_cell', '').strip()
        status = data.get('status', 'Under Repair' if not repair_datetime else 'Resolved').strip()
        location = data.get('location', '').strip()
        if not location and asset_id:
            matching_dev = DeviceAsset.objects.filter(models.Q(asset_id__iexact=asset_id)).first()
            if matching_dev:
                loc_parts = [p for p in [matching_dev.building_name, matching_dev.floor_name, matching_dev.room_name] if p]
                location = " - ".join(loc_parts) if loc_parts else (matching_dev.room_name or '')

        new_record = EquipmentBreakdown.objects.create(
            breakdown_date=breakdown_date,
            breakdown_time=breakdown_time,
            asset_id=asset_id,
            device_name=device_name,
            location=location,
            breakdown_cause=breakdown_cause,
            equipment_type=equipment_type,
            intimation_datetime=intimation_datetime,
            checkin_datetime=checkin_datetime,
            dept_hod_name=dept_hod_name,
            it_staff_name=it_staff_name,
            repair_datetime=repair_datetime,
            tat_duration=tat_duration,
            sign_dept_hod=sign_dept_hod,
            sign_it_cell=sign_it_cell,
            status=status
        )

        # Database Bidirectional Sync: if status is Under Repair, update DeviceAsset
        if status == 'Under Repair':
            matching_dev = DeviceAsset.objects.filter(models.Q(asset_id__iexact=asset_id)).first()
            if matching_dev:
                matching_dev.status = 'Maintenance'
                matching_dev.save(update_fields=['status'])

        return JsonResponse({
            'success': True,
            'message': f'Breakdown record #{new_record.id} logged for {new_record.asset_id}!',
            'id': new_record.id,
            'asset_id': new_record.asset_id
        })

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)


@csrf_exempt
def api_resolve_breakdown(request, pk):
    """Resolve / close out an active equipment breakdown and restore DeviceAsset status."""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
        except Exception:
            data = request.POST

        record = get_object_or_404(EquipmentBreakdown, pk=pk)
        repair_date = _sanitize_datetime(data.get('repair_datetime', ''))
        tat = data.get('tat_duration', '').strip()
        sign_it = data.get('sign_it_cell', '').strip()

        if not repair_date:
            repair_date = timezone.now().strftime('%d/%m/%Y %I:%M %p').lower()
        if not tat:
            tat = '30 minutes'
        if not sign_it:
            sign_it = record.it_staff_name or 'IT CELL Engineer'

        record.repair_datetime = repair_date
        record.tat_duration = tat
        record.sign_it_cell = sign_it
        record.status = 'Resolved'
        record.save()

        # Database Bidirectional Sync: Restore hardware asset back to Active
        matching_dev = DeviceAsset.objects.filter(models.Q(asset_id__iexact=record.asset_id)).first()
        if matching_dev:
            matching_dev.status = 'Active'
            matching_dev.save(update_fields=['status'])

        return JsonResponse({
            'success': True,
            'message': f'Breakdown #{record.id} resolved!',
            'repair_datetime': record.repair_datetime,
            'tat_duration': record.tat_duration
        })

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)


@csrf_exempt
def api_update_breakdown(request, pk):
    """Update all fields of an existing equipment breakdown incident."""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
        except Exception:
            data = request.POST

        record = get_object_or_404(EquipmentBreakdown, pk=pk)

        if 'breakdown_date' in data:
            record.breakdown_date = _sanitize_date_slash(data.get('breakdown_date', record.breakdown_date))
        if 'breakdown_time' in data:
            record.breakdown_time = _sanitize_time_colon(data.get('breakdown_time', record.breakdown_time))
        if 'asset_id' in data:
            record.asset_id = data.get('asset_id', record.asset_id).strip()
        if 'device_name' in data:
            record.device_name = data.get('device_name', record.device_name).strip()
        if 'breakdown_cause' in data:
            record.breakdown_cause = data.get('breakdown_cause', record.breakdown_cause).strip()
        if 'equipment_type' in data:
            record.equipment_type = data.get('equipment_type', record.equipment_type).strip()
        if 'intimation_datetime' in data:
            record.intimation_datetime = _sanitize_datetime(data.get('intimation_datetime', record.intimation_datetime))
        if 'checkin_datetime' in data:
            record.checkin_datetime = _sanitize_datetime(data.get('checkin_datetime', record.checkin_datetime))
        if 'dept_hod_name' in data:
            record.dept_hod_name = data.get('dept_hod_name', record.dept_hod_name).strip()
        if 'it_staff_name' in data:
            record.it_staff_name = data.get('it_staff_name', record.it_staff_name).strip()
        if 'repair_datetime' in data:
            record.repair_datetime = _sanitize_datetime(data.get('repair_datetime', record.repair_datetime))
        if 'tat_duration' in data:
            record.tat_duration = data.get('tat_duration', record.tat_duration).strip()
        if 'sign_dept_hod' in data:
            record.sign_dept_hod = data.get('sign_dept_hod', record.sign_dept_hod).strip()
        if 'sign_it_cell' in data:
            record.sign_it_cell = data.get('sign_it_cell', record.sign_it_cell).strip()
        if 'location' in data:
            record.location = data.get('location', record.location).strip()
        if 'status' in data:
            record.status = data.get('status', record.status).strip()

        record.save()

        # Database Bidirectional Sync
        matching_dev = DeviceAsset.objects.filter(models.Q(asset_id__iexact=record.asset_id)).first()
        if matching_dev:
            matching_dev.status = 'Maintenance' if record.status == 'Under Repair' else 'Active'
            matching_dev.save(update_fields=['status'])

        return JsonResponse({
            'success': True,
            'message': f'Breakdown record #{record.id} updated successfully!',
            'id': record.id,
            'asset_id': record.asset_id,
            'status': record.status
        })

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)


@csrf_exempt
def api_delete_breakdown(request, pk):
    """Delete an equipment breakdown incident."""
    if request.method in ['POST', 'DELETE']:
        record = get_object_or_404(EquipmentBreakdown, pk=pk)
        asset_id = record.asset_id
        was_under_repair = (record.status == 'Under Repair')
        record.delete()

        # If it was under repair, check if any other breakdown for this asset is active
        if was_under_repair:
            still_active = EquipmentBreakdown.objects.filter(asset_id=asset_id, status='Under Repair').exists()
            if not still_active:
                matching_dev = DeviceAsset.objects.filter(models.Q(asset_id__iexact=asset_id)).first()
                if matching_dev:
                    matching_dev.status = 'Active'
                    matching_dev.save(update_fields=['status'])

        return JsonResponse({'success': True, 'message': f'Breakdown record #{pk} for {asset_id} deleted successfully!'})

    return JsonResponse({'success': False, 'error': 'POST/DELETE method required.'}, status=405)


@csrf_exempt
def api_import_breakdown_excel(request):
    """Import equipment breakdown records from Excel (.xlsx, .xls) or CSV."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required.'}, status=405)

    import json
    import csv
    import io
    import datetime

    rows_data = []

    # 1. Check if multipart file was uploaded
    if 'file' in request.FILES:
        uploaded_file = request.FILES['file']
        filename = uploaded_file.name.lower()
        
        if filename.endswith('.csv'):
            try:
                content = uploaded_file.read().decode('utf-8-sig', errors='replace')
                reader = csv.DictReader(io.StringIO(content))
                for r in reader:
                    rows_data.append(r)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Failed to parse CSV file: {str(e)}'}, status=400)
        elif filename.endswith(('.xlsx', '.xlsm', '.xltx', '.xls')):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(io.BytesIO(uploaded_file.read()), data_only=True)
                ws = wb.active
                iter_rows = list(ws.iter_rows(values_only=True))
                if not iter_rows:
                    return JsonResponse({'success': False, 'error': 'Uploaded Excel file is empty.'}, status=400)
                
                header_row = iter_rows[0]
                headers = [str(h).strip() if h is not None else f"col_{idx}" for idx, h in enumerate(header_row)]
                
                for row_vals in iter_rows[1:]:
                    if not any(row_vals):
                        continue
                    row_dict = {}
                    for idx, val in enumerate(row_vals):
                        if idx < len(headers):
                            if isinstance(val, (datetime.datetime, datetime.date)):
                                row_dict[headers[idx]] = val.strftime('%d/%m/%Y' if isinstance(val, datetime.date) and not isinstance(val, datetime.datetime) else '%d/%m/%Y %H:%M')
                            elif isinstance(val, datetime.time):
                                row_dict[headers[idx]] = val.strftime('%H:%M')
                            else:
                                row_dict[headers[idx]] = str(val).strip() if val is not None else ''
                    rows_data.append(row_dict)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Failed to parse Excel file: {str(e)}'}, status=400)
        else:
            return JsonResponse({'success': False, 'error': 'Unsupported file format. Please upload an Excel (.xlsx) or CSV file.'}, status=400)

    # 2. Check if JSON payload was passed
    elif request.body:
        try:
            payload = json.loads(request.body)
            if isinstance(payload, list):
                rows_data = payload
            elif isinstance(payload, dict):
                rows_data = payload.get('rows', [])
        except Exception:
            pass

    if not rows_data:
        return JsonResponse({'success': False, 'error': 'No valid data rows found in uploaded file or request.'}, status=400)

    def find_val(row_dict, aliases, default=''):
        lower_map = {str(k).strip().lower(): v for k, v in row_dict.items() if k is not None}
        for a in aliases:
            al = a.lower()
            if al in lower_map and lower_map[al] not in (None, ''):
                return str(lower_map[al]).strip()
        return default

    created_records = []

    for r in rows_data:
        asset_id = find_val(r, [
            'asset id', 'asset_id', 'it asset id', 'asset number', 'asset no', 'instrument / equipment name', 
            'equipment name', 'device asset', 'asset'
        ])
        device_name = find_val(r, ['device name', 'device_name', 'device', 'instrument name', 'equipment'], 'CPU')
        
        # If row is completely empty, skip
        if not asset_id and not any(r.values()):
            continue
            
        if not asset_id:
            random_sfx = random.randint(100, 999)
            asset_id = f"IT-{device_name[:3].upper()}-{random_sfx}"

        breakdown_date = _sanitize_date_slash(find_val(r, ['breakdown date', 'breakdown_date', 'date', 'incident date'], timezone.now().strftime('%d/%m/%Y')))
        breakdown_time = _sanitize_time_colon(find_val(r, ['breakdown time', 'breakdown_time', 'time', 'incident time'], timezone.now().strftime('%H:%M')))
        breakdown_cause = find_val(r, ['breakdown cause', 'breakdown_cause', 'cause', 'fault', 'issue', 'problem', 'reason'], 'Hardware fault')
        equipment_type = find_val(r, ['type of equipment critical/routine', 'equipment type', 'equipment_type', 'type', 'critical/routine'], 'Routine')
        
        if 'crit' in equipment_type.lower():
            equipment_type = 'Critical'
        else:
            equipment_type = 'Routine'

        intimation_datetime = _sanitize_datetime(find_val(r, ['intimation date & time to it cell / bme', 'intimation date & time to bio medical engineer', 'intimation date & time', 'intimation datetime', 'intimation_datetime', 'intimation', 'notified at']))
        checkin_datetime = _sanitize_datetime(find_val(r, ['checkin date & time', 'checkin datetime', 'checkin_datetime', 'checkin', 'received at']))
        dept_hod_name = find_val(r, ['name of departmental hod', 'dept hod name', 'dept_hod_name', 'hod name', 'department hod', 'dept hod'])
        it_staff_name = find_val(r, ['name of it cell / bme staff', 'name of bme staff', 'it staff name', 'it_staff_name', 'it staff', 'bme staff', 'technician'], 'IT Support')
        repair_datetime = _sanitize_datetime(find_val(r, ['repair date & time', 'repair datetime', 'repair_datetime', 'repaired at', 'completion date']))
        tat_duration = find_val(r, ['total turn around time (tat)', 'turn around time', 'tat duration', 'tat_duration', 'tat'])
        sign_dept_hod = find_val(r, ['sign of departmental hod', 'sign dept hod', 'sign_dept_hod', 'hod sign'])
        sign_it_cell = find_val(r, ['sign of it cell / bme staff', 'sign of bme staff', 'sign it cell', 'sign_it_cell', 'it sign'])
        location = find_val(r, ['location', 'room', 'room / location', 'room location', 'department', 'dept', 'ward', 'building', 'floor'])
        if not location and asset_id:
            dev = DeviceAsset.objects.filter(models.Q(asset_id__iexact=asset_id)).first()
            if dev:
                loc_parts = [p for p in [dev.building_name, dev.floor_name, dev.room_name] if p]
                location = " - ".join(loc_parts) if loc_parts else (dev.room_name or '')

        raw_status = find_val(r, ['status'])
        if raw_status:
            s_low = raw_status.lower()
            if 'resolve' in s_low or 'repaired' in s_low or 'closed' in s_low or 'fixed' in s_low or 'completed' in s_low:
                status = 'Resolved'
            elif 'repair' in s_low or 'progress' in s_low or 'pending' in s_low or 'open' in s_low:
                status = 'Under Repair'
            else:
                status = 'Resolved' if (repair_datetime or tat_duration) else 'Under Repair'
        else:
            status = 'Resolved' if (repair_datetime or tat_duration) else 'Under Repair'

        rec = EquipmentBreakdown.objects.create(
            breakdown_date=breakdown_date,
            breakdown_time=breakdown_time,
            asset_id=asset_id,
            device_name=device_name,
            location=location,
            breakdown_cause=breakdown_cause,
            equipment_type=equipment_type,
            intimation_datetime=intimation_datetime,
            checkin_datetime=checkin_datetime,
            dept_hod_name=dept_hod_name,
            it_staff_name=it_staff_name,
            repair_datetime=repair_datetime,
            tat_duration=tat_duration,
            sign_dept_hod=sign_dept_hod,
            sign_it_cell=sign_it_cell,
            status=status
        )
        created_records.append(rec)

    return JsonResponse({
        'success': True,
        'count': len(created_records),
        'message': f'Successfully imported {len(created_records)} equipment breakdown records from Excel!'
    })


@csrf_exempt
def api_import_devices_excel(request):
    """Import devices/hardware inventory records from Excel (.xlsx, .xls) or CSV into DeviceAsset."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required.'}, status=405)

    import json
    import csv
    import io
    import datetime
    import uuid
    import random

    rows_data = []

    # 1. Check if multipart file was uploaded
    if 'file' in request.FILES:
        uploaded_file = request.FILES['file']
        filename = uploaded_file.name.lower()

        if filename.endswith('.csv'):
            try:
                content = uploaded_file.read().decode('utf-8-sig', errors='replace')
                reader = csv.DictReader(io.StringIO(content))
                for r in reader:
                    rows_data.append(r)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Failed to parse CSV file: {str(e)}'}, status=400)
        elif filename.endswith(('.xlsx', '.xlsm', '.xltx', '.xls')):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(io.BytesIO(uploaded_file.read()), data_only=True)
                ws = wb.active
                iter_rows = list(ws.iter_rows(values_only=True))
                if not iter_rows:
                    return JsonResponse({'success': False, 'error': 'Uploaded Excel file is empty.'}, status=400)

                header_row = iter_rows[0]
                headers = [str(h).strip() if h is not None else f"col_{idx}" for idx, h in enumerate(header_row)]

                for row_vals in iter_rows[1:]:
                    if not any(row_vals):
                        continue
                    row_dict = {}
                    for idx, val in enumerate(row_vals):
                        if idx < len(headers):
                            if isinstance(val, (datetime.datetime, datetime.date)):
                                row_dict[headers[idx]] = val.strftime('%d-%b-%Y')
                            elif isinstance(val, datetime.time):
                                row_dict[headers[idx]] = val.strftime('%H:%M')
                            else:
                                row_dict[headers[idx]] = str(val).strip() if val is not None else ''
                    rows_data.append(row_dict)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Failed to parse Excel file: {str(e)}'}, status=400)
        else:
            return JsonResponse({'success': False, 'error': 'Unsupported file format. Please upload an Excel (.xlsx, .xls) or CSV file.'}, status=400)

    # 2. Check if JSON payload was passed
    elif request.body:
        try:
            payload = json.loads(request.body)
            if isinstance(payload, list):
                rows_data = payload
            elif isinstance(payload, dict):
                rows_data = payload.get('rows', [])
        except Exception:
            pass

    if not rows_data:
        return JsonResponse({'success': False, 'error': 'No valid data rows found in uploaded file or request.'}, status=400)

    def find_val(row_dict, aliases, default=''):
        lower_map = {str(k).strip().lower(): v for k, v in row_dict.items() if k is not None}
        for a in aliases:
            al = a.lower()
            if al in lower_map and lower_map[al] not in (None, ''):
                return str(lower_map[al]).strip()
        return default

    saved_count = 0
    created_count = 0
    updated_count = 0

    for r in rows_data:
        if not any(str(v).strip() for v in r.values() if v is not None):
            continue

        asset_id = find_val(r, [
            'asset id', 'asset_id', 'it asset id', 'asset tag', 'asset tag / id',
            'asset number', 'asset no', 'tag id', 'tag', 'device asset id', 'device tag', 'asset'
        ])
        serial_number = find_val(r, [
            'serial number', 'serial_number', 'serial no', 'serial', 'sn', 's/n'
        ])

        if not asset_id and not serial_number:
            continue

        if not asset_id:
            raw_t = find_val(r, ['device type', 'device_type', 'type', 'device category', 'category', 'device', 'equipment type'], 'CPU')
            t_map = {'CPU': 'C', 'Display': 'D', 'Mouse': 'M', 'Keyboard': 'K', 'Printer': 'P', 'Tablet': 'T', 'UPS': 'U'}
            t_code = t_map.get(raw_t, 'C')
            now_str = timezone.localtime().strftime("%m%y")
            all_m_tags = set(DeviceAsset.objects.filter(asset_id__contains=f"/{now_str}/").values_list('asset_id', flat=True))
            max_n = 0
            for t_tag in all_m_tags:
                p_parts = t_tag.strip().split('/')
                if len(p_parts) >= 5:
                    try:
                        n_val = int(p_parts[4])
                        if n_val > max_n: max_n = n_val
                    except (ValueError, TypeError): pass
            next_n = max_n + 1
            while f"PSM/IT/{t_code}/{now_str}/{next_n:03d}" in all_m_tags:
                next_n += 1
            asset_id = f"PSM/IT/{t_code}/{now_str}/{next_n:03d}"


        device_type_raw = find_val(r, [
            'device type', 'device_type', 'type', 'device category', 'category', 'device', 'equipment type'
        ], '')
        device_type = normalize_device_type(device_type_raw, asset_id)

        if not serial_number:
            serial_number = f"SN-{random.randint(10000000, 99999999)}"

        building_name = find_val(r, ['building name', 'building', 'bldg', 'wing', 'facility'], 'PSM Hospital')
        floor_name = find_val(r, ['floor name', 'floor', 'level'], '2nd Floor')
        room_name = find_val(r, ['room / location', 'room name', 'room', 'location', 'lab', 'department / room', 'ward', 'dept'], 'ICU Complex')

        assigned_user_name = find_val(r, [
            'custodian / user', 'custodian', 'assigned user', 'assigned user name',
            'user', 'staff name', 'employee name', 'doctor / staff', 'doctor name', 'user name', 'custodian name'
        ], 'Unassigned')
        assigned_emp_id = find_val(r, ['emp id', 'employee id', 'staff id', 'assigned emp id', 'emp_id'])

        cpu_processor = find_val(r, ['compute hardware', 'cpu / processor', 'cpu processor', 'cpu', 'processor', 'hardware specs', 'processor / cpu'], 'Intel Core i7-13700 (16-Core)')
        storage_ram = find_val(r, ['ram & storage', 'ram and storage', 'storage / ram', 'storage ram', 'ram', 'storage', 'memory', 'disk', 'ram/storage'], '16GB RAM / 512GB NVMe SSD')
        monitor_spec = find_val(r, ['monitor specs', 'monitor spec', 'monitor', 'display', 'screen', 'monitor / display'], 'Dell 24" UltraSharp FHD')
        operating_system = find_val(r, ['operating system', 'operating_system', 'os & display', 'os', 'system os'], 'Windows 11 Pro')
        ip_address = find_val(r, ['network & ip', 'ip address', 'ip_address', 'ip', 'network ip', 'ip addr'], f"10.20.10.{random.randint(10, 240)}")
        mac_address = find_val(r, ['mac address', 'mac_address', 'mac', 'physical address'], f"B4-2E-99-{random.randint(10,99)}-{random.randint(10,99)}-FA")

        purchase_date = find_val(r, ['purchase date', 'purchase_date', 'procurement date', 'date of purchase'], datetime.date.today().strftime('%d-%b-%Y'))
        warranty_expiry_date = find_val(r, ['warranty expiry date', 'warranty expiry', 'warranty_expiry_date', 'warranty date', 'warranty'], (datetime.date.today() + datetime.timedelta(days=1095)).strftime('%d-%b-%Y'))

        status_raw = find_val(r, ['status & health', 'status', 'health', 'state'], 'Active')
        st_lower = status_raw.lower()
        if 'maint' in st_lower:
            status = 'In Maintenance'
        elif 'storage' in st_lower or 'spare' in st_lower:
            status = 'In Storage'
        elif 'decom' in st_lower:
            status = 'Decommissioned'
        else:
            status = 'Active'

        # Look up existing record by asset_id (or serial_number)
        dev = DeviceAsset.objects.filter(asset_id__iexact=asset_id).first()
        if not dev and serial_number:
            dev = DeviceAsset.objects.filter(serial_number__iexact=serial_number).first()

        if dev:
            dev.device_type = device_type
            dev.serial_number = serial_number
            dev.building_name = building_name
            dev.floor_name = floor_name
            dev.room_name = room_name
            dev.assigned_user_name = assigned_user_name
            dev.assigned_emp_id = assigned_emp_id
            dev.cpu_processor = cpu_processor
            dev.storage_ram = storage_ram
            dev.monitor_spec = monitor_spec
            dev.operating_system = operating_system
            dev.ip_address = ip_address
            dev.mac_address = mac_address
            dev.purchase_date = purchase_date
            dev.warranty_expiry_date = warranty_expiry_date
            dev.status = status
            dev.save()
            updated_count += 1
        else:
            dev_id = f"dev-{uuid.uuid4().hex[:8]}"
            DeviceAsset.objects.create(
                dev_id=dev_id,
                asset_id=asset_id,
                device_type=device_type,
                serial_number=serial_number,
                org_id='HOSP',
                org_name='PSM Hospital',
                building_name=building_name,
                floor_name=floor_name,
                room_name=room_name,
                assigned_user_id='',
                assigned_user_name=assigned_user_name,
                assigned_emp_id=assigned_emp_id,
                cpu_processor=cpu_processor,
                storage_ram=storage_ram,
                monitor_spec=monitor_spec,
                operating_system=operating_system,
                ip_address=ip_address,
                mac_address=mac_address,
                purchase_date=purchase_date,
                warranty_expiry_date=warranty_expiry_date,
                status=status
            )
            created_count += 1

        saved_count += 1

    return JsonResponse({
        'success': True,
        'count': saved_count,
        'created': created_count,
        'updated': updated_count,
        'message': f'Successfully imported {saved_count} device(s) ({created_count} registered, {updated_count} updated) into Inventory!'
    })