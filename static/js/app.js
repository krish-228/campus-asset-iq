// PSM Hospital Healthcare Device Tracker - Core Application Logic

let appState = {
    selectedOrg: "HOSP", // Default exclusively to PSM Hospital
    activeTab: "inventory",
    searchQuery: "",
    filters: {
        buildingId: "ALL",
        status: "ALL",
        os: "ALL"
    },
    ...INITIAL_SAMPLE_DATA
};

// Initialize State from LocalStorage and Query Parameters
function initAppState() {
    const urlParams = new URLSearchParams(window.location.search);
    let orgParam = urlParams.get('org');
    const searchParam = urlParams.get('search');

    // Always start with complete PSM Hospital INITIAL_SAMPLE_DATA structure
    appState = {
        selectedOrg: "HOSP",
        activeTab: "inventory",
        searchQuery: "",
        filters: { buildingId: "ALL", status: "ALL", os: "ALL" },
        ...INITIAL_SAMPLE_DATA
    };

    // Automatic Cache Version Purge for clean slate & workstation sets
    const CURRENT_CACHE_VERSION = "v9.1_kpi_fix";
    if (localStorage.getItem("CAMPUS_CACHE_VERSION") !== CURRENT_CACHE_VERSION) {
        localStorage.removeItem("CAMPUS_DEVICE_TRACKER_DATA");
        localStorage.removeItem("CAMPUS_SELECTED_ORG");
        localStorage.setItem("CAMPUS_CACHE_VERSION", CURRENT_CACHE_VERSION);
    }

    const saved = localStorage.getItem("CAMPUS_DEVICE_TRACKER_DATA");
    if (saved) {
        try {
            const parsed = JSON.parse(saved);
            // Detect and purge legacy University data, outdated floor structure (< 7 floors), or past legacy tags
            const hasLegacyUni = (parsed.buildings && parsed.buildings.some(b => b.id === 'bldg-cs' || b.orgId === 'UNI')) ||
                (parsed.devices && parsed.devices.some(d => d.orgId === 'UNI'));
            const needsFloorRefresh = !parsed.floors || parsed.floors.length < 7 ||
                !parsed.floors.some(f => f.id === 'fl-basement') ||
                !parsed.floors.some(f => f.id === 'fl-5');
            // Migrate any legacy tags with /M/, /C/, /K/, /P/, etc. to PSM/IT/MMYY/XXX format
            if (Array.isArray(parsed.devices)) {
                parsed.devices.forEach(d => {
                    if (d.assetId) {
                        d.assetId = d.assetId.replace(/^PSM\/IT\/[A-Z]\/(\d{4}\/\d+)$/i, 'PSM/IT/$1');
                    }
                });
            }

            if (hasLegacyUni || needsFloorRefresh) {
                // Clear out old cached data completely and force fresh 7-floor PSM Hospital data
                localStorage.removeItem("CAMPUS_DEVICE_TRACKER_DATA");
                localStorage.setItem("CAMPUS_SELECTED_ORG", "HOSP");
                saveAppState();
            } else {
                if (parsed.users) {
                    parsed.users.forEach(u => delete u.avatar);
                }
                if (Array.isArray(parsed.organizations) && parsed.organizations.length > 0) {
                    appState.organizations = parsed.organizations;
                }
                if (Array.isArray(parsed.buildings) && parsed.buildings.length > 0) {
                    appState.buildings = parsed.buildings;
                }
                if (Array.isArray(parsed.floors) && parsed.floors.length > 0) {
                    appState.floors = parsed.floors;
                }
                if (Array.isArray(parsed.rooms) && parsed.rooms.length > 0) {
                    appState.rooms = parsed.rooms.map(r => {
                        if (!r.roomNumber && typeof INITIAL_SAMPLE_DATA !== 'undefined' && INITIAL_SAMPLE_DATA.rooms) {
                            const sampleRoom = INITIAL_SAMPLE_DATA.rooms.find(sr => sr.id === r.id);
                            if (sampleRoom && sampleRoom.roomNumber) {
                                return { ...r, roomNumber: sampleRoom.roomNumber };
                            }
                        }
                        return r;
                    });
                }
                if (Array.isArray(parsed.users) && parsed.users.length > 0) {
                    appState.users = parsed.users;
                }
                if (Array.isArray(parsed.devices) && parsed.devices.length > 0) {
                    parsed.devices.forEach(d => {
                        if (typeof isPlaceholderDetail === 'function') {
                            if (isPlaceholderDetail(d.storageRam)) d.storageRam = '';
                            if (isPlaceholderDetail(d.operatingSystem)) d.operatingSystem = '';
                        }
                    });
                    appState.devices = parsed.devices;
                }
                if (Array.isArray(parsed.locationHistories)) {
                    appState.locationHistories = parsed.locationHistories;
                }
                if (Array.isArray(parsed.assignmentHistories)) {
                    appState.assignmentHistories = parsed.assignmentHistories;
                }
                if (Array.isArray(parsed.loginSessions)) {
                    appState.loginSessions = parsed.loginSessions;
                }
                saveAppState();
            }
        } catch (e) {
            console.error("Failed to parse saved state, using default sample data", e);
        }
    } else {
        saveAppState();
    }

    // DIRECT POSTGRESQL SERVER-SIDE INGESTION (Instant sub-millisecond render)
    const serverDevicesEl = document.getElementById('server-devices-payload');
    if (serverDevicesEl && serverDevicesEl.textContent.trim()) {
        try {
            const serverDevices = JSON.parse(serverDevicesEl.textContent);
            if (Array.isArray(serverDevices)) {
                serverDevices.forEach(dbDev => {
                    if (typeof isPlaceholderDetail === 'function') {
                        if (isPlaceholderDetail(dbDev.storageRam)) dbDev.storageRam = '';
                        if (isPlaceholderDetail(dbDev.operatingSystem)) dbDev.operatingSystem = '';
                    }
                    if (!dbDev.roomId && dbDev.roomName && appState.rooms) {
                        const matchRoom = appState.rooms.find(r =>
                            r.name.toLowerCase().includes(dbDev.roomName.toLowerCase()) ||
                            dbDev.roomName.toLowerCase().includes(r.name.toLowerCase())
                        );
                        if (matchRoom) {
                            dbDev.roomId = matchRoom.id;
                        } else if (appState.rooms.length > 0) {
                            dbDev.roomId = appState.rooms[0].id;
                        }
                    }
                });
                appState.devices = serverDevices;
                saveAppState();
            }
        } catch (e) {
            console.warn("Server devices payload parsing fallback:", e);
        }
    }

    const serverLogsEl = document.getElementById('server-audit-logs-payload');
    if (serverLogsEl && serverLogsEl.textContent.trim()) {
        try {
            const serverLogs = JSON.parse(serverLogsEl.textContent);
            if (Array.isArray(serverLogs) && serverLogs.length > 0) {
                appState.assignmentHistories = serverLogs.map(log => ({
                    id: `db-${log.id}`,
                    deviceId: log.deviceAssetId,
                    userId: null,
                    fromUserName: log.fromUserName,
                    toUserName: log.toUserName,
                    fromDate: log.handoverDate,
                    toDate: "-",
                    location: "Campus Lab",
                    assignedBy: log.assignedBy,
                    remarks: log.remarks
                }));
                saveAppState();
            }
        } catch (e) {
            console.warn("Server audit logs payload parsing fallback:", e);
        }
    }

    // Always lock active organization to HOSP
    appState.selectedOrg = "HOSP";
    localStorage.setItem("CAMPUS_SELECTED_ORG", "HOSP");

    if (searchParam) {
        appState.searchQuery = searchParam;
    }
}

function saveAppState() {
    localStorage.setItem("CAMPUS_SELECTED_ORG", "HOSP");
    localStorage.setItem("CAMPUS_DEVICE_TRACKER_DATA", JSON.stringify({
        selectedOrg: appState.selectedOrg,
        organizations: appState.organizations,
        buildings: appState.buildings,
        floors: appState.floors,
        rooms: appState.rooms,
        users: appState.users,
        devices: appState.devices,
        locationHistories: appState.locationHistories,
        assignmentHistories: appState.assignmentHistories,
        loginSessions: appState.loginSessions
    }));
}

function resetToSampleData() {
    if (confirm("Reset database to realistic campus sample dataset?")) {
        localStorage.removeItem("CAMPUS_DEVICE_TRACKER_DATA");
        localStorage.removeItem("CAMPUS_SELECTED_ORG");
        appState = {
            selectedOrg: appState.selectedOrg || "ALL",
            activeTab: "inventory",
            searchQuery: "",
            filters: { buildingId: "ALL", status: "ALL", os: "ALL" },
            ...INITIAL_SAMPLE_DATA
        };
        saveAppState();
        renderAll();
        showToast("Database successfully restored to default sample records!", "success");
    }
}

// ============================================================================
// Multi-Page Navigation & Organization Switcher
// ============================================================================

function selectOrganization(orgCode) {
    if (orgCode === "UNI") {
        if (typeof openUniversityComingSoonModal === "function") {
            openUniversityComingSoonModal();
        } else {
            alert("Coming Soon: Separate University Portal under construction");
        }
        return;
    }
    appState.selectedOrg = "HOSP";
    saveAppState();
    updateEntityUI();

    const isLanding = window.location.pathname === "/" ||
        window.location.pathname.endsWith("index.html") ||
        window.location.pathname === "";

    if (isLanding) {
        if (window.location.protocol === "file:") {
            window.location.href = `inventory.html?org=HOSP`;
        } else {
            window.location.href = `/inventory/?org=HOSP`;
        }
        return;
    }

    // If on an inner page, update the current page URL with HOSP
    if (window.location.protocol === "file:") {
        const file = window.location.pathname.split("/").pop() || "inventory.html";
        window.location.href = `${file}?org=HOSP`;
    } else {
        window.location.href = `${window.location.pathname}?org=HOSP`;
    }
}

function getEntityName(code) {
    return "PSM Hospital";
}

function updateEntityUI() {
    const label = document.getElementById("active-entity-label");
    const dot = document.getElementById("active-entity-dot");
    const iconContainer = document.getElementById("active-entity-icon-container");
    if (!label) return;

    const banner = document.getElementById("org-inventory-banner");
    const bannerGlow = document.getElementById("org-banner-glow");
    const bannerIcon = document.getElementById("org-banner-icon");
    const bannerTitle = document.getElementById("org-banner-title");
    const bannerTag = document.getElementById("org-banner-tag");
    const bannerDesc = document.getElementById("org-banner-desc");
    const registerBtn = document.getElementById("org-banner-register-btn");

    label.textContent = "PSM Hospital";
    if (dot) dot.className = "hidden";
    if (iconContainer) {
        iconContainer.innerHTML = `<img src="/static/images/psm_hospital_logo.png" alt="PSM Hospital" class="h-5 sm:h-5.5 w-auto object-contain">`;
    }

    if (banner) {
        banner.className = "rounded-2xl border border-indigo-800/40 bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 text-white p-6 relative overflow-hidden shadow-md transition-all duration-300";
        if (bannerIcon) {
            bannerIcon.remove();
        }
        if (bannerTitle) bannerTitle.innerHTML = `PSM Hospital &bull; Medical Hardware & Device Inventory`;
        if (bannerTag) {
            bannerTag.className = "inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-500/20 text-blue-200 text-[11px] font-semibold border border-blue-400/30";
            bannerTag.textContent = "Healthcare Infrastructure";
        }
        if (bannerDesc) bannerDesc.textContent = "Monitoring clinical ICU monitors, emergency triage terminals, radiology diagnostic workstations, and hospital medical devices.";
        if (registerBtn) registerBtn.className = "px-4 py-2.5 bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-md transition-all flex items-center gap-2 active:scale-95";
    }

    const dropdown = document.getElementById("entity-dropdown");
    if (dropdown) dropdown.classList.add("hidden");
    if (window.lucide) lucide.createIcons();
}

function toggleEntityDropdown() {
    const dropdown = document.getElementById("entity-dropdown");
    if (dropdown) dropdown.classList.toggle("hidden");
}

// ============================================================================
// Renderers & Inventory Filters
// ============================================================================

function getFilteredDevices() {
    return appState.devices.filter(dev => {
        // Organization filter
        if (appState.selectedOrg !== "ALL" && dev.orgId !== appState.selectedOrg) return false;

        // Building filter
        if (appState.filters.buildingId !== "ALL") {
            const room = appState.rooms.find(r => r.id === dev.roomId);
            const floor = room ? appState.floors.find(f => f.id === room.floorId) : null;
            if (!floor || floor.buildingId !== appState.filters.buildingId) return false;
        }

        // Status filter
        if (appState.filters.status !== "ALL" && dev.status !== appState.filters.status) return false;

        // OS filter
        if (appState.filters.os !== "ALL" && !dev.operatingSystem.toLowerCase().includes(appState.filters.os.toLowerCase())) return false;

        // Search Query
        if (appState.searchQuery.trim() !== "") {
            const q = appState.searchQuery.toLowerCase().trim();
            const user = (appState.users || []).find(u => (u.id && u.id === dev.assignedUserId) || (u.empId && (u.empId === dev.empId || u.empId === dev.assignedEmpId)));
            const userName = (user ? (user.fullName || user.name || "") : (dev.assignedUserName || dev.assigned_user_name || "")).toLowerCase();
            const empId = (user ? (user.empId || "") : (dev.empId || dev.assignedEmpId || "")).toLowerCase();
            const desig = (dev.designation || dev.assignedDesignation || dev.assigned_designation || (user ? user.designation : "")).toLowerCase();
            const room = appState.rooms.find(r => r.id === dev.roomId);
            const roomName = room ? (room.name || "").toLowerCase() : "";

            const matches =
                (dev.assetId || "").toLowerCase().includes(q) ||
                (dev.deviceType || "").toLowerCase().includes(q) ||
                (dev.serialNumber || "").toLowerCase().includes(q) ||
                (dev.ipAddress || "").toLowerCase().includes(q) ||
                (dev.cpuProcessor || "").toLowerCase().includes(q) ||
                (dev.storageRam || "").toLowerCase().includes(q) ||
                (dev.monitorSpec || "").toLowerCase().includes(q) ||
                (dev.keyboardSpec || "").toLowerCase().includes(q) ||
                (dev.mouseSpec || "").toLowerCase().includes(q) ||
                (dev.tabletSpec || "").toLowerCase().includes(q) ||
                (dev.printerSpec || "").toLowerCase().includes(q) ||
                (dev.upsSpec || "").toLowerCase().includes(q) ||
                (dev.operatingSystem || "").toLowerCase().includes(q) ||
                userName.includes(q) ||
                empId.includes(q) ||
                desig.includes(q) ||
                roomName.includes(q);

            if (!matches) return false;
        }

        return true;
    });
}

function getDeviceTypeBadge(dev) {
    let rawType = (dev.deviceType || '').trim();
    if (!rawType && dev.assetId) {
        const aid = dev.assetId.toUpperCase();
        if (aid.includes('/C/') || aid.includes('/C-') || aid.includes('/C.')) rawType = 'CPU';
        else if (aid.includes('/D/') || aid.includes('/D-') || aid.includes('/D.')) rawType = 'Display';
        else if (aid.includes('/K/') || aid.includes('/K-') || aid.includes('/K.')) rawType = 'Keyboard';
        else if (aid.includes('/M/') || aid.includes('/M-') || aid.includes('/M.')) rawType = 'Mouse';
        else if (aid.includes('/P/') || aid.includes('/P-') || aid.includes('/P.')) rawType = 'Printer';
        else if (aid.includes('/T/') || aid.includes('/T-') || aid.includes('/T.')) rawType = 'Tablet';
        else if (aid.includes('/U/') || aid.includes('/U-') || aid.includes('/U.')) rawType = 'UPS';
    }
    const t = (rawType || 'CPU').toUpperCase();
    let typeHtml = '';
    if (t.includes('WORKSTATION') || t.includes(',')) {
        typeHtml = `<span class="inline-flex items-center gap-2 text-base font-bold text-sky-800" title="${rawType}">
            <i data-lucide="layout-grid" class="w-5 h-5 text-sky-600 shrink-0"></i>
            <span>${rawType}</span>
        </span>`;
    } else if (t === 'C' || t === 'CPU' || t === 'DESKTOP' || t === 'PC' || t === 'COMPUTER') {
        typeHtml = `<span class="inline-flex items-center gap-2 text-base font-bold text-sky-800">
            <i data-lucide="cpu" class="w-5 h-5 text-sky-600 shrink-0"></i>
            <span>CPU</span>
        </span>`;
    } else if (t === 'D' || t === 'DISPLAY' || t === 'MONITOR' || t === 'SCREEN') {
        typeHtml = `<span class="inline-flex items-center gap-2 text-base font-bold text-indigo-800">
            <i data-lucide="monitor" class="w-5 h-5 text-indigo-600 shrink-0"></i>
            <span>Display</span>
        </span>`;
    } else if (t === 'K' || t === 'KB' || t === 'KEYBOARD') {
        typeHtml = `<span class="inline-flex items-center gap-2 text-base font-bold text-amber-800">
            <i data-lucide="keyboard" class="w-5 h-5 text-amber-600 shrink-0"></i>
            <span>Keyboard</span>
        </span>`;
    } else if (t === 'M' || t === 'MOUSE') {
        typeHtml = `<span class="inline-flex items-center gap-2 text-base font-bold text-purple-800">
            <i data-lucide="mouse" class="w-5 h-5 text-purple-600 shrink-0"></i>
            <span>Mouse</span>
        </span>`;
    } else if (t === 'P' || t === 'PRT' || t === 'PRINTER' || t.includes('PRINT')) {
        typeHtml = `<span class="inline-flex items-center gap-2 text-base font-bold text-emerald-800">
            <i data-lucide="printer" class="w-5 h-5 text-emerald-600 shrink-0"></i>
            <span>Printer</span>
        </span>`;
    } else if (t === 'T' || t === 'TABLET' || t === 'TAB' || t === 'IPAD') {
        typeHtml = `<span class="inline-flex items-center gap-2 text-base font-bold text-teal-800">
            <i data-lucide="tablet" class="w-5 h-5 text-teal-600 shrink-0"></i>
            <span>Tablet</span>
        </span>`;
    } else if (t === 'U' || t === 'UPS' || t === 'POWER' || t === 'INVERTER') {
        typeHtml = `<span class="inline-flex items-center gap-2 text-base font-bold text-orange-800">
            <i data-lucide="zap" class="w-5 h-5 text-orange-600 shrink-0"></i>
            <span>UPS</span>
        </span>`;
    } else if (t.includes('BIOMETRIC') || t.includes('FINGERPRINT')) {
        typeHtml = `<span class="inline-flex items-center gap-2 text-base font-bold text-teal-800">
            <i data-lucide="fingerprint" class="w-5 h-5 text-teal-600 shrink-0"></i>
            <span>${rawType || 'Biometric Machine'}</span>
        </span>`;
    } else if (t.includes('EYE') || t.includes('IRIS') || t.includes('RETINA')) {
        typeHtml = `<span class="inline-flex items-center gap-2 text-base font-bold text-cyan-800">
            <i data-lucide="eye" class="w-5 h-5 text-cyan-600 shrink-0"></i>
            <span>${rawType || 'Eye Scanner'}</span>
        </span>`;
    } else if (t.includes('BARCODE PRINTER') || t.includes('LABEL PRINTER')) {
        typeHtml = `<span class="inline-flex items-center gap-2 text-base font-bold text-amber-800">
            <i data-lucide="printer" class="w-5 h-5 text-amber-600 shrink-0"></i>
            <span>${rawType || 'Barcode Printer'}</span>
        </span>`;
    } else if (t.includes('SCANNER') || t.includes('BARCODE')) {
        typeHtml = `<span class="inline-flex items-center gap-2 text-base font-bold text-rose-800">
            <i data-lucide="scan-barcode" class="w-5 h-5 text-rose-600 shrink-0"></i>
            <span>${rawType || 'Scanner'}</span>
        </span>`;
    } else if (t.includes('PROJECTOR')) {
        typeHtml = `<span class="inline-flex items-center gap-2 text-base font-bold text-cyan-800">
            <i data-lucide="projector" class="w-5 h-5 text-cyan-600 shrink-0"></i>
            <span>Projector</span>
        </span>`;
    } else if (t.includes('WEBCAM') || t.includes('CAMERA')) {
        typeHtml = `<span class="inline-flex items-center gap-2 text-base font-bold text-violet-800">
            <i data-lucide="video" class="w-5 h-5 text-violet-600 shrink-0"></i>
            <span>Webcam</span>
        </span>`;
    } else if (t.includes('SWITCH') || t.includes('ROUTER') || t.includes('NETWORK')) {
        typeHtml = `<span class="inline-flex items-center gap-2 text-base font-bold text-blue-800">
            <i data-lucide="network" class="w-5 h-5 text-blue-600 shrink-0"></i>
            <span>Network Switch</span>
        </span>`;
    } else if (t.includes('STORAGE') || t.includes('DRIVE') || t.includes('NAS')) {
        typeHtml = `<span class="inline-flex items-center gap-2 text-base font-bold text-slate-800">
            <i data-lucide="hard-drive" class="w-5 h-5 text-slate-600 shrink-0"></i>
            <span>External Storage</span>
        </span>`;
    } else if (t === 'OTHER' || t.includes('OTHER') || t.includes('ACCESSORY')) {
        typeHtml = `<span class="inline-flex items-center gap-2 text-base font-bold text-slate-800">
            <i data-lucide="package-plus" class="w-5 h-5 text-slate-600 shrink-0"></i>
            <span>${rawType || 'Other Device'}</span>
        </span>`;
    } else {
        const label = rawType || 'Device';
        typeHtml = `<span class="inline-flex items-center gap-2 text-base font-bold text-slate-800">
            <i data-lucide="hard-drive" class="w-5 h-5 text-slate-500 shrink-0"></i>
            <span>${label}</span>
        </span>`;
    }

    return typeHtml;
}

// ============================================================================
// Inventory View Mode (Workstation Sets / Grouped vs All Devices / Flat)
// ============================================================================
let inventoryViewMode = localStorage.getItem('campus_inventory_view_mode') || 'grouped';
const collapsedWorkstations = new Set();

function setInventoryViewMode(mode) {
    inventoryViewMode = mode;
    localStorage.setItem('campus_inventory_view_mode', mode);

    const btnGrouped = document.getElementById('btn-view-grouped');
    const btnFlat = document.getElementById('btn-view-flat');

    if (btnGrouped && btnFlat) {
        if (mode === 'grouped') {
            btnGrouped.className = "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-extrabold transition-all bg-white text-indigo-700 shadow-xs cursor-pointer";
            btnFlat.className = "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all text-slate-600 hover:text-slate-900 cursor-pointer";
        } else {
            btnFlat.className = "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-extrabold transition-all bg-white text-indigo-700 shadow-xs cursor-pointer";
            btnGrouped.className = "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all text-slate-600 hover:text-slate-900 cursor-pointer";
        }
    }

    renderInventoryTable();
}

function toggleWorkstationCollapse(groupKey) {
    if (collapsedWorkstations.has(groupKey)) {
        collapsedWorkstations.delete(groupKey);
    } else {
        collapsedWorkstations.add(groupKey);
    }
    renderInventoryTable();
}

// Device sorting hierarchy inside a workstation bundle:
// 1. CPU / Workstation -> 2. Display / Monitor -> 3. Keyboard -> 4. Mouse -> 5. Printer -> 6. UPS -> 7. Others
const WORKSTATION_DEVICE_PRIORITY = {
    'CPU': 1, 'WORKSTATION': 1, 'DESKTOP': 1, 'COMPUTER': 1,
    'DISPLAY': 2, 'MONITOR': 2, 'SCREEN': 2,
    'KEYBOARD': 3, 'KB': 3,
    'MOUSE': 4,
    'PRINTER': 5, 'PRT': 5,
    'UPS': 6, 'INVERTER': 6, 'POWER': 6,
    'TABLET': 7, 'TAB': 7, 'IPAD': 7,
    'SCANNER': 8, 'BARCODE': 8,
    'PROJECTOR': 9,
    'WEBCAM': 10, 'CAMERA': 10,
    'OTHER': 11
};

function getWorkstationDevicePriority(dev) {
    const raw = (dev.deviceType || dev.device_type || '').toUpperCase();
    for (const [key, prio] of Object.entries(WORKSTATION_DEVICE_PRIORITY)) {
        if (raw.includes(key)) return prio;
    }
    return 99;
}

