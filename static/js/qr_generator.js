// CampusAssetIQ — High-Precision Vector QR & Asset Sticker Card Generator
// Screen: Rich Workstation Cards (User, Category, Location, Status & QR)
// Print: Strict A4 Sticker Engine (5.0 cm x 2.5 cm, 4 Columns x 12 Rows = 48 Stickers/Page)

let currentStickerLayout = 'standard';

function setStickerLayout(mode) {
    currentStickerLayout = mode;
    if (typeof getFilteredDevices === 'function') {
        renderStickerCards(getFilteredDevices());
    } else if (typeof appState !== 'undefined' && appState.devices) {
        renderStickerCards(appState.devices);
    }
}

// Helper to parse Asset Tag into readable components
// e.g. "PSM/IT/0826/001" -> prefix: "PSM/IT", code: "0826/001", full: "PSM/IT/0826/001"
function parseAssetIdParts(assetId) {
    const raw = (assetId || '').trim();
    if (!raw) return { prefix: 'PSM/IT', code: '000', full: 'PSM/IT/000', isSplit: true };
    
    const parts = raw.split('/');
    if (parts.length === 4 && /^\d{4}$/.test(parts[2])) {
        // Standard PSM / IT / MMYY / XXX -> Prefix: PSM/IT, Code: MMYY/XXX (e.g. 0826/001)
        return {
            prefix: parts[0] + '/' + parts[1],
            code: parts[2] + '/' + parts[3],
            full: raw,
            isSplit: true
        };
    } else if (parts.length >= 3) {
        return {
            prefix: parts.slice(0, parts.length - 1).join('/'),
            code: parts[parts.length - 1],
            full: raw,
            isSplit: true
        };
    } else if (parts.length === 2) {
        return {
            prefix: parts[0],
            code: parts[1],
            full: raw,
            isSplit: true
        };
    }
    return { prefix: 'TAG', code: raw, full: raw, isSplit: false };
}

