"""
CampusAssetIQ — Developer Handover & Project Walkthrough Note (Informal & Clear)
A friendly, straightforward engineering guide for IT HOD & Team.
Swaminarayan University & PSM Hospital.
"""

import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
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
            return

        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))
        self.drawString(54, 800, "CampusAssetIQ — Project Overview & Developer Walkthrough")
        self.setFont("Helvetica", 8)
        self.drawRightString(558, 800, "PSM Hospital & Swaminarayan University")
        
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.75)
        self.line(54, 792, 558, 792)
        self.line(54, 45, 558, 45)
        
        self.setFont("Helvetica", 8)
        self.drawString(54, 32, "IT Department Developer Note — Built for Our Campus")
        self.drawRightString(558, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def generate_informal_pdf(output_filename="CampusAssetIQ_Developer_Walkthrough_Note.pdf"):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        leftMargin=50,
        rightMargin=50,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()
    
    # Modern Friendly Color Palette
    c_dark = colors.HexColor("#0f172a")      # Slate 900
    c_blue = colors.HexColor("#2563eb")      # Blue 600
    c_green = colors.HexColor("#16a34a")     # Green 600
    c_amber = colors.HexColor("#d97706")     # Amber 600
    c_bg = colors.HexColor("#f8fafc")        # Soft Slate 50
    c_border = colors.HexColor("#e2e8f0")    # Slate 200
    c_card_bg = colors.HexColor("#ffffff")

    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_dark,
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=c_blue,
        spaceAfter=10
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=c_dark,
        spaceBefore=11,
        spaceAfter=4,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=c_blue,
        spaceBefore=7,
        spaceAfter=2,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=c_dark,
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=c_dark,
        leftIndent=10,
        firstLineIndent=-6,
        spaceAfter=2.5
    )

    table_cell = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=c_dark
    )

    table_header = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.white
    )

    story = []

    # =========================================================================
    # HEADER & QUICK SUMMARY
    # =========================================================================
    story.append(Paragraph("CampusAssetIQ — Developer Project Overview", title_style))
    story.append(Paragraph("A Clear & Practical Walkthrough of What We Built for Swaminarayan University & PSM Hospital", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_blue, spaceAfter=8, spaceBefore=0))

    quick_info = [
        [
            Paragraph("<b>To:</b> IT Head of Department (HOD) & Team", table_cell),
            Paragraph("<b>Status:</b> <font color='#16a34a'><b>LIVE ONLINE 24/7 (Singapore Cloud)</b></font>", table_cell)
        ],
        [
            Paragraph("<b>From:</b> IT Development / Engineering Desk", table_cell),
            Paragraph("<b>Live Website:</b> <font color='#2563eb'><u>https://it-support-6np1.onrender.com</u></font>", table_cell)
        ],
        [
            Paragraph("<b>Project:</b> Campus Hardware Tracking & QR Helpdesk", table_cell),
            Paragraph("<b>Future Subdomain:</b> support.swaminarayanuniversity.ac.in", table_cell)
        ]
    ]
    t_quick = Table(quick_info, colWidths=[245, 255])
    t_quick.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_bg),
        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_quick)
    story.append(Spacer(1, 8))

    # =========================================================================
    # 1. WHY WE BUILT THIS (THE REAL PROBLEMS WE SOLVED)
    # =========================================================================
    story.append(Paragraph("1. Why We Built This (The Real Problems We Solved)", h1_style))
    story.append(Paragraph(
        "Until now, our campus and hospital IT management had a lot of manual headaches:",
        body_style
    ))
    
    problems = [
        [Paragraph("The Old Problem", table_header), Paragraph("How CampusAssetIQ Solves It", table_header)],
        [
            Paragraph("<b>Scattered Excel Sheets</b><br/>Hardware records were spread across different files, making it hard to know which computer is in which room.", table_cell),
            Paragraph("<b>Single Central Database</b><br/>Every single CPU, monitor, keyboard, mouse, and printer is in one live database with exact Building, Floor, and Room locations.", table_cell)
        ],
        [
            Paragraph("<b>Endless Phone Calls from Doctors</b><br/>When a PC in ICU or OPD broke down, doctors had to call IT and try to explain what PC is having the issue.", table_cell),
            Paragraph("<b>5-Second Smartphone QR Scan</b><br/>Doctors simply point their phone camera at the PC sticker. It opens a reporting page with the PC ID already filled in. No login needed!", table_cell)
        ],
        [
            Paragraph("<b>Confusing Duplicate Names</b><br/>Calling PCs by generic names like 'ICU-PC-1' created chaos because multiple rooms had similar labels.", table_cell),
            Paragraph("<b>Single Permanent Asset Tag</b><br/>One unique tag (e.g. <code>PSM/IT/2F/C-201</code>) represents that exact machine forever across all reports and stickers.", table_cell)
        ],
        [
            Paragraph("<b>Manual Servicing / PMS Tracking</b><br/>Remembering vendor warranty expiries and quarterly maintenance schedules was completely manual.", table_cell),
            Paragraph("<b>Automated PMS & Breakdown Register</b><br/>Clear dashboard showing which machines are due for service, MTTR (repair time), and active breakdown tickets.", table_cell)
        ]
    ]
    t_problems = Table(problems, colWidths=[180, 320])
    t_problems.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_dark),
        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg]),
    ]))
    story.append(t_problems)
    story.append(Spacer(1, 8))

    # =========================================================================
    # 2. HOW IT WORKS IN REAL LIFE (THE 5 MAIN MODULES)
    # =========================================================================
    story.append(Paragraph("2. How It Works in Real Life (The Core Features)", h1_style))

    story.append(Paragraph("<b>A. 📱 The 5-Second Mobile QR Complaint System</b>", h2_style))
    story.append(Paragraph(
        "This is the biggest convenience feature for our hospital staff. Every computer gets a physical sticker with a scannable QR code. "
        "When an issue happens: "
        "<br/>1. The nurse or doctor points their phone camera at the QR code on the machine."
        "<br/>2. It opens <code>/report/&lt;asset_id&gt;/</code> instantly. The system <b>already knows</b> the Asset Tag, room number, and assigned user."
        "<br/>3. The doctor chooses the issue (e.g. 'Display Flickering' or 'Network Drop'), types 2 words, and taps Submit."
        "<br/>4. The ticket appears instantly on the IT Admin Desk dashboard. <b>Zero phone calls, zero confusion!</b>",
        body_style
    ))

    story.append(Paragraph("<b>B. 🏷️ Instant Asset Tag & Sticker Printing</b>", h2_style))
    story.append(Paragraph(
        "Whenever you add a new PC or printer in the Inventory page, our system automatically creates a clean, ready-to-print sticker card in the <b>Asset Tag Center</b>. "
        "We designed it so only the <b>vital physical information</b> is printed on the tag (Asset ID, Device Type, Assigned Custodian, Room, Serial Number, and QR Code). "
        "We intentionally kept technical clutter (like internal RAM chip speeds or MAC addresses) off the physical sticker so it looks clean and readable from 5 feet away!",
        body_style
    ))

    story.append(Paragraph("<b>C. 🏢 Location Explorer (Building ➔ Floor ➔ Room)</b>", h2_style))
    story.append(Paragraph(
        "You can click on any floor (e.g. PSM Hospital ➔ 2nd Floor ➔ ICU or Trauma Ward) and see every device running in that specific room at a glance, "
        "including who is responsible for it and whether it is active or in maintenance.",
        body_style
    ))

    story.append(Paragraph("<b>D. 📊 Equipment Breakdown & Maintenance (PMS) Registers</b>", h2_style))
    story.append(Paragraph(
        "Keeps an honest log of repairs, which technician fixed it, how many hours it was down, and when the next quarterly or annual servicing is due from the vendor.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # =========================================================================
    # 3. HOW IT IS BUILT (THE TECH IN SIMPLE WORDS)
    # =========================================================================
    story.append(Paragraph("3. How It Is Built (In Simple Engineering Words)", h1_style))

    tech_simple = [
        [Paragraph("Component", table_header), Paragraph("What We Used", table_header), Paragraph("Why This Is Great For Our Campus", table_header)],
        [
            Paragraph("<b>Backend</b>", table_cell),
            Paragraph("Python & Django 6.1", table_cell),
            Paragraph("Rock-solid, super fast page loading. No heavy complicated JavaScript frameworks that slow down older hospital PCs.", table_cell)
        ],
        [
            Paragraph("<b>Database</b>", table_cell),
            Paragraph("PostgreSQL 16 (Cloud)", table_cell),
            Paragraph("Enterprise relational database. 100% reliable, zero risk of file corruption, completely independent of our laptops.", table_cell)
        ],
        [
            Paragraph("<b>Cloud Host</b>", table_cell),
            Paragraph("Render (Singapore Edge)", table_cell),
            Paragraph("Located close to India (low ping). Runs <b>24 hours a day, 7 days a week</b> even when all our office laptops are shut down.", table_cell)
        ],
        [
            Paragraph("<b>Security & SSL</b>", table_cell),
            Paragraph("Cloudflare HTTPS", table_cell),
            Paragraph("Gives us the official green security lock. Modern smartphone cameras require HTTPS to allow QR code scanning.", table_cell)
        ],
        [
            Paragraph("<b>Code Updates</b>", table_cell),
            Paragraph("GitHub Auto-Deploy", table_cell),
            Paragraph("Whenever we make an improvement in code and push it to GitHub, the live cloud website automatically updates itself in 60 seconds.", table_cell)
        ]
    ]
    t_tech = Table(tech_simple, colWidths=[80, 130, 290])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_dark),
        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg]),
    ]))
    story.append(t_tech)
    story.append(Spacer(1, 8))

    # =========================================================================
    # 4. STORAGE & CAPACITY (CAN IT HANDLE OUR CAMPUS?)
    # =========================================================================
    story.append(Paragraph("4. Storage & Capacity (Can It Handle Our Entire Campus?)", h1_style))
    story.append(Paragraph(
        "<b>YES, easily!</b> Here is the exact capacity math for our cloud setup:",
        body_style
    ))
    
    cap_points = [
        "<b>Database Capacity:</b> 1 GB dedicated storage on PostgreSQL. Since each equipment and ticket record is clean text (~0.5 KB), 1 GB can hold <b>over 20,00,000 (20 Lakh) records</b>!",
        "<b>Real Campus Consumption:</b> Our university and hospital will create roughly ~10 MB of data per year (including 5,000 PCs and 10,000 repair tickets). That means our current setup gives us <b>50 to 100 YEARS of storage</b> before getting full.",
        "<b>Traffic Capacity:</b> 100 GB of free bandwidth per month, which easily covers <b>over 10,00,000 (10 Lakh) page views every month</b>."
    ]
    for pt in cap_points:
        story.append(Paragraph(f"• {pt}", bullet_style))
    story.append(Spacer(1, 8))

    # =========================================================================
    # 5. CONNECTING OUR OFFICIAL UNIVERSITY LINK
    # =========================================================================
    story.append(Paragraph("5. Connecting Our Official Subdomain (Next 2-Minute Step)", h1_style))
    story.append(Paragraph(
        "Our site is already working 24/7 on: <b><code>https://it-support-6np1.onrender.com</code></b>. "
        "To make it open when someone types <b><code>support.swaminarayanuniversity.ac.in</code></b>, we just need our IT network admin to add <b>ONE standard CNAME record</b>:",
        body_style
    ))

    cname_box = [
        [Paragraph("<b>Type:</b>", table_cell), Paragraph("<code>CNAME</code>", table_cell)],
        [Paragraph("<b>Host / Name:</b>", table_cell), Paragraph("<code>support</code>", table_cell)],
        [Paragraph("<b>Points to / Value:</b>", table_cell), Paragraph("<code>it-support-6np1.onrender.com</code>", table_cell)],
        [Paragraph("<b>Impact on main site:</b>", table_cell), Paragraph("<b>ZERO RISK.</b> Main university site (<code>swaminarayanuniversity.ac.in</code>) and emails stay 100% untouched.", table_cell)]
    ]
    t_cname = Table(cname_box, colWidths=[120, 380])
    t_cname.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_bg),
        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_cname)
    story.append(Spacer(1, 8))

    # =========================================================================
    # 6. SUMMARY & NEXT STEPS
    # =========================================================================
    story.append(Paragraph("6. Summary & How We Can Roll This Out", h1_style))
    story.append(Paragraph(
        "1. <b>Test the live link on your phone:</b> Open <code>https://it-support-6np1.onrender.com/report/</code> and see how smoothly the QR complaint page loads."
        "<br/>2. <b>Print a sample sheet of QR tags:</b> From <code>/tag/</code>, print 1 A4 sheet on our office printer and test scanning with any smartphone camera."
        "<br/>3. <b>Add the DNS CNAME:</b> Have our domain manager point <code>support</code> to <code>it-support-6np1.onrender.com</code>.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # Friendly sign-off
    story.append(Paragraph("<b>Submitted by:</b> IT Systems Development Desk &bull; Swaminarayan University &amp; PSM Hospital", subtitle_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {output_filename}")


if __name__ == "__main__":
    generate_informal_pdf()