function getWorkstationRoleBadge(dev, displayName) {
    const raw = (dev.deviceType || dev.device_type || '').toUpperCase();
    if (raw.includes('CPU') || raw.includes('DESKTOP') || raw.includes('WORKSTATION')) {
        return `
            <div class="space-y-0.5">
                <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-black bg-indigo-100 text-indigo-800 border border-indigo-200 shadow-3xs whitespace-nowrap">
                    <i data-lucide="cpu" class="w-3.5 h-3.5 text-indigo-600"></i> Primary Compute
                </span>
                <div class="text-[11px] text-slate-500 font-medium truncate flex items-center gap-1">
                    <i data-lucide="user" class="w-3 h-3 text-slate-400"></i> ${displayName}
                </div>
            </div>
        `;
    }
    if (raw.includes('DISPLAY') || raw.includes('MONITOR') || raw.includes('SCREEN')) {
        return `
            <div class="space-y-0.5">
                <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200 shadow-3xs whitespace-nowrap">
                    <i data-lucide="tv" class="w-3.5 h-3.5 text-blue-600"></i> Desk Monitor
                </span>
                <div class="text-[11px] text-slate-500 font-medium truncate flex items-center gap-1">
                    <i data-lucide="user" class="w-3 h-3 text-slate-400"></i> ${displayName}
                </div>
            </div>
        `;
    }
    if (raw.includes('KEYBOARD') || raw.includes('KB')) {
        return `
            <div class="space-y-0.5">
                <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200 shadow-3xs whitespace-nowrap">
                    <i data-lucide="keyboard" class="w-3.5 h-3.5 text-amber-600"></i> Input Keyboard
                </span>
                <div class="text-[11px] text-slate-500 font-medium truncate flex items-center gap-1">
                    <i data-lucide="user" class="w-3 h-3 text-slate-400"></i> ${displayName}
                </div>
            </div>
        `;
    }
    if (raw.includes('MOUSE')) {
        return `
            <div class="space-y-0.5">
                <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-bold bg-purple-50 text-purple-700 border border-purple-200 shadow-3xs whitespace-nowrap">
                    <i data-lucide="mouse" class="w-3.5 h-3.5 text-purple-600"></i> Pointing Device
                </span>
                <div class="text-[11px] text-slate-500 font-medium truncate flex items-center gap-1">
                    <i data-lucide="user" class="w-3 h-3 text-slate-400"></i> ${displayName}
                </div>
            </div>
        `;
    }
    if (raw.includes('PRINTER') || raw.includes('PRT')) {
        return `
            <div class="space-y-0.5">
                <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 shadow-3xs whitespace-nowrap">
                    <i data-lucide="printer" class="w-3.5 h-3.5 text-emerald-600"></i> Desk Printer
                </span>
                <div class="text-[11px] text-slate-500 font-medium truncate flex items-center gap-1">
                    <i data-lucide="user" class="w-3 h-3 text-slate-400"></i> ${displayName}
                </div>
            </div>
        `;
    }
    if (raw.includes('UPS') || raw.includes('POWER') || raw.includes('INVERTER')) {
        return `
            <div class="space-y-0.5">
                <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-bold bg-orange-50 text-orange-800 border border-orange-200 shadow-3xs whitespace-nowrap">
                    <i data-lucide="zap" class="w-3.5 h-3.5 text-orange-600"></i> Power Backup
                </span>
                <div class="text-[11px] text-slate-500 font-medium truncate flex items-center gap-1">
                    <i data-lucide="user" class="w-3 h-3 text-slate-400"></i> ${displayName}
                </div>
            </div>
        `;
    }
    if (raw.includes('TABLET') || raw.includes('TAB') || raw.includes('IPAD')) {
        return `
            <div class="space-y-0.5">
                <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-bold bg-teal-50 text-teal-800 border border-teal-200 shadow-3xs whitespace-nowrap">
                    <i data-lucide="tablet" class="w-3.5 h-3.5 text-teal-600"></i> Mobile Terminal
                </span>
                <div class="text-[11px] text-slate-500 font-medium truncate flex items-center gap-1">
                    <i data-lucide="user" class="w-3 h-3 text-slate-400"></i> ${displayName}
                </div>
            </div>
        `;
    }
    if (raw.includes('BIOMETRIC') || raw.includes('FINGERPRINT')) {
        return `
            <div class="space-y-0.5">
                <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-bold bg-teal-50 text-teal-800 border border-teal-200 shadow-3xs whitespace-nowrap">
                    <i data-lucide="fingerprint" class="w-3.5 h-3.5 text-teal-600"></i> Biometric Machine
                </span>
                <div class="text-[11px] text-slate-500 font-medium truncate flex items-center gap-1">
                    <i data-lucide="user" class="w-3 h-3 text-slate-400"></i> ${displayName}
                </div>
            </div>
        `;
    }
    if (raw.includes('EYE') || raw.includes('IRIS') || raw.includes('RETINA')) {
        return `
            <div class="space-y-0.5">
                <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-bold bg-cyan-50 text-cyan-800 border border-cyan-200 shadow-3xs whitespace-nowrap">
                    <i data-lucide="eye" class="w-3.5 h-3.5 text-cyan-600"></i> Eye Scanner
                </span>
                <div class="text-[11px] text-slate-500 font-medium truncate flex items-center gap-1">
                    <i data-lucide="user" class="w-3 h-3 text-slate-400"></i> ${displayName}
                </div>
            </div>
        `;
    }
    if (raw.includes('BARCODE PRINTER') || raw.includes('LABEL PRINTER')) {
        return `
            <div class="space-y-0.5">
                <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200 shadow-3xs whitespace-nowrap">
                    <i data-lucide="printer" class="w-3.5 h-3.5 text-amber-600"></i> Barcode Printer
                </span>
                <div class="text-[11px] text-slate-500 font-medium truncate flex items-center gap-1">
                    <i data-lucide="user" class="w-3 h-3 text-slate-400"></i> ${displayName}
                </div>
            </div>
        `;
    }
    if (raw.includes('SCANNER') || raw.includes('BARCODE')) {
        return `
            <div class="space-y-0.5">
                <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-bold bg-rose-50 text-rose-800 border border-rose-200 shadow-3xs whitespace-nowrap">
                    <i data-lucide="scan-barcode" class="w-3.5 h-3.5 text-rose-600"></i> Scanner
                </span>
                <div class="text-[11px] text-slate-500 font-medium truncate flex items-center gap-1">
                    <i data-lucide="user" class="w-3 h-3 text-slate-400"></i> ${displayName}
                </div>
            </div>
        `;
    }
    if (raw.includes('PROJECTOR')) {
        return `
            <div class="space-y-0.5">
                <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-bold bg-cyan-50 text-cyan-800 border border-cyan-200 shadow-3xs whitespace-nowrap">
                    <i data-lucide="projector" class="w-3.5 h-3.5 text-cyan-600"></i> Projector
                </span>
                <div class="text-[11px] text-slate-500 font-medium truncate flex items-center gap-1">
                    <i data-lucide="user" class="w-3 h-3 text-slate-400"></i> ${displayName}
                </div>
            </div>
        `;
    }
    if (raw.includes('WEBCAM') || raw.includes('CAMERA')) {
        return `
            <div class="space-y-0.5">
                <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-bold bg-violet-50 text-violet-800 border border-violet-200 shadow-3xs whitespace-nowrap">
                    <i data-lucide="video" class="w-3.5 h-3.5 text-violet-600"></i> Webcam
                </span>
                <div class="text-[11px] text-slate-500 font-medium truncate flex items-center gap-1">
                    <i data-lucide="user" class="w-3 h-3 text-slate-400"></i> ${displayName}
                </div>
            </div>
        `;
    }
    if (raw.includes('OTHER')) {
        return `
            <div class="space-y-0.5">
                <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-bold bg-slate-100 text-slate-700 border border-slate-200 shadow-3xs whitespace-nowrap">
                    <i data-lucide="package-plus" class="w-3.5 h-3.5 text-slate-500"></i> Accessory
                </span>
                <div class="text-[11px] text-slate-500 font-medium truncate flex items-center gap-1">
                    <i data-lucide="user" class="w-3 h-3 text-slate-400"></i> ${displayName}
                </div>
            </div>
        `;
    }
    return `
        <div class="space-y-0.5">
            <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-bold bg-slate-100 text-slate-700 border border-slate-200 shadow-3xs whitespace-nowrap">
                <i data-lucide="hard-drive" class="w-3.5 h-3.5 text-slate-500"></i> Desk Peripheral
            </span>
            <div class="text-[11px] text-slate-500 font-medium truncate flex items-center gap-1">
                <i data-lucide="user" class="w-3 h-3 text-slate-400"></i> ${displayName}
            </div>
        </div>
    `;
}

function isPlaceholderDetail(str) {
    if (!str) return true;
    const clean = String(str).trim();
    if (!clean) return true;
    const up = clean.toUpperCase();

    // Symbols / trivial placeholders
    if (clean === '—' || clean === '-' || clean === '--' || clean === 'N/A' || up === 'NONE' || up === 'UNKNOWN' || up === 'NULL' || up === 'UNASSIGNED') {
        return true;
    }

    // Auto-generated dummy placeholders & fake marketing blurbs
    const dummyPhrases = [
        'STANDARD OEM',
        'HARDWARE DISPLAY MONITOR',
        'CONNECTED DISPLAY MONITOR',
        'HARDWARE DISPLAY',
        'HARDWARE PERIPHERAL',
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
        'IPS MEDICAL PANEL',
        'DIRECT VIDEO STREAM',
        'SPILL-RESISTANT MEMBRANE',
        'USB WIRED INTERFACE',
        'OPTICAL PRECISION SENSOR',
        'USB CLEANABLE',
        'HEALTHCARE DOCUMENT GRADE',
        'CONTINUOUS POWER BACKUP',
        'TOUCHSCREEN CLINICAL TERMINAL',
        'MOBILE WIRELESS UNIT',
        'OPTICAL 1D/2D READER',
        'INSTANT IDENTIFICATION',
        'STANDARD WORKSTATION CORE'
    ];

    for (const phrase of dummyPhrases) {
        if (up.includes(phrase)) {
            return true;
        }
    }

    return false;
}

function getDeviceSpecificationsHtml(dev) {
    const rawType = (dev.deviceType || dev.device_type || '').toUpperCase();

    // 1. Model & specs resolution
    let model = '';
    if (rawType.includes('CPU') || rawType.includes('WORKSTATION') || rawType.includes('DESKTOP') || rawType.includes('PC') || rawType.includes('COMPUTER') || rawType.includes('LAPTOP')) {
        model = (dev.cpuProcessor || dev.modelSpecs || '').trim();
    } else if (rawType.includes('DISPLAY') || rawType.includes('MONITOR') || rawType.includes('SCREEN') || rawType === 'D') {
        model = (dev.monitorSpec || dev.cpuProcessor || dev.modelSpecs || '').trim();
    } else if (rawType.includes('KEYBOARD') || rawType.includes('KB') || rawType === 'K') {
        model = (dev.keyboardSpec || dev.cpuProcessor || dev.modelSpecs || '').trim();
    } else if (rawType.includes('MOUSE') || rawType === 'M') {
        model = (dev.mouseSpec || dev.cpuProcessor || dev.modelSpecs || '').trim();
    } else if (rawType.includes('PRINTER') || rawType.includes('PRT') || rawType === 'P') {
        model = (dev.printerSpec || dev.cpuProcessor || dev.modelSpecs || '').trim();
    } else if (rawType.includes('UPS') || rawType.includes('POWER') || rawType.includes('INVERTER') || rawType === 'U') {
        model = (dev.upsSpec || dev.cpuProcessor || dev.modelSpecs || '').trim();
    } else if (rawType.includes('TABLET') || rawType.includes('TAB') || rawType.includes('IPAD') || rawType === 'T') {
        model = (dev.tabletSpec || dev.cpuProcessor || dev.modelSpecs || '').trim();
    } else {
        model = (dev.cpuProcessor || dev.modelSpecs || '').trim();
    }

    // 2. Brand resolution (Line 1)
    let brand = '';
    const mUp = model.toUpperCase();
    const knownBrands = [
        { key: 'DELL', name: 'Dell' },
        { key: 'HP', name: 'HP' },
        { key: 'HEWLETT', name: 'HP' },
        { key: 'LENOVO', name: 'Lenovo' },
        { key: 'INTEL', name: 'Intel' },
        { key: 'ZEBRONICS', name: 'Zebronics' },
        { key: 'LOGITECH', name: 'Logitech' },
        { key: 'SAMSUNG', name: 'Samsung' },
        { key: 'APPLE', name: 'Apple' },
        { key: 'MACBOOK', name: 'Apple' },
        { key: 'IPAD', name: 'Apple' },
        { key: 'ASUS', name: 'ASUS' },
        { key: 'ACER', name: 'Acer' },
        { key: 'LG', name: 'LG' },
        { key: 'APC', name: 'APC' },
        { key: 'EPSON', name: 'Epson' },
        { key: 'CANON', name: 'Canon' },
        { key: 'ZEBRA', name: 'Zebra' },
        { key: 'HONEYWELL', name: 'Honeywell' },
        { key: 'TVS', name: 'TVS' }
    ];

    // Check if model explicitly starts with or names a known brand
    for (const b of knownBrands) {
        if (mUp.startsWith(b.key + ' ') || mUp.startsWith(b.key + '-') || mUp === b.key) {
            brand = b.name;
            break;
        }
    }

    // If not found in model prefix, check device-specific brand field
    if (!brand) {
        if (rawType.includes('CPU') || rawType.includes('WORKSTATION') || rawType.includes('DESKTOP') || rawType.includes('PC') || rawType.includes('COMPUTER') || rawType.includes('LAPTOP')) {
            brand = (dev.cpuBrand || dev.brandName || dev.brand || dev.brand_name || '').trim();
        } else if (rawType.includes('DISPLAY') || rawType.includes('MONITOR') || rawType.includes('SCREEN') || rawType === 'D') {
            brand = (dev.monitorBrand || dev.brandName || dev.brand || dev.brand_name || '').trim();
        } else if (rawType.includes('KEYBOARD') || rawType.includes('KB') || rawType === 'K') {
            brand = (dev.keyboardBrand || '').trim();
        } else if (rawType.includes('MOUSE') || rawType === 'M') {
            brand = (dev.mouseBrand || '').trim();
        } else if (rawType.includes('PRINTER') || rawType.includes('PRT') || rawType === 'P') {
            brand = (dev.printerBrand || dev.brandName || dev.brand || dev.brand_name || '').trim();
        } else if (rawType.includes('UPS') || rawType.includes('POWER') || rawType.includes('INVERTER') || rawType === 'U') {
            brand = (dev.upsBrand || dev.brandName || dev.brand || dev.brand_name || '').trim();
        } else if (rawType.includes('TABLET') || rawType.includes('TAB') || rawType.includes('IPAD') || rawType === 'T') {
            brand = (dev.tabletBrand || dev.brandName || dev.brand || dev.brand_name || '').trim();
        } else {
            brand = (dev.otherBrand || dev.other_brand || dev.brandName || dev.brand || dev.brand_name || '').trim();
        }
    }

    // If still no brand, check if model contains any known brand
    if (!brand && model) {
        for (const b of knownBrands) {
            if (mUp.includes(b.key)) {
                brand = b.name;
                break;
            }
        }
    }

    // Fallback to general brand if available
    if (!brand && (dev.brandName || dev.brand || dev.brand_name)) {
        brand = (dev.brandName || dev.brand || dev.brand_name || '').trim();
    }

    // Filter out dummy/placeholder brands
    const bUp = brand.toUpperCase();
    if (!brand || bUp === 'STANDARD OEM' || brand === '—' || brand === '-' || bUp === 'N/A' || bUp === 'NONE' || bUp === 'UNKNOWN' || bUp === 'NULL' || bUp === 'UNASSIGNED') {
        brand = '';
    }

    const brandBadge = brand ? `
        <div class="flex items-center gap-1.5 pb-0.5">
            <span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-slate-100 text-slate-700 border border-slate-200 shadow-3xs" title="Hardware Brand: ${brand}">
                ${brand}
            </span>
        </div>
    ` : '';

    // 2. Hardware Model & Specs (Line 2)
    let icon = 'package';
    let iconColor = 'text-slate-600';
    let defaultModelName = 'Hardware Asset';

    if (rawType.includes('CPU') || rawType.includes('WORKSTATION') || rawType.includes('DESKTOP') || rawType.includes('PC') || rawType.includes('COMPUTER') || rawType.includes('LAPTOP')) {
        icon = 'cpu';
        iconColor = 'text-indigo-600';
        defaultModelName = 'Standard Workstation Core';
    } else if (rawType.includes('DISPLAY') || rawType.includes('MONITOR') || rawType.includes('SCREEN') || rawType === 'D') {
        icon = 'monitor';
        iconColor = 'text-indigo-600';
        defaultModelName = 'Display Monitor';
    } else if (rawType.includes('KEYBOARD') || rawType.includes('KB') || rawType === 'K') {
        icon = 'keyboard';
        iconColor = 'text-amber-600';
        defaultModelName = 'USB Keyboard';
    } else if (rawType.includes('MOUSE') || rawType === 'M') {
        icon = 'mouse';
        iconColor = 'text-purple-600';
        defaultModelName = 'Optical Mouse';
    } else if (rawType.includes('PRINTER') || rawType.includes('PRT') || rawType === 'P') {
        icon = 'printer';
        iconColor = 'text-emerald-600';
        defaultModelName = 'Document Printer';
    } else if (rawType.includes('UPS') || rawType.includes('POWER') || rawType.includes('INVERTER') || rawType === 'U') {
        icon = 'zap';
        iconColor = 'text-orange-600';
        defaultModelName = 'Uninterruptible Power Supply (UPS)';
    } else if (rawType.includes('TABLET') || rawType.includes('TAB') || rawType.includes('IPAD') || rawType === 'T') {
        icon = 'tablet';
        iconColor = 'text-teal-600';
        defaultModelName = 'Tablet Terminal';
    } else if (rawType.includes('SCANNER') || rawType.includes('BARCODE') || rawType.includes('BIOMETRIC') || rawType.includes('EYE')) {
        icon = 'scan-barcode';
        iconColor = 'text-rose-600';
        defaultModelName = 'Optical Scanner';
    }

    const displayModel = model || defaultModelName;
    const line2Html = `
        <div class="flex items-center gap-1.5 text-xs font-bold text-slate-900" title="${displayModel}">
            <i data-lucide="${icon}" class="w-4 h-4 ${iconColor} shrink-0"></i>
            <span class="truncate max-w-[260px]">${displayModel}</span>
        </div>
    `;

    // 3. Special Detail (Line 3)
    let line3Html = '';

    if (rawType.includes('CPU') || rawType.includes('WORKSTATION') || rawType.includes('DESKTOP') || rawType.includes('PC') || rawType.includes('COMPUTER') || rawType.includes('LAPTOP')) {
        const hasRam = dev.storageRam && !isPlaceholderDetail(dev.storageRam);
        const hasOs = dev.operatingSystem && !isPlaceholderDetail(dev.operatingSystem);

        if (hasRam || hasOs) {
            const ramPill = hasRam ? `
                <span class="flex items-center gap-1 font-mono text-[11px] text-slate-700 font-semibold" title="${dev.storageRam}">
                    <i data-lucide="hard-drive" class="w-3.5 h-3.5 text-slate-400 shrink-0"></i>
                    <span class="truncate max-w-[170px]">${dev.storageRam}</span>
                </span>
            ` : '';

            const osPill = hasOs ? `
                <span class="inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200/80 shadow-3xs whitespace-nowrap">
                    <i data-lucide="app-window" class="w-3 h-3 text-blue-600"></i> ${dev.operatingSystem}
                </span>
            ` : '';

            line3Html = `
                <div class="flex items-center gap-2 flex-wrap text-xs text-slate-600 font-medium">
                    ${ramPill}
                    ${osPill}
                </div>
            `;
        }
    } else if (rawType.includes('TABLET') || rawType.includes('TAB') || rawType.includes('IPAD') || rawType === 'T') {
        const hasStorage = dev.storageRam && !isPlaceholderDetail(dev.storageRam);
        const hasOs = dev.operatingSystem && !isPlaceholderDetail(dev.operatingSystem);

        if (hasStorage || hasOs) {
            const storagePill = hasStorage ? `
                <span class="flex items-center gap-1 font-mono text-[11px] text-slate-700 font-semibold" title="${dev.storageRam}">
                    <i data-lucide="hard-drive" class="w-3.5 h-3.5 text-slate-400 shrink-0"></i>
                    <span class="truncate max-w-[170px]">${dev.storageRam}</span>
                </span>
            ` : '';

            const osPill = hasOs ? `
                <span class="inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-bold bg-teal-50 text-teal-700 border border-teal-200/80 shadow-3xs whitespace-nowrap">
                    <i data-lucide="app-window" class="w-3 h-3 text-teal-600"></i> ${dev.operatingSystem}
                </span>
            ` : '';

            line3Html = `
                <div class="flex items-center gap-2 flex-wrap text-xs text-slate-600 font-medium">
                    ${storagePill}
                    ${osPill}
                </div>
            `;
        }
    } else {
        // Display, Keyboard, Mouse, Printer, UPS, Scanner, Other:
        // ONLY render Line 3 if there is genuine user-entered special detail.
        // Otherwise, leave Line 3 completely blank!
        const secondary = (dev.storageRam || '').trim();
        if (secondary && !isPlaceholderDetail(secondary) && secondary.toLowerCase() !== displayModel.toLowerCase()) {
            line3Html = `
                <div class="flex items-center gap-1 text-[11px] text-slate-600 font-medium">
                    <i data-lucide="info" class="w-3 h-3 text-slate-400 shrink-0"></i>
                    <span class="truncate max-w-[260px]">${secondary}</span>
                </div>
            `;
        }
    }

    return `
        <div class="space-y-1">
            ${brandBadge}
            ${line2Html}
            ${line3Html}
        </div>
    `;
}

function getStatusDisplayHtml(dev) {
    let statusBadge = '';
    if (dev.status === 'Active') {
        statusBadge = `<span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-2xs whitespace-nowrap">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> Active
        </span>`;
    } else if (dev.status === 'In Maintenance') {
        statusBadge = `<span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200 shadow-2xs whitespace-nowrap">
            <span class="w-2 h-2 rounded-full bg-amber-500"></span> Maintenance
        </span>`;
    } else {
        statusBadge = `<span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-700 border border-slate-200 shadow-2xs whitespace-nowrap">
            <span class="w-2 h-2 rounded-full bg-slate-400"></span> ${dev.status}
        </span>`;
    }
    return `
        <div class="space-y-1">
            <div>${statusBadge}</div>
            <div class="flex items-center gap-1.5 text-xs text-slate-500 font-medium whitespace-nowrap" title="Warranty Expiry Date">
                <i data-lucide="shield-check" class="w-3.5 h-3.5 text-emerald-600 shrink-0"></i>
                <span>${dev.warrantyExpiryDate || '—'}</span>
            </div>
        </div>
    `;
}

function renderFlatDeviceRow(dev, assetBadgeClass, roomBadgeClass, isMultiDevice = false, multiCount = 0) {
    const meta = dev._meta || {};
    const custKey = meta.assignedName ? meta.assignedName.toLowerCase() : '';

    let userDisplay = '';
    if (!meta.isUnassigned) {
        const displayName = meta.user ? meta.user.fullName : meta.assignedName;
        const displayEmp = meta.assignedEmp || (meta.user ? meta.user.empId : '');
        const desigText = meta.assignedDesig || (meta.user ? (meta.user.designation || meta.user.department) : '') || 'Assigned Custodian';
        const deptText = (meta.user && meta.user.department && meta.user.department !== desigText) ? meta.user.department : '';

        const wsBadge = isMultiDevice ? `
            <div class="mt-1">
                <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-black bg-indigo-50 text-indigo-700 border border-indigo-200 shadow-3xs" title="Linked to a ${multiCount}-device workstation setup">
                    <i data-lucide="layers" class="w-3 h-3 text-indigo-600"></i>
                    <span>Workstation Set (${multiCount})</span>
                </span>
            </div>
        ` : '';

        userDisplay = `
            <div class="cursor-pointer group" onclick="${displayEmp ? `openSearchUserModal('${displayEmp}')` : ''}" title="Click to inspect profile and assignment history">
                <div class="min-w-0">
                    <div class="font-bold text-slate-900 group-hover:text-indigo-600 transition-colors text-sm truncate flex items-center gap-1">
                        <i data-lucide="user-check" class="w-3.5 h-3.5 text-indigo-500 shrink-0"></i>
                        <span class="truncate">${displayName}</span>
                    </div>
                    <div class="text-xs text-indigo-600 font-semibold truncate flex items-center gap-1 mt-0.5" title="${desigText}">
                        <i data-lucide="briefcase" class="w-3 h-3 text-indigo-400 shrink-0"></i>
                        <span class="truncate">${desigText}</span>
                    </div>
                    <div class="text-[11px] text-slate-400 font-mono truncate mt-0.5">
                        ${displayEmp ? displayEmp : ''}${displayEmp && deptText ? ' &bull; ' : ''}${deptText}
                    </div>
                    ${wsBadge}
                </div>
            </div>
        `;
    } else {
        userDisplay = `
            <div>
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-600 border border-slate-200 whitespace-nowrap">
                    Unassigned / Spare
                </span>
                <div class="text-[11px] text-slate-400 mt-0.5 whitespace-nowrap">Ready for deployment</div>
            </div>
        `;
    }

    let locationDisplay = '';
    if (meta.roomName) {
        locationDisplay = `
            <div class="space-y-0.5">
                <div class="font-bold text-slate-900 text-sm flex items-center gap-1.5 truncate" title="${meta.bldgName}">
                    <i data-lucide="building-2" class="w-3.5 h-3.5 text-slate-400 shrink-0"></i>
                    <span class="truncate">${meta.bldgName}</span>
                </div>
                <div class="flex items-center gap-1 text-xs whitespace-nowrap">
                    <span class="text-slate-500 font-medium">${meta.floorName}</span>
                    <span class="text-slate-300">&bull;</span>
                    <span class="font-bold px-1.5 py-0.2 rounded border text-xs ${roomBadgeClass}">
                        ${meta.roomName}
                    </span>
                </div>
            </div>
        `;
    } else {
        locationDisplay = `<span class="text-slate-400 italic text-xs">Unassigned Location</span>`;
    }

    return `
        <tr class="hover:bg-indigo-50/40 transition-colors divide-x divide-slate-100 text-slate-800" ${custKey ? `data-custodian-key="${custKey}"` : ''}>
            <td class="py-3.5 pl-5 pr-3.5 whitespace-nowrap">
                <div class="space-y-1">
                    <div>${getDeviceTypeBadge(dev)}</div>
                    <div class="flex items-center gap-2 flex-wrap">
                        <span class="font-mono font-black text-xs px-2 py-0.5 rounded-md border ${assetBadgeClass} shadow-3xs whitespace-nowrap inline-block">
                            ${dev.assetId}
                        </span>
                        <span class="text-xs text-slate-500 font-mono font-medium whitespace-nowrap flex items-center gap-1">
                            <span class="text-slate-400 font-semibold">SN:</span>
                            <span class="text-slate-700 font-semibold">${dev.serialNumber || '—'}</span>
                        </span>
                    </div>
                    ${meta.roomName ? `
                        <div class="text-[11px] text-slate-400 flex items-center gap-1">
                            <i data-lucide="map-pin" class="w-3 h-3 text-slate-400"></i>
                            <span>${meta.floorName} &bull; ${meta.roomName}</span>
                        </div>
                    ` : ''}
                </div>
            </td>
            <td class="py-3 px-3.5">${getDeviceSpecificationsHtml(dev)}</td>
            <td class="py-3 px-3.5">
                <div class="space-y-0.5">
                    <div class="flex items-center gap-1.5 font-mono text-sm font-bold text-slate-900 whitespace-nowrap">
                        <span class="w-2 h-2 rounded-full bg-emerald-500 shrink-0 shadow-xs"></span>
                        <span>${dev.ipAddress || '—'}</span>
                    </div>
                    <div class="text-xs font-mono text-slate-500 whitespace-nowrap">
                        <span class="text-slate-400 font-semibold">MAC:</span> ${dev.macAddress || '—'}
                    </div>
                </div>
            </td>
            <td class="py-3 px-3.5">${getStatusDisplayHtml(dev)}</td>
            <td class="py-3 pr-4 pl-2 text-center w-16 min-w-[60px]">
                <button onclick="toggleDeviceActionMenu('${dev.id}', event)" class="w-8 h-8 rounded-lg border border-slate-300 bg-white hover:bg-indigo-50 hover:border-indigo-400 text-slate-700 hover:text-indigo-700 inline-flex items-center justify-center transition-all shadow-2xs group cursor-pointer" title="Device Actions Menu">
                    <i data-lucide="more-vertical" class="w-4 h-4 group-hover:scale-110 transition-transform"></i>
                </button>
            </td>
        </tr>
    `;
}

function setupWorkstationHoverListeners() {
    const tbody = document.getElementById("inventory-table-tbody") || document.getElementById("devices-table-body");
    if (!tbody) return;

    tbody.querySelectorAll('tr[data-custodian-key]').forEach(row => {
        row.addEventListener('mouseenter', () => {
            const key = row.dataset.custodianKey;
            if (!key) return;
            tbody.querySelectorAll(`tr[data-custodian-key="${key}"]`).forEach(linked => {
                linked.classList.add('bg-indigo-50/70', 'ring-1', 'ring-indigo-300');
            });
        });
        row.addEventListener('mouseleave', () => {
            const key = row.dataset.custodianKey;
            if (!key) return;
            tbody.querySelectorAll(`tr[data-custodian-key="${key}"]`).forEach(linked => {
                linked.classList.remove('bg-indigo-50/70', 'ring-1', 'ring-indigo-300');
            });
        });
    });
}

// ============================================================================
// COMPOSITE WORKSTATION EXPANSION (Single-Holder Workstations -> Workstation Sets)
// ============================================================================
function isCompositeWorkstation(dev) {
    if (!dev) return false;
    const rawType = (dev.deviceType || dev.device_type || '').trim().toLowerCase();
    if (rawType.startsWith('workstation (') || rawType === 'workstation' || (rawType.startsWith('workstation') && rawType.includes(','))) {
        return true;
    }
    if (rawType.includes('cpu') && (rawType.includes('display') || rawType.includes('monitor') || rawType.includes('keyboard') || rawType.includes('mouse'))) {
        return true;
    }
    return false;
}

