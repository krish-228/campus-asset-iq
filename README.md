# 🏥 CampusAssetIQ — Hospital Hardware Asset Intelligence & Incident Tracking System

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.1-092e20.svg?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Status](https://img.shields.io/badge/Campus%20Network-Active%20Wi--Fi-success.svg)](#)
[![Deployment](https://img.shields.io/badge/Client-PSM%20Hospital-red.svg)](#)

CampusAssetIQ is a mission-critical, enterprise-grade hardware lifecycle management, preventative maintenance (PMS), and incident intelligence web application engineered for **PSM Hospital & Academic Campus**. 

---

## 🌟 Key Highlights & Capabilities

### 1. 🏷️ Dynamic Asset Tagging & ISO QR Center
- Standardized floor-wise syntax: `PSM/IT/<FLOOR_NUM>/<DEVICE-TYPE>-<CODE>`
  - Basement (`B`), Ground Floor (`GF`), 1st–5th Floors (`1F`–`5F`)
  - Categories: Computer (`C`), Mouse (`M`), Keyboard (`K`), Printer (`P`)
- **Zero-Barcode Pure Stickers:** High-density vector QR matrix with printable A4 sticker sheet formatting (`@media print`), tailored for physical equipment labeling.

### 2. 🏢 Floor & Location Explorer
- Interactive multi-tenant location visualizer tracking 36+ clinical & academic hardware assets.
- Instant department, room, and floor-level custody mapping.

### 3. 🛠️ Equipment Breakdown & PMS Schedule Registers
- 24/7 incident lodging, MTBF/MTTR analytics, and downtime tracking.
- Preventative Maintenance Service (PMS) schedule with status tracking, Excel bulk export/import, and service history logs.

### 4. 👥 Dual-Portal Architecture
- **Admin Command Center (`/admin-login/`):** Deep obsidian cyber-command interface for IT Systems Engineers, Superusers, and Biomedical Heads.
- **Staff Self-Service Portal (`/portal/login/`):** Clean clinical interface for doctors, nurses, and technicians to lodge repair tickets and verify equipment.

---

## 🏗️ Technology Architecture

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | Python 3.12+ / Django 6.1 | MTV Architecture with RESTful JSON endpoints |
| **Primary Database** | **PostgreSQL 16** (`campus_asset_db`) | Relational schema with strict data integrity |
| **Frontend** | Semantic HTML5 + Tailwind CSS | Sub-millisecond server-rendered templates |
| **Vector Engine** | Pure ECMAScript (ES6+) | Real-time dynamic SVG QR Code synthesis |
| **Intranet Server** | Local Wi-Fi Socket Binding | Multi-device access via `0.0.0.0:8000` |

---

## 🚀 Quick Start & Local Wi-Fi Deployment

### 1. 1-Click Campus Launcher (Windows)
Double-click `start_campus_server.bat`. It automatically detects your machine's local Wi-Fi IP and binds Django to `0.0.0.0:8000`.

### 2. Manual Terminal Launch
```bash
# Activate virtual environment
.\venv\Scripts\activate

# Apply migrations to PostgreSQL
python manage.py migrate

# Run server on campus Wi-Fi network
python manage.py runserver 0.0.0.0:8000
```

Access links from any mobile phone or laptop connected to the same Wi-Fi:
- **Landing Gateway:** `http://<YOUR_LOCAL_IP>:8000/`
- **Admin Console:** `http://<YOUR_LOCAL_IP>:8000/admin-login/`
- **QR Sticker Center:** `http://<YOUR_LOCAL_IP>:8000/tag/`
- **Staff Portal:** `http://<YOUR_LOCAL_IP>:8000/portal/login/`

---

## 🛡️ License & Institutional Rights
Engineered exclusively for **PSM Hospital & Academic Campus** IT & Biomedical Engineering Department. All rights reserved.
