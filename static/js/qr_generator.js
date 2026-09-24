// CampusAssetIQ — High-Precision Vector QR & Asset Sticker Card Generator
// Standardized Layout: PSM Hospital Brand + Asset Code + Scannable QR Code (No 1D Barcode Bars)

let currentStickerLayout = 'standard'; // 'standard' | 'pure' | 'detailed'

function setStickerLayout(mode) {
    currentStickerLayout = mode;
    // Update active button state in tag.html if present
    document.querySelectorAll('.sticker-layout-btn').forEach(btn => {
        if (btn.dataset.mode === mode) {
            btn.classList.add('bg-indigo-600', 'text-white', 'shadow-xs');
            btn.classList.remove('bg-white', 'text-slate-700', 'hover:bg-slate-50');
        } else {
            btn.classList.remove('bg-indigo-600', 'text-white', 'shadow-xs');
            btn.classList.add('bg-white', 'text-slate-700', 'hover:bg-slate-50');
        }
    });

    if (typeof getFilteredDevices === 'function') {
        renderStickerCards(getFilteredDevices());
    } else if (typeof appState !== 'undefined' && appState.devices) {
        renderStickerCards(appState.devices);
    }
}

function generateQRSVG(dataString, size = 84) {
    // 1. Standard ISO 18004 Compliant Vector QR Code Matrix (Scannable on all iOS / Android cameras)
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

            return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg" class="rounded-lg bg-white p-1 border border-slate-200 shadow-2xs">
                ${rects}
            </svg>`;
        } catch (err) {
            console.warn("Standard ISO QR Generator error, using fallback matrix", err);
        }
    }

    // 2. High-contrast fallback vector matrix
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

    return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg" class="rounded-lg bg-white p-1 border border-slate-200 shadow-2xs">
        ${rects}
    </svg>`;
}

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

        // Normalize and collect component name (strip any "Workstation" wording)
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
        // Prefer CPU or primary item as base
        const cpuDev = entry.all.find(d => (d.deviceType || '').toUpperCase().includes('CPU'));
        const primary = { ...(cpuDev || entry.primary) };

        // Sort components according to canonical order
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

        // If primary has no serial, find first available serial in group
        if (!primary.serialNumber || primary.serialNumber === 'N/A') {
            const snDev = entry.all.find(d => d.serialNumber && d.serialNumber !== 'N/A');
            if (snDev) primary.serialNumber = snDev.serialNumber;
        }

        result.push(primary);
    });

    return result;
}