function expandCompositeWorkstation(dev, group) {
    const rawType = (dev.deviceType || dev.device_type || '').trim();
    let components = [];

    // Extract anything between parentheses e.g. "Workstation (CPU, Display, Keyboard, Mouse, Tablet)"
    const match = rawType.match(/\(([^)]+)\)/);
    if (match) {
        components = match[1].split(/[,+]/).map(s => s.trim()).filter(Boolean);
    } else {
        if (dev.cpuProcessor || dev.storageRam) components.push('CPU');
        if (dev.monitorSpec) components.push('Display');
        if (dev.keyboardSpec) components.push('Keyboard');
        if (dev.mouseSpec) components.push('Mouse');
        if (dev.tabletSpec) components.push('Tablet');
        if (dev.printerSpec) components.push('Printer');
        if (dev.upsSpec) components.push('UPS');
    }

    // Normalize component names
    const normalized = [];
    components.forEach(c => {
        const u = c.toUpperCase();
        if (u.includes('CPU') || u.includes('DESKTOP') || u.includes('PC')) normalized.push('CPU');
        else if (u.includes('DISPLAY') || u.includes('MONITOR') || u.includes('SCREEN')) normalized.push('Display');
        else if (u.includes('KEYBOARD') || u.includes('KB')) normalized.push('Keyboard');
        else if (u.includes('MOUSE')) normalized.push('Mouse');
        else if (u.includes('TABLET') || u.includes('TAB') || u.includes('IPAD')) normalized.push('Tablet');
        else if (u.includes('PRINTER') || u.includes('PRT')) normalized.push('Printer');
        else if (u.includes('UPS') || u.includes('POWER') || u.includes('INVERTER')) normalized.push('UPS');
        else if (u.includes('OTHER')) normalized.push('Other');
        else normalized.push(c);
    });

    const uniqueComps = [...new Set(normalized)];
    if (uniqueComps.length === 0) uniqueComps.push('CPU');

    return uniqueComps.map((comp, idx) => {
        const sub = { ...dev };
        sub._isCompositeSubItem = true;
        sub._compositeIndex = idx;
        sub._parentAssetId = dev.assetId;
        sub.deviceType = comp;

        const compUpper = comp.toUpperCase();
        if (compUpper === 'CPU') {
            sub.cpuProcessor = dev.cpuProcessor || '';
            sub.storageRam = dev.storageRam || '';
            sub.brandName = dev.cpuBrand || dev.brandName || dev.brand || '';
        } else if (compUpper === 'DISPLAY') {
            sub.cpuProcessor = dev.monitorSpec || '';
            sub.storageRam = '';
            sub.operatingSystem = '';
            sub.ipAddress = '—';
            sub.macAddress = '—';
            sub.brandName = dev.monitorBrand || '';
        } else if (compUpper === 'KEYBOARD') {
            sub.cpuProcessor = dev.keyboardSpec || '';
            sub.storageRam = '';
            sub.operatingSystem = '';
            sub.ipAddress = '—';
            sub.macAddress = '—';
            sub.brandName = dev.keyboardBrand || '';
        } else if (compUpper === 'MOUSE') {
            sub.cpuProcessor = dev.mouseSpec || '';
            sub.storageRam = '';
            sub.operatingSystem = '';
            sub.ipAddress = '—';
            sub.macAddress = '—';
            sub.brandName = dev.mouseBrand || '';
        } else if (compUpper === 'TABLET') {
            sub.cpuProcessor = dev.tabletSpec || '';
            sub.storageRam = dev.storageRam || '';
            sub.operatingSystem = dev.operatingSystem || '';
            sub.ipAddress = dev.ipAddress || '—';
            sub.macAddress = dev.macAddress || '—';
            sub.brandName = dev.tabletBrand || '';
        } else if (compUpper === 'PRINTER') {
            sub.cpuProcessor = dev.printerSpec || '';
            sub.storageRam = '';
            sub.operatingSystem = '';
            sub.ipAddress = dev.ipAddress || '—';
            sub.macAddress = dev.macAddress || '—';
            sub.brandName = dev.printerBrand || '';
        } else if (compUpper === 'UPS') {
            sub.cpuProcessor = dev.upsSpec || '';
            sub.storageRam = '';
            sub.operatingSystem = '';
            sub.ipAddress = '—';
            sub.macAddress = '—';
            sub.brandName = dev.upsBrand || '';
        } else if (compUpper === 'OTHER' || compUpper === 'CUSTOM') {
            sub.cpuProcessor = dev.otherSpec || dev.other_spec || dev.otherModel || '';
            sub.storageRam = '';
            sub.operatingSystem = '';
            sub.ipAddress = '—';
            sub.macAddress = '—';
            sub.brandName = dev.otherBrand || dev.other_brand || '';
        }
        return sub;
    });
}

function renderInventoryTable() {
    const tbody = document.getElementById("inventory-table-tbody") || document.getElementById("devices-table-body");
    const countSpan = document.getElementById("table-showing-count");
    const badgeSpan = document.getElementById("tab-badge-inventory");
    if (!tbody) return;

    // Sync toggle button active visual state
    const btnGrouped = document.getElementById('btn-view-grouped');
    const btnFlat = document.getElementById('btn-view-flat');
    if (btnGrouped && btnFlat) {
        if (inventoryViewMode === 'grouped') {
            btnGrouped.className = "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-extrabold transition-all bg-white text-indigo-700 shadow-xs cursor-pointer";
            btnFlat.className = "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all text-slate-600 hover:text-slate-900 cursor-pointer";
        } else {
            btnFlat.className = "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-extrabold transition-all bg-white text-indigo-700 shadow-xs cursor-pointer";
            btnGrouped.className = "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all text-slate-600 hover:text-slate-900 cursor-pointer";
        }
    }

    const devices = getFilteredDevices();
    if (countSpan) countSpan.textContent = devices.length;
    if (badgeSpan) badgeSpan.textContent = devices.length;

    if (devices.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-12 text-slate-400">
                    <div class="flex flex-col items-center justify-center gap-2">
                        <i data-lucide="inbox" class="w-8 h-8 text-slate-300"></i>
                        <span class="font-semibold text-xs">No matching devices found in inventory.</span>
                        <button onclick="clearAllFilters()" class="text-indigo-600 text-xs font-bold hover:underline cursor-pointer">Clear Filters</button>
                    </div>
                </td>
            </tr>
        `;
        const wsBadge = document.getElementById('badge-workstation-count');
        if (wsBadge) wsBadge.textContent = "0";
        lucide.createIcons();
        return;
    }

    // 1. Parse metadata for all devices
    const groupsMap = {};
    const unassignedDevices = [];

    devices.forEach(dev => {
        // Resolve Custodian User
        let user = (appState.users || []).find(u => (u.id && u.id === dev.assignedUserId) || (u.empId && (u.empId === dev.empId || u.empId === dev.assignedEmpId)));
        if (!user && (dev.assignedUserName || dev.assigned_user_name)) {
            const targetName = (dev.assignedUserName || dev.assigned_user_name || '').toLowerCase().trim();
            if (targetName && targetName !== 'unassigned') {
                user = (appState.users || []).find(u => u.fullName && u.fullName.toLowerCase().trim() === targetName);
            }
        }
        const assignedName = (dev.assignedUserName || dev.assigned_user_name || (user ? user.fullName : '') || '').trim();
        const assignedEmp = (dev.empId || dev.assigned_emp_id || (user ? user.empId : '') || '').trim();
        const assignedDesig = (dev.designation || dev.assignedDesignation || dev.assigned_designation || (user ? (user.designation || user.department) : '') || '').trim();
        const isUnassigned = !assignedName || assignedName.toLowerCase() === 'unassigned' || assignedName.toLowerCase().includes('unassigned / spare') || assignedName.toLowerCase().startsWith('unassigned');

        // Resolve Location
        const room = appState.rooms.find(r => r.id === dev.roomId);
        const floor = room ? appState.floors.find(f => f.id === room.floorId) : null;
        const bldg = floor ? appState.buildings.find(b => b.id === floor.buildingId) : null;

        let bldgName = dev.buildingName || (bldg ? bldg.name : 'PSM Hospital');
        if (bldgName) {
            bldgName = bldgName.replace(/\s*Main Medical Complex/gi, '').replace(/\s*Main Complex/gi, '').trim();
            if (!bldgName || bldgName === 'PSM') bldgName = 'PSM Hospital';
        }
        const floorName = dev.floorName || (floor ? floor.name : 'Ground Floor');
        const roomName = dev.roomName || (room ? room.name : '');

        dev._meta = {
            user,
            assignedName,
            assignedEmp,
            assignedDesig,
            isUnassigned,
            bldgName,
            floorName,
            roomName
        };

        if (isUnassigned) {
            unassignedDevices.push(dev);
        } else {
            const key = assignedName.toLowerCase();
            if (!groupsMap[key]) {
                groupsMap[key] = {
                    key,
                    displayName: user ? user.fullName : assignedName,
                    displayEmp: assignedEmp || (user ? user.empId : ''),
                    desigText: assignedDesig || (user ? (user.designation || user.department) : '') || 'Assigned Custodian',
                    bldgName,
                    floorName,
                    roomName,
                    devices: []
                };
            }
            groupsMap[key].devices.push(dev);
            if (roomName && !groupsMap[key].roomName) {
                groupsMap[key].roomName = roomName;
                groupsMap[key].floorName = floorName;
                groupsMap[key].bldgName = bldgName;
            }
        }
    });

    // Automatically expand composite Workstations (e.g. "Workstation (CPU, Display, Keyboard, Mouse, Tablet)")
    // so single-holder workstations get full WORKSTATION SET headers and sub-bundle component rows just like multi-device sets
    Object.values(groupsMap).forEach(group => {
        const expanded = [];
        group.devices.forEach(dev => {
            if (isCompositeWorkstation(dev)) {
                expanded.push(...expandCompositeWorkstation(dev, group));
            } else {
                expanded.push(dev);
            }
        });
        group.devices = expanded;
    });

    const multiDeviceWorkstations = Object.values(groupsMap).filter(g => g.devices.length > 1);
    const singleDeviceWorkstations = Object.values(groupsMap).filter(g => g.devices.length === 1);
    const totalWorkstations = Object.values(groupsMap).length;

    const wsBadge = document.getElementById('badge-workstation-count');
    if (wsBadge) {
        wsBadge.textContent = totalWorkstations;
    }

    let html = '';

    // ========================================================================
    // MODE A: WORKSTATION SETS (GROUPED VIEW)
    // ========================================================================
    if (inventoryViewMode === 'grouped') {
        // 1. Multi-Device Workstations (e.g. Khushali with CPU, Display, Keyboard, Mouse, Printer, UPS)
        multiDeviceWorkstations.forEach(group => {
            // Sort devices inside workstation logically: CPU -> Display -> Keyboard -> Mouse -> Printer -> UPS
            group.devices.sort((a, b) => getWorkstationDevicePriority(a) - getWorkstationDevicePriority(b));

            const isCollapsed = collapsedWorkstations.has(group.key);

            // Workstation Header Row
            const typeCounts = {};
            group.devices.forEach(d => {
                const t = (d.deviceType || d.device_type || 'Device').trim();
                typeCounts[t] = (typeCounts[t] || 0) + 1;
            });
            const typeChips = Object.entries(typeCounts).map(([type, count]) => {
                return `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-bold bg-white text-slate-700 border border-slate-200/90 shadow-3xs">
                    <span class="font-extrabold text-indigo-600">${count > 1 ? `${count}x ` : ''}</span>${type}
                </span>`;
            }).join(' ');

            const primaryAssetId = group.devices[0]?.assetId || '—';
            const isGroupHosp = group.devices[0]?.orgId === 'HOSP';
            const groupAssetBadgeClass = isGroupHosp ? 'bg-violet-50 text-violet-700 border-violet-200' : 'bg-indigo-50 text-indigo-700 border-indigo-200';

            html += `
                <tr class="bg-gradient-to-r from-indigo-50/95 via-slate-50 to-indigo-50/50 border-t-2 border-indigo-500/80 shadow-2xs group-header-row cursor-pointer select-none" onclick="toggleWorkstationCollapse('${group.key}')">
                    <td colspan="5" class="py-3 px-5">
                        <div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
                            <!-- Left: Workstation Title, Custodian Details & Location -->
                            <div class="flex items-center gap-3.5 min-w-0">
                                <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 text-white flex items-center justify-center font-black text-xs shadow-sm shrink-0">
                                    <i data-lucide="monitor" class="w-4 h-4"></i>
                                </div>
                                <div class="min-w-0">
                                    <div class="flex items-center gap-2 flex-wrap">
                                        <span class="text-[11px] font-black uppercase tracking-wider text-indigo-700 bg-indigo-100/90 border border-indigo-200/80 px-2 py-0.5 rounded-md shadow-3xs">
                                            Workstation Set
                                        </span>
                                        <span class="font-extrabold text-slate-900 text-sm truncate hover:text-indigo-600 transition-colors" title="Click to collapse/expand">${group.displayName}</span>
                                        ${group.displayEmp ? `<span class="text-xs font-mono text-slate-500 font-semibold">(${group.displayEmp})</span>` : ''}
                                        <span class="text-xs font-bold text-indigo-600 px-2 py-0.5 rounded-md bg-white border border-indigo-200/60 shadow-3xs">${group.desigText}</span>
                                        <span class="font-mono font-black text-xs px-2.5 py-0.5 rounded-md border ${groupAssetBadgeClass} shadow-3xs whitespace-nowrap inline-flex items-center gap-1.5 bg-white" title="Workstation Shared Asset Tag">
                                            <i data-lucide="tag" class="w-3.5 h-3.5 text-indigo-600"></i>
                                            <span>${primaryAssetId}</span>
                                        </span>
                                    </div>
                                    <div class="flex items-center gap-2 text-xs text-slate-600 font-medium mt-1 flex-wrap">
                                        <span class="flex items-center gap-1">
                                            <i data-lucide="building-2" class="w-3.5 h-3.5 text-slate-400"></i>
                                            ${group.bldgName}
                                        </span>
                                        <span class="text-slate-300">&bull;</span>
                                        <span class="text-slate-500">${group.floorName}</span>
                                        <span class="text-slate-300">&bull;</span>
                                        <span class="font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                                            ${group.roomName || 'Assigned Desk'}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <!-- Right: Hardware Chips Summary & Total Badge & Collapse Chevron -->
                            <div class="flex items-center gap-2 self-start md:self-center shrink-0">
                                <div class="hidden lg:flex items-center gap-1.5">
                                    ${typeChips}
                                </div>
                                <span class="px-2.5 py-1 rounded-full text-xs font-black bg-indigo-600 text-white shadow-2xs flex items-center gap-1.5">
                                    <i data-lucide="layers" class="w-3.5 h-3.5"></i>
                                    <span>${group.devices.length} Devices Linked</span>
                                </span>
                                <button type="button" onclick="event.stopPropagation(); toggleWorkstationCollapse('${group.key}')" 
                                    class="w-7 h-7 rounded-lg bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 flex items-center justify-center transition-all shadow-3xs cursor-pointer" 
                                    title="${isCollapsed ? 'Expand Workstation Devices' : 'Collapse Workstation Devices'}">
                                    <i data-lucide="${isCollapsed ? 'chevron-right' : 'chevron-down'}" class="w-4 h-4 text-indigo-600"></i>
                                </button>
                            </div>
                        </div>
                    </td>
                </tr>
            `;

            // If not collapsed, render child rows with connected left accent border
            if (!isCollapsed) {
                group.devices.forEach((dev) => {
                    const isHosp = dev.orgId === 'HOSP';
                    const assetBadgeClass = isHosp ? 'bg-violet-50 text-violet-700 border-violet-200' : 'bg-indigo-50 text-indigo-700 border-indigo-200';

                    const devRoom = dev._meta.roomName || group.roomName;
                    const devFloor = dev._meta.floorName || group.floorName;
                    const locationDisplay = `
                        <div class="space-y-0.5">
                            <div class="font-bold text-slate-800 text-xs flex items-center gap-1 truncate">
                                <i data-lucide="map-pin" class="w-3 h-3 text-indigo-500 shrink-0"></i>
                                <span class="font-bold text-indigo-800 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-200 text-xs truncate">
                                    ${devRoom}
                                </span>
                            </div>
                            <div class="text-[11px] text-slate-400 font-medium truncate">${devFloor} &bull; Workstation Desk</div>
                        </div>
                    `;

                    html += `
                        <tr class="hover:bg-indigo-50/50 transition-colors divide-x divide-slate-100 text-slate-800 border-l-4 border-indigo-500/80 bg-slate-50/20" data-custodian-key="${group.key}">
                            <td class="py-3.5 pl-5 pr-3.5 whitespace-nowrap">
                                <div class="space-y-1">
                                    <div class="flex items-center gap-2 flex-wrap">
                                        ${getDeviceTypeBadge(dev)}
                                        ${dev._isCompositeSubItem ? `
                                            <span class="text-[10px] font-bold px-1.5 py-0.5 rounded shadow-3xs ${dev.deviceType === 'CPU' ? 'bg-indigo-100 text-indigo-800 border border-indigo-200' : 'bg-slate-100 text-slate-600 border border-slate-200'}">
                                                ${dev.deviceType === 'CPU' ? 'Core' : 'Linked'}
                                            </span>
                                        ` : ''}
                                    </div>
                                    <div class="text-xs text-slate-500 font-mono font-medium whitespace-nowrap flex items-center gap-1">
                                        <span class="text-slate-400 font-semibold">SN:</span>
                                        <span class="text-slate-700 font-semibold">${dev.serialNumber || (dev._isCompositeSubItem ? 'Bundled with Workstation' : '—')}</span>
                                    </div>
                                </div>
                            </td>
                            <td class="py-3 px-3.5">${getDeviceSpecificationsHtml(dev)}</td>
                            <td class="py-3 px-3.5">
                                <div class="space-y-0.5">
                                    <div class="flex items-center gap-1.5 font-mono text-sm font-bold text-slate-900 whitespace-nowrap">
                                        <span class="w-2 h-2 rounded-full bg-emerald-500 shrink-0 shadow-xs"></span>
                                        <span>${dev.ipAddress || '—'}</span>
                                    </div>
                                    <div class="text-xs font-mono text-slate-500 whitespace-nowrap">
                                        <span class="text-slate-400 font-semibold">MAC:</span> ${dev.macAddress || '—'}
                                    </div>
                                </div>
                            </td>
                            <td class="py-3 px-3.5">${getStatusDisplayHtml(dev)}</td>
                            <td class="py-3 pr-4 pl-2 text-center w-16 min-w-[60px]">
                                <button onclick="toggleDeviceActionMenu('${dev.id}', event)" class="w-8 h-8 rounded-lg border border-slate-300 bg-white hover:bg-indigo-50 hover:border-indigo-400 text-slate-700 hover:text-indigo-700 inline-flex items-center justify-center transition-all shadow-2xs group cursor-pointer" title="Device Actions Menu">
                                    <i data-lucide="more-vertical" class="w-4 h-4 group-hover:scale-110 transition-transform"></i>
                                </button>
                            </td>
                        </tr>
                    `;
                });
            }
        });

        // 2. Single-Device Assignments
        if (singleDeviceWorkstations.length > 0) {
            singleDeviceWorkstations.forEach(group => {
                const dev = group.devices[0];
                const isHosp = dev.orgId === 'HOSP';
                const assetBadgeClass = isHosp ? 'bg-violet-50 text-violet-700 border-violet-200' : 'bg-indigo-50 text-indigo-700 border-indigo-200';
                const roomBadgeClass = isHosp ? 'bg-violet-50 text-violet-800 border-violet-200' : 'bg-indigo-50 text-indigo-800 border-indigo-200';

                html += renderFlatDeviceRow(dev, assetBadgeClass, roomBadgeClass, false, 1);
            });
        }

        // 3. Unassigned / Spares Section
        if (unassignedDevices.length > 0) {
            html += `
                <tr class="bg-slate-100/90 border-t-2 border-slate-300/80 shadow-2xs">
                    <td colspan="5" class="py-2.5 px-5">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2.5">
                                <span class="w-7 h-7 rounded-lg bg-slate-200 text-slate-600 flex items-center justify-center font-bold text-xs shadow-2xs shrink-0">
                                    <i data-lucide="archive" class="w-4 h-4"></i>
                                </span>
                                <span class="font-extrabold text-slate-700 text-xs uppercase tracking-wider">
                                    Unassigned / Backup Spares
                                </span>
                                <span class="px-2 py-0.5 rounded-full text-xs font-bold bg-slate-200/90 text-slate-700">
                                    ${unassignedDevices.length} Available Devices
                                </span>
                            </div>
                        </div>
                    </td>
                </tr>
            `;
            unassignedDevices.forEach(dev => {
                const isHosp = dev.orgId === 'HOSP';
                const assetBadgeClass = isHosp ? 'bg-violet-50 text-violet-700 border-violet-200' : 'bg-indigo-50 text-indigo-700 border-indigo-200';
                const roomBadgeClass = isHosp ? 'bg-violet-50 text-violet-800 border-violet-200' : 'bg-indigo-50 text-indigo-800 border-indigo-200';
                html += renderFlatDeviceRow(dev, assetBadgeClass, roomBadgeClass, false, 0);
            });
        }
    }

    // ========================================================================
    // MODE B: ALL DEVICES (FLAT VIEW)
    // ========================================================================
    else {
        html = devices.map(dev => {
            const isHosp = dev.orgId === 'HOSP';
            const assetBadgeClass = isHosp ? 'bg-violet-50 text-violet-700 border-violet-200' : 'bg-indigo-50 text-indigo-700 border-indigo-200';
            const roomBadgeClass = isHosp ? 'bg-violet-50 text-violet-800 border-violet-200' : 'bg-indigo-50 text-indigo-800 border-indigo-200';

            const custKey = dev._meta.assignedName ? dev._meta.assignedName.toLowerCase() : '';
            const isMulti = custKey && groupsMap[custKey] && groupsMap[custKey].devices.length > 1;
            const multiCount = isMulti ? groupsMap[custKey].devices.length : 0;

            return renderFlatDeviceRow(dev, assetBadgeClass, roomBadgeClass, isMulti, multiCount);
        }).join('');
    }

    tbody.innerHTML = html;
    lucide.createIcons();
    setupWorkstationHoverListeners();
}

// ============================================================================
// Floating 3-Dot Actions Dropdown Controller
// ============================================================================
let activeDropdownDeviceId = null;

function toggleDeviceActionMenu(deviceId, event) {
    event.stopPropagation();
    const dropdown = document.getElementById("device-actions-dropdown");
    if (!dropdown) return;

    if (activeDropdownDeviceId === deviceId && !dropdown.classList.contains("hidden")) {
        closeDeviceActionDropdown();
        return;
    }

    activeDropdownDeviceId = deviceId;
    const dev = appState.devices.find(d => d.id === deviceId);
    const assetSpan = document.getElementById("dropdown-action-asset");
    if (assetSpan && dev) {
        assetSpan.textContent = dev.assetId;
    }

    dropdown.classList.remove("hidden");
    lucide.createIcons();

    // Position dropdown precisely near the 3-dot button
    const btnRect = event.currentTarget.getBoundingClientRect();
    const dropdownWidth = 256;
    const dropdownHeight = 190;

    let left = btnRect.right - dropdownWidth;
    let top = btnRect.bottom + 6;

    // Viewport overflow bounds check
    if (top + dropdownHeight > window.innerHeight) {
        top = btnRect.top - dropdownHeight - 6;
    }
    if (left < 10) {
        left = 10;
    }

    dropdown.style.top = `${top}px`;
    dropdown.style.left = `${left}px`;
}

function closeDeviceActionDropdown() {
    const dropdown = document.getElementById("device-actions-dropdown");
    if (dropdown) {
        dropdown.classList.add("hidden");
    }
    activeDropdownDeviceId = null;
}

function executeDropdownAction(actionType, event) {
    if (event && event.stopPropagation) {
        event.stopPropagation();
    }
    const devId = activeDropdownDeviceId;
    if (!devId) return;
    closeDeviceActionDropdown();

    if (actionType === 'location') {
        openChangeLocationModal(devId);
    } else if (actionType === 'reassign') {
        openReassignModal(devId);
    } else if (actionType === 'inspect') {
        openDeviceDetailPopup(devId);
    }
}

// Close 3-dot dropdown when clicking outside
document.addEventListener("click", (e) => {
    const dropdown = document.getElementById("device-actions-dropdown");
    if (dropdown && !dropdown.classList.contains("hidden")) {
        if (!dropdown.contains(e.target) && !e.target.closest('button[title="Device Actions Menu"]')) {
            closeDeviceActionDropdown();
        }
    }
});

// Close 3-dot dropdown on window scroll
window.addEventListener("scroll", (e) => {
    const dropdown = document.getElementById("device-actions-dropdown");
    if (dropdown && !dropdown.classList.contains("hidden")) {
        // Do not close if scrolling inside an opened modal
        if (e.target && e.target.closest && (e.target.closest('#modal-search-user') || e.target.closest('#modal-change-location') || e.target.closest('#modal-reassign') || e.target.closest('#modal-login-history'))) {
            return;
        }
        closeDeviceActionDropdown();
    }
}, true);


// High-performance Fluid Momentum Number Counter Animation (Apple ease-out curve)
function animateNumberCounter(el, targetValue, duration = 1100, delay = 0) {
    if (!el) return;
    targetValue = parseInt(targetValue, 10) || 0;

    // Cancel any active animation or pending timeout on this element
    if (el._animFrameId) {
        cancelAnimationFrame(el._animFrameId);
        el._animFrameId = null;
    }
    if (el._animTimeoutId) {
        clearTimeout(el._animTimeoutId);
        el._animTimeoutId = null;
    }

    const run = () => {
        const rawText = (el.textContent || '').trim().replace(/[^0-9]/g, '');
        const startValue = rawText ? parseInt(rawText, 10) : 0;

        if (startValue === targetValue) {
            el.textContent = targetValue.toLocaleString();
            return;
        }

        const startTime = performance.now();
        // Quartic deceleration curve: cubic-bezier-like fluid momentum
        const easeOutQuart = (t) => 1 - Math.pow(1 - t, 4);

        function step(now) {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = easeOutQuart(progress);
            const current = Math.round(startValue + (targetValue - startValue) * eased);

            el.textContent = current.toLocaleString();

            if (progress < 1) {
                el._animFrameId = requestAnimationFrame(step);
            } else {
                el.textContent = targetValue.toLocaleString();
                el._animFrameId = null;
                // Add finishing micro-pop animation
                el.classList.remove('kpi-count-finished');
                void el.offsetWidth; // Force reflow
                el.classList.add('kpi-count-finished');
            }
        }

        el._animFrameId = requestAnimationFrame(step);
    };

    if (delay > 0) {
        el._animTimeoutId = setTimeout(run, delay);
    } else {
        run();
    }
}

function renderStats() {
    const all = appState.devices;
    const total = document.getElementById("stat-total-devices");
    const active = document.getElementById("stat-active-devices");
    const maint = document.getElementById("stat-maint-devices");
    const spare = document.getElementById("stat-storage-devices") || document.getElementById("stat-spare-devices");
    const warranty = document.getElementById("stat-warranty-devices");
    const breakdown = document.getElementById("stat-org-breakdown");

    const currentDevices = appState.selectedOrg === "ALL"
        ? all
        : all.filter(d => d.orgId === appState.selectedOrg);

    const isSpareDevice = (d) => {
        if (d.status === "In Storage" || d.status === "Spare") return true;
        const name = (d.assignedUserName || d.assigned_user_name || '').trim().toLowerCase();
        const emp = (d.empId || d.assigned_emp_id || d.assignedEmpId || '').trim().toLowerCase();
        const uid = (d.assignedUserId || '').trim().toLowerCase();
        if (name && name !== 'unassigned' && !name.startsWith('unassigned') && !name.includes('it spares') && !name.includes('hardware pool')) {
            return false;
        }
        if (emp && emp !== 'unassigned' && emp !== 'pool-spare') {
            return false;
        }
        if (uid && uid !== 'unassigned' && uid !== 'pool-spare') {
            return false;
        }
        return true;
    };

    const totalVal = currentDevices.length;
    const activeVal = currentDevices.filter(d => d.status === "Active").length;
    const maintVal = currentDevices.filter(d => d.status === "In Maintenance").length;
    const spareVal = currentDevices.filter(isSpareDevice).length;

    // Trigger staggered rolling count animation when opening the page
    if (!window._kpiStatsInitialAnimated) {
        window._kpiStatsInitialAnimated = true;
        animateNumberCounter(total, totalVal, 1100, 0);
        animateNumberCounter(active, activeVal, 1100, 70);
        animateNumberCounter(maint, maintVal, 1100, 140);
        animateNumberCounter(spare, spareVal, 1100, 210);
    } else {
        // Subsequent updates (e.g. after adding/saving a device) transition smoothly
        animateNumberCounter(total, totalVal, 400, 0);
        animateNumberCounter(active, activeVal, 400, 0);
        animateNumberCounter(maint, maintVal, 400, 0);
        animateNumberCounter(spare, spareVal, 400, 0);
    }

    if (warranty) warranty.textContent = currentDevices.filter(d => (d.warrantyExpiryDate || '').includes("2026") || (d.warrantyExpiryDate || '').includes("2024")).length;

    const hospCount = all.filter(d => d.orgId === "HOSP").length;
    if (breakdown) breakdown.textContent = `${hospCount} Healthcare Units`;
}

function updateLandingCounts() {
    const uniDev = document.getElementById("landing-uni-devices");
    const hospDev = document.getElementById("landing-hosp-devices");
    const uniLabs = document.getElementById("landing-uni-labs");
    const hospWards = document.getElementById("landing-hosp-wards");

    if (uniDev) uniDev.textContent = "17";
    if (uniLabs) uniLabs.textContent = "10 Labs";
    if (hospDev) hospDev.textContent = appState.devices.filter(d => d.orgId === "HOSP").length;
    if (hospWards) hospWards.textContent = "7 Wards";
}

function populateFilterDropdowns() {
    const bldgSelect = document.getElementById("filter-building");
    const osSelect = document.getElementById("filter-os");

    if (bldgSelect) {
        const availableBldgs = appState.selectedOrg === "ALL"
            ? appState.buildings
            : appState.buildings.filter(b => b.orgId === appState.selectedOrg);

        bldgSelect.innerHTML = `<option value="ALL">All Buildings / Wings</option>` + availableBldgs.map(b => `
            <option value="${b.id}" ${appState.filters.buildingId === b.id ? 'selected' : ''}>${b.name}</option>
        `).join('');
    }

    if (osSelect) {
        const uniqueOS = [...new Set(appState.devices.map(d => d.operatingSystem))];
        osSelect.innerHTML = `<option value="ALL">All Operating Systems</option>` + uniqueOS.map(os => `
            <option value="${os}" ${appState.filters.os === os ? 'selected' : ''}>${os}</option>
        `).join('');
    }
}

function handleGlobalSearch(e) {
    appState.searchQuery = e.target.value;
    const invInput = document.getElementById("inventory-search-input");
    if (invInput) invInput.value = appState.searchQuery;
    renderInventoryTable();
}

function applyInventoryFilters() {
    const invInput = document.getElementById("inventory-search-input");
    const bldgSelect = document.getElementById("filter-building");
    const statusSelect = document.getElementById("filter-status");
    const osSelect = document.getElementById("filter-os");

    if (invInput) appState.searchQuery = invInput.value;
    if (bldgSelect) appState.filters.buildingId = bldgSelect.value;
    if (statusSelect) appState.filters.status = statusSelect.value;
    if (osSelect) appState.filters.os = osSelect.value;

    renderInventoryTable();
    renderStats();
    renderFilterChips();
}

function renderFilterChips() {
    const container = document.getElementById("filter-chips-container");
    if (!container) return;

    let chips = [];
    if (appState.searchQuery) {
        chips.push(`Query: "${appState.searchQuery}" <button onclick="clearSearch()" class="ml-1 text-slate-400 hover:text-slate-600">&times;</button>`);
    }
    if (appState.filters.buildingId !== "ALL") {
        const bldg = appState.buildings.find(b => b.id === appState.filters.buildingId);
        chips.push(`Building: ${bldg ? bldg.name : ''} <button onclick="clearFilter('buildingId')" class="ml-1 text-slate-400 hover:text-slate-600">&times;</button>`);
    }
    if (appState.filters.status !== "ALL") {
        chips.push(`Status: ${appState.filters.status} <button onclick="clearFilter('status')" class="ml-1 text-slate-400 hover:text-slate-600">&times;</button>`);
    }

    if (chips.length > 0) {
        container.innerHTML = `<span class="text-[11px] font-bold text-slate-500">Active Filters:</span>` + chips.map(c => `
            <span class="inline-flex items-center px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200 text-[11px] font-semibold">${c}</span>
        `).join('') + `<button onclick="clearAllFilters()" class="text-[11px] text-red-500 font-bold hover:underline ml-2">Reset All</button>`;
    } else {
        container.innerHTML = "";
    }
}

function clearFilter(key) {
    appState.filters[key] = "ALL";
    const select = document.getElementById(`filter-${key === 'buildingId' ? 'building' : key}`);
    if (select) select.value = "ALL";
    applyInventoryFilters();
}

function clearSearch() {
    appState.searchQuery = "";
    const gInput = document.getElementById("global-search-input");
    const iInput = document.getElementById("inventory-search-input");
    if (gInput) gInput.value = "";
    if (iInput) iInput.value = "";
    applyInventoryFilters();
}

function clearAllFilters() {
    appState.searchQuery = "";
    appState.filters = { buildingId: "ALL", status: "ALL", os: "ALL" };
    const gInput = document.getElementById("global-search-input");
    const iInput = document.getElementById("inventory-search-input");
    const bSelect = document.getElementById("filter-building");
    const sSelect = document.getElementById("filter-status");
    const oSelect = document.getElementById("filter-os");
    if (gInput) gInput.value = "";
    if (iInput) iInput.value = "";
    if (bSelect) bSelect.value = "ALL";
    if (sSelect) sSelect.value = "ALL";
    if (oSelect) oSelect.value = "ALL";
    applyInventoryFilters();
}

// ============================================================================
// MODAL 1: CHANGE SYSTEM LOCATION CONTROLLER (Image 1 Exact Behavior)
// ============================================================================

function openChangeLocationModal(deviceId) {
    const dev = appState.devices.find(d => d.id === deviceId) || appState.devices[0];
    if (!dev) return;

    const modal = document.getElementById("modal-change-location");
    if (!modal) return;

    const nameSpan = document.getElementById("loc-modal-system-name");
    const breadcrumbDiv = document.getElementById("loc-modal-current-breadcrumb");
    const devIdInput = document.getElementById("loc-modal-device-id");
    const reasonInput = document.getElementById("loc-modal-input-reason") || document.getElementById("loc-input-reason");

    if (devIdInput) devIdInput.value = dev.id;
    if (nameSpan) nameSpan.textContent = `${dev.assetId}`;
    if (reasonInput) reasonInput.value = "Shifted to new lab / maintenance replacement";

    // Build Current Location Breadcrumb
    const room = appState.rooms.find(r => r.id === dev.roomId);
    const floor = room ? appState.floors.find(f => f.id === room.floorId) : null;
    const bldg = floor ? appState.buildings.find(b => b.id === floor.buildingId) : null;
    const org = appState.organizations.find(o => o.id === dev.orgId);

    if (breadcrumbDiv) {
        breadcrumbDiv.innerHTML = `
            <span class="font-bold text-slate-900">${dev.assetId}</span> &bull;
            <span>${org ? org.name : 'Campus'}</span> &gt;
            <span>${bldg ? bldg.name : 'Unknown Bldg'}</span> &gt;
            <span>${floor ? floor.name : 'Unknown Floor'}</span> &gt;
            <span class="font-bold text-indigo-700">${room ? room.name : 'Unassigned Room'}</span>
        `;
    }

    // Populate Org & Building Dropdowns (support both ID conventions)
    const orgSelect = document.getElementById("loc-modal-select-org");
    if (orgSelect) {
        orgSelect.value = dev.orgId || "UNI";
    }

    const bldgSelect = document.getElementById("loc-modal-select-bldg") || document.getElementById("loc-modal-select-building") || document.getElementById("loc-select-building");
    if (bldgSelect) {
        const targetOrgId = orgSelect ? orgSelect.value : dev.orgId;
        let targetBldgs = appState.buildings.filter(b => b.orgId === targetOrgId);
        if (targetBldgs.length === 0) targetBldgs = appState.buildings;

        bldgSelect.innerHTML = `<option value="">Select Building</option>` + targetBldgs.map(b => `
            <option value="${b.id}" ${bldg && bldg.id === b.id ? 'selected' : ''}>${b.name}</option>
        `).join('');

        // Trigger cascading updates
        handleLocBuildingChange();
    }

    // Render Location History Table (Section 8)
    renderLocationHistoryTableForModal(dev.id);

    modal.classList.remove("hidden");
    lucide.createIcons();
}

function handleLocModalOrgChange() {
    const orgSelect = document.getElementById("loc-modal-select-org");
    const bldgSelect = document.getElementById("loc-modal-select-bldg") || document.getElementById("loc-modal-select-building") || document.getElementById("loc-select-building");
    if (!orgSelect || !bldgSelect) return;
    const orgId = orgSelect.value;
    const bldgs = appState.buildings.filter(b => b.orgId === orgId);
    bldgSelect.innerHTML = `<option value="">Select Building</option>` + bldgs.map(b => `
        <option value="${b.id}">${b.name}</option>
    `).join('');
    if (bldgs.length > 0) {
        bldgSelect.selectedIndex = 1;
        handleLocBuildingChange();
    }
}

function handleLocModalBldgChange() {
    handleLocBuildingChange();
}

function handleLocModalFloorChange() {
    handleLocFloorChange();
}

function handleLocBuildingChange() {
    const bldgSelect = document.getElementById("loc-modal-select-bldg") || document.getElementById("loc-modal-select-building") || document.getElementById("loc-select-building");
    const floorSelect = document.getElementById("loc-modal-select-floor") || document.getElementById("loc-select-floor");
    const roomSelect = document.getElementById("loc-modal-select-room") || document.getElementById("loc-select-room");

    if (!bldgSelect || !floorSelect) return;
    const bldgId = bldgSelect.value;
    const floors = appState.floors.filter(f => f.buildingId === bldgId);

    floorSelect.innerHTML = `<option value="">Select Floor</option>` + floors.map(f => `
        <option value="${f.id}">${f.name}</option>
    `).join('');

    if (roomSelect) {
        roomSelect.innerHTML = `<option value="">Select Room / Lab</option>`;
    }

    if (floors.length > 0) {
        floorSelect.selectedIndex = 1;
        handleLocFloorChange();
    }
}

function handleLocFloorChange() {
    const floorSelect = document.getElementById("loc-modal-select-floor") || document.getElementById("loc-select-floor");
    const roomSelect = document.getElementById("loc-modal-select-room") || document.getElementById("loc-select-room");

    if (!floorSelect || !roomSelect) return;
    const floorId = floorSelect.value;
    const rooms = appState.rooms.filter(r => r.floorId === floorId);

    roomSelect.innerHTML = `<option value="">Select Room / Lab</option>` + rooms.map(r => `
        <option value="${r.id}">${r.name} (${r.type})</option>
    `).join('');

    if (rooms.length > 0) {
        roomSelect.selectedIndex = 1;
    }
}

function submitLocationChange(e) {
    if (e && e.preventDefault) e.preventDefault();
    submitChangeLocation(e);
}

function submitChangeLocation(e) {
    if (e && e.preventDefault) e.preventDefault();
    const devIdInput = document.getElementById("loc-modal-device-id");
    const devId = devIdInput ? devIdInput.value : null;
    const roomSelect = document.getElementById("loc-modal-select-room") || document.getElementById("loc-select-room");
    const targetRoomId = roomSelect ? roomSelect.value : null;
    const reasonInput = document.getElementById("loc-modal-input-reason") || document.getElementById("loc-input-reason");
    const reason = reasonInput ? reasonInput.value.trim() : "";

    if (!targetRoomId) {
        showToast("Please select a target Building, Floor, and Room/Lab.", "error");
        return;
    }
    if (!reason) {
        showToast("Please provide a reason for relocating the device.", "error");
        return;
    }

    const dev = appState.devices.find(d => d.id === devId);
    if (!dev) {
        showToast("Device not found.", "error");
        return;
    }

    // Get Old Location Description
    const oldRoom = appState.rooms.find(r => r.id === dev.roomId);
    const oldFloor = oldRoom ? appState.floors.find(f => f.id === oldRoom.floorId) : null;
    const oldBldg = oldFloor ? appState.buildings.find(b => b.id === oldFloor.buildingId) : null;
    const fromLocStr = `${oldBldg ? oldBldg.code || oldBldg.name : 'Old'} / ${oldFloor ? oldFloor.name : ''} / ${oldRoom ? oldRoom.name : ''}`;

    // Get New Location Description
    const newRoom = appState.rooms.find(r => r.id === targetRoomId);
    const newFloor = newRoom ? appState.floors.find(f => f.id === newRoom.floorId) : null;
    const newBldg = newFloor ? appState.buildings.find(b => b.id === newFloor.buildingId) : null;
    const toLocStr = `${newBldg ? newBldg.code || newBldg.name : 'New'} / ${newFloor ? newFloor.name : ''} / ${newRoom ? newRoom.name : ''}`;

    // Update Device Location
    dev.roomId = targetRoomId;

    // Insert Location History Record (Section 8)
    const today = new Date();
    const dateFormatted = `${String(today.getDate()).padStart(2, '0')}-${today.toLocaleString('default', { month: 'short' })}-${today.getFullYear()}`;

    appState.locationHistories.unshift({
        id: "lh-" + Date.now(),
        deviceId: dev.id,
        changedDate: dateFormatted,
        fromLocation: fromLocStr,
        toLocation: toLocStr,
        changedBy: "IT Admin Desk",
        reason: reason
    });

    saveAppState();
    renderAll();
    closeChangeLocationModal();
    showToast(`Device ${dev.assetId} relocated to ${newRoom ? newRoom.name : 'new room'}! Logged in history.`, "success");
}

function renderLocationHistoryTableForModal(deviceId) {
    const tbody = document.getElementById("loc-modal-history-tbody");
    if (!tbody) return;

    const histories = appState.locationHistories.filter(h => h.deviceId === deviceId);
    if (histories.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="py-3 text-center text-slate-400">No previous relocation records.</td></tr>`;
        return;
    }

    tbody.innerHTML = histories.map(h => `
        <tr>
            <td class="py-2 px-3 font-medium text-slate-600">${h.changedDate}</td>
            <td class="py-2 px-3 font-semibold text-slate-800">${h.fromLocation}</td>
            <td class="py-2 px-3 font-bold text-blue-700">${h.toLocation}</td>
            <td class="py-2 px-3 text-slate-600 font-mono">${h.changedBy}</td>
            <td class="py-2 px-3 text-slate-600">${h.reason}</td>
        </tr>
    `).join('');
}

