"""
CampusAssetIQ — Visual & Beginner-Friendly Project Overview (Cheatsheet Style)
Clean, visual, punchy, minimal reading, maximum clarity.
Swaminarayan University & PSM Hospital.
"""

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
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(40, 808, "CampusAssetIQ — Quick Visual Guide")
        self.setFont("Helvetica", 8)
        self.drawRightString(555, 808, "PSM Hospital & Swaminarayan University")
        
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.8)
        self.line(40, 800, 555, 800)
        self.line(40, 36, 555, 36)
        
        self.setFont("Helvetica-Bold", 8)
        self.drawString(40, 24, "IT Department Quick Note — Live 24/7")
        self.drawRightString(555, 24, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def generate_visual_pdf(output_filename="CampusAssetIQ_Quick_Visual_Guide.pdf"):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=46,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()
    
    # Modern Color Palette
    c_slate = colors.HexColor("#0f172a")
    c_blue = colors.HexColor("#2563eb")
    c_emerald = colors.HexColor("#059669")
    c_amber = colors.HexColor("#d97706")
    c_purple = colors.HexColor("#7c3aed")
    c_card_bg = colors.HexColor("#f8fafc")
    c_border = colors.HexColor("#cbd5e1")
    c_border_light = colors.HexColor("#e2e8f0")

    title_style = ParagraphStyle(
        'VTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_slate,
        spaceAfter=2
    )

    sub_style = ParagraphStyle(
        'VSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=c_blue,
        spaceAfter=8
    )

    sec_header = ParagraphStyle(
        'VSecHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=c_slate,
        spaceBefore=8,
        spaceAfter=4
    )

    box_title = ParagraphStyle(
        'VBoxTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=c_blue
    )

    box_text = ParagraphStyle(
        'VBoxText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=c_slate
    )

    badge_style = ParagraphStyle(
        'VBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    center_text = ParagraphStyle(
        'VCenter',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11.5,
        alignment=1,
        textColor=c_slate
    )

    story = []

    # =========================================================================
    # HEADER HERO
    # =========================================================================
    story.append(Paragraph("CampusAssetIQ — Quick Visual Overview", title_style))
    story.append(Paragraph("Smart Hardware Asset Tracking & 5-Second QR Complaint System", sub_style))

    # Hero KPI Cards (4 Badges)
    kpis = [
        [
            Paragraph("<font color='#2563eb'><b>LIVE 24/7</b></font><br/><font size=7 color='#64748b'>Cloud Hosted</font>", center_text),
            Paragraph("<font color='#059669'><b>5 SECONDS</b></font><br/><font size=7 color='#64748b'>QR Mobile Report</font>", center_text),
            Paragraph("<font color='#7c3aed'><b>20+ LAKH</b></font><br/><font size=7 color='#64748b'>Records Capacity</font>", center_text),
            Paragraph("<font color='#d97706'><b>ZERO</b></font><br/><font size=7 color='#64748b'>Phone Calls Needed</font>", center_text)
        ]
    ]
    t_kpi = Table(kpis, colWidths=[128, 128, 128, 128])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.75, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 8))

    # =========================================================================
    # 1. WHAT IS THIS IN 1 SENTENCE?
    # =========================================================================
    story.append(Paragraph("1. What Is CampusAssetIQ in 1 Simple Sentence?", sec_header))
    story.append(Paragraph(
        "👉 <b>It replaces all messy Excel sheets & phone calls with a simple website:</b> "
        "Every computer gets a QR sticker. Doctors scan it with their phone camera to report issues in 5 seconds, and IT sees everything on one live screen!",
        box_text
    ))
    story.append(Spacer(1, 6))

    # =========================================================================
    # 2. THE 3-STEP MAGIC FLOW (HOW IT WORKS IN REAL LIFE)
    # =========================================================================
    story.append(Paragraph("2. How It Works in Real Life (3 Simple Steps)", sec_header))

    flow_data = [
        [
            Paragraph("<b>STEP 1: POINT PHONE CAMERA</b>", box_title),
            Paragraph("<b>STEP 2: PICK ISSUE & SUBMIT</b>", box_title),
            Paragraph("<b>STEP 3: IT DESK FIXES IT</b>", box_title)
        ],
        [
            Paragraph("• Doctor/Nurse scans QR sticker on the computer.<br/>• Opens instantly on phone.<br/>• <b>No login required!</b>", box_text),
            Paragraph("• System <b>already knows</b> PC tag & room.<br/>• Doctor taps: 'Screen Flickering' or 'No Internet'.<br/>• Taps Submit (5 seconds total).", box_text),
            Paragraph("• Ticket pops up on IT Admin screen instantly.<br/>• Technician sees exact room & machine.<br/>• Marks 'Resolved' when fixed.", box_text)
        ]
    ]
    t_flow = Table(flow_data, colWidths=[170, 172, 170])
    t_flow.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_card_bg),
        ('BOX', (0, 0), (-1, -1), 1, c_blue),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border_light),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_flow)
    story.append(Spacer(1, 8))

    # =========================================================================
    # 3. THE 4 MAIN FEATURES WE BUILT
    # =========================================================================
    story.append(Paragraph("3. The 4 Main Features (All Working Live Right Now)", sec_header))

    features = [
        [
            Paragraph("<font color='#2563eb'><b>🖥️ 1. Complete Inventory</b></font>", box_title),
            Paragraph("<font color='#059669'><b>🏷️ 2. Instant QR Stickers</b></font>", box_title)
        ],
        [
            Paragraph("• Tracks CPUs, Monitors, Keyboards, Mice, Printers.<br/>• Search by Doctor name, Serial number, or IP.<br/>• 1-Click Excel Import & CSV Export.", box_text),
            Paragraph("• Adding a PC in Inventory <b>auto-creates a sticker</b>!<br/>• Only vital info printed: Tag, User, Room & QR.<br/>• Print 1 sticker or a full A4 sheet in 1 click.", box_text)
        ],
        [
            Paragraph("<font color='#7c3aed'><b>🏢 3. Location Explorer</b></font>", box_title),
            Paragraph("<font color='#d97706'><b>🛠️ 4. Breakdown & Servicing</b></font>", box_title)
        ],
        [
            Paragraph("• Click any building ➔ floor ➔ room.<br/>• See all machines in ICU, Trauma, or Lab at a glance.<br/>• Instant count of working vs. spare computers.", box_text),
            Paragraph("• Tracks repair times (how long was PC down?).<br/>• Preventive Maintenance (PMS) schedule tracker.<br/>• Tells you when vendor servicing is due.", box_text)
        ]
    ]
    t_feat = Table(features, colWidths=[256, 256])
    t_feat.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border_light),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
    ]))
    story.append(t_feat)
    story.append(Spacer(1, 8))

    # =========================================================================
    # 4. TECH HIGHLIGHTS IN PLAIN WORDS
    # =========================================================================
    story.append(Paragraph("4. Tech Stack (Explained for Non-Programmers)", sec_header))

    tech_box = [
        [Paragraph("<b>Where is it hosted?</b>", box_title), Paragraph("In the <b>Cloud (Render, Singapore)</b>. Runs 24/7 even if all our laptops are turned off.", box_text)],
        [Paragraph("<b>Where is data saved?</b>", box_title), Paragraph("In a real <b>PostgreSQL Database</b>. Super safe, holds <b>20,00,000+ records (50+ years)</b>.", box_text)],
        [Paragraph("<b>Why is it so fast?</b>", box_title), Paragraph("Built with <b>Python & Django</b>. Zero slow loading, zero heavy lag.", box_text)],
        [Paragraph("<b>How do we update code?</b>", box_title), Paragraph("Connected to <b>GitHub</b>. Any change we make goes live in <b>60 seconds</b> automatically.", box_text)],
        [Paragraph("<b>Is it secure?</b>", box_title), Paragraph("Has official <b>HTTPS SSL Green Lock</b>. Allows phones to safely use camera for QR scanning.", box_text)]
    ]
    t_tech = Table(tech_box, colWidths=[140, 372])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_card_bg),
        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border_light),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_tech)
    story.append(Spacer(1, 8))

    # =========================================================================
    # 5. LIVE WEBSITE LINKS
    # =========================================================================
    story.append(Paragraph("5. Live Links (Open On Any Phone or Laptop)", sec_header))

    links_box = [
        [
            Paragraph("<b>🏠 Main Website:</b>", box_title),
            Paragraph("<u>https://it-support-6np1.onrender.com</u>", box_text)
        ],
        [
            Paragraph("<b>📱 Mobile QR Report:</b>", box_title),
            Paragraph("<u>https://it-support-6np1.onrender.com/report/</u>", box_text)
        ],
        [
            Paragraph("<b>🏷️ Asset Tag Center:</b>", box_title),
            Paragraph("<u>https://it-support-6np1.onrender.com/tag/</u>", box_text)
        ],
        [
            Paragraph("<b>🔐 Admin Command:</b>", box_title),
            Paragraph("<u>https://it-support-6np1.onrender.com/admin-login/</u>", box_text)
        ]
    ]
    t_links = Table(links_box, colWidths=[140, 372])
    t_links.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#93c5fd")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#bfdbfe")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_links)
    story.append(Spacer(1, 8))

    # =========================================================================
    # 6. ONLY 1 THING NEEDED FROM UNIVERSITY
    # =========================================================================
    story.append(Paragraph("6. The Only Step Needed from University IT (Takes 2 Minutes)", sec_header))
    story.append(Paragraph(
        "To make our official link <b><code>support.swaminarayanuniversity.ac.in</code></b> open this site, "
        "our network admin just adds <b>1 simple CNAME in DNS</b>:",
        box_text
    ))

    cname_table = [
        [
            Paragraph("<b>Type:</b> <code>CNAME</code>", box_text),
            Paragraph("<b>Name:</b> <code>support</code>", box_text),
            Paragraph("<b>Points to:</b> <code>it-support-6np1.onrender.com</code>", box_text),
            Paragraph("<font color='#059669'><b>100% Safe</b> (Zero risk to main website)</font>", box_text)
        ]
    ]
    t_cname = Table(cname_table, colWidths=[80, 95, 195, 142])
    t_cname.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#86efac")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#bbf7d0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_cname)
    story.append(Spacer(1, 10))

    # Sign-off
    story.append(Paragraph("<b>Prepared by:</b> IT Systems Engineering Team &bull; Swaminarayan University &amp; PSM Hospital", box_title))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {output_filename}")


if __name__ == "__main__":
    generate_visual_pdf()
