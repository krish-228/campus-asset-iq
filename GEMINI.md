# CampusAssetIQ — Project Memory & Architecture Guide (GEMINI.md)

This file defines the core architecture, technical stack, design conventions, and operational rules for **CampusAssetIQ**. All AI assistants and developers must adhere to these guidelines.

---

## 1. Project Overview
* **System Name:** CampusAssetIQ — Physical Campus Server
* **Domain:** Academic & Hospital Hardware Asset Tracking & Incident Intelligence System
* **Client / Institution:** Swaminarayan University & PSM Hospital
* **Root Directory:** `d:\tracker\`

---

## 2. Technology Stack & Environment

### Backend
* **Language:** Python 3.12+
* **Framework:** Django 6.1 (MTV Architecture)
* **Application Core:** `app` (models, views, forms, context processors)
* **Configuration:** `tracker` (`settings.py`, `urls.py`, `wsgi.py`)

### Database (STRICT RULE)
* **Engine:** **PostgreSQL 16** (`campus_asset_db`)
* **User:** `postgres`
* **Rule:** Always keep PostgreSQL as the primary database. **Never** revert to or default to SQLite for application operations. All models and migrations must preserve PostgreSQL relational integrity.

### Frontend
* **Markup:** Semantic HTML5 (`template/` directory)
  * **Admin Templates (`template/admin/`):** All admin pages including `index.html`, `inventory.html`, `user.html`, `location.html`, `audit.html`, `tag.html`, `pms_schedule.html`, `equipment_breakdown.html`, `admin_complaints.html`, `admin_login.html`, `admin_signup.html`.
  * **User / Staff Portal Templates (`template/user/`):** All staff self-service pages including `user_dashboard.html`, `user_login.html`, `user_signup.html`.
  * **Shared Master Template (`template/base.html`):** The common base layout extended by admin pages.
* **CSS Framework:** Tailwind CSS + Custom Vanilla CSS Design System (`static/css/style.css`)
* **JavaScript:** Pure Vanilla ECMAScript (ES6+) (`static/js/app.js`, `static/js/data.js`).
* **Framework Policy:** Do NOT introduce heavyweight SPA frameworks (React, Vue, Angular). Maintain server-rendered Django templates with lightweight vanilla JS for instantaneous sub-millisecond page loads.
* **Icons:** Lucide SVG Vector Icon System.

---

## 3. UI/UX Design System & Aesthetics

### Motion & Animations
* **Physics Curve:** Apple iOS fluid momentum easing: `cubic-bezier(0.16, 1, 0.3, 1)`.
* **Zero-Shift Icons:** All navigation icons must reside in fixed 44px flex containers (`.sidebar-icon-wrapper`) so icons never jump horizontally upon hover or expand.
* **Folding Labels:** Navigation labels must transition using `max-width`, `opacity`, and `transform: translateX()`. Never use `display: none` inside transition targets to prevent abrupt snapping.

### Branding & Top Navigation
* **PSM Brand Pill:** Compact `h-9` (36px height) pill container with `rounded-xl`, subtle border, and soft shadow.
* **Logo Proportions:** PSM Hospital logo scaled cleanly to `h-5 sm:h-5.5` (20–22px).
* **Badge Policy:** Do NOT add the "Healthcare Wing" badge to the brand pill. Keep it clean: Logo + "PSM Hospital" title only.
* **Sidebar Footer:** Keep the sidebar bottom footer clean (System & Admin Status only; no bulky "Staff Portal" action button).

### Hero Banners & Cards
* **Hero Banners:** Keep admin hero banners clean and minimalist (Title, category badge, description, action buttons). Do NOT insert logo emblems or bulky 4-KPI bars into page hero headers.
* **Device Cards:** In floor/location explorers, keep device cards direct and unboxed (clean section heading bar + independent device cards, without double-nested card wrappers).

### Inventory Table & Device Type Layout
* **Device Type Placement:** Must always sit immediately behind **Asset Tag / ID** as Column 2.
* **Unboxed Badge Rule:** Do NOT wrap Device Types inside filled colored background boxes (e.g. no outer yellow/amber background pill containers). Render with clean, unboxed vector Lucide icons (`w-5 h-5` / 20px) paired with prominent `text-base font-bold` typography.
* **Supported Hardware Types:** `CPU`, `Display`, `Keyboard`, `Mouse`, `Printer`.

### Admin Authentication Portal
* **Theme**: Deep obsidian & cyber-command palette (`#070b14` with radiant blue/cyan aurora glows), matching the mission-critical aesthetic of the Admin Console and completely distinct from the light clinical theme of the Staff Portal.
* **Routes**: `/admin-login/`, `/admin-signup/`, `/admin-logout/`.
* **Testing Convenience**: Always provide 1-click Quick Demo Admin login for frictionless development and colleague testing.
* **Security & Account Provisioning**: Admin signup automatically provisions administrator accounts with Django `is_staff=True` and creates associated UserProfile models without requiring extra passkeys.
* **Top Navigation Sync**: Display dynamic admin name, role, dynamic initials avatar, and one-click logout button in the top navbar.