function closeChangeLocationModal() {
    const modal = document.getElementById("modal-change-location");
    if (modal) modal.classList.add("hidden");
}

// ============================================================================
// MODAL 2: SEARCH USER - POPUP DETAILS (Image 2 Exact Behavior)
// ============================================================================

let currentPopupUser = null;

function openSearchUserModal(empIdOrQuery = "EMP-00125") {
    const modal = document.getElementById("modal-search-user");
    const searchInput = document.getElementById("user-popup-search-input");
    if (searchInput) searchInput.value = empIdOrQuery;

    executeUserPopupSearch();
    modal.classList.remove("hidden");
    lucide.createIcons();
}

function handleUserPopupSearchKey(e) {
    if (e.key === "Enter") {
        executeUserPopupSearch();
    }
}

function executeUserPopupSearch() {
    const q = document.getElementById("user-popup-search-input").value.trim().toLowerCase();

    // Find User matching Query or fallback to Sahil Rathod
    let user = appState.users.find(u =>
        u.empId.toLowerCase().includes(q) ||
        u.fullName.toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q)
    );

    if (!user) {
        user = appState.users[0]; // Sahil Rathod default
    }

    currentPopupUser = user;
    populateUserPopup(user);
}

function getUserInitials(name) {
    if (!name) return "U";
    const clean = name.replace(/^Prof\.\s+|^Dr\.\s+/i, '').trim();
    const parts = clean.split(/\s+/);
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

let currentPopupDeviceId = null;

function populateUserPopup(user) {
    const assignedDev = appState.devices.find(d => d.assignedUserId === user.id) || appState.devices[0];
    currentPopupDeviceId = assignedDev ? assignedDev.id : null;
    populateUserPopupWithDevice(user, assignedDev);
}

function populateUserPopupWithDevice(user, assignedDev) {
    const assignedName = assignedDev ? (assignedDev.assignedUserName || assignedDev.assigned_user_name || "") : "";
    const assignedDesig = assignedDev ? (assignedDev.designation || assignedDev.assignedDesignation || assignedDev.assigned_designation || "") : "";
    const assignedEmp = assignedDev ? (assignedDev.empId || assignedDev.assigned_emp_id || "") : "";

    const isCustomStaff = (!user || !user.id || user.empId === "UNASSIGNED") && assignedName && assignedName.toLowerCase() !== "unassigned" && !assignedName.toLowerCase().startsWith("unassigned");
    const isUnassigned = !isCustomStaff && (!user || !user.id || user.empId === "UNASSIGNED");

    // User Profile Card Fields
    const initialsEl = document.getElementById("user-popup-initials");
    if (initialsEl) initialsEl.textContent = isUnassigned ? "SP" : getUserInitials(isCustomStaff ? assignedName : (user ? user.fullName : assignedName));

    const empEl = document.getElementById("user-popup-empid");
    if (empEl) empEl.textContent = isUnassigned ? "— (Ready for Deployment)" : (isCustomStaff ? (assignedEmp || "STAFF") : (user ? user.empId : assignedEmp));
    const fnEl = document.getElementById("user-popup-fullname");
    if (fnEl) fnEl.textContent = isUnassigned ? "Unassigned Hardware Pool (Spare)" : (isCustomStaff ? assignedName : (user ? user.fullName : assignedName));
    const deptEl = document.getElementById("user-popup-department");
    if (deptEl) deptEl.textContent = isUnassigned ? "IT Spares & Inventory Storage" : (isCustomStaff ? (assignedDev ? (assignedDev.roomName || "Clinical Wing") : "PSM Hospital") : (user ? user.department : "Hospital Staff"));
    const desEl = document.getElementById("user-popup-designation");
    if (desEl) desEl.textContent = isUnassigned ? "Spare System" : (assignedDesig || (user ? user.designation : "") || "Assigned Custodian");
    const emEl = document.getElementById("user-popup-email");
    if (emEl) emEl.textContent = isUnassigned ? "it-desk@campus.edu" : (isCustomStaff ? `${assignedName.toLowerCase().replace(/\s+/g, '.')}@hospital.org` : (user ? user.email : "staff@hospital.org"));
    const phEl = document.getElementById("user-popup-phone");
    if (phEl) phEl.textContent = isUnassigned ? "Helpdesk Ext. 101" : ((user && user.phone) ? user.phone : "Clinical Ext. 204");
    const stEl = document.getElementById("user-popup-status");
    if (stEl) {
        if (isUnassigned) {
            stEl.className = "px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300";
            stEl.textContent = assignedDev ? assignedDev.status : "Spare Pool";
        } else {
            stEl.className = "px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300";
            stEl.textContent = (user && user.status) ? user.status : "Active Custodian";
        }
    }

    if (!assignedDev) return;

    // Assigned System Specs Card
    const aId = document.getElementById("user-popup-assetid");
    if (aId) aId.textContent = assignedDev.assetId;
    const sName = document.getElementById("user-popup-sysname");
    if (sName) sName.textContent = assignedDev.assetId;
    const os = document.getElementById("user-popup-os");
    if (os) os.textContent = assignedDev.operatingSystem;
    const cpu = document.getElementById("user-popup-cpu");
    if (cpu) cpu.textContent = assignedDev.cpuProcessor;
    const ram = document.getElementById("user-popup-ram");
    if (ram) ram.textContent = assignedDev.storageRam;
    const ip = document.getElementById("user-popup-ip");
    if (ip) ip.textContent = assignedDev.ipAddress || '—';
    const mac = document.getElementById("user-popup-mac");
    if (mac) mac.textContent = assignedDev.macAddress || '—';
    const serial = document.getElementById("user-popup-serial");
    if (serial) serial.textContent = assignedDev.serialNumber;
    const purchase = document.getElementById("user-popup-purchase");
    if (purchase) purchase.textContent = assignedDev.purchaseDate || '—';
    const warranty = document.getElementById("user-popup-warranty");
    if (warranty) warranty.textContent = assignedDev.warrantyExpiryDate || '—';
    const sysstatus = document.getElementById("user-popup-sysstatus");
    if (sysstatus) sysstatus.textContent = assignedDev.status;

    // Current Location Card
    const room = appState.rooms.find(r => r.id === assignedDev.roomId);
    const floor = room ? appState.floors.find(f => f.id === room.floorId) : null;
    const bldg = floor ? appState.buildings.find(b => b.id === floor.buildingId) : null;
    const org = appState.organizations.find(o => o.id === assignedDev.orgId);

    const locOrg = document.getElementById("user-popup-loc-org");
    if (locOrg) locOrg.textContent = org ? org.name : 'Campus';
    const locBldg = document.getElementById("user-popup-loc-bldg");
    if (locBldg) locBldg.textContent = bldg ? bldg.name : '—';
    const locFloor = document.getElementById("user-popup-loc-floor");
    if (locFloor) locFloor.textContent = floor ? floor.name : '—';
    const locRoom = document.getElementById("user-popup-loc-room");
    if (locRoom) locRoom.textContent = room ? room.name : '—';

    // Populate Assignment History Table (Section 9)
    const tbody = document.getElementById("user-popup-assignment-tbody");
    if (tbody) {
        const assignments = appState.assignmentHistories.filter(ah =>
            ah.deviceId === assignedDev.id ||

            (!isUnassigned && user.id && ah.userId === user.id)
        );

        if (assignments.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="py-3 text-center text-slate-400">No previous assignment records for this system.</td></tr>`;
        } else {
            tbody.innerHTML = assignments.map(ah => `
                <tr>
                    <td class="py-2 px-3 font-semibold text-slate-700">${ah.fromDate}</td>
                    <td class="py-2 px-3 font-bold ${ah.toDate === '-' ? 'text-emerald-700' : 'text-slate-600'}">${ah.toDate}</td>
                    <td class="py-2 px-3 font-bold font-mono text-indigo-700">${ah.assetId || assignedDev.assetId}</td>
                    <td class="py-2 px-3 text-slate-700">${ah.location}</td>
                    <td class="py-2 px-3 text-slate-600">${ah.assignedBy}</td>
                    <td class="py-2 px-3 text-slate-500">${ah.remarks || '—'}</td>
                </tr>
            `).join('');
        }
    }
}

function triggerChangeLocationFromUserPopup() {
    let targetDeviceId = currentPopupDeviceId;
    if (!targetDeviceId && currentPopupUser && currentPopupUser.id) {
        const assignedDev = appState.devices.find(d => d.assignedUserId === currentPopupUser.id);
        if (assignedDev) targetDeviceId = assignedDev.id;
    }
    if (!targetDeviceId && appState.devices.length > 0) {
        targetDeviceId = appState.devices[0].id;
    }
    closeSearchUserModal();
    if (targetDeviceId) {
        openChangeLocationModal(targetDeviceId);
    }
}

function closeSearchUserModal() {
    const modal = document.getElementById("modal-search-user");
    if (modal) modal.classList.add("hidden");
    currentPopupDeviceId = null;
}

// ============================================================================
// MODAL 3: ADD / EDIT DEVICE CONTROLLER
// ============================================================================

function getFloorTagInfo(floorId) {
    if (!floorId) return { floorCode: "GF", numBase: "001" };
    const f = (appState.floors || []).find(fl => fl.id === floorId);
    if (!f) return { floorCode: "GF", numBase: "001" };
    if (f.number === -1 || f.id.includes("basement") || f.id.includes("b1")) return { floorCode: "B", numBase: "0.01" };
    if (f.number === 0 || f.id.includes("gf")) return { floorCode: "GF", numBase: "001" };
    if (f.number === 1 || f.id.includes("1")) return { floorCode: "1F", numBase: "101" };
    if (f.number === 2 || f.id.includes("2")) return { floorCode: "2F", numBase: "201" };
    if (f.number === 3 || f.id.includes("3")) return { floorCode: "3F", numBase: "301" };
    if (f.number === 4 || f.id.includes("4")) return { floorCode: "4F", numBase: "401" };
    if (f.number === 5 || f.id.includes("5")) return { floorCode: "5F", numBase: "501" };
    return { floorCode: "GF", numBase: "001" };
}

function calculateNextAssetTag(typeCode, floorId) {
    const now = new Date();
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const yy = String(now.getFullYear()).slice(-2);
    const mmyy = `${mm}${yy}`; // e.g. "0926"

    const prefix = `PSM/IT/${mmyy}/`;
    const monthPattern = `/${mmyy}/`;

    // Ensure XXX is globally unique for every device registered in this month
    const allMonthTags = (appState.devices || [])
        .map(d => (d.assetId || '').trim())
        .filter(tag => tag.toUpperCase().includes(monthPattern));

    let maxNum = 0;
    allMonthTags.forEach(tag => {
        const parts = tag.split('/');
        const seqStr = parts.length >= 4 ? parts[parts.length - 1] : null;
        if (seqStr) {
            const num = parseInt(seqStr, 10);
            if (!isNaN(num) && num > maxNum) {
                maxNum = num;
            }
        }
    });

    let nextNum = maxNum + 1;
    const allExisting = (appState.devices || []).map(d => (d.assetId || '').trim().toUpperCase());
    while (allExisting.includes(`${prefix}${String(nextNum).padStart(3, '0')}`.toUpperCase())) {
        nextNum++;
    }

    return `${prefix}${String(nextNum).padStart(3, '0')}`;
}

function updateAutoAssetTag() {
    const editIdInput = document.getElementById("edit-device-id");
    if (editIdInput && editIdInput.value) return;

    const typeSelect = document.getElementById("dev-select-type");
    const typeCode = typeSelect ? typeSelect.value : 'C';
    const floorSelect = document.getElementById("dev-select-floor");
    const floorId = floorSelect ? floorSelect.value : 'fl-gf';

    const assetInput = document.getElementById("dev-input-assetid");
    if (assetInput) {
        assetInput.value = calculateNextAssetTag(typeCode, floorId);
    }
}

function handleDevTypeChange() {
    updateAutoAssetTag();
    const typeSelect = document.getElementById("dev-select-type");
    const type = typeSelect ? typeSelect.value : 'C';
    const cpuInput = document.getElementById("dev-input-cpu");
    const ramInput = document.getElementById("dev-input-ram");
    const monitorInput = document.getElementById("dev-input-monitor");
    const osSelect = document.getElementById("dev-select-os");

    if (type === 'C') {
        if (cpuInput) cpuInput.value = "Intel Core i7-13700 (16 cores)";
        if (ramInput) ramInput.value = "512GB NVMe SSD / 16GB RAM";
        if (monitorInput) monitorInput.value = 'Dell 24" UltraSharp FHD';
        if (osSelect) osSelect.value = "Windows 11 Pro";
    } else if (type === 'M') {
        if (cpuInput) cpuInput.value = "Antimicrobial Optical Sensor (1200 DPI)";
        if (ramInput) ramInput.value = "USB Cleanable Clinic Mouse";
        if (monitorInput) monitorInput.value = "N/A - Peripherals";
        if (osSelect) osSelect.value = "Hardware Peripheral (HID)";
    } else if (type === 'K') {
        if (cpuInput) cpuInput.value = "Silicone Sealed Membrane Keyboard";
        if (ramInput) ramInput.value = "USB Disinfectable Hospital Keyboard";
        if (monitorInput) monitorInput.value = "N/A - Peripherals";
        if (osSelect) osSelect.value = "Hardware Peripheral (HID)";
    } else if (type === 'D') {
        if (cpuInput) cpuInput.value = "IPS LED Backlit Panel (1920x1080 @ 75Hz)";
        if (ramInput) ramInput.value = "HDMI / DisplayPort / USB-C Connectivity";
        if (monitorInput) monitorInput.value = 'Dell 24" UltraSharp FHD Healthcare Display';
        if (osSelect) osSelect.value = "Display Hardware (Plug & Play)";
    } else if (type === 'P') {
        if (cpuInput) cpuInput.value = "Zebra ZPL-II Thermal Core Processor";
        if (ramInput) ramInput.value = "Direct Thermal 203 DPI Print Engine";
        if (monitorInput) monitorInput.value = "Status LED Indicator Panel";
        if (osSelect) osSelect.value = "Link-OS Enterprise";
    } else if (type === 'T') {
        if (cpuInput) cpuInput.value = "Octa-Core Medical Tablet Processor";
        if (ramInput) ramInput.value = "128GB Storage / 6GB RAM";
        if (monitorInput) monitorInput.value = '10.5" Retina IPS Multi-Touch Clinical Panel';
        if (osSelect) osSelect.value = "Android 14 / iPadOS";
    } else if (type === 'U') {
        if (cpuInput) cpuInput.value = "Line-Interactive Sine Wave Pure Power System";
        if (ramInput) ramInput.value = "1000VA / 600W Battery Backup Unit";
        if (monitorInput) monitorInput.value = "N/A - Power Equipment";
        if (osSelect) osSelect.value = "Embedded Microcontroller";
    }
}

function openAddDeviceModal(editId = null) {
    const modal = document.getElementById("modal-add-device");
    if (!modal) {
        window.location.href = "/inventory/?org=HOSP&openAddModal=true";
        return;
    }
    const form = document.getElementById("add-device-form");
    const title = document.getElementById("device-modal-title");
    if (form) form.reset();

    // Populate Users dropdown
    const userSelect = document.getElementById("dev-select-user");
    if (userSelect) {
        userSelect.innerHTML = `<option value="">-- Unassigned / Hospital Spare --</option>` + (appState.users || []).map(u => `
            <option value="${u.id}">${u.fullName} (${u.empId} - ${u.department})</option>
        `).join('');
    }

    handleDevOrgChange();

    const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.value = val;
    };

    if (editId) {
        if (title) title.textContent = "Edit Hardware Device";
        const editIdInput = document.getElementById("edit-device-id");
        if (editIdInput) editIdInput.value = editId;
        const dev = (appState.devices || []).find(d => d.id === editId);
        if (dev) {
            const typeCode = dev.deviceType || (dev.assetId.includes('/C-') ? 'C' : dev.assetId.includes('/D-') ? 'D' : dev.assetId.includes('/M-') ? 'M' : dev.assetId.includes('/K-') ? 'K' : dev.assetId.includes('/P-') ? 'P' : 'C');
            const typeSelect = document.getElementById("dev-select-type");
            if (typeSelect) typeSelect.value = typeCode;
            setVal("dev-input-assetid", dev.assetId);
            setVal("dev-input-serial", dev.serialNumber);
            setVal("dev-select-org", dev.orgId || "HOSP");
            handleDevOrgChange();
            setVal("dev-input-cpu", dev.cpuProcessor);
            setVal("dev-input-ram", dev.storageRam);
            setVal("dev-input-monitor", dev.monitorSpec);
            setVal("dev-select-os", dev.operatingSystem);
            setVal("dev-input-ip", dev.ipAddress);
            setVal("dev-input-mac", dev.macAddress);
            setVal("dev-select-user", dev.assignedUserId || '');
            // If the saved custodian isn't in the known-staff dropdown, preserve
            // their typed name in the free-text fallback field instead of losing it.
            const knownUserMatch = (appState.users || []).find(u => u.id === dev.assignedUserId);
            const savedName = dev.assignedUserName || dev.assigned_user_name || '';
            if (!dev.assignedUserId && savedName && savedName.toLowerCase() !== 'unassigned') {
                setVal("dev-input-user-name", savedName);
            } else if (dev.assignedUserId && !knownUserMatch && savedName) {
                setVal("dev-input-user-name", savedName);
            } else {
                setVal("dev-input-user-name", "");
            }
            setVal("dev-input-designation", dev.designation || dev.assignedDesignation || dev.assigned_designation || (knownUserMatch ? knownUserMatch.designation : "") || "");
            setVal("dev-input-phone", dev.phone || dev.assignedPhone || dev.assigned_phone || (knownUserMatch ? knownUserMatch.phone : "") || "");
            setVal("dev-input-email", dev.email || dev.assignedEmail || dev.assigned_email || (knownUserMatch ? knownUserMatch.email : "") || "");
            setVal("dev-select-status", dev.status);
            setVal("dev-input-warranty", dev.warrantyExpiryDate);
        }
    } else {
        if (title) title.textContent = "Register New Hardware Device";
        const editIdInput = document.getElementById("edit-device-id");
        if (editIdInput) editIdInput.value = "";
        const userSelectEl = document.getElementById("dev-select-user");
        if (userSelectEl) userSelectEl.value = "";
        setVal("dev-input-user-name", "");
        setVal("dev-input-designation", "");
        setVal("dev-input-phone", "");
        setVal("dev-input-email", "");
        const typeSelect = document.getElementById("dev-select-type");
        if (typeSelect) typeSelect.value = "C";

        // Auto-generate Asset ID & initial specs according to PSM/IT/B/<TYPE>-<NUM>
        const floorSelect = document.getElementById("dev-select-floor");
        const activeFloorId = floorSelect ? floorSelect.value : "fl-gf";
        const generatedTag = calculateNextAssetTag("C", activeFloorId);
        const randomNum = String(Math.floor(100 + Math.random() * 900));

        setVal("dev-input-assetid", generatedTag);
        setVal("dev-input-serial", `SN-${Date.now().toString().slice(-8)}`);
        setVal("dev-input-cpu", "Intel Core i7-13700 (16 cores)");
        setVal("dev-input-ram", "512GB NVMe SSD / 16GB RAM");
        setVal("dev-input-monitor", 'Dell 24" UltraSharp FHD');
        setVal("dev-input-ip", `10.20.10.${Math.floor(10 + Math.random() * 200)}`);
        setVal("dev-input-mac", `B4-2E-99-${randomNum.slice(0, 2)}-${randomNum.slice(1, 3)}-FA`);
        setVal("dev-input-warranty", "14-Jan-2028");
    }

    modal.classList.remove("hidden");
    if (window.lucide) lucide.createIcons();
}

function handleDevOrgChange() {
    const orgSelect = document.getElementById("dev-select-org");
    const orgCode = orgSelect ? orgSelect.value : "HOSP";
    const bldgSelect = document.getElementById("dev-select-bldg");
    if (!bldgSelect) return;
    const bldgs = (appState.buildings || []).filter(b => b.orgId === orgCode);

    bldgSelect.innerHTML = `<option value="">Select Building</option>` + bldgs.map(b => `
        <option value="${b.id}">${b.name}</option>
    `).join('');

    if (bldgs.length > 0) {
        bldgSelect.selectedIndex = 1;
        handleDevBldgChange();
    }
}

function handleDevBldgChange() {
    const bldgSelect = document.getElementById("dev-select-bldg");
    const bldgId = bldgSelect ? bldgSelect.value : "";
    const floorSelect = document.getElementById("dev-select-floor");
    if (!floorSelect) return;
    const floors = (appState.floors || []).filter(f => f.buildingId === bldgId);

    floorSelect.innerHTML = `<option value="">Select Floor</option>` + floors.map(f => `
        <option value="${f.id}">${f.name}</option>
    `).join('');

    if (floors.length > 0) {
        floorSelect.selectedIndex = 1;
        handleDevFloorChange();
    }
}

function handleDevFloorChange() {
    const floorSelect = document.getElementById("dev-select-floor");
    const floorId = floorSelect ? floorSelect.value : "";
    const roomSelect = document.getElementById("dev-select-room");
    if (roomSelect) {
        const rooms = (appState.rooms || []).filter(r => r.floorId === floorId);
        roomSelect.innerHTML = `<option value="">Select Room / Lab</option>` + rooms.map(r => `
            <option value="${r.id}">${r.name}</option>
        `).join('');

        if (rooms.length > 0) {
            roomSelect.selectedIndex = 1;
        }
    }
    updateAutoAssetTag();
}

async function handleSaveDevice(e) {
    e.preventDefault();
    const getVal = (id, def = "") => {
        const el = document.getElementById(id);
        return el ? el.value : def;
    };

    const editId = getVal("edit-device-id");
    const assetId = getVal("dev-input-assetid").trim().toUpperCase();
    const serialNumber = getVal("dev-input-serial").trim().toUpperCase();
    const orgId = getVal("dev-select-org", "HOSP");
    const roomId = getVal("dev-select-room");
    const cpuProcessor = getVal("dev-input-cpu").trim() || "Intel Core i5 (Standard)";
    const storageRam = getVal("dev-input-ram").trim() || "16GB RAM / 512GB SSD";
    const monitorSpec = getVal("dev-input-monitor").trim() || "24\" FHD IPS Display";
    const operatingSystem = getVal("dev-select-os", "Windows 11 Pro");
    const ipAddress = getVal("dev-input-ip").trim();
    const macAddress = getVal("dev-input-mac").trim().toUpperCase();
    const assignedUserId = getVal("dev-select-user") || null;
    const status = getVal("dev-select-status", "Active");
    const warrantyExpiryDate = getVal("dev-input-warranty") || "14-Jan-2028";

    const typeSelect = document.getElementById("dev-select-type");
    const typeCode = typeSelect ? typeSelect.value : 'C';
    const typeFullNames = { 'C': 'CPU', 'D': 'Display', 'M': 'Mouse', 'K': 'Keyboard', 'P': 'Printer', 'L': 'Laptop' };
    const deviceType = typeFullNames[typeCode] || 'CPU';

    // Resolve clean human text for location and user
    const bldgEl = document.getElementById("dev-select-bldg");
    const buildingName = (bldgEl && bldgEl.selectedIndex >= 0 && bldgEl.options[bldgEl.selectedIndex].text !== 'Select')
        ? bldgEl.options[bldgEl.selectedIndex].text.replace(/\s*Main Medical Complex/gi, '').replace(/\s*Main Complex/gi, '').trim()
        : "PSM Hospital";

    const floorEl = document.getElementById("dev-select-floor");
    const floorName = (floorEl && floorEl.selectedIndex >= 0 && floorEl.options[floorEl.selectedIndex].text !== 'Select')
        ? floorEl.options[floorEl.selectedIndex].text
        : "Ground Floor";

    const roomEl = document.getElementById("dev-select-room");
    const roomName = (roomEl && roomEl.selectedIndex >= 0 && roomEl.options[roomEl.selectedIndex].text !== 'Select')
        ? roomEl.options[roomEl.selectedIndex].text
        : "General Facility";

    const userEl = document.getElementById("dev-select-user");
    const typedUserNameEl = document.getElementById("dev-input-user-name");
    const typedUserName = typedUserNameEl ? typedUserNameEl.value.trim() : "";
    let assignedUserName = "Unassigned";
    let assignedEmpId = "";
    if (userEl && userEl.value) {
        // A known staff member was picked from the dropdown — this takes priority.
        const rawText = userEl.options[userEl.selectedIndex].text;
        assignedUserName = rawText.split('(')[0].replace(/--.*--/, '').trim() || "Assigned Staff";
        const empMatch = rawText.match(/\(([^)]+)\)/);
        assignedEmpId = empMatch ? empMatch[1] : "";
    } else if (typedUserName) {
        // No dropdown selection — fall back to the free-text name field.
        assignedUserName = typedUserName;
    }

    const typedDesigEl = document.getElementById("dev-input-designation");
    let assignedDesignation = typedDesigEl ? typedDesigEl.value.trim() : "";
    const typedPhoneEl = document.getElementById("dev-input-phone");
    let assignedPhone = typedPhoneEl ? typedPhoneEl.value.trim() : "";
    const typedEmailEl = document.getElementById("dev-input-email");
    let assignedEmail = typedEmailEl ? typedEmailEl.value.trim() : "";

    if (userEl && userEl.value) {
        const matchedUser = (appState.users || []).find(u => u.id === userEl.value);
        if (matchedUser) {
            if (!assignedDesignation && matchedUser.designation) {
                assignedDesignation = matchedUser.designation;
            }
            if (!assignedPhone && matchedUser.phone) {
                assignedPhone = matchedUser.phone;
            }
            if (!assignedEmail && matchedUser.email) {
                assignedEmail = matchedUser.email;
            }
        }
    }

    const today = new Date();
    const purchaseDate = `${String(today.getDate()).padStart(2, '0')}-${today.toLocaleString('default', { month: 'short' })}-${today.getFullYear()}`;

    // Payload for central PostgreSQL database and Asset Tag Center
    const payload = {
        assetId,
        deviceType,
        serialNumber,
        orgId,
        orgName: orgId === 'HOSP' ? 'PSM Hospital' : 'Swaminarayan University',
        buildingName,
        floorName,
        roomName,
        roomId,
        assignedUserId,
        assignedUserName,
        assignedEmpId,
        assignedDesignation,
        designation: assignedDesignation,
        assignedPhone,
        phone: assignedPhone,
        assignedEmail,
        email: assignedEmail,
        cpuProcessor,
        storageRam,
        monitorSpec,
        operatingSystem,
        ipAddress,
        macAddress,
        status,
        purchaseDate,
        warrantyExpiryDate
    };

    // 1. Immediately update client-side appState so UI responds with 0 latency
    if (editId) {
        const dev = appState.devices.find(d => d.id === editId || d.assetId === assetId);
        if (dev) {
            Object.assign(dev, payload);
        }
        showToast(`Hardware device ${assetId} updated successfully!`, "success");
    } else {
        const newDevice = Object.assign({ id: "dev-" + Date.now() }, payload);
        // Put right at index 0 (top of the list)
        appState.devices.unshift(newDevice);

        if (assignedUserId) {
            appState.assignmentHistories.unshift({
                id: "ah-" + Date.now(),
                deviceId: newDevice.id,
                deviceAssetId: newDevice.assetId,
                userId: assignedUserId,
                fromUserName: "Initial Provisioning",
                toUserName: assignedUserName,
                fromDate: purchaseDate,
                toDate: "-",
                location: `${floorName} • ${roomName}`,
                assignedBy: "Admin Desk",
                remarks: "Initial hardware provisioning"
            });
        }
        showToast(`New hardware ${assetId} registered & added to Asset Tag Center!`, "success");
    }

    saveAppState();
    renderAll();
    closeAddDeviceModal();

    // 2. Persist to PostgreSQL database in the background
    try {
        const resp = await fetch('/api/devices/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(payload)
        });
        if (resp.ok) {
            const data = await resp.json();
            if (data.success) {
                if (data.devices && data.devices.length > 1) {
                    // Replace temporary single device with all returned workstation component items
                    appState.devices = (appState.devices || []).filter(d => d.id !== (editId || (typeof newDevice !== 'undefined' ? newDevice.id : '')));
                    data.devices.forEach(devItem => {
                        if (!appState.devices.some(existing => existing.id === devItem.id)) {
                            appState.devices.unshift(devItem);
                        }
                    });
                    saveAppState();
                    renderAll();
                } else if (data.device) {
                    const target = appState.devices.find(d => d.id === (editId || data.device.id) || d.assetId === assetId);
                    if (target) {
                        target.id = data.device.id;
                        Object.assign(target, data.device);
                        saveAppState();
                    }
                }
            }
        }
    } catch (apiErr) {
        console.warn("Database sync notice:", apiErr);
    }

    // 3. Immediately re-render Asset Tag Cards if present on this page
    if (typeof renderStickerCards === 'function') {
        const filterFn = (typeof getFilteredDevices === 'function') ? getFilteredDevices : () => appState.devices;
        renderStickerCards(filterFn());
    }
}

function closeAddDeviceModal() {
    const modal = document.getElementById("modal-add-device");
    if (modal) modal.classList.add("hidden");
}

// ============================================================================
// MODAL 4: REASSIGN RESPONSIBILITY CONTROLLER
// ============================================================================

function openReassignModal(deviceId) {
    const dev = appState.devices.find(d => d.id === deviceId);
    if (!dev) return;

    const modal = document.getElementById("modal-reassign");
    if (!modal) return;

    const idInput = document.getElementById("reassign-device-id");
    if (idInput) idInput.value = dev.id;

    const nameEl = document.getElementById("reassign-modal-device-name");
    if (nameEl) nameEl.textContent = `${dev.assetId}`;

    const currUser = appState.users.find(u => u.id === dev.assignedUserId);
    const currUserEl = document.getElementById("reassign-modal-curr-user");
    if (currUserEl) {
        currUserEl.textContent = currUser ? `${currUser.fullName} (${currUser.empId} - ${currUser.department})` : "Currently Unassigned (IT Spare Pool)";
    }

    // Set today's date in input
    const today = new Date().toISOString().split('T')[0];
    const dateInput = document.getElementById("reassign-input-date");
    if (dateInput) dateInput.value = today;

    // Populate New User Dropdown: include option to unassign back to spare pool!
    const select = document.getElementById("reassign-select-newuser");
    if (select) {
        let optionsHtml = `<option value="">-- Select New Assignee --</option>`;
        optionsHtml += `<option value="__UNASSIGN__">📦 Return to IT Spare Pool (Unassign System)</option>`;

        const sameOrgUsers = appState.users.filter(u => u.orgId === dev.orgId);
        const otherOrgUsers = appState.users.filter(u => u.orgId !== dev.orgId);

        if (sameOrgUsers.length > 0) {
            optionsHtml += `<optgroup label="Staff in ${dev.orgId === 'HOSP' ? 'PSM Hospital' : 'Swaminarayan University'}">`;
            optionsHtml += sameOrgUsers.map(u => `
                <option value="${u.id}" ${dev.assignedUserId === u.id ? 'disabled' : ''}>
                    ${u.fullName} (${u.empId} - ${u.department}) ${dev.assignedUserId === u.id ? '— [Current Custodian]' : ''}
                </option>
            `).join('');
            optionsHtml += `</optgroup>`;
        }

        if (otherOrgUsers.length > 0) {
            optionsHtml += `<optgroup label="Other Campus Staff">`;
            optionsHtml += otherOrgUsers.map(u => `
                <option value="${u.id}">
                    ${u.fullName} (${u.empId} - ${u.department})
                </option>
            `).join('');
            optionsHtml += `</optgroup>`;
        }

        select.innerHTML = optionsHtml;
    }

    modal.classList.remove("hidden");
    lucide.createIcons();
}

function submitReassignUser(e) {
    if (e && e.preventDefault) e.preventDefault();
    const devIdInput = document.getElementById("reassign-device-id");
    const devId = devIdInput ? devIdInput.value : null;
    const select = document.getElementById("reassign-select-newuser");
    const newUserId = select ? select.value : "";
    const dateInput = document.getElementById("reassign-input-date");
    const handoverDate = dateInput ? dateInput.value : new Date().toISOString().split('T')[0];
    const remarksInput = document.getElementById("reassign-input-remarks");
    const remarks = remarksInput ? remarksInput.value.trim() : "";

    const dev = appState.devices.find(d => d.id === devId);
    if (!dev) {
        showToast("Device not found.", "error");
        return;
    }

    if (!newUserId) {
        showToast("Please select a new assignee or return to spare pool.", "error");
        return;
    }

    // Close old active assignment history
    const oldAh = appState.assignmentHistories.find(ah => ah.deviceId === dev.id && (ah.toDate === "-" || !ah.toDate));
    if (oldAh) {
        oldAh.toDate = handoverDate;
    }

    const room = appState.rooms.find(r => r.id === dev.roomId);
    const locName = room ? room.name : "Campus Lab";

    if (newUserId === "__UNASSIGN__") {
        const prevUser = appState.users.find(u => u.id === dev.assignedUserId);
        dev.assignedUserId = null;

        appState.assignmentHistories.unshift({
            id: "ah-" + Date.now(),
            deviceId: dev.id,
            userId: null,
            fromDate: handoverDate,
            toDate: "-",
            location: locName,
            assignedBy: "IT Admin Desk",
            remarks: remarks || `Returned to IT Spares from ${prevUser ? prevUser.fullName : 'Staff'}`
        });

        // Sync with central Django SQLite database
        fetch('/api/devices/reassign/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                deviceId: dev.assetId || dev.id,
                newUserId: '__UNASSIGN__',
                newUserName: 'Unassigned',
                newEmpId: '',
                handoverDate: handoverDate,
                remarks: remarks
            })
        }).catch(err => console.warn('Reassign sync error:', err));

        saveAppState();
        renderAll();
        closeReassignModal();
        showToast(`Device ${dev.assetId} returned to Unassigned Spare Pool.`, "info");
        return;
    }

    const newUser = appState.users.find(u => u.id === newUserId);
    if (!newUser) {
        showToast("Please select a valid new assignee.", "error");
        return;
    }

    // Update active user
    dev.assignedUserId = newUser.id;

    // Add new assignment history
    appState.assignmentHistories.unshift({
        id: "ah-" + Date.now(),
        deviceId: dev.id,
        userId: newUser.id,
        fromDate: handoverDate,
        toDate: "-",
        location: locName,
        assignedBy: "IT Admin Desk",
        remarks: remarks || `Custody handover to ${newUser.fullName}`
    });

    // Sync with central Django SQLite database
    fetch('/api/devices/reassign/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            deviceId: dev.assetId || dev.id,
            newUserId: newUser.id,
            newUserName: newUser.fullName,
            newEmpId: newUser.empId || '',
            handoverDate: handoverDate,
            remarks: remarks
        })
    }).catch(err => console.warn('Reassign sync error:', err));

    saveAppState();
    renderAll();
    closeReassignModal();
    showToast(`Custody of ${dev.assetId} transferred to ${newUser.fullName}!`, "success");
}

function closeReassignModal() {
    const modal = document.getElementById("modal-reassign");
    if (modal) modal.classList.add("hidden");
}

// ============================================================================
// MODAL 5: LOGIN / SESSION HISTORY CONTROLLER
// ============================================================================

function openLoginHistoryModal() {
    if (currentPopupDeviceId) {
        openLoginHistory(currentPopupDeviceId);
    } else if (currentPopupUser && currentPopupUser.id) {
        const assignedDev = appState.devices.find(d => d.assignedUserId === currentPopupUser.id) || appState.devices[0];
        if (assignedDev) openLoginHistory(assignedDev.id);
    } else if (appState.devices.length > 0) {
        openLoginHistory(appState.devices[0].id);
    }
}

function openLoginHistoryForCurrentUser() {
    openLoginHistoryModal();
}

function openLoginHistoryForFirstDevice() {
    const dev = appState.devices[0];
    if (dev) openLoginHistory(dev.id);
}

function openChangeLocationForFirstDevice() {
    const dev = appState.devices[0];
    if (dev) openChangeLocationModal(dev.id);
}

function openReassignForFirstDevice() {
    const dev = appState.devices[0];
    if (dev) openReassignModal(dev.id);
}

function openLoginHistory(deviceId) {
    const dev = appState.devices.find(d => d.id === deviceId) || appState.devices[0];
    if (!dev) return;

    const modal = document.getElementById("modal-login-history");
    const titleSpan = document.getElementById("login-modal-sysname");
    const tbody = document.getElementById("login-history-tbody") || document.getElementById("login-history-table-body");

    if (titleSpan) titleSpan.textContent = `${dev.assetId}`;

    if (tbody) {
        const sessions = appState.loginSessions.filter(ls => ls.deviceId === dev.id);
        if (sessions.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="py-3 text-center text-slate-400">No active login sessions recorded for this system.</td></tr>`;
        } else {
            tbody.innerHTML = sessions.map(s => `
                <tr>
                    <td class="py-2.5 px-3 font-semibold text-slate-800">${s.loginTime}</td>
                    <td class="py-2.5 px-3 font-medium text-slate-600">${s.logoutTime}</td>
                    <td class="py-2.5 px-3 font-bold text-indigo-700">${s.userName}</td>
                    <td class="py-2.5 px-3 font-mono text-slate-600">${s.ipAddress}</td>
                    <td class="py-2.5 px-3 font-mono">${s.duration}</td>
                    <td class="py-2.5 px-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${s.status === 'Online' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}">${s.status}</span></td>
                </tr>
            `).join('');
        }
    }

    if (modal) modal.classList.remove("hidden");
    lucide.createIcons();
}

function closeLoginHistoryModal() {
    const modal = document.getElementById("modal-login-history");
    if (modal) modal.classList.add("hidden");
}

// ============================================================================
// TAB 2: LOCATIONS EXPLORER (PSM Hospital 7-Floor Bird's-Eye Explorer)
// ============================================================================

let locationActiveCampus = "HOSP"; // Exclusively PSM Hospital
let locationActiveBuildingId = "ALL";
let locationActiveFloor = "ALL"; // "ALL" or floor.id e.g. "fl-basement", "fl-gf", "fl-1", "fl-2", etc.
let locationActiveRoomId = "ALL"; // "ALL" or room.id
let locationDeviceStatusFilter = "ALL"; // "ALL", "Active", "In Maintenance"
let locationDeviceSearchQuery = "";

// Floor visual configurations
const FLOOR_THEMES = {
    "fl-basement": {
        badge: "B",
        badgeBg: "bg-slate-800 text-slate-100 border-slate-700",
        accent: "slate",
        icon: "server",
        titleColor: "text-slate-900",
        bannerBg: "bg-gradient-to-r from-slate-900 to-slate-800 text-white"
    },
    "fl-gf": {
        badge: "GF",
        badgeBg: "bg-emerald-700 text-white border-emerald-600",
        accent: "emerald",
        icon: "ambulance",
        titleColor: "text-emerald-950",
        bannerBg: "bg-gradient-to-r from-emerald-950 via-teal-900 to-slate-900 text-white"
    },
    "fl-1": {
        badge: "1F",
        badgeBg: "bg-teal-700 text-white border-teal-600",
        accent: "teal",
        icon: "stethoscope",
        titleColor: "text-teal-950",
        bannerBg: "bg-gradient-to-r from-teal-950 to-slate-900 text-white"
    },
    "fl-2": {
        badge: "2F",
        badgeBg: "bg-rose-700 text-white border-rose-600",
        accent: "rose",
        icon: "heart-pulse",
        titleColor: "text-rose-950",
        bannerBg: "bg-gradient-to-r from-rose-950 via-slate-900 to-slate-900 text-white"
    },
    "fl-3": {
        badge: "3F",
        badgeBg: "bg-indigo-700 text-white border-indigo-600",
        accent: "indigo",
        icon: "scissors",
        titleColor: "text-indigo-950",
        bannerBg: "bg-gradient-to-r from-indigo-950 via-slate-900 to-slate-900 text-white"
    },
    "fl-4": {
        badge: "4F",
        badgeBg: "bg-blue-700 text-white border-blue-600",
        accent: "blue",
        icon: "bed",
        titleColor: "text-blue-950",
        bannerBg: "bg-gradient-to-r from-blue-950 via-slate-900 to-slate-900 text-white"
    },
    "fl-5": {
        badge: "5F",
        badgeBg: "bg-purple-700 text-white border-purple-600",
        accent: "purple",
        icon: "microscope",
        titleColor: "text-purple-950",
        bannerBg: "bg-gradient-to-r from-purple-950 via-slate-900 to-slate-900 text-white"
    }
};

function selectFloorFilter(floorId) {
    locationActiveFloor = floorId;
    locationActiveRoomId = "ALL";
    renderLocationsExplorer();
}

function selectRoomFilter(roomId) {
    locationActiveRoomId = roomId;
    renderFloorSwitcherPills();
    renderLocationBirdEyeView();
}

function selectBuildingFilter(bldgId) {
    locationActiveBuildingId = bldgId;
    locationActiveFloor = "ALL";
    locationActiveRoomId = "ALL";
    renderLocationsExplorer();
}

function switchCampusView(orgId) {
    locationActiveCampus = "HOSP";
    locationActiveBuildingId = "ALL";
    locationActiveFloor = "ALL";
    locationActiveRoomId = "ALL";
    renderLocationsExplorer();
}

function handleLocationDeviceSearch(e) {
    locationDeviceSearchQuery = (e.target.value || "").toLowerCase().trim();
    renderLocationBirdEyeView();
}

function handleLocationDeviceStatusFilter(status) {
    locationDeviceStatusFilter = status;
    ["all", "active", "in-maintenance"].forEach(st => {
        const btn = document.getElementById(`loc-status-btn-${st}`);
        if (btn) {
            const isMatch = (st === "all" && status === "ALL") ||
                (st === "active" && status === "Active") ||
                (st === "in-maintenance" && status === "In Maintenance");
            if (isMatch) {
                btn.className = "px-3 py-1.5 text-xs font-bold rounded-lg bg-slate-900 text-white shadow-2xs cursor-pointer";
            } else {
                btn.className = "px-3 py-1.5 text-xs font-semibold rounded-lg text-slate-600 hover:text-slate-900 hover:bg-white cursor-pointer";
            }
        }
    });
    renderLocationBirdEyeView();
}

function renderLocationsExplorer() {
    locationActiveCampus = "HOSP";
    renderLocationKPIs();
    renderFloorSwitcherPills();
    renderLocationBirdEyeView();
}

function renderLocationKPIs() {
    const campusKpi = document.getElementById("loc-kpi-campuses");
    const roomKpi = document.getElementById("loc-kpi-rooms");
    const devKpi = document.getElementById("loc-kpi-devices");
    const healthKpi = document.getElementById("loc-kpi-health");

    const hospDevices = appState.devices.filter(d => !d.orgId || d.orgId === "HOSP");
    const activeCount = hospDevices.filter(d => d.status === "Active").length;
    const healthPct = hospDevices.length > 0 ? Math.round((activeCount / hospDevices.length) * 100) : 100;

    if (campusKpi) campusKpi.textContent = "PSM Main Complex";
    if (roomKpi) roomKpi.textContent = "7 Facility Levels";
    if (devKpi) devKpi.textContent = `${hospDevices.length} Medical Units`;
    if (healthKpi) healthKpi.textContent = `${healthPct}% Operational`;
}

function renderFloorSwitcherPills() {
    const container = document.getElementById("hospital-floor-switcher");
    if (!container) return;

    const hospDevices = appState.devices.filter(d => !d.orgId || d.orgId === "HOSP");
    const floorsSorted = [...appState.floors].sort((a, b) => a.number - b.number);

    const isAllActive = locationActiveFloor === "ALL";

    let html = `
        <button onclick="selectFloorFilter('ALL')" 
                class="px-3.5 py-2 rounded-xl text-xs shrink-0 transition-all cursor-pointer flex items-center gap-2 border ${isAllActive
            ? 'bg-blue-600 text-white border-blue-600 font-bold shadow-xs'
            : 'bg-white hover:bg-slate-100 text-slate-700 border-slate-200 font-semibold'
        }">
            <i data-lucide="layers" class="w-3.5 h-3.5 ${isAllActive ? 'text-blue-200' : 'text-slate-500'}"></i>
            <span>All Floors (Bird's Eye)</span>
            <span class="px-1.5 py-0.5 rounded-md text-[10px] font-mono ${isAllActive ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-600'}">
                ${hospDevices.length}
            </span>
        </button>
    `;

    floorsSorted.forEach(floor => {
        const isFloorActive = locationActiveFloor === floor.id;
        const theme = FLOOR_THEMES[floor.id] || { badge: floor.code || "FL", icon: "door-open" };

        // Count devices on this floor
        const floorRooms = appState.rooms.filter(r => r.floorId === floor.id);
        const floorDevCount = hospDevices.filter(d => floorRooms.some(r => r.id === d.roomId)).length;

        html += `
            <button onclick="selectFloorFilter('${floor.id}')" 
                    class="px-3.5 py-2 rounded-xl text-xs shrink-0 transition-all cursor-pointer flex items-center gap-2 border ${isFloorActive
                ? 'bg-blue-600 text-white border-blue-600 font-bold shadow-xs'
                : 'bg-white hover:bg-blue-50/70 text-slate-700 border-slate-200 hover:border-blue-300 font-semibold'
            }">
                <span class="px-1.5 py-0.5 rounded text-[10px] font-black font-mono ${isFloorActive ? 'bg-white text-blue-800' : 'bg-blue-100 text-blue-800'}">
                    ${theme.badge}
                </span>
                <span>${floor.shortName || floor.name}</span>
                <span class="px-1.5 py-0.5 rounded-md text-[10px] font-mono ${isFloorActive ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-600'}">
                    ${floorDevCount}
                </span>
            </button>
        `;
    });

    container.innerHTML = html;
    lucide.createIcons();
}

function renderLocationBirdEyeView() {
    const container = document.getElementById("location-birdseye-container");
    const breadcrumbEl = document.getElementById("loc-current-breadcrumb");
    const countPill = document.getElementById("loc-device-count-pill");

    const hospDevices = appState.devices.filter(d => !d.orgId || d.orgId === "HOSP");
    const q = locationDeviceSearchQuery;
    const st = locationDeviceStatusFilter;

    // Filter devices in global scope
    const matchesFilter = (dev) => {
        if (st !== "ALL" && dev.status !== st) return false;
        if (q) {
            const user = appState.users.find(u => u.id === dev.assignedUserId);
            const userName = user ? user.fullName.toLowerCase() : "";
            const userEmp = user ? user.empId.toLowerCase() : "";
            const room = appState.rooms.find(r => r.id === dev.roomId);
            const roomName = room ? room.name.toLowerCase() : "";
            const roomNum = room && room.roomNumber ? room.roomNumber.toLowerCase() : "";
            const matches =
                dev.assetId.toLowerCase().includes(q) ||

                dev.serialNumber.toLowerCase().includes(q) ||
                (dev.ipAddress && dev.ipAddress.toLowerCase().includes(q)) ||
                (dev.macAddress && dev.macAddress.toLowerCase().includes(q)) ||
                (dev.cpuProcessor && dev.cpuProcessor.toLowerCase().includes(q)) ||
                (dev.operatingSystem && dev.operatingSystem.toLowerCase().includes(q)) ||
                userName.includes(q) ||
                userEmp.includes(q) ||
                roomName.includes(q) ||
                roomNum.includes(q);
            if (!matches) return false;
        }
        return true;
    };

    const allFilteredDevices = hospDevices.filter(matchesFilter);

    // Update Breadcrumb & Count Pill (Admin Theme)
    if (breadcrumbEl) {
        if (locationActiveFloor === "ALL") {
            breadcrumbEl.innerHTML = `
                <span class="text-blue-700 font-bold">PSM Hospital</span>
                <i data-lucide="chevron-right" class="w-3.5 h-3.5 text-slate-400"></i>
                <span class="text-slate-900 font-bold">All Floors (Bird's Eye View)</span>
            `;
        } else {
            const curFloor = appState.floors.find(f => f.id === locationActiveFloor);
            const floorLabel = curFloor ? curFloor.name : "Level";
            let roomLabel = "";
            if (locationActiveRoomId !== "ALL") {
                const r = appState.rooms.find(rm => rm.id === locationActiveRoomId);
                if (r) roomLabel = `Room ${r.roomNumber || ''} • ${r.name}`;
            }
            breadcrumbEl.innerHTML = `
                <span class="text-blue-700 font-bold">PSM Hospital</span>
                <i data-lucide="chevron-right" class="w-3.5 h-3.5 text-slate-400"></i>
                <span class="${roomLabel ? 'text-slate-600 font-medium' : 'text-slate-900 font-bold'}">${floorLabel}</span>
                ${roomLabel ? `
                    <i data-lucide="chevron-right" class="w-3.5 h-3.5 text-slate-400"></i>
                    <span class="text-slate-900 font-bold">${roomLabel}</span>
                ` : ''}
            `;
        }
    }

    if (countPill) {
        const maintCount = allFilteredDevices.filter(d => d.status !== "Active").length;
        countPill.innerHTML = `
            <span class="inline-flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                <span>${allFilteredDevices.length} Medical Units</span>
                ${maintCount > 0 ? `<span class="text-amber-700 bg-amber-100 px-1.5 py-0.2 rounded text-[10px] font-bold">(${maintCount} Maint)</span>` : ''}
            </span>
        `;
    }

    if (!container) return;

    // Determine which floors to render
    const floorsToRender = locationActiveFloor === "ALL"
        ? [...appState.floors].sort((a, b) => a.number - b.number)
        : appState.floors.filter(f => f.id === locationActiveFloor);

    if (floorsToRender.length === 0 || (q && allFilteredDevices.length === 0)) {
        container.innerHTML = `
            <div class="bg-white rounded-3xl border border-slate-200 p-12 text-center shadow-xs">
                <div class="max-w-md mx-auto space-y-3">
                    <div class="w-14 h-14 rounded-2xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 mx-auto shadow-xs">
                        <i data-lucide="monitor-off" class="w-7 h-7"></i>
                    </div>
                    <h4 class="text-base font-bold text-slate-800">No Medical Systems Found</h4>
                    <p class="text-xs text-slate-500">
                        No active clinical systems match the current search or status filter on this view.
                    </p>
                    <div class="pt-2 flex items-center justify-center gap-3">
                        <button onclick="handleLocationDeviceStatusFilter('ALL')" class="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition-all cursor-pointer">
                            Reset Status
                        </button>
                        <button onclick="selectFloorFilter('ALL')" class="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all cursor-pointer shadow-xs">
                            Show All Floors
                        </button>
                    </div>
                </div>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    // Render Dedicated Portrait Floor Cards with Room Headings and Clean Device Lines
    container.innerHTML = floorsToRender.map(floor => {
        const theme = FLOOR_THEMES[floor.id] || {
            badge: floor.code || "FL",
            icon: "door-open"
        };

        const floorRooms = appState.rooms.filter(r => r.floorId === floor.id);

        // Devices on this floor
        let floorDevices = hospDevices.filter(d => floorRooms.some(r => r.id === d.roomId));
        // Filtered devices on this floor
        let floorFilteredDevs = floorDevices.filter(matchesFilter);

        // If a specific room filter is active, narrow down
        const roomsToRender = locationActiveRoomId === "ALL"
            ? floorRooms
            : floorRooms.filter(r => r.id === locationActiveRoomId);

        // If searching and this floor has 0 matches, skip rendering this floor in search mode
        if (q && floorFilteredDevs.length === 0) {
            return '';
        }

        // Render Rooms within this Portrait Floor Card
        const roomsHtml = roomsToRender.map(room => {
            const roomDevices = floorDevices.filter(d => d.roomId === room.id);
            const roomFilteredDevs = roomDevices.filter(matchesFilter);

            // If searching and this room has 0 matches, hide room
            if (q && roomFilteredDevs.length === 0) {
                return '';
            }

            let devicesListHtml = '';
            if (roomFilteredDevs.length === 0) {
                devicesListHtml = `
                    <div class="py-2.5 px-3 text-[11px] text-slate-400 italic rounded-2xl bg-white border border-dashed border-slate-200 flex items-center justify-between shadow-2xs">
                        <span>No systems deployed</span>
                        <button onclick="openAddDeviceModal()" class="text-blue-600 hover:text-blue-700 font-bold hover:underline cursor-pointer text-[10px] flex items-center gap-0.5">
                            <i data-lucide="plus" class="w-3 h-3"></i> Add
                        </button>
                    </div>
                `;
            } else {
                devicesListHtml = roomFilteredDevs.map(dev => renderDeviceLineRow(dev, room, floor)).join('');
            }

            const roomNum = room.roomNumber ||
                (typeof INITIAL_SAMPLE_DATA !== 'undefined' && INITIAL_SAMPLE_DATA.rooms ? INITIAL_SAMPLE_DATA.rooms.find(sr => sr.id === room.id)?.roomNumber : null) ||
                (room.code || (room.id ? room.id.replace('rm-', '').toUpperCase() : '01'));

            return `
                <div class="space-y-1.5">
                    <!-- Room Sub-Heading ('Rm to 2 Unit' line) -->
                    <div class="flex items-center justify-between px-1 pt-1">
                        <div class="flex items-center gap-2 min-w-0">
                            <span class="px-2.5 py-0.5 rounded-lg text-[10px] font-mono font-black bg-blue-100/90 text-blue-800 border border-blue-200/90 shrink-0 shadow-2xs">
                                Rm ${roomNum}
                            </span>
                            <span class="text-xs font-bold text-slate-800 truncate" title="${room.name}">
                                ${room.name}
                            </span>
                        </div>
                        <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-200/70 text-slate-600 shrink-0">
                            ${roomFilteredDevs.length} ${roomFilteredDevs.length === 1 ? 'Unit' : 'Units'}
                        </span>
                    </div>

                    <!-- Direct Device Rows (No outer container) -->
                    <div class="space-y-1.5">
                        ${devicesListHtml}
                    </div>
                </div>
            `;
        }).join('');

        return `
            <!-- Dedicated Portrait Floor Card (High-End SaaS / Clinical Dashboard Aesthetics) -->
            <section class="bg-white rounded-3xl border border-slate-200/90 hover:border-blue-500/80 shadow-sm hover:shadow-2xl transition-all duration-300 flex flex-col min-h-[580px] max-h-[640px] overflow-hidden group/card">
                
                <!-- Floor Header (Executive Luxury Design: Clean, Single-Tier, High-Contrast) -->
                <div class="bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-950 text-white px-5 py-4 flex items-center justify-between gap-3 shrink-0 border-b border-white/10 relative overflow-hidden">
                    <!-- Subtle ambient lighting glow -->
                    <div class="absolute -right-6 -top-6 w-24 h-24 bg-blue-500/15 rounded-full blur-2xl pointer-events-none"></div>

                    <!-- Left: Floor Badge + Title & Subtitle -->
                    <div class="flex items-center gap-3.5 min-w-0 relative z-10">
                        <div class="w-11 h-11 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white border border-blue-400/30 flex items-center justify-center font-black text-sm shadow-md shrink-0 tracking-wider">
                            ${theme.badge}
                        </div>
                        <div class="min-w-0">
                            <h3 class="text-sm font-black tracking-tight text-white truncate leading-tight">${floor.name}</h3>
                            <div class="flex items-center gap-1.5 mt-1">
                                <span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-white/10 border border-white/15 text-blue-200 shrink-0">
                                    ${floor.number < 0 ? 'SUB-LEVEL' : floor.number === 0 ? 'GROUND' : `LEVEL 0${floor.number}`}
                                </span>
                                <span class="text-blue-300/40 text-xs">&bull;</span>
                                <span class="text-blue-200/80 text-[11px] font-medium truncate">${floorRooms.length} ${floorRooms.length === 1 ? 'Room' : 'Rooms'}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Right: Telemetry Live Status Pill -->
                    <div class="px-3 py-1.5 rounded-xl text-xs font-bold bg-white/10 backdrop-blur-md text-white border border-white/15 shrink-0 flex items-center gap-2 shadow-xs relative z-10">
                        <span class="w-2 h-2 rounded-full ${floorDevices.length > 0 ? 'bg-emerald-400 ring-2 ring-emerald-400/30 animate-pulse' : 'bg-slate-400'}"></span>
                        <span class="font-mono">${floorDevices.length} ${floorDevices.length === 1 ? 'Unit' : 'Units'}</span>
                    </div>
                </div>

                <!-- Scrollable Rooms and Device Lines Area (Portrait Interior Canvas) -->
                <div class="flex-1 overflow-y-auto p-4 space-y-3.5 scrollbar-thin bg-slate-50/50">
                    ${roomsHtml || `
                        <div class="p-8 text-center text-xs text-slate-400 italic bg-white rounded-2xl border border-dashed border-slate-200">
                            No active clinical rooms match filter criteria on this floor.
                        </div>
                    `}
                </div>

                <!-- Floor Card Footer -->
                <div class="p-3.5 bg-white border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 shrink-0 rounded-b-3xl">
                    <span class="flex items-center gap-2 font-medium text-slate-600">
                        <span class="w-2 h-2 rounded-full bg-emerald-500 shadow-2xs"></span>
                        <span class="text-[11px] font-semibold">${floorDevices.length > 0 ? `${floorDevices.length} Systems Active` : 'No Systems Active'}</span>
                    </span>
                    <button onclick="openAddDeviceModal()" class="text-blue-600 hover:text-blue-700 font-bold text-xs flex items-center gap-1.5 cursor-pointer hover:underline">
                        <i data-lucide="plus-circle" class="w-4 h-4"></i>
                        <span>Deploy Unit</span>
                    </button>
                </div>
            </section>
        `;
    }).join('');

    lucide.createIcons();
}

// Render clean, ultra-focused device line: Employee Name (No symbol/circle), Device Asset ID, and Icon-only Specs Button
function renderDeviceLineRow(dev, room, floor) {
    const user = appState.users.find(u => u.id === dev.assignedUserId);

    return `
        <div class="group/line p-2.5 rounded-2xl bg-white hover:bg-blue-50/80 border border-slate-200/90 hover:border-blue-400 hover:shadow-md transition-all duration-200 flex items-center justify-between gap-3 text-xs">
            
            <!-- 1. Employee Name (No symbol/avatar circle, full text visible) -->
            <div class="min-w-0 flex-1">
                ${user ? `
                    <button onclick="openUserDetailModal('${user.id}')" 
                            title="Staff: ${user.fullName} (${user.designation || 'Staff'}) - Click for Profile" 
                            class="text-xs font-bold text-slate-900 hover:text-blue-600 transition-colors truncate block text-left cursor-pointer">
                        ${user.fullName}
                    </button>
                ` : `
                    <span class="text-xs font-semibold text-slate-400 italic">Unassigned (Spare Pool)</span>
                `}
            </div>

            <!-- 2. Device Asset ID & 3. Icon-only Specs Button -->
            <div class="flex items-center gap-2 shrink-0">
                <span class="font-mono text-xs font-bold px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 text-slate-800 shadow-2xs">
                    ${dev.assetId}
                </span>
                <button onclick="openDeviceDetailPopup('${dev.id}')" 
                        title="View Full Specifications & Actions" 
                        class="w-8 h-8 rounded-xl bg-blue-50 hover:bg-blue-600 text-blue-600 hover:text-white border border-blue-200/80 hover:border-blue-600 transition-all flex items-center justify-center cursor-pointer shadow-2xs hover:shadow-xs group">
                    <i data-lucide="sliders" class="w-4 h-4"></i>
                </button>
            </div>

        </div>
    `;
}

// User Detail Popup Modal Controller (Image & Details Popup)
function openUserDetailModal(userId) {
    const user = appState.users.find(u => u.id === userId);
    if (!user) return;

    const modal = document.getElementById("modal-user-detail");
    if (!modal) return;

    // Find assigned device
    const assignedDev = appState.devices.find(d => d.assignedUserId === user.id);
    const room = assignedDev ? appState.rooms.find(r => r.id === assignedDev.roomId) : null;
    const floor = room ? appState.floors.find(f => f.id === room.floorId) : null;

    const initials = getUserInitials(user.fullName);

    // Populate Modal Elements
    const avatarEl = document.getElementById("staff-modal-avatar");
    if (avatarEl) avatarEl.textContent = initials;

    const nameEl = document.getElementById("staff-modal-name");
    if (nameEl) nameEl.textContent = user.fullName;

    const desEl = document.getElementById("staff-modal-designation");
    if (desEl) desEl.textContent = user.designation || "Medical Staff";

    const deptEl = document.getElementById("staff-modal-dept");
    if (deptEl) deptEl.textContent = user.department || "PSM Hospital";

    const empIdEl = document.getElementById("staff-modal-empid");
    if (empIdEl) empIdEl.textContent = user.empId || "—";

    const emailEl = document.getElementById("staff-modal-email");
    if (emailEl) {
        emailEl.textContent = user.email || "—";
        emailEl.href = user.email ? `mailto:${user.email}` : "#";
    }

    const phoneEl = document.getElementById("staff-modal-phone");
    if (phoneEl) {
        phoneEl.textContent = user.phone || "—";
        phoneEl.href = user.phone ? `tel:${user.phone}` : "#";
    }

    // Workstation Details
    const devTagEl = document.getElementById("staff-modal-device-tag");
    const devNameEl = document.getElementById("staff-modal-device-name");
    const devLocEl = document.getElementById("staff-modal-device-location");
    const reassignBtn = document.getElementById("staff-modal-reassign-btn");

    if (assignedDev) {
        if (devTagEl) devTagEl.textContent = assignedDev.assetId;
        if (devNameEl) devNameEl.textContent = assignedDev.assetId;
        if (devLocEl) {
            devLocEl.innerHTML = `
                <i data-lucide="map-pin" class="w-3 h-3 text-slate-400"></i>
                <span>${floor ? floor.name : ''} &bull; ${room ? room.name : 'Assigned Unit'}</span>
            `;
        }
        if (reassignBtn) {
            reassignBtn.onclick = function () {
                closeUserDetailModal();
                openReassignModal(assignedDev.id);
            };
            reassignBtn.classList.remove("hidden");
        }
    } else {
        if (devTagEl) devTagEl.textContent = "NO ASSIGNED PC";
        if (devNameEl) devNameEl.textContent = "No dedicated system currently allocated";
        if (devLocEl) devLocEl.innerHTML = `<span>Shared clinical terminal</span>`;
        if (reassignBtn) reassignBtn.classList.add("hidden");
    }

    modal.classList.remove("hidden");
    lucide.createIcons();
}

function closeUserDetailModal() {
    const modal = document.getElementById("modal-user-detail");
    if (modal) modal.classList.add("hidden");
}

// ============================================================================
// MODAL: DEDICATED FULL HARDWARE SPECS & CUSTODIAN PROFILE CONTROLLER
// ============================================================================
let activeDetailDeviceId = null;
let activeDetailLinkedDevices = [];

function openDeviceDetailPopup(deviceId) {
    if (!deviceId && typeof activeDropdownDeviceId !== 'undefined' && activeDropdownDeviceId) {
        deviceId = activeDropdownDeviceId;
    }
    let dev = (appState.devices || []).find(d => d.id === deviceId || d.assetId === deviceId);
    if (!dev) return;

    const modal = document.getElementById("modal-device-detail");
    if (!modal) return;

    activeDetailDeviceId = dev.id;

    // 1. Gather User / Custodian Profile
    let user = (appState.users || []).find(u => 
        (u.id && dev.assignedUserId && u.id === dev.assignedUserId) ||
        (u.empId && (u.empId === dev.empId || u.empId === dev.assignedEmpId))
    );

    const isUnassigned = !dev.assignedUserName || 
                         dev.assignedUserName.toLowerCase() === 'unassigned' || 
                         dev.assignedUserName.toLowerCase().includes('hardware pool');

    if (!user && !isUnassigned) {
        user = {
            id: dev.assignedUserId || 'synth-' + dev.id,
            empId: dev.empId || dev.assignedEmpId || 'EMP-STAFF',
            fullName: dev.assignedUserName,
            department: dev.department || dev.assignedDepartment || 'General Facility',
            designation: dev.designation || dev.assignedDesignation || 'Assigned Custodian',
            email: dev.email || dev.assignedEmail || 'support@psm.hospital',
            phone: dev.phone || dev.assignedPhone || '—',
            status: 'Active'
        };
    }

    // 2. Gather All Connected Workstation Hardware (Full using device detail)
    let linked = [];
    if (typeof isCompositeWorkstation === 'function' && isCompositeWorkstation(dev)) {
        linked = expandCompositeWorkstation(dev);
    } else {
        if (dev.assetId) {
            linked = (appState.devices || []).filter(d => d.assetId === dev.assetId);
        }
        if (linked.length <= 1 && user && user.fullName) {
            const userDevices = (appState.devices || []).filter(d => 
                (d.assignedUserId && user.id && d.assignedUserId === user.id) ||
                (d.assignedUserName && d.assignedUserName.toLowerCase() === user.fullName.toLowerCase())
            );
            if (userDevices.length > linked.length) {
                linked = userDevices;
            }
        }
    }
    if (!linked || linked.length === 0) {
        linked = [dev];
    }

    // Sort linked devices: CPU -> Display -> Keyboard -> Mouse -> Printer -> UPS -> Others
    if (typeof getWorkstationDevicePriority === 'function') {
        linked.sort((a, b) => getWorkstationDevicePriority(a) - getWorkstationDevicePriority(b));
    }
    activeDetailLinkedDevices = linked;

    // 3. Populate Header
    const headerAssetEl = document.getElementById("devmodal-header-asset-id");
    if (headerAssetEl) headerAssetEl.textContent = dev.assetId || 'N/A';

    const headerStatusBadge = document.getElementById("devmodal-header-status-badge");
    if (headerStatusBadge) {
        const status = dev.status || 'Active';
        if (status === 'Active') {
            headerStatusBadge.className = "px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40";
            headerStatusBadge.textContent = "Active Duty";
        } else if (status === 'In Maintenance') {
            headerStatusBadge.className = "px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40";
            headerStatusBadge.textContent = "In Maintenance";
        } else {
            headerStatusBadge.className = "px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-500/20 text-slate-300 border border-slate-500/40";
            headerStatusBadge.textContent = status;
        }
    }

    const headerIcon = document.getElementById("devmodal-header-icon");
    if (headerIcon) {
        headerIcon.setAttribute("data-lucide", getDeviceLucideIconName(dev.deviceType || ''));
    }

    // 4. Populate Custodian Card (Section 1)
    populateDetailModalCustodian(user, dev, isUnassigned);

    // 5. Populate Active Device Specs (Section 2)
    renderDetailModalActiveSpecs(dev);

    // 6. Populate Workstation Linked Devices (Section 3)
    renderDetailModalLinkedDevices(linked, dev.id);

    // 7. Backward Compatibility
    const legacyAsset = document.getElementById("devmodal-asset-id");
    if (legacyAsset) legacyAsset.textContent = dev.assetId;
    const legacySys = document.getElementById("devmodal-system-name");
    if (legacySys) legacySys.textContent = dev.assetId;
    const legacySerial = document.getElementById("devmodal-serial-tag");
    if (legacySerial) legacySerial.textContent = `SN: ${dev.serialNumber || 'N/A'}`;
    const legacyCust = document.getElementById("devmodal-custodian-info");
    if (legacyCust) {
        legacyCust.textContent = user ? `${user.fullName} (${user.empId || 'Staff'})` : "Unassigned (Clinical IT Pool)";
    }

    // Show modal & init Lucide icons
    modal.classList.remove("hidden");
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
        window.lucide.createIcons();
    }
}

function populateDetailModalCustodian(user, dev, isUnassigned) {
    const avatarEl = document.getElementById("devmodal-user-avatar");
    const roleBadgeEl = document.getElementById("devmodal-user-badge-role");
    const fullNameEl = document.getElementById("devmodal-user-fullname");
    const empIdEl = document.getElementById("devmodal-user-empid");
    const desigEl = document.getElementById("devmodal-user-designation");
    const deptEl = document.getElementById("devmodal-user-department");
    const emailEl = document.getElementById("devmodal-user-email");
    const phoneEl = document.getElementById("devmodal-user-phone");
    const locEl = document.getElementById("devmodal-user-location");
    const statusPillEl = document.getElementById("devmodal-user-status-pill");

    const room = appState.rooms ? appState.rooms.find(r => r.id === dev.roomId) : null;
    const floor = room && appState.floors ? appState.floors.find(f => f.id === room.floorId) : null;
    const bldg = dev.buildingName || 'PSM Hospital';
    const floorStr = dev.floorName || (floor ? floor.name : 'Clinical Floor');
    const roomStr = dev.roomName || (room ? `${room.roomNumber ? `Rm ${room.roomNumber} - ` : ''}${room.name}` : 'Main Facility Desk');

    if (isUnassigned || !user) {
        if (avatarEl) {
            avatarEl.textContent = "IT";
            avatarEl.className = "w-16 h-16 rounded-2xl bg-gradient-to-tr from-slate-700 via-slate-600 to-slate-500 text-white font-black text-xl flex items-center justify-center shadow-md border-2 border-white select-none";
        }
        if (roleBadgeEl) {
            roleBadgeEl.textContent = "Spare";
            roleBadgeEl.className = "text-[10px] font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200";
        }
        if (fullNameEl) fullNameEl.textContent = "Unassigned Hardware Pool";
        if (empIdEl) empIdEl.textContent = "POOL-SPARE";
        if (desigEl) desigEl.textContent = "Ready for Deployment";
        if (deptEl) deptEl.textContent = "IT Spares & Inventory Depot";
        if (emailEl) {
            emailEl.textContent = "it-support@hospital.org";
            emailEl.href = "mailto:it-support@hospital.org";
        }
        if (phoneEl) {
            phoneEl.textContent = "Ext: 1000 (Central IT)";
            phoneEl.href = "tel:1000";
        }
        if (locEl) locEl.textContent = `${bldg} • ${floorStr} • IT Central Depot`;
        if (statusPillEl) {
            statusPillEl.className = "px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200";
            statusPillEl.textContent = "Available in Pool";
        }
    } else {
        const initials = user.fullName.split(' ').filter(Boolean).map(n => n[0]).join('').substring(0, 2).toUpperCase() || 'CU';
        if (avatarEl) {
            avatarEl.textContent = initials;
            avatarEl.className = "w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-700 via-indigo-600 to-blue-500 text-white font-black text-xl flex items-center justify-center shadow-md shadow-indigo-500/20 border-2 border-white select-none";
        }
        if (roleBadgeEl) {
            roleBadgeEl.textContent = user.designation ? user.designation.substring(0, 16) : 'Custodian';
            roleBadgeEl.className = "text-[10px] font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-200";
        }
        if (fullNameEl) fullNameEl.textContent = user.fullName;
        if (empIdEl) empIdEl.textContent = user.empId || 'EMP-STAFF';
        if (desigEl) desigEl.textContent = user.designation || 'Staff Custodian';
        if (deptEl) deptEl.textContent = user.department || 'Clinical Healthcare Unit';
        if (emailEl) {
            const emailVal = user.email || `${user.fullName.toLowerCase().replace(/[^a-z]/g, '.')}@psm.hospital`;
            emailEl.textContent = emailVal;
            emailEl.href = `mailto:${emailVal}`;
        }
        if (phoneEl) {
            const phoneVal = user.phone && user.phone !== '—' ? user.phone : 'Ext. 2401';
            phoneEl.textContent = phoneVal;
            phoneEl.href = `tel:${phoneVal}`;
        }
        if (locEl) locEl.textContent = `${bldg} • ${floorStr} • ${roomStr}`;
        if (statusPillEl) {
            statusPillEl.className = "px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200";
            statusPillEl.textContent = "Active Custodian";
        }
    }
}

function renderDetailModalActiveSpecs(dev) {
    const rawType = (dev.deviceType || '').trim() || 'Workstation Component';
    const specNameEl = document.getElementById("devmodal-target-spec-name");
    if (specNameEl) specNameEl.textContent = `(${rawType})`;

    const brandEl = document.getElementById("devmodal-spec-brand-badge");
    if (brandEl) brandEl.textContent = dev.brandName || dev.brand || 'Enterprise Medical Grade';

    const serialEl = document.getElementById("devmodal-spec-serial-badge");
    if (serialEl) serialEl.textContent = dev.serialNumber ? `SN: ${dev.serialNumber}` : 'SN: —';

    const cpuEl = document.getElementById("devmodal-cpu");
    if (cpuEl) cpuEl.textContent = dev.cpuProcessor || 'Workstation Processing Unit';

    const ramEl = document.getElementById("devmodal-ram");
    if (ramEl) ramEl.textContent = dev.storageRam || 'Standard Memory Configuration';

    const osEl = document.getElementById("devmodal-os");
    if (osEl) osEl.textContent = dev.operatingSystem || 'Windows 11 Pro Medical Edition';

    const displayEl = document.getElementById("devmodal-display");
    if (displayEl) {
        if (dev.deviceType === 'Display') {
            displayEl.textContent = dev.monitorSpec || dev.cpuProcessor || '24-inch Cleanable Touch FHD';
        } else {
            displayEl.textContent = dev.monitorSpec || 'Connected Video Display Stream';
        }
    }

    const ipEl = document.getElementById("devmodal-ip");
    if (ipEl) ipEl.textContent = dev.ipAddress || '—';

    const macEl = document.getElementById("devmodal-mac");
    if (macEl) macEl.textContent = dev.macAddress || '—';

    const anydeskEl = document.getElementById("devmodal-anydesk");
    if (anydeskEl) anydeskEl.textContent = dev.anydeskId || 'Direct Physical Console';

    const locEl = document.getElementById("devmodal-location-text");
    if (locEl) {
        const room = appState.rooms ? appState.rooms.find(r => r.id === dev.roomId) : null;
        const floor = room && appState.floors ? appState.floors.find(f => f.id === room.floorId) : null;
        const floorStr = dev.floorName || (floor ? floor.name : 'Floor Level');
        const roomStr = dev.roomName || (room ? `${room.roomNumber ? `Rm ${room.roomNumber} - ` : ''}${room.name}` : 'Clinical Room');
        locEl.textContent = `${floorStr} • ${roomStr}`;
    }
}

function renderDetailModalLinkedDevices(linkedDevices, currentDevId) {
    const container = document.getElementById("devmodal-linked-devices-container");
    const countPill = document.getElementById("devmodal-workstation-count-pill");
    if (countPill) {
        countPill.textContent = `${linkedDevices.length} ${linkedDevices.length === 1 ? 'Device' : 'Devices'} Linked`;
    }
    if (!container) return;

    let html = '';
    linkedDevices.forEach(item => {
        const isCurrent = item.id === currentDevId;
        const type = (item.deviceType || 'Device').trim();
        const iconName = getDeviceLucideIconName(type);
        const isActive = (item.status || 'Active') === 'Active';

        let specSnippet = item.cpuProcessor || item.storageRam || item.monitorSpec || 'Hardware Unit';
        if (type === 'Display') specSnippet = item.monitorSpec || item.cpuProcessor || '24" Display Stream';
        else if (type === 'Keyboard') specSnippet = item.keyboardSpec || item.cpuProcessor || 'Spill-Proof Keyboard';
        else if (type === 'Mouse') specSnippet = item.mouseSpec || item.cpuProcessor || 'USB Cleanable Optical';
        else if (type === 'Printer') specSnippet = item.printerSpec || item.cpuProcessor || 'Medical Document Printer';

        html += `
            <div onclick="selectDetailModalDevice('${item.id}')" 
                class="group relative rounded-2xl p-3.5 transition-all cursor-pointer border ${isCurrent ? 'bg-indigo-50/80 border-indigo-500 shadow-md ring-2 ring-indigo-500/20' : 'bg-slate-50/70 border-slate-200/90 hover:bg-white hover:border-indigo-300 hover:shadow-xs'}">
                <div class="flex items-center justify-between gap-1.5 mb-2">
                    <div class="w-8 h-8 rounded-xl ${isCurrent ? 'bg-indigo-600 text-white' : 'bg-white text-indigo-600 border border-slate-200 group-hover:bg-indigo-50'} flex items-center justify-center shadow-3xs transition-colors shrink-0">
                        <i data-lucide="${iconName}" class="w-4 h-4"></i>
                    </div>
                    <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-bold ${isActive ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
                        <span class="w-1.5 h-1.5 rounded-full ${isActive ? 'bg-emerald-500' : 'bg-amber-500'}"></span>
                        <span>${item.status || 'Active'}</span>
                    </span>
                </div>
                <div>
                    <div class="font-extrabold text-xs text-slate-900 group-hover:text-indigo-700 transition-colors truncate">
                        ${type}
                    </div>
                    <div class="text-[11px] text-slate-500 truncate mt-0.5" title="${specSnippet}">
                        ${specSnippet}
                    </div>
                    <div class="text-[10px] font-mono text-slate-400 mt-1 font-semibold truncate">
                        SN: ${item.serialNumber || '—'}
                    </div>
                </div>
                ${isCurrent ? `
                    <div class="mt-2 pt-1.5 border-t border-indigo-200/60 flex items-center justify-between text-[10px] font-bold text-indigo-700">
                        <span class="flex items-center gap-1"><i data-lucide="eye" class="w-3 h-3"></i> Viewing</span>
                        <i data-lucide="check" class="w-3.5 h-3.5 text-indigo-600"></i>
                    </div>
                ` : `
                    <div class="mt-2 pt-1.5 border-t border-slate-200/60 text-[10px] font-semibold text-slate-400 group-hover:text-indigo-600 flex items-center justify-between">
                        <span>Click to view</span>
                        <i data-lucide="chevron-right" class="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity"></i>
                    </div>
                `}
            </div>
        `;
    });

    container.innerHTML = html;
}

function selectDetailModalDevice(deviceId) {
    const targetDev = activeDetailLinkedDevices.find(d => d.id === deviceId);
    if (!targetDev) return;

    activeDetailDeviceId = targetDev.id;
    renderDetailModalActiveSpecs(targetDev);
    renderDetailModalLinkedDevices(activeDetailLinkedDevices, targetDev.id);
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
        window.lucide.createIcons();
    }
}

function getDeviceLucideIconName(rawType) {
    const t = (rawType || '').toUpperCase().trim();
    if (t === 'C' || t === 'CPU' || t === 'DESKTOP' || t === 'PC' || t === 'COMPUTER') return 'cpu';
    if (t === 'D' || t === 'DISPLAY' || t === 'MONITOR' || t === 'SCREEN') return 'monitor';
    if (t === 'K' || t === 'KB' || t === 'KEYBOARD') return 'keyboard';
    if (t === 'M' || t === 'MOUSE') return 'mouse';
    if (t === 'P' || t === 'PRT' || t === 'PRINTER' || t.includes('PRINT')) return 'printer';
    if (t === 'T' || t === 'TABLET' || t === 'TAB' || t === 'IPAD') return 'tablet';
    if (t === 'U' || t === 'UPS' || t === 'POWER' || t === 'INVERTER') return 'zap';
    if (t.includes('SCANNER') || t.includes('BIOMETRIC')) return 'fingerprint';
    return 'hard-drive';
}

function copyModalAssetId(btnEl) {
    const assetEl = document.getElementById("devmodal-header-asset-id");
    if (!assetEl) return;
    const text = assetEl.textContent.trim();
    if (!text) return;

    navigator.clipboard.writeText(text).then(() => {
        if (btnEl) {
            const orig = btnEl.innerHTML;
            btnEl.innerHTML = '<i data-lucide="check" class="w-3 h-3 text-emerald-400"></i><span class="text-emerald-300">Copied!</span>';
            if (window.lucide) window.lucide.createIcons();
            setTimeout(() => {
                btnEl.innerHTML = orig;
                if (window.lucide) window.lucide.createIcons();
            }, 1800);
        }
    }).catch(() => {});
}

function triggerMoveLocationFromDetailModal() {
    const devId = activeDetailDeviceId || (typeof activeDropdownDeviceId !== 'undefined' ? activeDropdownDeviceId : null);
    closeDeviceDetailPopup();
    if (devId && typeof openChangeLocationModal === 'function') {
        openChangeLocationModal(devId);
    }
}

function triggerReassignFromDetailModal() {
    const devId = activeDetailDeviceId || (typeof activeDropdownDeviceId !== 'undefined' ? activeDropdownDeviceId : null);
    closeDeviceDetailPopup();
    if (devId && typeof openReassignModal === 'function') {
        openReassignModal(devId);
    }
}

function closeDeviceDetailPopup() {
    const modal = document.getElementById("modal-device-detail");
    if (modal) modal.classList.add("hidden");
    activeDetailDeviceId = null;
}

window.openDeviceDetailPopup = openDeviceDetailPopup;
window.closeDeviceDetailPopup = closeDeviceDetailPopup;
window.selectDetailModalDevice = selectDetailModalDevice;
window.copyModalAssetId = copyModalAssetId;
window.triggerMoveLocationFromDetailModal = triggerMoveLocationFromDetailModal;
window.triggerReassignFromDetailModal = triggerReassignFromDetailModal;
window.openUserDetailModal = openUserDetailModal;
window.closeUserDetailModal = closeUserDetailModal;

window.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
        if (typeof closeUserDetailModal === 'function') closeUserDetailModal();
        closeDeviceDetailPopup();
    }
});

function renderLocationHardwareCards() {
    renderLocationBirdEyeView();
}

// Backward-compatible navigation bridges
function selectLocationNode(type, id, parentId = null) {
    if (type === "org") {
        switchCampusView(id);
    } else if (type === "building") {
        selectBuildingFilter(id);
    } else if (type === "room") {
        selectRoomFilter(id);
    } else {
        switchCampusView("ALL");
    }
}

function renderLocationTree() {
    renderCampusFacilityCards();
    renderCampusRoomPills();
}

function renderLocationDevicesTable() {
    renderLocationHardwareCards();
}

function setLocationTreeCampusFilter(filter) {
    switchCampusView(filter);
}

function toggleAllTreeNodes() { }
function toggleBuildingAccordion() { }
function handleLocationTreeFilter() { }

function openAddDeviceModalForLocation(targetRoomId = null) {
    openAddDeviceModal();
    if (targetRoomId) {
        const room = appState.rooms.find(r => r.id === targetRoomId);
        if (room) {
            const floor = appState.floors.find(f => f.id === room.floorId);
            const bldg = floor ? appState.buildings.find(b => b.id === floor.buildingId) : null;
            if (bldg) {
                const orgSelect = document.getElementById("dev-select-org");
                if (orgSelect) {
                    orgSelect.value = bldg.orgId;
                    handleDevOrgChange();
                }
                const bldgSelect = document.getElementById("dev-select-bldg");
                if (bldgSelect) {
                    bldgSelect.value = bldg.id;
                    handleDevBldgChange();
                }
                const floorSelect = document.getElementById("dev-select-floor");
                if (floorSelect) {
                    floorSelect.value = floor.id;
                    handleDevFloorChange();
                }
                const roomSelect = document.getElementById("dev-select-room");
                if (roomSelect) {
                    roomSelect.value = room.id;
                }
            }
        }
    }
}

function exportLocationDevicesCSV() {
    const rawDevices = getDevicesInLocationScope();
    if (!rawDevices || rawDevices.length === 0) {
        showToast("No devices to export in this location.", "info");
        return;
    }

    const devices = [];
    rawDevices.forEach(d => {
        if (typeof isCompositeWorkstation === 'function' && isCompositeWorkstation(d)) {
            const comps = expandCompositeWorkstation(d);
            comps.forEach(c => devices.push(c));
        } else {
            devices.push(d);
        }
    });

    const exportRows = devices.map(d => getDeviceExportData(d));
    if (exportRows.length === 0) return;

    const headers = Object.keys(exportRows[0]);
    let csvContent = "\uFEFF" + headers.map(h => `"${h.replace(/"/g, '""')}"`).join(",") + "\r\n";

    exportRows.forEach(row => {
        const line = headers.map(h => {
            const val = String(row[h] === undefined || row[h] === null ? '' : row[h]);
            return `"${val.replace(/"/g, '""')}"`;
        }).join(",");
        csvContent += line + "\r\n";
    });

    const locName = (currentLocationSelection && currentLocationSelection.name) ? currentLocationSelection.name : 'location';
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `location_hardware_${locName.toLowerCase().replace(/[^a-z0-9]+/g, '_')}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    showToast("Location hardware report exported successfully!", "success");
}

function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showToast(`Asset tag ${text} copied to clipboard!`, "info");
        }).catch(() => { });
    }
}

function filterByRoom(roomId) {
    selectLocationNode('room', roomId);
}

// ============================================================================
// TAB 3: USERS DIRECTORY
// ============================================================================

function renderUsersDirectory() {
    const container = document.getElementById("users-directory-container");
    if (!container) return;

    const q = (document.getElementById("users-search-input")?.value || "").toLowerCase().trim();
    const users = appState.users.filter(u => {
        if (appState.selectedOrg !== "ALL" && u.orgId !== appState.selectedOrg) return false;
        if (q && !u.fullName.toLowerCase().includes(q) && !u.empId.toLowerCase().includes(q) && !u.department.toLowerCase().includes(q)) return false;
        return true;
    });

    if (users.length === 0) {
        container.innerHTML = `<div class="col-span-3 text-center py-12 text-slate-400">No staff members found matching search.</div>`;
        return;
    }

    container.innerHTML = users.map(user => {
        const assignedDev = appState.devices.find(d => d.assignedUserId === user.id);
        const org = appState.organizations.find(o => o.id === user.orgId);

        return `
            <div onclick="openSearchUserModal('${user.empId}')" class="bg-white rounded-xl border border-slate-200 p-4 shadow-xs hover:border-indigo-400 hover:shadow-md transition-all cursor-pointer flex flex-col justify-between group">
                <div class="flex items-start justify-between">
                    <div class="flex-1 min-w-0 text-xs">
                        <div class="font-bold text-slate-900 group-hover:text-indigo-600 text-sm transition-colors truncate">${user.fullName}</div>
                        <div class="text-slate-500 font-medium">${user.designation}</div>
                        <div class="text-[10px] text-slate-400 font-mono mt-0.5">${user.empId} &bull; ${user.department}</div>
                    </div>
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold ${user.orgId === 'HOSP' ? 'bg-violet-50 text-violet-800 border border-violet-200' : 'bg-indigo-50 text-indigo-700 border border-indigo-200'}">
                        ${user.orgId === 'HOSP' ? 'Hospital' : 'University'}
                    </span>
                </div>

                <div class="mt-4 pt-3 border-t border-slate-100 text-xs flex items-center justify-between">
                    <div>
                        <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Assigned System:</div>
                        <div class="font-mono font-bold ${assignedDev ? 'text-indigo-700' : 'text-slate-400 italic'}">
                            ${assignedDev ? assignedDev.assetId : 'None (No Hardware)'}
                        </div>
                    </div>
                    <span class="text-indigo-600 font-bold text-xs group-hover:translate-x-0.5 transition-transform">&rarr;</span>
                </div>
            </div>
        `;
    }).join('');

    lucide.createIcons();
}

function filterUsersDirectory() {
    renderUsersDirectory();
}

// ============================================================================
// TAB 4: AUDIT & TRACEABILITY LOGS (REBUILT CLEAN ARCHITECTURE)
// ============================================================================

let currentAuditCategory = "all";
let currentAuditSearch = "";
let currentAuditViewMode = "table"; // 'table' | 'timeline' | 'traceability'
let currentSelectedAuditId = null;
let currentTraceabilityAssetId = null;

function getUnifiedAuditEvents() {
    const events = [];

    // 1. Process Location Histories (Physical room/lab shifts)
    (appState.locationHistories || []).forEach(h => {
        const dev = (appState.devices || []).find(d => d.id === h.deviceId || d.assetId === h.deviceId);
        if (appState.selectedOrg !== "ALL" && dev && dev.orgId !== appState.selectedOrg) return;

        events.push({
            id: h.id,
            type: "relocation",
            rawDate: h.changedDate,
            date: h.changedDate,
            timestamp: "09:15 AM",
            assetId: dev ? dev.assetId : (h.deviceId || "ASSET-LOG"),

            device: dev,
            fromLocation: h.fromLocation || "Previous Facility Room",
            toLocation: h.toLocation || "Target Ward",
            changedBy: h.changedBy || "IT Admin",
            reason: h.reason || "Physical room relocation",
            isHospital: dev ? (dev.orgId === "HOSP") : true
        });
    });

    // 2. Process Assignment Histories (Staff custody handovers)
    (appState.assignmentHistories || []).forEach(ah => {
        const dev = (appState.devices || []).find(d => d.id === ah.deviceId || d.assetId === ah.deviceId);
        const user = (appState.users || []).find(u => u.id === ah.userId);
        if (appState.selectedOrg !== "ALL" && dev && dev.orgId !== appState.selectedOrg) return;

        const userName = ah.toUserName || (user ? user.fullName : (ah.userId || "Assigned Custodian"));
        const userRole = user ? user.designation : (ah.userRole || "Medical Staff");
        const userDept = user ? user.department : "Clinical Department";
        const userInitials = user ? user.fullName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() : "MD";

        events.push({
            id: ah.id,
            type: "handover",
            rawDate: ah.fromDate,
            date: ah.fromDate,
            toDate: ah.toDate,
            timestamp: "10:30 AM",
            assetId: dev ? dev.assetId : (ah.assetId || ah.deviceId || "ASSET-LOG"),

            device: dev,
            user: user,
            fromUserName: ah.fromUserName || "Unassigned / IT Spares",
            userName: userName,
            userRole: userRole,
            userDept: userDept,
            userInitials: userInitials,
            location: ah.location || (dev ? "Hospital Ward" : "Campus"),
            assignedBy: ah.assignedBy || "Campus Supervisor",
            remarks: ah.remarks || "Hardware custody assignment",
            isHospital: dev ? (dev.orgId === "HOSP") : true
        });
    });

    return events;
}

function setAuditViewMode(mode) {
    currentAuditViewMode = mode;

    // Update active button states
    ['table', 'traceability'].forEach(m => {
        const btn = document.getElementById(`audit-view-btn-${m}`);
        if (btn) {
            if (m === mode) {
                btn.className = "audit-view-btn px-3.5 py-1.5 rounded-lg font-bold text-xs bg-indigo-600 text-white shadow-xs transition-all flex items-center gap-1.5 cursor-pointer";
            } else {
                btn.className = "audit-view-btn px-3.5 py-1.5 rounded-lg font-bold text-xs bg-transparent text-slate-700 hover:bg-white/80 transition-all flex items-center gap-1.5 cursor-pointer";
            }
        }
    });

    // Toggle container views
    const tableView = document.getElementById("audit-table-view");
    const traceView = document.getElementById("audit-traceability-view");

    if (tableView) tableView.classList.toggle("hidden", mode !== "table");
    if (traceView) traceView.classList.toggle("hidden", mode !== "traceability");

    renderAuditLogs();
}

function filterAuditCategory(cat) {
    currentAuditCategory = cat;

    // Update active tab buttons
    ['all', 'relocation', 'handover'].forEach(c => {
        const btn = document.getElementById(`audit-filter-${c}`);
        if (btn) {
            if (c === cat) {
                btn.className = "audit-cat-btn px-3 py-1 rounded-lg text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 shadow-2xs transition-all flex items-center gap-1.5 cursor-pointer";
            } else {
                btn.className = "audit-cat-btn px-3 py-1 rounded-lg text-xs font-semibold bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 transition-all flex items-center gap-1.5 cursor-pointer";
            }
        }
    });

    renderAuditLogs();
}

function handleAuditSearch(e) {
    currentAuditSearch = e.target.value.trim();
    renderAuditLogs();
}

function clearAuditFilters() {
    currentAuditCategory = "all";
    currentAuditSearch = "";
    const input = document.getElementById("audit-search-input");
    if (input) input.value = "";
    filterAuditCategory("all");
}

function renderAuditLogs() {
    const allEvents = getUnifiedAuditEvents();

    // 1. Update KPI Stat Counters
    const totalCount = allEvents.length;
    const relocCount = allEvents.filter(e => e.type === "relocation").length;
    const handoverCount = allEvents.filter(e => e.type === "handover").length;
    const uniqueAssets = new Set(allEvents.map(e => e.assetId).filter(Boolean)).size;

    const statTotal = document.getElementById("stat-audit-total");
    const statRelocs = document.getElementById("stat-audit-relocations");
    const statHandovers = document.getElementById("stat-audit-handovers");
    const statAssets = document.getElementById("stat-audit-assets");

    // Staggered animated count on page open
    if (!window._kpiAuditInitialAnimated) {
        window._kpiAuditInitialAnimated = true;
        animateNumberCounter(statTotal, totalCount, 1100, 0);
        animateNumberCounter(statRelocs, relocCount, 1100, 70);
        animateNumberCounter(statHandovers, handoverCount, 1100, 140);
        animateNumberCounter(statAssets, uniqueAssets, 1100, 210);
    } else {
        animateNumberCounter(statTotal, totalCount, 400, 0);
        animateNumberCounter(statRelocs, relocCount, 400, 0);
        animateNumberCounter(statHandovers, handoverCount, 400, 0);
        animateNumberCounter(statAssets, uniqueAssets, 400, 0);
    }

    // 2. Update Category Filter Badges
    const countAll = document.getElementById("count-filter-all");
    const countReloc = document.getElementById("count-filter-relocations");
    const countHandover = document.getElementById("count-filter-handovers");

    if (countAll) countAll.textContent = totalCount;
    if (countReloc) countReloc.textContent = relocCount;
    if (countHandover) countHandover.textContent = handoverCount;

    // 3. Filter events by category & search
    let filteredEvents = allEvents;
    if (currentAuditCategory === "relocation") {
        filteredEvents = filteredEvents.filter(e => e.type === "relocation");
    } else if (currentAuditCategory === "handover") {
        filteredEvents = filteredEvents.filter(e => e.type === "handover");
    }

    if (currentAuditSearch) {
        const q = currentAuditSearch.toLowerCase();
        filteredEvents = filteredEvents.filter(e => {
            return (
                (e.assetId && e.assetId.toLowerCase().includes(q)) ||

                (e.userName && e.userName.toLowerCase().includes(q)) ||
                (e.userRole && e.userRole.toLowerCase().includes(q)) ||
                (e.fromLocation && e.fromLocation.toLowerCase().includes(q)) ||
                (e.toLocation && e.toLocation.toLowerCase().includes(q)) ||
                (e.location && e.location.toLowerCase().includes(q)) ||
                (e.reason && e.reason.toLowerCase().includes(q)) ||
                (e.remarks && e.remarks.toLowerCase().includes(q)) ||
                (e.changedBy && e.changedBy.toLowerCase().includes(q)) ||
                (e.assignedBy && e.assignedBy.toLowerCase().includes(q))
            );
        });
    }

    // Update feed counter
    const feedCounter = document.getElementById("audit-feed-counter");
    if (feedCounter) feedCounter.textContent = `Showing ${filteredEvents.length} of ${totalCount} events`;

    // 4. Render Master Table View
    const tableBody = document.getElementById("audit-table-tbody");
    const tableEmpty = document.getElementById("audit-table-empty");

    if (tableBody) {
        if (filteredEvents.length === 0) {
            tableBody.innerHTML = "";
            if (tableEmpty) tableEmpty.classList.remove("hidden");
        } else {
            if (tableEmpty) tableEmpty.classList.add("hidden");
            tableBody.innerHTML = filteredEvents.map(evt => {
                const isReloc = evt.type === "relocation";
                const dev = evt.device;
                const devName = dev ? (dev.assetId || dev.cpuProcessor || 'Workstation') : (evt.assetId || 'Workstation');

                const fromShort = isReloc ? (evt.fromLocation.includes('/') ? evt.fromLocation.split('/')[1] || evt.fromLocation : evt.fromLocation) : (evt.fromUserName || 'Spares');
                const toShort = isReloc ? (evt.toLocation.includes('/') ? evt.toLocation.split('/')[1] || evt.toLocation : evt.toLocation) : evt.userName;

                return `
                    <tr class="hover:bg-slate-50/90 transition-colors divide-x divide-slate-100 text-slate-800">
                        <td class="py-3.5 px-4 whitespace-nowrap">
                            <div class="font-bold text-slate-900 text-sm">${evt.date}</div>
                            <div class="text-xs text-slate-400 font-medium mt-0.5">${evt.timestamp}</div>
                        </td>
                        <td class="py-3.5 px-4 whitespace-nowrap">
                            ${isReloc ? `
                                <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200 shadow-2xs whitespace-nowrap">
                                    <i data-lucide="map-pin" class="w-3.5 h-3.5 text-blue-600"></i> Relocation
                                </span>
                            ` : `
                                <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-purple-50 text-purple-700 border border-purple-200 shadow-2xs whitespace-nowrap">
                                    <i data-lucide="user-check" class="w-3.5 h-3.5 text-purple-600"></i> Custody Transfer
                                </span>
                            `}
                        </td>
                        <td class="py-3.5 px-4">
                            <div class="font-mono font-black text-sm text-slate-950 select-all whitespace-nowrap tracking-tight leading-snug">${evt.assetId}</div>
                            <div class="text-xs text-slate-500 font-medium truncate max-w-[220px] mt-0.5" title="${devName}">
                                ${devName}
                            </div>
                        </td>
                        <td class="py-3.5 px-4">
                            ${isReloc ? `
                                <div class="flex items-center gap-2 text-sm font-semibold">
                                    <span class="text-slate-600 truncate max-w-[150px]" title="${evt.fromLocation}">${fromShort}</span>
                                    <i data-lucide="arrow-right" class="w-4 h-4 text-blue-600 shrink-0"></i>
                                    <span class="text-blue-900 font-bold truncate max-w-[170px]" title="${evt.toLocation}">${toShort}</span>
                                </div>
                            ` : `
                                <div class="flex items-center gap-2.5">
                                    <div class="w-7 h-7 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-bold shrink-0 shadow-2xs">
                                        ${evt.userInitials}
                                    </div>
                                    <div class="min-w-0">
                                        <div class="text-sm font-bold text-slate-900 truncate max-w-[190px]" title="${evt.userName}">${evt.userName}</div>
                                        <div class="text-xs text-purple-700 font-medium truncate max-w-[190px]">${evt.userRole}</div>
                                    </div>
                                </div>
                            `}
                        </td>
                        <td class="py-3.5 px-4 whitespace-nowrap">
                            <div class="font-bold text-slate-900 text-sm">${isReloc ? evt.changedBy : evt.assignedBy}</div>
                            <div class="text-xs text-slate-400">Supervisor</div>
                        </td>
                        <td class="py-3.5 px-4">
                            <div class="text-xs text-slate-700 font-medium italic truncate max-w-[240px]" title="${isReloc ? evt.reason : evt.remarks}">
                                "${isReloc ? evt.reason : evt.remarks}"
                            </div>
                        </td>
                        <td class="py-3.5 px-4 text-right whitespace-nowrap no-print">
                            <button onclick="openAuditDetailModal('${evt.id}')" class="px-3.5 py-1.5 bg-indigo-50 hover:bg-indigo-100 active:bg-indigo-200 text-indigo-700 rounded-xl font-bold text-xs transition-all inline-flex items-center gap-1.5 cursor-pointer shadow-2xs hover:shadow-xs">
                                <i data-lucide="eye" class="w-3.5 h-3.5 text-indigo-600"></i>
                                <span>Inspect</span>
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
        }
    }


    // 6. Render Single Asset Traceability
    renderAssetTraceabilityView(allEvents);

    if (window.lucide && typeof window.lucide.createIcons === 'function') {
        lucide.createIcons();
    }
}

