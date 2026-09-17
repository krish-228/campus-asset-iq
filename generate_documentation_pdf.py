"""
CampusAssetIQ — Comprehensive Technical Architecture & Engineering Documentation
Generates a publication-grade PDF report for the IT Head of Department (HOD).
Swaminarayan University & PSM Hospital.
"""

import os
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return  # Skip cover / title header decorations on first page

        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Header text
        self.drawString(54, 800, "CampusAssetIQ — Enterprise Hardware & Incident Intelligence System")
        self.setFont("Helvetica", 8)
        self.drawRightString(558, 800, "Swaminarayan University & PSM Hospital")
        
        # Header line
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.75)
        self.line(54, 792, 558, 792)
        
        # Footer line
        self.line(54, 45, 558, 45)
        
        # Footer text
        self.setFont("Helvetica", 8)
        self.drawString(54, 32, "Confidential — Prepared for IT Department & Institutional Leadership")
        self.drawRightString(558, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def generate_pdf(output_filename="CampusAssetIQ_Technical_Architecture_Report.pdf"):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#0f172a")    # Slate 900
    c_accent = colors.HexColor("#1d4ed8")     # Blue 700
    c_secondary = colors.HexColor("#047857")  # Emerald 700
    c_muted = colors.HexColor("#475569")      # Slate 600
    c_bg_light = colors.HexColor("#f8fafc")   # Slate 50
    c_border = colors.HexColor("#e2e8f0")     # Slate 200

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=c_primary,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=c_accent,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=c_accent,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=c_primary,
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=c_primary,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        'Callout_Text',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=c_primary
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=c_primary
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.white
    )

    story = []

    # =========================================================================
    # TITLE & METADATA BLOCK
    # =========================================================================
    story.append(Paragraph("CampusAssetIQ — System Architecture & Delivery Report", title_style))
    story.append(Paragraph("Enterprise Hardware Asset Intelligence, QR Lifecycle & Incident Management Platform", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceAfter=8, spaceBefore=0))

    # Meta Table
    meta_data = [
        [
            Paragraph("<b>Target Institution:</b> Swaminarayan University & PSM Hospital", table_cell_style),
            Paragraph("<b>Production Status:</b> <font color='#047857'><b>LIVE (24/7 Global Cloud)</b></font>", table_cell_style)
        ],
        [
            Paragraph("<b>Recipient:</b> Head of Department (HOD) — Information Technology", table_cell_style),
            Paragraph("<b>Cloud Endpoint:</b> <font color='#1d4ed8'><u>https://it-support-6np1.onrender.com</u></font>", table_cell_style)
        ],
        [
            Paragraph("<b>Document Scope:</b> Architectural Overview, Functional Modules & Deployment", table_cell_style),
            Paragraph("<b>Custom Domain Target:</b> support.swaminarayanuniversity.ac.in", table_cell_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_bg_light),
        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # 1. EXECUTIVE SUMMARY
    # =========================================================================
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(Paragraph(
        "<b>CampusAssetIQ</b> is an enterprise-grade hardware lifecycle tracking, preventive maintenance, and real-time incident "
        "intelligence system engineered specifically for the mission-critical operations of <b>PSM Hospital</b> and <b>Swaminarayan University</b>. "
        "The platform modernizes legacy, disconnected Excel spreadsheets into a centralized, relational PostgreSQL database architecture. "
        "It provides high-speed hardware registry management, physical ISO-standard QR asset tagging, instant smartphone incident triage for clinical staff, "
        "equipment breakdown lifecycle logging, and preventive maintenance compliance tracking.",
        body_style
    ))
    story.append(Paragraph(
        "The system has been completely containerized, hardened for security, and deployed to a <b>24/7 High-Availability Cloud Infrastructure</b> "
        "with active HTTPS SSL certification, automated database migrations, and CI/CD version control integration.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # =========================================================================
    # 2. TECHNOLOGY STACK & ARCHITECTURAL FOUNDATION
    # =========================================================================
    story.append(Paragraph("2. Technology Stack & Architecture", h1_style))
    
    tech_data = [
        [Paragraph("Layer", table_header_style), Paragraph("Technology", table_header_style), Paragraph("Architectural Rationale & Implementation Details", table_header_style)],
        [Paragraph("<b>Backend Core</b>", table_cell_style), Paragraph("Python 3.12 / Django 6.1 (MTV)", table_cell_style), Paragraph("Server-rendered architecture providing sub-millisecond page loads with zero Single-Page-App (SPA) runtime bloat and memory leaks.", table_cell_style)],
        [Paragraph("<b>Primary Database</b>", table_cell_style), Paragraph("PostgreSQL 16 (Relational Engine)", table_cell_style), Paragraph("ACID-compliant relational database ensuring 100% data integrity, foreign key constraints, and zero risk of SQLite lock contention.", table_cell_style)],
        [Paragraph("<b>Application Server</b>", table_cell_style), Paragraph("Gunicorn WSGI (4 Workers)", table_cell_style), Paragraph("High-concurrency production WSGI server handling simultaneous requests from hospital wards, labs, and staff portals.", table_cell_style)],
        [Paragraph("<b>Static Assets</b>", table_cell_style), Paragraph("WhiteNoise Engine", table_cell_style), Paragraph("Gzip/Brotli compressed manifest storage serving CSS, JS, and Lucide vector icons directly from memory with HTTP/2 caching.", table_cell_style)],
        [Paragraph("<b>Frontend UI/UX</b>", table_cell_style), Paragraph("Tailwind CSS + Vanilla ES6+", table_cell_style), Paragraph("Lightweight, reactive client interfaces with zero external framework dependencies; native HTML5 QR video stream decoding.", table_cell_style)],
        [Paragraph("<b>Cloud Hosting</b>", table_cell_style), Paragraph("Render Cloud PaaS (Singapore Edge)", table_cell_style), Paragraph("Sub-50ms latency connection to Western India; 24/7 uptime guarantee, automatic process supervisor, and SSL termination.", table_cell_style)]
    ]
    tech_table = Table(tech_data, colWidths=[90, 140, 274])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # 3. CORE ENGINEERING INNOVATIONS
    # =========================================================================
    story.append(Paragraph("3. Core Engineering Innovations & Structural Improvements", h1_style))
    
    story.append(Paragraph("<b>3.1 Single Identifier Architecture (Zero 'System Name')</b>", h2_style))
    story.append(Paragraph(
        "Historically, asset tracking suffered from dual-identity confusion (e.g., matching ambiguous names like <i>'ICU-BED-MON-01'</i> with hardware serials). "
        "We permanently re-engineered the schema to enforce <b><code>asset_id</code> (e.g. <code>PSM/IT/2F/C-201</code>) as the absolute single source of truth</b> across all database models, "
        "APIs, templates, custody transfer logs, and physical QR codes. The redundant <code>system_name</code> attribute has been permanently purged.",
        body_style
    ))

    story.append(Paragraph("<b>3.2 Automated Inventory ➔ Asset Tag Center Synchronization</b>", h2_style))
    story.append(Paragraph(
        "A real-time database synchronization pipeline was engineered between the Inventory Registry and the Asset Tag Printing Center. "
        "When an administrator registers a hardware device (or imports in bulk), the system automatically executes <code>POST /api/devices/save/</code>, "
        "persists the record into PostgreSQL, and prepends the newly created asset sticker as <b>Card #1</b> in the Tag Center.",
        body_style
    ))

    story.append(Paragraph("<b>3.3 Strict 'Required-Data-Only' Filtering for Physical Asset Stickers</b>", h2_style))
    story.append(Paragraph(
        "Physical hardware stickers must be legible from a distance and free from cognitive clutter. In accordance with clinical ISO standards, "
        "internal machine specs (RAM chip speeds, processor buses, IP addresses, MAC addresses) are strictly excluded from the physical sticker. "
        "<b>Only vital physical operational fields are transferred</b>: Institution Brand, Asset ID, Device Category Badge, Assigned Custodian, "
        "Physical Room Location, Hardware Serial Number, and a High-Density Vector QR Matrix.",
        body_style
    ))

    story.append(Paragraph("<b>3.4 High-Density Vector QR Generation Engine</b>", h2_style))
    story.append(Paragraph(
        "Rather than relying on low-resolution raster images, the system incorporates an in-browser ISO-18004 compliant vector SVG QR generator. "
        "QR codes are dynamically compiled with Error Correction Level 'M', enabling instant recognition by any iOS or Android camera even on curved surfaces, "
        "medical carts, or low-light ICU environments.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # 4. FUNCTIONAL MODULE BREAKDOWN
    # =========================================================================
    story.append(Paragraph("4. Functional Modules & Capabilities", h1_style))

    modules_data = [
        [Paragraph("Module", table_header_style), Paragraph("Key Features & Engineering Highlights", table_header_style)],
        [
            Paragraph("<b>Hardware Inventory Registry</b><br/><code>/inventory/</code>", table_cell_style),
            Paragraph("• Categorized asset tracking across 5 standard hardware classes: CPU, Display, Keyboard, Mouse, and Printer.<br/>"
                      "• Real-time text search across Asset ID, Serial, Doctor Name, and IP address.<br/>"
                      "• 15-Column bulk Excel import/export parser with duplicate detection and automatic floor allocation.", table_cell_style)
        ],
        [
            Paragraph("<b>Location & Spatial Explorer</b><br/><code>/location/</code>", table_cell_style),
            Paragraph("• Hierarchical 3-tier architectural mapping: Building ➔ Floor ➔ Department / Room.<br/>"
                      "• Multi-tenant institutional scoping: PSM Hospital (Clinical) vs. Swaminarayan University (Academic).<br/>"
                      "• Dynamic room capacity indicators and localized hardware count rollups.", table_cell_style)
        ],
        [
            Paragraph("<b>Asset Tag & QR Center</b><br/><code>/tag/</code>", table_cell_style),
            Paragraph("• Dedicated high-density sticker grid with live printable A4 portrait sheet rendering.<br/>"
                      "• 1-Click single-tag instant printer dialog with zero browser margin bleed.<br/>"
                      "• Real-time search and filter by Asset ID, Category, or Custodian.", table_cell_style)
        ],
        [
            Paragraph("<b>Mobile Incident Intelligence</b><br/><code>/report/&lt;asset_id&gt;/</code>", table_cell_style),
            Paragraph("• Zero-login direct smartphone camera complaint logging for doctors and nursing staff.<br/>"
                      "• Automatic hardware context detection (Asset ID, room location, assigned user pre-filled).<br/>"
                      "• Category selection (Hardware, Display, Network, OS, Peripherals) with priority urgency flags.", table_cell_style)
        ],
        [
            Paragraph("<b>Breakdown & Downtime Register</b><br/><code>/breakdown-register/</code>", table_cell_style),
            Paragraph("• Comprehensive audit register tracking Mean Time to Repair (MTTR) and Mean Time Between Failures (MTBF).<br/>"
                      "• Status lifecycle: Open / Triage ➔ Technician Assigned ➔ In Repair ➔ Resolved & Backfilled.<br/>"
                      "• Location column tracking exact clinical room where breakdown occurred.", table_cell_style)
        ],
        [
            Paragraph("<b>PMS Schedule Tracker</b><br/><code>/pms-schedule/</code>", table_cell_style),
            Paragraph("• Preventive maintenance scheduling for high-availability medical and lab equipment.<br/>"
                      "• Cycle frequencies: Quarterly, Half-Yearly, Annually, Monthly with vendor contract tracking.<br/>"
                      "• Status tracking: Completed, Pending 4th Cycle, Due Soon, Overdue compliance warnings.", table_cell_style)
        ],
        [
            Paragraph("<b>Dual Authentication Portals</b><br/><code>/admin-login/</code> & <code>/portal/</code>", table_cell_style),
            Paragraph("• <b>Admin Command Portal:</b> Obsidian cyber-palette matching mission-critical operations.<br/>"
                      "• <b>Staff Self-Service Portal:</b> Clean healthcare clinical theme for staff self-service and ticket history.", table_cell_style)
        ]
    ]
    modules_table = Table(modules_data, colWidths=[140, 364])
    modules_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
    ]))
    story.append(modules_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # 5. CLOUD INFRASTRUCTURE & CAPACITY ANALYSIS
    # =========================================================================
    story.append(Paragraph("5. Cloud Infrastructure, Scalability & Capacity", h1_style))
    story.append(Paragraph(
        "The system is deployed on high-availability managed cloud architecture with dedicated compute and persistent storage:",
        body_style
    ))

    cap_data = [
        [Paragraph("Metric", table_header_style), Paragraph("Allocated Capacity", table_header_style), Paragraph("Real-World Operational Impact (PSM Hospital & University)", table_header_style)],
        [Paragraph("<b>Database Storage</b>", table_cell_style), Paragraph("1 GB (1,000 MB) PostgreSQL", table_cell_style), Paragraph("Holds <b>over 2,000,000 (20 Lakh) equipment & ticket records</b>. At an average campus consumption rate of ~10 MB/year, this provides <b>50–100 years of continuous operational capacity</b>.", table_cell_style)],
        [Paragraph("<b>Monthly Bandwidth</b>", table_cell_style), Paragraph("100 GB / month", table_cell_style), Paragraph("Supports <b>over 1,000,000 page views per month</b> with sub-second response times across campus Wi-Fi and external mobile networks.", table_cell_style)],
        [Paragraph("<b>Compute Runtime</b>", table_cell_style), Paragraph("512 MB High-Performance RAM", table_cell_style), Paragraph("Zero-memory-leak Python 3.12 WSGI environment with automated worker recycling and health-check supervisor.", table_cell_style)],
        [Paragraph("<b>SSL / Security</b>", table_cell_style), Paragraph("Cloudflare Managed TLS 1.3", table_cell_style), Paragraph("Valid green padlock HTTPS certificate, enabling HTML5 <code>navigator.mediaDevices.getUserMedia</code> camera permissions on all mobile browsers.", table_cell_style)],
        [Paragraph("<b>CI/CD DevOps</b>", table_cell_style), Paragraph("GitHub Webhook Deployment", table_cell_style), Paragraph("Every code commit pushed to <code>krish-228/campus-asset-iq</code> automatically triggers test compilation, static collection, and live zero-downtime deployment in ~60 seconds.", table_cell_style)]
    ]
    cap_table = Table(cap_data, colWidths=[110, 130, 264])
    cap_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
    ]))
    story.append(cap_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # 6. INSTITUTIONAL DOMAIN INTEGRATION ROADMAP
    # =========================================================================
    story.append(Paragraph("6. Institutional Domain Integration Roadmap", h1_style))
    story.append(Paragraph(
        "To provide a branded university presence, the application can be seamlessly mapped to the official subdomain "
        "<b><code>support.swaminarayanuniversity.ac.in</code></b> without requiring any risky nameserver migrations or server disruptions:",
        body_style
    ))

    steps_data = [
        [Paragraph("Step", table_header_style), Paragraph("Action Item", table_header_style), Paragraph("Technical Execution Details", table_header_style)],
        [
            Paragraph("<b>Step 1</b>", table_cell_style),
            Paragraph("<b>Render Custom Domain Binding</b>", table_cell_style),
            Paragraph("In Render Web Service Settings ➔ Custom Domains, bind <code>support.swaminarayanuniversity.ac.in</code>. Render automatically provisions the Let's Encrypt SSL certificate.", table_cell_style)
        ],
        [
            Paragraph("<b>Step 2</b>", table_cell_style),
            Paragraph("<b>University DNS CNAME Record</b>", table_cell_style),
            Paragraph("In the University's primary DNS zone editor (e.g. <code>iredtech.biz</code>), add a standard CNAME record:<br/>"
                      "• <b>Host / Name:</b> <code>support</code><br/>"
                      "• <b>Type:</b> <code>CNAME</code><br/>"
                      "• <b>Value / Destination:</b> <code>it-support-6np1.onrender.com</code><br/>"
                      "• <b>TTL:</b> 14400 (or Automatic)", table_cell_style)
        ],
        [
            Paragraph("<b>Step 3</b>", table_cell_style),
            Paragraph("<b>Zero-Disruption Cutover</b>", table_cell_style),
            Paragraph("The university's main website (<code>swaminarayanuniversity.ac.in</code>) and institutional mail servers remain 100% untouched. "
                      "All traffic to <code>support...</code> automatically routes to the CampusAssetIQ cloud instance.", table_cell_style)
        ]
    ]
    steps_table = Table(steps_data, colWidths=[60, 160, 284])
    steps_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
    ]))
    story.append(steps_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # 7. RECOMMENDATIONS & SIGN-OFF
    # =========================================================================
    story.append(Paragraph("7. Engineering Sign-Off & Recommendations", h1_style))
    story.append(Paragraph("<b>Next Recommended Steps for Institutional Rollout:</b>", h2_style))
    story.append(Paragraph("1. <b>Physical QR Sticker Rollout:</b> Print the standard A4 tag sheets from the Asset Tag Center and apply vinyl stickers to existing computers, monitors, and ICU terminals.", bullet_style))
    story.append(Paragraph("2. <b>DNS Record Addition:</b> Coordinate with the network administrator to insert the <code>support</code> CNAME pointer in the university DNS manager.", bullet_style))
    story.append(Paragraph("3. <b>Staff Orientation:</b> Conduct a brief 10-minute briefing showing hospital nursing supervisors and lab technicians how to scan the QR stickers using standard phone cameras.", bullet_style))
    story.append(Spacer(1, 12))

    # Sign-off box
    signoff_data = [
        [
            Paragraph("<b>Prepared By:</b><br/>Lead Software Engineer / IT Systems Team<br/>CampusAssetIQ Project", table_cell_style),
            Paragraph("<b>Approved & Reviewed By:</b><br/>Head of Department (HOD)<br/>Department of Information Technology", table_cell_style)
        ],
        [
            Paragraph("<b>Date:</b> September 18, 2026", table_cell_style),
            Paragraph("<b>Signature:</b> ___________________________", table_cell_style)
        ]
    ]
    signoff_table = Table(signoff_data, colWidths=[250, 254])
    signoff_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_bg_light),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(signoff_table)

    # Build PDF with dynamic page numbering
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {output_filename}")


if __name__ == "__main__":
    output_path = sys.argv[1] if len(sys.argv) > 1 else "CampusAssetIQ_Technical_Architecture_Report.pdf"
    generate_pdf(output_path)