---

## 4. Code Quality & Standards

### Single Identifier Architecture (Zero "System Name")
* **Strict Policy:** The redundant `System Name` (`system_name` / `systemName`, e.g. `ICU-BED-MON-01`) is permanently purged across the entire platform. **Never** reintroduce `system_name` into Django models, API responses, templates, forms, QR stickers, or CSV exports.
* **Single Source of Truth:** `asset_id` (e.g., `PSM/IT/2F/C-201`) is the sole hardware identifier for inventory tracking, transfers, complaints, breakdown records, and physical tags.

### Bulk Excel Import & Template Standards
* **24-Column Standard Format:** Template download (`downloadInventoryExcelTemplate()`), export functions (`exportToExcel()`, `exportToCSV()`), and backend import parser (`api_import_devices_excel`) strictly maintain the 24-column Hardware Specs & Workstation Profile format:
  1. `Asset Tag`, 2. `Device Type`, 3. `Brand / Make`, 4. `Hardware Model & Specs`, 5. `Serial Number`, 6. `Processor (CPU)`, 7. `RAM & Storage`, 8. `Monitor / Screen`, 9. `Operating System`, 10. `IP Address`, 11. `MAC Address`, 12. `AnyDesk Remote ID`, 13. `Campus Organization`, 14. `Building`, 15. `Floor`, 16. `Room / Location`, 17. `Assigned Custodian`, 18. `Employee ID`, 19. `Department`, 20. `Designation`, 21. `Custodian Contact`, 22. `Hardware Status`, 23. `Purchase Date`, 24. `Warranty Expiry`.
* **Sample Data Types:** The downloaded template and import parser actively support `CPU`, `Display`, `Keyboard`, `Mouse`, `Printer`, `UPS`, and `Tablet` with realistic hospital specifications, auto-provisioning `UserProfile` entries and preventing device collisions.

### JavaScript & Template Cleanliness
* **Safe Template Data Ingestion:** Never write Django template loops (e.g. `{% for item in items %}`) directly inside `<script>` executable statements to avoid code editor syntax errors.
* **JSON Payloads:** Always extract Django data into `<script type="application/json" id="data-payload">` elements, and parse safely via:
  ```javascript
  const data = JSON.parse(document.getElementById('data-payload').textContent);
  ```
* **HTML ID Uniqueness:** Never duplicate IDs in templates or copy-pasted modals. Use HTML5 `data-*` attributes on trigger buttons (e.g., `data-ticket-id`, `data-asset-id`) to bind modal interactions cleanly.

---

## 5. Multi-Tenant & Institutional Scoping

* **Hospital Wing (`HOSP`):**
  * Focus: Clinical & high-availability hardware (ICU, Trauma, OT, Radiology, Pathology).
  * Priority: Emergency downtime tracking, MTBF, 24/7 SLA.
* **Academic Campus (`CAMPUS`):**
  * Focus: Computer labs, lecture halls, faculty desks, administrative offices.
  * Priority: Semester maintenance schedules, batch procurement.

---

## 6. Local Wi-Fi Network & Execution

* **1-Click Launcher:** `start_campus_server.bat`
  * Automatically detects the host laptop's current local Wi-Fi IP address.
  * Runs Django bound to `0.0.0.0:8000` to allow colleagues on the same Wi-Fi to access the system.
* **Network Settings:**
  * `ALLOWED_HOSTS = ['*']`
  * `CSRF_TRUSTED_ORIGINS` dynamically auto-appends detected local Wi-Fi IPs via socket probing.

---

## 7. Data Preservation & Cloud Deployment Roadmap

* **Live Office Practice Data:**
  * All colleague testing and real equipment entries are saved directly to PostgreSQL `campus_asset_db` on the local machine.
* **Cloud Migration Protocol:**
  1. Export local database:
     `pg_dump -U postgres -d campus_asset_db > campus_database_backup.sql`
  2. Import directly into cloud PostgreSQL on deployment.
* **Target Production Stack:**
  * Linux (Ubuntu 24.04 LTS)
  * Gunicorn (WSGI Application Server)
  * Nginx (Reverse Proxy, SSL Termination via Let's Encrypt)
  * Systemd / Docker (24/7 Process Daemon)