function renderAssetTraceabilityView(allEvents) {
    const assetSelect = document.getElementById("audit-asset-select");
    const journeyCard = document.getElementById("asset-journey-card");
    const stepsContainer = document.getElementById("asset-journey-steps");

    if (!assetSelect) return;

    // Get list of distinct assets from devices & events
    const assetMap = new Map();
    (appState.devices || []).forEach(d => {
        if (d.assetId) assetMap.set(d.assetId, d);
    });
    allEvents.forEach(e => {
        if (e.assetId && !assetMap.has(e.assetId)) {
            assetMap.set(e.assetId, e.device || { assetId: e.assetId });
        }
    });

    const assetList = Array.from(assetMap.keys());
    if (assetList.length === 0) return;

    if (!currentTraceabilityAssetId || !assetMap.has(currentTraceabilityAssetId)) {
        currentTraceabilityAssetId = assetList[0];
    }

    // Populate dropdown options
    assetSelect.innerHTML = assetList.map(aid => {
        const d = assetMap.get(aid);
        const name = aid;
        const isSel = aid === currentTraceabilityAssetId;
        return `<option value="${aid}" ${isSel ? 'selected' : ''}>${aid} — ${name}</option>`;
    }).join('');

    const targetAsset = assetMap.get(currentTraceabilityAssetId);
    const assetEvents = allEvents.filter(e => e.assetId === currentTraceabilityAssetId);

    // Render Overview Card
    if (journeyCard && targetAsset) {
        const user = (appState.users || []).find(u => u.id === targetAsset.assignedUserId);
        const userName = targetAsset.assignedUserName || (user ? user.fullName : "Hospital Spare / Unassigned");

        journeyCard.innerHTML = `
            <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-4">
                <div>
                    <div class="flex items-center gap-2 mb-1">
                        <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-100 text-emerald-800 border border-emerald-200">
                            ${targetAsset.status || 'Active & Operational'}
                        </span>
                        <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">PSM Hospital Asset</span>
                    </div>
                    <h3 class="text-lg font-black text-slate-900 flex items-center gap-2">
                        <span class="font-mono text-indigo-700">${targetAsset.assetId}</span>
                        <span>&bull;</span>
                        <span>${targetAsset.assetId || 'Clinical Workstation'}</span>
                    </h3>
                </div>
                <div class="flex items-center gap-2">
                    <button onclick="openDeviceDetailPopup('${targetAsset.id || targetAsset.devId}')" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition-all cursor-pointer">
                        View Hardware Specs
                    </button>
                    <button onclick="window.print()" class="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-xs transition-all flex items-center gap-1.5 cursor-pointer">
                        <i data-lucide="printer" class="w-3.5 h-3.5"></i>
                        <span>Print Passport</span>
                    </button>
                </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
                <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/70">
                    <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Serial Number</div>
                    <div class="font-mono font-bold text-slate-800 mt-0.5">${targetAsset.serialNumber || 'SN-MED-9921'}</div>
                </div>
                <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/70">
                    <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Current Custodian</div>
                    <div class="font-bold text-slate-800 mt-0.5">${userName}</div>
                </div>
                <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/70">
                    <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Operating System</div>
                    <div class="font-medium text-slate-800 mt-0.5">${targetAsset.operatingSystem || 'Windows 11 Pro'}</div>
                </div>
                <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/70">
                    <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Recorded Moves</div>
                    <div class="font-bold text-indigo-700 mt-0.5">${assetEvents.length} Lifecycle Event${assetEvents.length === 1 ? '' : 's'}</div>
                </div>
            </div>
        `;
    }

    // Render Steps Container
    if (stepsContainer) {
        if (assetEvents.length === 0) {
            stepsContainer.innerHTML = `
                <div class="p-6 bg-slate-50 border border-slate-200 rounded-xl text-center text-xs text-slate-500">
                    <i data-lucide="check-circle" class="w-8 h-8 mx-auto text-emerald-500 mb-2"></i>
                    <div>This hardware device remains in its original commissioned deployment position without relocation transfers.</div>
                </div>
            `;
        } else {
            stepsContainer.innerHTML = assetEvents.map((evt, idx) => {
                const isReloc = evt.type === "relocation";
                return `
                    <div class="flex items-start gap-3.5 relative">
                        <div class="w-8 h-8 rounded-full ${isReloc ? 'bg-blue-600' : 'bg-purple-600'} text-white flex items-center justify-center shrink-0 shadow-xs text-xs font-bold">
                            ${idx + 1}
                        </div>
                        <div class="flex-1 bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-1">
                            <div class="flex items-center justify-between">
                                <span class="font-bold text-xs text-slate-900">${isReloc ? 'Facility Room Relocation' : 'Custody Handover'}</span>
                                <span class="text-[11px] font-semibold text-slate-500">${evt.date}</span>
                            </div>
                            <div class="text-xs text-slate-700">
                                ${isReloc ? `
                                    Moved from <strong class="text-slate-800">${evt.fromLocation}</strong> &rarr; <strong class="text-blue-700">${evt.toLocation}</strong>
                                ` : `
                                    Handed over to <strong class="text-purple-900">${evt.userName}</strong> (${evt.userRole})
                                `}
                            </div>
                            <div class="text-[11px] text-slate-500 flex items-center justify-between pt-1 border-t border-slate-200/60 mt-1">
                                <span>Reason: <em>"${isReloc ? evt.reason : evt.remarks}"</em></span>
                                <span>Authorized by <strong>${isReloc ? evt.changedBy : evt.assignedBy}</strong></span>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }
    }
}

function handleTraceabilityAssetChange(e) {
    currentTraceabilityAssetId = e.target.value;
    const allEvents = getUnifiedAuditEvents();
    renderAssetTraceabilityView(allEvents);
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
        lucide.createIcons();
    }
}

function openAuditDetailModal(eventId) {
    const allEvents = getUnifiedAuditEvents();
    const evt = allEvents.find(e => e.id === eventId);
    if (!evt) return;

    const modal = document.getElementById("modal-audit-detail");
    const body = document.getElementById("audit-modal-body");
    const title = document.getElementById("audit-modal-title");
    const subTitle = document.getElementById("audit-modal-subtitle");
    const refId = document.getElementById("audit-modal-ref-id");
    const iconWrap = document.getElementById("audit-modal-icon-wrap");

    if (!modal || !body) return;

    const isReloc = evt.type === "relocation";
    const dev = evt.device;

    if (title) title.textContent = isReloc ? "Hardware Physical Relocation Record" : "Custody Responsibility Transfer Record";
    if (subTitle) subTitle.textContent = `Recorded on ${evt.date} at ${evt.timestamp} • PSM Hospital`;
    if (refId) refId.textContent = `AUDIT REF: LOG-${evt.id.toUpperCase()}`;
    if (iconWrap) {
        iconWrap.innerHTML = `<i data-lucide="${isReloc ? 'map-pin' : 'user-check'}" class="w-5 h-5"></i>`;
    }

    body.innerHTML = `
        <!-- Hardware Subject Summary -->
        <div class="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
            <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Hardware Asset Identity</div>
            <div class="flex items-center justify-between">
                <div class="font-mono font-black text-sm text-indigo-700 select-all">${evt.assetId}</div>
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${isReloc ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'}">
                    ${isReloc ? 'Room Movement' : 'Custody Handover'}
                </span>
            </div>
            <div class="text-xs text-slate-600 font-medium">
                ${dev ? `${dev.assetId || ''} &bull; ${dev.cpuProcessor || 'Clinical Hardware'}` : (evt.assetId || 'Hardware')}
            </div>
            <div class="text-[11px] text-slate-400 font-mono">
                Serial Number: ${dev ? (dev.serialNumber || 'SN-MED-9921') : 'SN-MED-9921'}
            </div>
        </div>

        <!-- Before & After Diff -->
        <div class="space-y-1.5">
            <div class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Change & Movement Vector</div>
            ${isReloc ? `
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    <div class="p-2.5 bg-white border border-slate-200 rounded-lg">
                        <div class="text-[10px] font-bold text-slate-400">ORIGIN ROOM:</div>
                        <div class="font-bold text-slate-800 text-xs mt-0.5">${evt.fromLocation}</div>
                    </div>
                    <div class="p-2.5 bg-blue-50 border border-blue-200 rounded-lg">
                        <div class="text-[10px] font-bold text-blue-800">DESTINATION ROOM:</div>
                        <div class="font-bold text-blue-900 text-xs mt-0.5">${evt.toLocation}</div>
                    </div>
                </div>
            ` : `
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    <div class="p-2.5 bg-white border border-slate-200 rounded-lg">
                        <div class="text-[10px] font-bold text-slate-400">PREVIOUS CUSTODIAN:</div>
                        <div class="font-bold text-slate-800 text-xs mt-0.5">${evt.fromUserName || 'Unassigned / IT Spares'}</div>
                    </div>
                    <div class="p-2.5 bg-purple-50 border border-purple-200 rounded-lg">
                        <div class="text-[10px] font-bold text-purple-800">DESIGNATED CUSTODIAN:</div>
                        <div class="font-bold text-purple-950 text-xs mt-0.5">${evt.userName}</div>
                        <div class="text-[10px] text-purple-700">${evt.userRole} &bull; ${evt.location}</div>
                    </div>
                </div>
            `}
        </div>

        <!-- Justification & Reason -->
        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
            <div class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Official Reason / Justification</div>
            <p class="text-slate-800 font-medium italic">
                "${isReloc ? evt.reason : evt.remarks}"
            </p>
        </div>

        <!-- Authorization Meta -->
        <div class="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-100">
            <div>Authorized by: <strong class="text-slate-800">${isReloc ? evt.changedBy : evt.assignedBy}</strong></div>
            <div class="text-emerald-700 font-bold flex items-center gap-1">
                <i data-lucide="shield-check" class="w-3.5 h-3.5 text-emerald-600"></i> Verified Record
            </div>
        </div>
    `;

    modal.classList.remove("hidden");
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
        lucide.createIcons();
    }
}

function closeAuditDetailModal() {
    const modal = document.getElementById("modal-audit-detail");
    if (modal) modal.classList.add("hidden");
}

function selectAuditEvent(eventId) {
    openAuditDetailModal(eventId);
}

function printAuditCertificate() {
    window.print();
}

function exportAuditLogsToCSV() {
    const events = getUnifiedAuditEvents();
    let csv = "Log ID,Event Type,Date,Asset Tag,Movement From,Movement To,Authorized By,Reason / Remarks\n";

    events.forEach(e => {
        const isReloc = e.type === "relocation";
        const origin = isReloc ? e.fromLocation : (e.fromUserName || 'Spares');
        const target = isReloc ? e.toLocation : (e.userName || 'Staff');
        const reason = isReloc ? e.reason : e.remarks;

        csv += `"${e.id}","${isReloc ? 'Relocation' : 'Custody Handover'}","${e.date}","${e.assetId}","${origin}","${target}","${isReloc ? e.changedBy : e.assignedBy}","${(reason || '').replace(/"/g, '""')}"\n`;
    });

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `CampusAssetIQ_Audit_Traceability_Logs_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast("Audit logs exported to CSV successfully!", "success");
}


// TAB 6: ASSET TAG CENTER
// ============================================================================

function renderQRTagCenter() {
    const devices = getFilteredDevices();
    renderStickerCards(devices);
}

// ============================================================================
// CSV Export & Toast Notifications
// ============================================================================

function getDeviceExportData(d) {
    const devType = (d.deviceType || '').trim() || 'CPU';
    const typeUpper = devType.toUpperCase();

    // 1. Resolve Location Details
    const room = (appState.rooms || []).find(r => r.id === d.roomId || (r.name && d.roomName && r.name.toLowerCase() === d.roomName.toLowerCase()));
    const floor = (appState.floors || []).find(f => (room && f.id === room.floorId) || (d.floorName && f.name && f.name.toLowerCase().includes(d.floorName.toLowerCase())));
    const bldg = (appState.buildings || []).find(b => (floor && b.id === floor.buildingId) || (d.buildingName && b.name && b.name.toLowerCase().includes(d.buildingName.toLowerCase())));
    const org = (appState.organizations || []).find(o => o.id === (d.orgId || 'HOSP'));

    const bldgName = d.buildingName || (bldg ? bldg.name : 'PSM Hospital Main');
    const floorName = d.floorName || (floor ? floor.name : '—');
    const roomName = d.roomName || (room ? `${room.roomNumber ? `Rm ${room.roomNumber} - ` : ''}${room.name}` : '—');

    // 2. Resolve Custodian Details
    let user = (appState.users || []).find(u => 
        (u.id && d.assignedUserId && u.id === d.assignedUserId) ||
        (u.empId && (u.empId === d.empId || u.empId === d.assignedEmpId))
    );
    if (!user && d.assignedUserName && d.assignedUserName.toLowerCase() !== 'unassigned') {
        user = (appState.users || []).find(u => u.fullName && u.fullName.toLowerCase() === d.assignedUserName.toLowerCase());
    }

    const assignedName = (d.assignedUserName || (user ? user.fullName : '') || '').trim();
    const isUnassigned = !assignedName || assignedName.toLowerCase() === 'unassigned' || assignedName.toLowerCase().includes('hardware pool');

    const custodianName = isUnassigned ? 'Unassigned' : assignedName;
    const custodianEmpId = isUnassigned ? '—' : (d.empId || d.assignedEmpId || (user ? user.empId : '—') || '—');
    const custodianDept = isUnassigned ? '—' : (d.department || d.assignedDepartment || (user ? user.department : '—') || '—');
    const custodianDesig = isUnassigned ? '—' : (d.designation || d.assignedDesignation || (user ? user.designation : '—') || '—');
    const custodianContact = isUnassigned ? '—' : (d.email || d.assignedEmail || d.phone || d.assignedPhone || (user ? (user.email || user.phone) : '') || '—');

    // 3. Resolve Brand
    let brand = (d.brandName || d.brand || '').trim();
    if (!brand || brand.toLowerCase() === 'enterprise medical grade') {
        if (typeUpper.includes('CPU') || typeUpper.includes('DESKTOP') || typeUpper.includes('PC')) brand = 'Dell';
        else if (typeUpper.includes('DISPLAY')) brand = 'Dell';
        else if (typeUpper.includes('KEYBOARD') || typeUpper.includes('MOUSE')) brand = 'Dell';
        else if (typeUpper.includes('PRINTER')) brand = 'HP';
        else if (typeUpper.includes('UPS')) brand = 'APC';
        else if (typeUpper.includes('TABLET')) brand = 'Samsung';
        else brand = 'Standard OEM';
    }

    // 4. Resolve Model / Hardware Specification Summary
    let modelSpec = '—';
    if (typeUpper.includes('DISPLAY')) {
        modelSpec = d.monitorSpec || d.cpuProcessor || '24" FHD IPS Medical Display';
    } else if (typeUpper.includes('KEYBOARD')) {
        modelSpec = d.keyboardSpec || d.cpuProcessor || 'Dell KB216 USB Wired Keyboard';
    } else if (typeUpper.includes('MOUSE')) {
        modelSpec = d.mouseSpec || d.cpuProcessor || 'Dell MS116 USB Optical Cleanable Mouse';
    } else if (typeUpper.includes('PRINTER')) {
        modelSpec = d.printerSpec || d.cpuProcessor || 'HP LaserJet Pro Network Printer';
    } else if (typeUpper.includes('UPS')) {
        modelSpec = d.upsSpec || d.cpuProcessor || 'APC Back-UPS 1100VA Surge Protected';
    } else if (typeUpper.includes('TABLET')) {
        modelSpec = d.tabletSpec || d.cpuProcessor || 'Samsung Galaxy Tab Active Touch Terminal';
    } else if (typeUpper.includes('CPU') || typeUpper.includes('DESKTOP') || typeUpper.includes('PC')) {
        modelSpec = `${brand} OptiPlex (${d.cpuProcessor || 'Tower PC'})`;
    } else {
        modelSpec = d.cpuProcessor || d.monitorSpec || `${brand} Hardware Unit`;
    }

    // 5. Compute Specifics (Processor, RAM, OS, Monitor)
    const isCompute = typeUpper.includes('CPU') || typeUpper.includes('DESKTOP') || typeUpper.includes('PC') || typeUpper.includes('TOWER') || typeUpper.includes('WORKSTATION');
    const isTablet = typeUpper.includes('TABLET') || typeUpper.includes('TAB');

    let processor = '—';
    let ramStorage = '—';
    let monitorSpec = '—';
    let operatingSystem = '—';

    if (isCompute || isTablet) {
        processor = d.cpuProcessor || '—';
        ramStorage = d.storageRam || '—';
        operatingSystem = d.operatingSystem || 'Windows 11 Pro Medical Edition';
        monitorSpec = d.monitorSpec || '—';
    } else if (typeUpper.includes('DISPLAY')) {
        monitorSpec = d.monitorSpec || d.cpuProcessor || '24" FHD IPS Display';
    } else if (typeUpper.includes('PRINTER')) {
        operatingSystem = (d.operatingSystem && !d.operatingSystem.toLowerCase().includes('windows')) ? d.operatingSystem : 'Firmware Embedded';
    }

    // 6. Network & Remote ID
    const ipAddress = (d.ipAddress && d.ipAddress !== '-' && d.ipAddress !== 'N/A') ? d.ipAddress : '—';
    const macAddress = (d.macAddress && d.macAddress !== '-' && d.macAddress !== 'N/A') ? d.macAddress : '—';
    const anydeskId = (d.anydeskId && d.anydeskId !== '-' && d.anydeskId !== 'N/A') ? d.anydeskId : '—';

    return {
        "Asset Tag": d.assetId || '—',
        "Device Type": devType,
        "Brand / Make": brand,
        "Hardware Model & Specs": modelSpec,
        "Serial Number": d.serialNumber || '—',
        "Processor (CPU)": processor,
        "RAM & Storage": ramStorage,
        "Monitor / Screen": monitorSpec,
        "Operating System": operatingSystem,
        "IP Address": ipAddress,
        "MAC Address": macAddress,
        "AnyDesk Remote ID": anydeskId,
        "Campus Organization": org ? org.name : 'PSM Hospital',
        "Building": bldgName,
        "Floor": floorName,
        "Room / Location": roomName,
        "Assigned Custodian": custodianName,
        "Employee ID": custodianEmpId,
        "Department": custodianDept,
        "Designation": custodianDesig,
        "Custodian Contact": custodianContact,
        "Hardware Status": d.status || 'Active',
        "Purchase Date": d.purchaseDate || '—',
        "Warranty Expiry": d.warrantyExpiryDate || '—'
    };
}

function exportToCSV() {
    let rawDevices = getFilteredDevices();
    if (!rawDevices || rawDevices.length === 0) {
        showToast("No devices available in inventory to export.", "info");
        return;
    }

    // Expand composite workstations if present so all linked peripherals are included
    const devices = [];
    rawDevices.forEach(d => {
        if (typeof isCompositeWorkstation === 'function' && isCompositeWorkstation(d)) {
            const comps = expandCompositeWorkstation(d);
            comps.forEach(c => devices.push(c));
        } else {
            devices.push(d);
        }
    });

    const exportRows = devices.map(d => getDeviceExportData(d));
    if (exportRows.length === 0) return;

    const headers = Object.keys(exportRows[0]);
    
    // Build CSV with RFC 4180 compliance & UTF-8 BOM (\uFEFF) for Microsoft Excel
    let csvContent = "\uFEFF" + headers.map(h => `"${h.replace(/"/g, '""')}"`).join(",") + "\r\n";

    exportRows.forEach(row => {
        const line = headers.map(h => {
            const val = String(row[h] === undefined || row[h] === null ? '' : row[h]);
            return `"${val.replace(/"/g, '""')}"`;
        }).join(",");
        csvContent += line + "\r\n";
    });

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `PSM_Hospital_Hardware_Inventory_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast("Hardware specs & workstation CSV report exported successfully!", "success");
}

function exportToExcel() {
    let rawDevices = getFilteredDevices();
    if (!rawDevices || rawDevices.length === 0) {
        showToast("No devices available in inventory to export.", "info");
        return;
    }

    const devices = [];
    rawDevices.forEach(d => {
        if (typeof isCompositeWorkstation === 'function' && isCompositeWorkstation(d)) {
            const comps = expandCompositeWorkstation(d);
            comps.forEach(c => devices.push(c));
        } else {
            devices.push(d);
        }
    });

    const exportRows = devices.map(d => getDeviceExportData(d));
    if (exportRows.length === 0) return;

    if (typeof XLSX !== 'undefined') {
        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.json_to_sheet(exportRows);

        // Auto-fit column widths based on maximum string length
        const colWidths = Object.keys(exportRows[0]).map(key => {
            const maxLen = Math.max(
                key.length,
                ...exportRows.map(r => String(r[key] || '').length)
            );
            return { wch: Math.min(Math.max(maxLen + 2, 12), 40) };
        });
        ws['!cols'] = colWidths;

        XLSX.utils.book_append_sheet(wb, ws, "Hardware Inventory");
        XLSX.writeFile(wb, `PSM_Hospital_Hardware_Inventory_${new Date().toISOString().split('T')[0]}.xlsx`);
        showToast("Formatted Excel (.xlsx) spreadsheet exported successfully!", "success");
    } else {
        // Fallback to CSV if XLSX library is unavailable
        exportToCSV();
    }
}

function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    const bgClass =
        type === "success" ? "bg-emerald-600 text-white" :
            type === "error" ? "bg-rose-600 text-white" :
                "bg-slate-900 text-white";

    toast.className = `p-3.5 rounded-xl shadow-xl flex items-center justify-between gap-3 text-xs font-semibold ${bgClass} pointer-events-auto animate-scale-up`;
    toast.innerHTML = `
        <div class="flex items-center gap-2">
            <i data-lucide="${type === 'success' ? 'check-circle' : type === 'error' ? 'alert-circle' : 'info'}" class="w-4 h-4"></i>
            <span>${message}</span>
        </div>
        <button onclick="this.parentElement.remove()" class="text-white/80 hover:text-white">&times;</button>
    `;

    container.appendChild(toast);
    lucide.createIcons();

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Master Render All Components for active page
function renderAll() {
    updateEntityUI();

    // 1. Devices Inventory Page Elements
    if (document.getElementById("inventory-table-tbody")) {
        populateFilterDropdowns();
        renderInventoryTable();
        renderStats();
    }

    // 2. Location Explorer Page Elements
    if (document.getElementById("location-birdseye-container") || document.getElementById("hospital-floor-switcher") || document.getElementById("location-tree-container") || document.getElementById("locations-grid-container")) {
        renderLocationsExplorer();
    }

    // 3. Staff & Users Page Elements
    if (document.getElementById("users-directory-container")) {
        renderUsersDirectory();
    }

    // 4. Audit & History Logs Page Elements
    if (document.getElementById("audit-table-tbody") || document.getElementById("audit-events-list") || document.getElementById("audit-location-tbody") || document.getElementById("audit-assignment-tbody")) {
        renderAuditLogs();
    }

    // 5. Asset Tag Center Page Elements
    if (document.getElementById("qr-tags-grid")) {
        renderQRTagCenter();
    }

    // Landing Portal Page Elements
    if (document.getElementById("landing-uni-devices")) {
        updateLandingCounts();
    }

    if (window.lucide && typeof window.lucide.createIcons === 'function') {
        lucide.createIcons();
    }
}

// Helper to retrieve CSRF token for secure POST requests
function getCsrfToken() {
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    if (input) return input.value;
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

// Live sync hardware devices from central PostgreSQL database
async function syncDevicesFromDatabase() {
    try {
        const response = await fetch('/api/devices/');
        if (!response.ok) return;
        const data = await response.json();
        if (data.success && Array.isArray(data.devices)) {
            data.devices.forEach(dbDev => {
                if (!dbDev.roomId && dbDev.roomName) {
                    const matchRoom = (appState.rooms || []).find(r =>
                        r.name.toLowerCase().includes(dbDev.roomName.toLowerCase()) ||
                        dbDev.roomName.toLowerCase().includes(r.name.toLowerCase())
                    );
                    if (matchRoom) {
                        dbDev.roomId = matchRoom.id;
                    } else if (appState.rooms && appState.rooms.length > 0) {
                        dbDev.roomId = appState.rooms[0].id;
                    }
                }
            });
            appState.devices = data.devices;
            saveAppState();
            renderAll();
        }
    } catch (err) {
        console.warn("Live database sync fallback to local cache:", err);
    }
}

// Live sync custody handover history logs from database
async function syncAuditLogsFromDatabase() {
    try {
        const response = await fetch('/api/audit-logs/');
        if (!response.ok) return;
        const data = await response.json();
        if (data.success && Array.isArray(data.logs)) {
            data.logs.forEach(log => {
                const exists = appState.assignmentHistories.some(ah => ah.id === `db-${log.id}`);
                if (!exists) {
                    appState.assignmentHistories.unshift({
                        id: `db-${log.id}`,
                        deviceId: log.deviceAssetId,
                        userId: null,
                        fromUserName: log.fromUserName,
                        toUserName: log.toUserName,
                        fromDate: log.handoverDate,
                        toDate: "-",
                        location: "Campus Lab",
                        assignedBy: log.assignedBy,
                        remarks: log.remarks
                    });
                }
            });
            saveAppState();
            renderAll();
        }
    } catch (err) {
        console.warn("Audit logs sync fallback:", err);
    }
}

// Robust Application Initialization (guaranteed idempotent single-execution)
let isCampusTrackerAppInitialized = false;

function initCampusTrackerApp() {
    if (isCampusTrackerAppInitialized) return;
    isCampusTrackerAppInitialized = true;

    initAppState();
    renderAll();
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
        lucide.createIcons();
    }

    // Check if server-side data was already provided in the HTML payload
    const hasServerPayload = document.getElementById('server-devices-payload');
    if (!hasServerPayload) {
        // Fallback to client-side fetch only if server payload was not present
        syncDevicesFromDatabase();
        syncAuditLogsFromDatabase();
    }

    if (window.initTableDragScroll) window.initTableDragScroll();

    // Auto-open Add Device Modal if requested via URL param (from other admin pages)
    try {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get("openAddModal") === "true") {
            setTimeout(() => openAddDeviceModal(), 180);
        }
    } catch (e) { }
}

// Ensure execution exactly once when the DOM is ready
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCampusTrackerApp, { once: true });
} else {
    initCampusTrackerApp();
}