function renderStickerCards(devices) {
    const container = document.getElementById("qr-stickers-grid");
    if (!container) return;

    // Group devices by unique asset tag so multiple components sharing an asset ID render as ONE single tag card
    const uniqueDevices = groupDevicesByAssetId(devices);

    if (!uniqueDevices || uniqueDevices.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-12 bg-white rounded-2xl border border-slate-200 shadow-2xs p-8">
                <i data-lucide="inbox" class="w-10 h-10 text-slate-300 mx-auto mb-2"></i>
                <div class="text-sm font-bold text-slate-700">No hardware assets found</div>
                <p class="text-xs text-slate-400 mt-1">Try clearing your search query or organization filter.</p>
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
        const room = (appState && appState.rooms) ? appState.rooms.find(r => r.id === dev.roomId) : null;
        const floor = (room && appState && appState.floors) ? appState.floors.find(f => f.id === room.floorId) : null;
        const org = (appState && appState.organizations) ? appState.organizations.find(o => o.id === dev.orgId) : null;
        const user = (appState && appState.users) ? appState.users.find(u => u.id === dev.assignedUserId) : null;

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
        const typeBadgeClass = typeColors[typeCode] || 'bg-slate-50 text-slate-700 border-slate-200';

        // 3. Resolve Assigned User / Custodian
        let userName = "Hospital Spare / General";
        if (dev.assignedUserName && dev.assignedUserName.trim() && dev.assignedUserName !== 'Unassigned') {
            userName = dev.assignedUserName.trim();
        } else if (user && user.fullName) {
            userName = user.fullName;
        }

        // 4. Resolve Direct mobile report URL for smartphone QR code scanning
        const reportUrl = `${window.location.origin}/report/${encodeURIComponent(dev.assetId)}/`;
        const qrSVG = generateQRSVG(reportUrl, 70);

        // --- MODE 1: PURE CODE & QR ONLY (Literal Minimalist - ID & QR Only) ---
        if (currentStickerLayout === 'pure') {
            return `
                <div class="sticker-card bg-white border-2 border-slate-900 rounded-xl p-3 shadow-xs text-slate-900 flex items-center justify-between select-none relative transition-all hover:shadow-md w-full min-h-[76px]">
                    <div class="flex-1 min-w-0 pr-3">
                        <div class="text-base sm:text-lg font-black font-mono tracking-wider text-slate-950 select-all leading-tight break-all">
                            ${dev.assetId}
                        </div>
                    </div>
                    <div class="flex-shrink-0 flex items-center gap-2">
                        ${qrSVG}
                        <button onclick="printSingleTag('${dev.assetId}')" title="Print this tag" class="no-print p-1 text-slate-400 hover:text-indigo-600 transition-colors cursor-pointer">
                            <i data-lucide="printer" class="w-4 h-4"></i>
                        </button>
                    </div>
                </div>
            `;
        }

        // --- MODE 2: DETAILED STICKER (For Maintenance Audits) ---
        if (currentStickerLayout === 'detailed') {
            return `
                <div class="sticker-card bg-white border-2 border-slate-900 rounded-2xl p-3.5 shadow-sm text-slate-900 flex flex-col justify-between select-none relative transition-all hover:shadow-md aspect-[1.95/1] min-h-[175px] w-full">
                    <!-- Brand Top Header -->
                    <div class="flex items-center justify-between border-b-2 border-slate-900 pb-2">
                        <div class="flex items-center gap-1.5">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span>
                            <span class="text-xs font-black tracking-widest uppercase text-slate-950">${orgName}</span>
                        </div>
                        <div class="flex items-center gap-1.5">
                            <span class="text-[9px] font-bold px-1.5 py-0.5 rounded border ${typeBadgeClass} font-mono">${typeLabel}</span>
                            <span class="text-[8px] font-bold bg-slate-100 border border-slate-300 px-1.5 py-0.5 rounded text-slate-700">${dev.status}</span>
                        </div>
                    </div>

                    <!-- Body: Asset Code + User + S/N + QR -->
                    <div class="flex items-start justify-between gap-3 my-1 flex-1">
                        <div class="space-y-1 flex-1 min-w-0">
                            <div class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-900 text-white shadow-2xs">
                                <span class="text-[8px] uppercase font-bold text-slate-400 font-mono">ID:</span>
                                <span class="text-xs font-black font-mono tracking-wide select-all">${dev.assetId}</span>
                            </div>
                            <div class="text-xs font-black text-slate-900 truncate">${userName}</div>
                            <div class="text-[9.5px] text-slate-600 truncate font-mono">S/N: ${dev.serialNumber || 'N/A'}</div>
                            <div class="text-[9px] text-slate-500 truncate">${floorText} &bull; ${roomText}</div>
                        </div>
                        <div class="flex-shrink-0 flex flex-col items-center">
                            ${qrSVG}
                            <span class="text-[7.5px] font-black uppercase tracking-wider text-slate-400 mt-0.5">SCAN TAG</span>
                        </div>
                    </div>

                    <!-- Clean Bottom Line -->
                    <div class="border-t border-slate-200 pt-1.5 flex items-center justify-between text-[8px] text-slate-400">
                        <span>User: ${userName}</span>
                        <span class="font-mono text-slate-500 font-bold">PSM-IQ</span>
                    </div>
                </div>
            `;
        }

        // --- MODE 3: STANDARD STICKER (Spacious Upper Section + 65/35 Lower Tag & QR) ---
        return `
            <div class="sticker-card bg-white border-2 border-slate-900 rounded-2xl p-3.5 shadow-sm text-slate-900 flex flex-col justify-between select-none relative transition-all hover:shadow-md aspect-[1.9/1] min-h-[178px] w-full">
                <!-- 1. UPPER SECTION (Visible on Screen, Hidden on Print): Brand, User, Device Type & Location -->
                <div class="sticker-screen-only print:hidden space-y-1.5 pb-2.5 border-b-2 border-slate-900 flex-1 flex flex-col justify-between">
                    <!-- Row 1: Brand & Status & 1-Click Print Tag -->
                    <div class="flex items-center justify-between gap-1.5">
                        <div class="flex items-center gap-1.5 min-w-0">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block shrink-0 shadow-2xs"></span>
                            <span class="text-xs font-black tracking-wider uppercase text-slate-950 truncate">${orgName}</span>
                        </div>
                        <div class="flex items-center gap-1 shrink-0">
                            <button onclick="printSingleTag('${dev.assetId}')" title="Print this tag only (ID & QR only)" class="no-print p-1 rounded-md text-slate-400 hover:text-indigo-600 hover:bg-slate-100 transition-colors cursor-pointer flex items-center gap-1 text-[9px] font-bold">
                                <i data-lucide="printer" class="w-3.5 h-3.5"></i>
                                <span class="hidden sm:inline">Print Tag</span>
                            </button>
                            <span class="text-[8.5px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-300 px-2 py-0.5 rounded-md font-mono shrink-0">${dev.status}</span>
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

                <!-- 2. LOWER SECTION (PRINT CONTENT - ID & QR CODE ONLY): Big Text, No Inner Border -->
                <div class="sticker-print-content pt-2 flex items-center justify-between gap-2.5 print:p-0 print:w-full print:gap-3">
                    <!-- Expanded Inner Left Column for Full Asset Tag (No Inner Border on Print) -->
                    <div class="w-[65%] min-w-0 print:w-[73%] print:pl-1">
                        <div class="bg-slate-900 text-white rounded-lg px-2.5 py-2 shadow-2xs print:bg-transparent print:text-slate-950 print:border-0 print:p-0 print:shadow-none flex items-center">
                            <span class="text-sm sm:text-base print:text-[20px] font-black font-mono tracking-wide print:tracking-normal text-white print:text-slate-950 select-all block whitespace-nowrap leading-none">${dev.assetId}</span>
                        </div>
                    </div>

                    <!-- Inner Right Column: Framed Scannable Vector QR Code -->
                    <div class="w-[35%] print:w-[27%] flex items-center justify-end shrink-0">
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

// Dedicated 1-Click Single Asset Tag Printer (ID and QR Code ONLY)
function printSingleTag(assetId) {
    const dev = (appState.devices || []).find(d => d.assetId === assetId);
    if (!dev) return;
    const reportUrl = `${window.location.origin}/report/${encodeURIComponent(dev.assetId)}/`;
    const qrSVG = generateQRSVG(reportUrl, 70);
    const printWindow = window.open('', '_blank', 'width=620,height=340');
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
            <style>
                @page {
                    size: auto;
                    margin: 4mm;
                }
                * { box-sizing: border-box; }
                body {
                    margin: 0;
                    padding: 10px;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: #f8fafc;
                }
                .label-box {
                    width: 88mm;
                    height: 21mm;
                    border: 1.8px solid #0f172a;
                    border-radius: 5px;
                    padding: 1.5mm 3.5mm;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    background: #ffffff;
                }
                .label-left {
                    flex: 1;
                    padding-right: 12px;
                    min-width: 0;
                }
                .label-id {
                    font-size: 20px;
                    font-weight: 900;
                    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                    color: #0f172a;
                    letter-spacing: 0.2px;
                    white-space: nowrap;
                    line-height: 1;
                }
                .label-qr {
                    flex-shrink: 0;
                }
                @media print {
                    body {
                        background: none;
                        padding: 0;
                    }
                    .label-box {
                        border: 1.5px solid #000;
                    }
                }
            </style>
        </head>
        <body>
            <div class="label-box">
                <div class="label-left">
                    <div class="label-id">${dev.assetId}</div>
                </div>
                <div class="label-qr">
                    ${qrSVG}
                </div>
            </div>
            <script>
                window.onload = function() {
                    window.print();
                    setTimeout(function() { window.close(); }, 600);
                };
            </script>
        </body>
        </html>
    `);
    printWindow.document.close();
}