// Standard ISO 18004 Vector QR Code Generator (Pure SVG, 100% vector scalability)
function generateQRSVG(dataString, size = 70, extraClass = '') {
    if (typeof qrcode !== 'undefined') {
        try {
            // Type 0 auto-detects minimum Version (v1 to v40) to fit URL size; 'M' error correction
            const qr = qrcode(0, 'M');
            qr.addData(dataString);
            qr.make();
            const count = qr.getModuleCount();
            const cellSize = (size / count).toFixed(3);
            let rects = "";

            for (let r = 0; r < count; r++) {
                for (let c = 0; c < count; c++) {
                    if (qr.isDark(r, c)) {
                        const x = (c * (size / count)).toFixed(2);
                        const y = (r * (size / count)).toFixed(2);
                        rects += `<rect x="${x}" y="${y}" width="${cellSize}" height="${cellSize}" fill="#0f172a" />`;
                    }
                }
            }

            const cls = extraClass || 'sticker-qr-svg rounded-lg bg-white p-1 border border-slate-200 shadow-2xs';
            return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg" class="${cls}">
                ${rects}
            </svg>`;
        } catch (err) {
            console.warn("Standard ISO QR Generator error, using fallback matrix", err);
        }
    }

    // High-contrast fallback vector matrix
    const gridSize = 21;
    const cellSize = size / gridSize;
    let rects = "";

    let hash = 0;
    for (let i = 0; i < dataString.length; i++) {
        hash = (hash << 5) - hash + dataString.charCodeAt(i);
        hash |= 0;
    }

    function drawFinder(startX, startY) {
        rects += `<rect x="${startX * cellSize}" y="${startY * cellSize}" width="${7 * cellSize}" height="${7 * cellSize}" fill="#0f172a" rx="1" />`;
        rects += `<rect x="${(startX + 1) * cellSize}" y="${(startY + 1) * cellSize}" width="${5 * cellSize}" height="${5 * cellSize}" fill="#ffffff" />`;
        rects += `<rect x="${(startX + 2) * cellSize}" y="${(startY + 2) * cellSize}" width="${3 * cellSize}" height="${3 * cellSize}" fill="#0f172a" rx="0.5" />`;
    }

    drawFinder(0, 0);
    drawFinder(gridSize - 7, 0);
    drawFinder(0, gridSize - 7);

    for (let i = 8; i < gridSize - 8; i += 2) {
        rects += `<rect x="${i * cellSize}" y="${6 * cellSize}" width="${cellSize * 0.95}" height="${cellSize * 0.95}" fill="#0f172a" />`;
        rects += `<rect x="${6 * cellSize}" y="${i * cellSize}" width="${cellSize * 0.95}" height="${cellSize * 0.95}" fill="#0f172a" />`;
    }

    const alignX = gridSize - 7;
    const alignY = gridSize - 7;
    rects += `<rect x="${alignX * cellSize}" y="${alignY * cellSize}" width="${5 * cellSize}" height="${5 * cellSize}" fill="#0f172a" rx="0.5" />`;
    rects += `<rect x="${(alignX + 1) * cellSize}" y="${(alignY + 1) * cellSize}" width="${3 * cellSize}" height="${3 * cellSize}" fill="#ffffff" />`;
    rects += `<rect x="${(alignX + 2) * cellSize}" y="${(alignY + 2) * cellSize}" width="${cellSize}" height="${cellSize}" fill="#0f172a" />`;

    for (let r = 0; r < gridSize; r++) {
        for (let c = 0; c < gridSize; c++) {
            if ((r < 8 && c < 8) || (r < 8 && c > gridSize - 9) || (r > gridSize - 9 && c < 8)) continue;
            if (r === 6 || c === 6) continue;
            if (r >= alignX - 1 && r <= alignX + 5 && c >= alignY - 1 && c <= alignY + 5) continue;

            const bit = Math.abs(Math.sin(hash + r * 37 + c * 19 + (r ^ c))) > 0.46;
            if (bit) {
                rects += `<rect x="${c * cellSize}" y="${r * cellSize}" width="${cellSize * 0.92}" height="${cellSize * 0.92}" rx="0.5" fill="#0f172a" />`;
            }
        }
    }

    const cls = extraClass || 'sticker-qr-svg rounded-lg bg-white p-1 border border-slate-200 shadow-2xs';
    return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg" class="${cls}">
        ${rects}
    </svg>`;
}

// Group devices by unique asset tag so multiple components sharing an asset ID render as ONE single tag card
function groupDevicesByAssetId(devices) {
    if (!devices || !Array.isArray(devices) || devices.length === 0) return [];

    const order = ['CPU', 'Display', 'Keyboard', 'Mouse', 'Printer', 'UPS', 'Tablet', 'Other'];
    const groups = new Map();

    devices.forEach(dev => {
        const rawTag = (dev.assetId || dev.id || '').trim();
        if (!rawTag) return;
        const key = rawTag.toUpperCase();

        if (!groups.has(key)) {
            groups.set(key, {
                primary: dev,
                all: [],
                components: []
            });
        }

        const entry = groups.get(key);
        entry.all.push(dev);

        let rawType = (dev.deviceType || '').trim();
        if (rawType) {
            rawType = rawType.replace(/workstation/gi, '').trim();
            if (rawType.includes('(') && rawType.includes(')')) {
                const inner = rawType.substring(rawType.indexOf('(') + 1, rawType.lastIndexOf(')'));
                inner.split(',').map(s => s.trim()).forEach(x => {
                    if (x && !entry.components.includes(x)) entry.components.push(x);
                });
            } else if (rawType && !entry.components.includes(rawType)) {
                entry.components.push(rawType);
            }
        }
    });

    const result = [];
    groups.forEach(entry => {
        const cpuDev = entry.all.find(d => (d.deviceType || '').toUpperCase().includes('CPU'));
        const primary = { ...(cpuDev || entry.primary) };

        const comps = entry.components.sort((a, b) => {
            const idxA = order.indexOf(a) !== -1 ? order.indexOf(a) : 99;
            const idxB = order.indexOf(b) !== -1 ? order.indexOf(b) : 99;
            return idxA - idxB;
        });

        if (comps.length > 1) {
            primary.deviceType = comps.join(', ');
        } else if (comps.length === 1) {
            primary.deviceType = comps[0];
        } else {
            primary.deviceType = 'CPU';
        }

        if (!primary.serialNumber || primary.serialNumber === 'N/A') {
            const snDev = entry.all.find(d => d.serialNumber && d.serialNumber !== 'N/A');
            if (snDev) primary.serialNumber = snDev.serialNumber;
        }

        result.push(primary);
    });

    return result;
}

// Master Render Function: Displays previous spacious cards on screen, while strictly formatting into 5cm x 2.5cm (4x12) on print
function renderStickerCards(devices) {
    const container = document.getElementById("qr-stickers-grid");
    if (!container) return;

    // Group devices by unique asset tag
    const uniqueDevices = groupDevicesByAssetId(devices);

    if (!uniqueDevices || uniqueDevices.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-16 bg-white rounded-2xl border border-slate-200 shadow-2xs p-8 max-w-2xl mx-auto my-6">
                <i data-lucide="inbox" class="w-12 h-12 text-slate-300 mx-auto mb-3"></i>
                <div class="text-base font-bold text-slate-700">No hardware assets found</div>
                <p class="text-xs text-slate-400 mt-1">Try clearing your search query or organization filter to view and print stickers.</p>
            </div>
        `;
        if (window.lucide && typeof window.lucide.createIcons === 'function') {
            lucide.createIcons();
        }
        return;
    }

    const typeLabels = { 'C': 'CPU', 'D': 'Display', 'M': 'Mouse', 'K': 'Keyboard', 'P': 'Printer', 'T': 'Tablet', 'U': 'UPS', 'L': 'Laptop' };
    const typeColors = {
        'C': 'bg-blue-50 text-blue-700 border-blue-200',
        'D': 'bg-sky-50 text-sky-700 border-sky-200',
        'M': 'bg-purple-50 text-purple-700 border-purple-200',
        'K': 'bg-amber-50 text-amber-700 border-amber-200',
        'P': 'bg-emerald-50 text-emerald-700 border-emerald-200',
        'T': 'bg-teal-50 text-teal-700 border-teal-200',
        'U': 'bg-orange-50 text-orange-700 border-orange-200',
        'L': 'bg-indigo-50 text-indigo-700 border-indigo-200'
    };

    container.innerHTML = uniqueDevices.map(dev => {
        // 1. Resolve Location text cleanly from device directly or appState
        const room = (typeof appState !== 'undefined' && appState.rooms) ? appState.rooms.find(r => r.id === dev.roomId) : null;
        const floor = (room && typeof appState !== 'undefined' && appState.floors) ? appState.floors.find(f => f.id === room.floorId) : null;
        const org = (typeof appState !== 'undefined' && appState.organizations) ? appState.organizations.find(o => o.id === dev.orgId) : null;
        const user = (typeof appState !== 'undefined' && appState.users) ? appState.users.find(u => u.id === dev.assignedUserId) : null;

        const floorText = dev.floorName || (floor ? (floor.shortName || floor.name) : (dev.buildingName || "Hospital Wing"));
        const roomText = dev.roomName || (room ? room.name : "Medical Complex");
        const orgName = dev.orgName || (org ? org.name : 'PSM HOSPITAL');

        // 2. Resolve Device Type (CPU, Display, Mouse, Keyboard, Printer, Tablet, UPS, Laptop)
        let typeCode = 'C';
        let typeLabel = 'CPU';
        if (dev.deviceType) {
            let cleanType = String(dev.deviceType)
                .replace(/workstation\s*\(/gi, '')
                .replace(/workstation/gi, '')
                .replace(/^\s*\(+|\)+\s*$/g, '')
                .trim();
            if (!cleanType) cleanType = 'CPU';

            const dtUpper = cleanType.toUpperCase();
            if (dtUpper.includes(',') || (dtUpper.includes('CPU') && dtUpper.includes('DISPLAY'))) {
                typeCode = 'C';
                typeLabel = cleanType;
            }
            else if (dtUpper.includes('DISP') || dtUpper.includes('MONITOR') || dtUpper === 'D') { typeCode = 'D'; typeLabel = 'Display'; }
            else if (dtUpper.includes('KEYB') || dtUpper === 'K') { typeCode = 'K'; typeLabel = 'Keyboard'; }
            else if (dtUpper.includes('MOUS') || dtUpper === 'M') { typeCode = 'M'; typeLabel = 'Mouse'; }
            else if (dtUpper.includes('PRINT') || dtUpper === 'P') { typeCode = 'P'; typeLabel = 'Printer'; }
            else if (dtUpper.includes('TAB') || dtUpper === 'T') { typeCode = 'T'; typeLabel = 'Tablet'; }
            else if (dtUpper.includes('UPS') || dtUpper === 'U') { typeCode = 'U'; typeLabel = 'UPS'; }
            else if (dtUpper.includes('LAP') || dtUpper === 'L') { typeCode = 'L'; typeLabel = 'Laptop'; }
            else { 
                typeCode = 'C'; 
                typeLabel = cleanType; 
            }
        } else {
            const aid = (dev.assetId || '').toUpperCase();
            const typeMatch = aid.match(/\/([CDKMPTU])(?:\/|-|\.)/);
            typeCode = (typeMatch ? typeMatch[1] : 'C').toUpperCase();
            typeLabel = typeLabels[typeCode] || 'CPU';
        }

        // 3. Resolve Assigned User / Custodian
        let userName = "Hospital Spare / General";
        if (dev.assignedUserName && dev.assignedUserName.trim() && dev.assignedUserName !== 'Unassigned') {
            userName = dev.assignedUserName.trim();
        } else if (user && user.fullName) {
            userName = user.fullName;
        }

        // 4. Resolve Direct mobile report URL for smartphone QR code scanning
        const parsed = parseAssetIdParts(dev.assetId);
        const reportUrl = `${window.location.origin}/report/${encodeURIComponent(dev.assetId)}/`;
        const qrSVG = generateQRSVG(reportUrl, 70);

        // Previous spacious card on screen + strict 50x25mm print layout when printing
        return `
            <div class="sticker-card bg-white border-2 border-slate-900 rounded-2xl p-3.5 shadow-sm text-slate-900 flex flex-col justify-between select-none relative transition-all hover:shadow-md aspect-[1.9/1] min-h-[178px] w-full" data-asset-id="${dev.assetId}">
                <!-- 1. UPPER SECTION (Visible on Screen, Hidden on Print): Brand, User, Device Type & Location -->
                <div class="sticker-screen-only print:hidden space-y-1.5 pb-2.5 border-b-2 border-slate-900 flex-1 flex flex-col justify-between">
                    <!-- Row 1: Brand & Status & 1-Click Print Tag -->
                    <div class="flex items-center justify-between gap-1.5">
                        <div class="flex items-center gap-1.5 min-w-0">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block shrink-0 shadow-2xs"></span>
                            <span class="text-xs font-black tracking-wider uppercase text-slate-950 truncate">${orgName}</span>
                        </div>
                        <div class="flex items-center gap-1 shrink-0">
                            <button type="button" onclick="printSingleTag('${dev.assetId}')" title="Print this tag only (5cm x 2.5cm)" class="no-print p-1 rounded-md text-slate-400 hover:text-indigo-600 hover:bg-slate-100 transition-colors cursor-pointer flex items-center gap-1 text-[9px] font-bold">
                                <i data-lucide="printer" class="w-3.5 h-3.5"></i>
                                <span class="hidden sm:inline">Print Tag</span>
                            </button>
                            <span class="text-[8.5px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-300 px-2 py-0.5 rounded-md font-mono shrink-0">${dev.status || 'Active'}</span>
                        </div>
                    </div>

                    <!-- Row 2: Prominent Assigned User & Device Type Below -->
                    <div class="space-y-0.5 py-0.5">
                        <span class="text-[8px] uppercase font-bold tracking-widest text-slate-400 block leading-none">ASSIGNED USER / CUSTODIAN</span>
                        <div class="text-sm sm:text-[15px] font-black text-slate-950 truncate leading-tight" title="${userName}">
                            ${userName}
                        </div>
                        <div class="flex items-center gap-1.5 pt-0.5 min-w-0">
                            <span class="text-[11px] font-bold text-slate-700 shrink-0">Device Type:</span>
                            <span class="text-xs sm:text-[13px] font-extrabold text-slate-950 truncate" title="${typeLabel}">${typeLabel}</span>
                        </div>
                    </div>

                    <!-- Row 3: Location Breadcrumb -->
                    <div class="text-[9.5px] font-medium text-slate-500 truncate flex items-center gap-1">
                        <span class="font-semibold text-slate-700">${floorText}</span>
                        <span>&bull;</span>
                        <span class="truncate">${roomText}</span>
                    </div>
                </div>

                <!-- 2. LOWER SECTION: On Screen shows dark asset box + QR; On Print fills 5cm x 2.5cm sticker with Asset ID & QR -->
                <div class="sticker-print-content pt-2 flex items-center justify-between gap-2.5 print:p-0 print:w-full print:h-full print:gap-1.5">
                    <!-- Left Column: Asset ID Details -->
                    <div class="sticker-print-left w-[65%] min-w-0 print:w-auto print:flex-1">
                        <!-- Screen Display: Dark Pill -->
                        <div class="bg-slate-900 text-white rounded-lg px-2.5 py-2 shadow-2xs print:hidden flex items-center">
                            <span class="text-sm sm:text-base font-black font-mono tracking-wide text-white select-all block whitespace-nowrap leading-none">${dev.assetId}</span>
                        </div>

                        <!-- Print Display: Calibrated 50mm x 25mm High-Contrast Layout -->
                        <div class="hidden print:flex flex-col justify-center">
                            <div class="sticker-print-brand">PSM HOSPITAL</div>
                            <div class="sticker-print-prefix">${parsed.prefix}</div>
                            <div class="sticker-print-code">${parsed.code}</div>
                            <div class="sticker-print-full" title="${userName}">${userName}</div>
                        </div>
                    </div>

                    <!-- Right Column: Scannable Vector QR Code -->
                    <div class="sticker-print-qr w-[35%] flex items-center justify-end shrink-0 print:w-[17.5mm] print:h-[17.5mm]">
                        ${qrSVG}
                    </div>
                </div>
            </div>
        `;
    }).join('');

    if (typeof window !== 'undefined' && window.lucide && typeof window.lucide.createIcons === 'function') {
        window.lucide.createIcons();
    }
}

// Dedicated 1-Click Single Asset Tag Printer (Zero-overflow calibrated to 1 physical sticker: 25mm x 50mm)
function printSingleTag(assetId) {
    const rawDevs = (typeof appState !== 'undefined' && appState.devices) ? appState.devices : [];
    const dev = rawDevs.find(d => (d.assetId || '').toUpperCase() === (assetId || '').toUpperCase()) || { assetId };
    
    // Resolve Assigned User / Custodian
    const user = (typeof appState !== 'undefined' && appState.users) ? appState.users.find(u => u.id === dev.assignedUserId) : null;
    let userName = "Hospital Spare / General";
    if (dev.assignedUserName && dev.assignedUserName.trim() && dev.assignedUserName !== 'Unassigned') {
        userName = dev.assignedUserName.trim();
    } else if (user && user.fullName) {
        userName = user.fullName;
    }

    const parsed = parseAssetIdParts(dev.assetId);
    const reportUrl = `${window.location.origin}/report/${encodeURIComponent(dev.assetId)}/`;
    const qrSVG = generateQRSVG(reportUrl, 68);

    const printWindow = window.open('', '_blank', 'width=680,height=680');
    if (!printWindow) {
        window.print();
        return;
    }

    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Asset Tag — ${dev.assetId}</title>
            <style id="print-page-style">
                @page {
                    size: 25mm 50mm;
                    margin: 0;
                }
            </style>
            <style>
                *, *::before, *::after {
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                }
                html, body {
                    margin: 0;
                    padding: 0;
                    background: #0b0f19;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    color: #f1f5f9;
                }

                /* Top Navigation Toolbar (Screen view only) */
                .no-print-toolbar {
                    background: #111827;
                    border-bottom: 1px solid #1f2937;
                    padding: 10px 16px;
                    display: flex;
                    flex-wrap: wrap;
                    align-items: center;
                    justify-content: space-between;
                    gap: 10px;
                    position: sticky;
                    top: 0;
                    z-index: 100;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                }
                .toolbar-brand {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .toolbar-brand-title {
                    font-size: 13px;
                    font-weight: 700;
                    color: #e2e8f0;
                    letter-spacing: 0.3px;
                }
                .toolbar-asset-tag {
                    font-size: 11px;
                    font-family: ui-monospace, monospace;
                    font-weight: 800;
                    background: #1e293b;
                    color: #38bdf8;
                    border: 1px solid #0284c7;
                    padding: 2px 7px;
                    border-radius: 6px;
                }
                .toolbar-controls {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    flex-wrap: wrap;
                }
                .mode-btn {
                    background: #1e293b;
                    border: 1px solid #334155;
                    color: #cbd5e1;
                    padding: 6px 11px;
                    border-radius: 7px;
                    font-size: 11px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.15s ease;
                    display: inline-flex;
                    align-items: center;
                    gap: 4px;
                }
                .mode-btn:hover {
                    background: #334155;
                    color: #ffffff;
                }
                .mode-btn.active {
                    background: #0284c7;
                    border-color: #38bdf8;
                    color: #ffffff;
                    box-shadow: 0 0 10px rgba(56, 189, 248, 0.4);
                }
                .btn-print {
                    background: #16a34a;
                    border: 1px solid #22c55e;
                    color: #ffffff;
                    padding: 6px 14px;
                    border-radius: 7px;
                    font-size: 12px;
                    font-weight: 700;
                    cursor: pointer;
                    transition: all 0.15s ease;
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    box-shadow: 0 2px 8px rgba(34, 197, 94, 0.3);
                }
                .btn-print:hover {
                    background: #15803d;
                }

                /* Screen Stage & Preview */
                .stage {
                    padding: 24px 16px 40px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: calc(100vh - 65px);
                }
                .stage-info {
                    max-width: 520px;
                    width: 100%;
                    background: #131d31;
                    border: 1px solid #1e3a5f;
                    border-radius: 10px;
                    padding: 10px 14px;
                    margin-bottom: 20px;
                    font-size: 11px;
                    line-height: 1.45;
                    color: #94a3b8;
                    text-align: center;
                }
                .stage-info strong {
                    color: #38bdf8;
                }
                .stage-hint-accent {
                    color: #4ade80;
                    font-weight: 700;
                }

                /* Physical Sticker Preview Wrapper on Screen */
                .sticker-mount {
                    position: relative;
                    padding: 14px;
                    background: #1e293b;
                    border: 1px dashed #475569;
                    border-radius: 14px;
                    display: inline-block;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                }
                .sticker-dimension-label {
                    position: absolute;
                    font-size: 9px;
                    font-weight: 700;
                    color: #64748b;
                    letter-spacing: 0.5px;
                    text-transform: uppercase;
                }
                .dim-width {
                    top: 2px;
                    left: 50%;
                    transform: translateX(-50%);
                }
                .dim-height {
                    right: -24px;
                    top: 50%;
                    transform: translateY(-50%) rotate(90deg);
                }

                /* Main Sticker Canvas (25mm x 50mm on roll, or 50mm x 25mm direct) */
                .sticker-canvas {
                    background: #ffffff;
                    position: relative;
                    overflow: hidden;
                    box-sizing: border-box;
                    box-shadow: 0 4px 14px rgba(0,0,0,0.4);
                }

                /* Default: 25mm wide x 50mm tall (Standard Roll Orientation) */
                body.mode-rot90 .sticker-canvas,
                body.mode-rot270 .sticker-canvas,
                body.mode-stacked .sticker-canvas {
                    width: 25mm;
                    height: 50mm;
                    border-radius: 4px;
                }

                /* Alternate: 50mm wide x 25mm tall (Direct Horizontal) */
                body.mode-direct .sticker-canvas {
                    width: 50mm;
                    height: 25mm;
                    border-radius: 4px;
                }

                /* Mode: Rotated 90° (Standard Along Length - Side-by-side Text & QR on 1 sticker) */
                body.mode-rot90 .label-box-horizontal {
                    position: absolute;
                    top: 1mm;
                    left: 1mm;
                    width: 48mm;
                    height: 23mm;
                    transform-origin: 0 0;
                    transform: translate(23mm, 0) rotate(90deg);
                    display: flex !important;
                }
                body.mode-rot90 .label-box-stacked { display: none !important; }

                /* Mode: Rotated 270° (Reverse Along Length) */
                body.mode-rot270 .label-box-horizontal {
                    position: absolute;
                    top: 1mm;
                    left: 1mm;
                    width: 48mm;
                    height: 23mm;
                    transform-origin: 0 0;
                    transform: translate(0, 48mm) rotate(-90deg);
                    display: flex !important;
                }
                body.mode-rot270 .label-box-stacked { display: none !important; }

                /* Mode: Direct Horizontal (50mm x 25mm) */
                body.mode-direct .label-box-horizontal {
                    position: relative;
                    top: 0;
                    left: 0;
                    width: 48mm;
                    height: 23mm;
                    margin: 1mm auto;
                    transform: none;
                    display: flex !important;
                }
                body.mode-direct .label-box-stacked { display: none !important; }

                /* Mode: Upright Stacked (25mm x 50mm) */
                body.mode-stacked .label-box-horizontal { display: none !important; }
                body.mode-stacked .label-box-stacked {
                    position: relative;
                    top: 0;
                    left: 0;
                    width: 23mm;
                    height: 48mm;
                    margin: 1mm auto;
                    transform: none;
                    display: flex !important;
                }

                /* Inner Horizontal Label Card Structure (48mm x 23mm) */
                .label-box-horizontal {
                    box-sizing: border-box;
                    padding: 1.2mm 1.8mm;
                    align-items: center;
                    justify-content: space-between;
                    border: 0.5px solid #000000;
                    border-radius: 1mm;
                    background: #ffffff;
                    color: #000000;
                    overflow: hidden;
                }
                .label-h-info {
                    flex: 1;
                    min-width: 0;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    padding-right: 1.5mm;
                }
                .label-h-brand {
                    font-size: 5.5pt;
                    font-weight: 800;
                    letter-spacing: 0.4px;
                    text-transform: uppercase;
                    color: #334155;
                    line-height: 1;
                    margin-bottom: 0.4mm;
                }
                .label-h-prefix {
                    font-size: 6.5pt;
                    font-weight: 800;
                    color: #1e293b;
                    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                    line-height: 1;
                }
                .label-h-code {
                    font-size: 12.5pt;
                    font-weight: 900;
                    color: #000000;
                    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                    line-height: 1.05;
                    letter-spacing: -0.3px;
                    word-break: break-all;
                    margin: 0.2mm 0;
                }
                .label-h-user {
                    font-size: 6pt;
                    font-weight: 800;
                    color: #0f172a;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    text-transform: uppercase;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    line-height: 1.1;
                }
                .label-h-qr {
                    width: 16.5mm;
                    height: 16.5mm;
                    flex-shrink: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .label-h-qr svg {
                    width: 16.5mm;
                    height: 16.5mm;
                    display: block;
                    background: transparent;
                }

                /* Inner Upright Stacked Card Structure (23mm x 48mm) */
                .label-box-stacked {
                    box-sizing: border-box;
                    padding: 1.8mm 1.2mm;
                    flex-direction: column;
                    align-items: center;
                    justify-content: space-between;
                    border: 0.5px solid #000000;
                    border-radius: 1mm;
                    background: #ffffff;
                    color: #000000;
                    overflow: hidden;
                    text-align: center;
                }
                .label-s-brand {
                    font-size: 5pt;
                    font-weight: 800;
                    letter-spacing: 0.3px;
                    text-transform: uppercase;
                    color: #334155;
                    line-height: 1;
                }
                .label-s-prefix {
                    font-size: 6pt;
                    font-weight: 800;
                    color: #1e293b;
                    font-family: ui-monospace, monospace;
                    line-height: 1.1;
                    margin-top: 0.5mm;
                }
                .label-s-code {
                    font-size: 11pt;
                    font-weight: 900;
                    color: #000000;
                    font-family: ui-monospace, monospace;
                    line-height: 1.05;
                    letter-spacing: -0.3px;
                }
                .label-s-user {
                    font-size: 5.5pt;
                    font-weight: 800;
                    color: #0f172a;
                    text-transform: uppercase;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    max-width: 20mm;
                    line-height: 1.1;
                    margin-bottom: 0.8mm;
                }
                .label-s-qr {
                    width: 17mm;
                    height: 17mm;
                    flex-shrink: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .label-s-qr svg {
                    width: 17mm;
                    height: 17mm;
                    display: block;
                    background: transparent;
                }

                /* Clean Print Media Output */
                @media print {
                    .no-print, .no-print-toolbar, .stage-info, .sticker-dimension-label {
                        display: none !important;
                    }
                    html, body {
                        background: #ffffff !important;
                        margin: 0 !important;
                        padding: 0 !important;
                        overflow: hidden !important;
                        width: 100% !important;
                        height: 100% !important;
                    }
                    .stage {
                        padding: 0 !important;
                        margin: 0 !important;
                        min-height: 0 !important;
                        display: block !important;
                        width: 100% !important;
                        height: 100% !important;
                    }
                    .sticker-mount {
                        padding: 0 !important;
                        margin: 0 !important;
                        border: none !important;
                        box-shadow: none !important;
                        background: transparent !important;
                        display: block !important;
                    }
                    .sticker-canvas {
                        border-radius: 0 !important;
                        box-shadow: none !important;
                        margin: 0 !important;
                    }
                    body.mode-rot90 .sticker-canvas,
                    body.mode-rot270 .sticker-canvas,
                    body.mode-stacked .sticker-canvas {
                        width: 25mm !important;
                        height: 50mm !important;
                    }
                    body.mode-direct .sticker-canvas {
                        width: 50mm !important;
                        height: 25mm !important;
                    }
                    .label-box-horizontal,
                    .label-box-stacked {
                        border: 0.5px solid #000000 !important;
                        page-break-inside: avoid !important;
                        break-inside: avoid !important;
                    }
                }
            </style>
        </head>
        <body class="mode-rot90">
            <!-- Screen Toolbar -->
            <div class="no-print-toolbar no-print">
                <div class="toolbar-brand">
                    <span class="toolbar-brand-title">PSM Single Sticker Print</span>
                    <span class="toolbar-asset-tag">${dev.assetId}</span>
                </div>
                <div class="toolbar-controls">
                    <button type="button" class="mode-btn active" id="btn-rot90" onclick="setMode('rot90')">
                        📐 90° Rotated (1 Sticker)
                    </button>
                    <button type="button" class="mode-btn" id="btn-rot270" onclick="setMode('rot270')">
                        🔄 270° Rotated
                    </button>
                    <button type="button" class="mode-btn" id="btn-direct" onclick="setMode('direct')">
                        📏 Direct (50×25mm)
                    </button>
                    <button type="button" class="mode-btn" id="btn-stacked" onclick="setMode('stacked')">
                        📱 Upright Stacked
                    </button>
                    <button type="button" class="btn-print" onclick="window.print()">
                        🖨️ Print Sticker
                    </button>
                </div>
            </div>

            <!-- Stage Preview -->
            <div class="stage">
                <div class="stage-info no-print" id="stage-desc">
                    <span class="stage-hint-accent">✅ Active Layout: Rotated 90°</span>. Both Text & QR code fit completely on <strong>1 single physical sticker (25mm × 50mm)</strong> without splitting onto sticker #2. When peeled, turn horizontal for a standard 5cm × 2.5cm tag.
                </div>

                <div class="sticker-mount">
                    <span class="sticker-dimension-label dim-width" id="dim-w-text">25mm Width (Roll Feed)</span>
                    <span class="sticker-dimension-label dim-height" id="dim-h-text">50mm Length</span>

                    <div class="sticker-canvas" id="sticker-canvas">
                        <!-- Horizontal Tag (used for rot90, rot270, and direct) -->
                        <div class="label-box-horizontal">
                            <div class="label-h-info">
                                <div class="label-h-brand">PSM HOSPITAL</div>
                                <div class="label-h-prefix">${parsed.prefix}</div>
                                <div class="label-h-code">${parsed.code}</div>
                                <div class="label-h-user" title="${userName}">${userName}</div>
                            </div>
                            <div class="label-h-qr">
                                ${qrSVG}
                            </div>
                        </div>

                        <!-- Stacked Tag (used for mode-stacked) -->
                        <div class="label-box-stacked">
                            <div>
                                <div class="label-s-brand">PSM HOSPITAL</div>
                                <div class="label-s-prefix">${parsed.prefix}</div>
                                <div class="label-s-code">${parsed.code}</div>
                                <div class="label-s-user" title="${userName}">${userName}</div>
                            </div>
                            <div class="label-s-qr">
                                ${qrSVG}
                            </div>
                        </div>
                    </div>
                </div>

                <div class="stage-info no-print" style="margin-top: 20px; font-size: 10.5px; border-color: #334155; background: #0f172a;">
                    💡 <strong>Print Dialog Tip:</strong> Ensure <em>Margins: None</em> and <em>Scale: 100%</em> in the Chrome print preview window.
                </div>
            </div>

            <script>
                // Load preferred mode or default to calibrated rot90
                let currentMode = localStorage.getItem('psm_single_tag_mode') || 'rot90';
                applyMode(currentMode);

                function setMode(mode) {
                    currentMode = mode;
                    localStorage.setItem('psm_single_tag_mode', mode);
                    applyMode(mode);
                }

                function applyMode(mode) {
                    const body = document.body;
                    const pageStyle = document.getElementById('print-page-style');
                    const desc = document.getElementById('stage-desc');
                    const dimW = document.getElementById('dim-w-text');
                    const dimH = document.getElementById('dim-h-text');

                    ['rot90', 'rot270', 'direct', 'stacked'].forEach(m => {
                        body.classList.remove('mode-' + m);
                        const btn = document.getElementById('btn-' + m);
                        if (btn) btn.classList.remove('active');
                    });

                    body.classList.add('mode-' + mode);
                    const activeBtn = document.getElementById('btn-' + mode);
                    if (activeBtn) activeBtn.classList.add('active');

                    if (mode === 'rot90') {
                        if (pageStyle) pageStyle.innerHTML = '@page { size: 25mm 50mm; margin: 0; }';
                        if (desc) desc.innerHTML = '<span class="stage-hint-accent">✅ Active Layout: Rotated 90° (Recommended)</span>. Both Text & QR code fit completely on <strong>1 single physical sticker (25mm × 50mm)</strong> without splitting onto sticker #2. When peeled, turn horizontal for a standard 5cm × 2.5cm tag.';
                        if (dimW) dimW.textContent = '25mm Width (Roll Feed)';
                        if (dimH) dimH.textContent = '50mm Length';
                    } else if (mode === 'rot270') {
                        if (pageStyle) pageStyle.innerHTML = '@page { size: 25mm 50mm; margin: 0; }';
                        if (desc) desc.innerHTML = '<span>🔄 Active Layout: Rotated 270° (Reverse Feed)</span>. QR code feeds first, followed by text along the 50mm length of <strong>1 single sticker</strong>.';
                        if (dimW) dimW.textContent = '25mm Width (Roll Feed)';
                        if (dimH) dimH.textContent = '50mm Length';
                    } else if (mode === 'direct') {
                        if (pageStyle) pageStyle.innerHTML = '@page { size: 50mm 25mm; margin: 0; }';
                        if (desc) desc.innerHTML = '<span>📏 Active Layout: Direct Horizontal (50mm × 25mm)</span>. Use this only if your printer driver is configured for 50×25mm landscape paper.';
                        if (dimW) dimW.textContent = '50mm Width';
                        if (dimH) dimH.textContent = '25mm Height';
                    } else if (mode === 'stacked') {
                        if (pageStyle) pageStyle.innerHTML = '@page { size: 25mm 50mm; margin: 0; }';
                        if (desc) desc.innerHTML = '<span>📱 Active Layout: Upright Stacked (25mm × 50mm)</span>. Text stacked upright above QR code on 1 single sticker.';
                        if (dimW) dimW.textContent = '25mm Width (Roll Feed)';
                        if (dimH) dimH.textContent = '50mm Length';
                    }
                }

                // Auto-trigger print with safe rendering timeout
                window.onload = function() {
                    setTimeout(function() {
                        window.print();
                    }, 400);
                };
            </script>
        </body>
        </html>
    `);
    printWindow.document.close();
}
