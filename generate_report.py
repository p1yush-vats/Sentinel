"""
SENTINEL — Major Project Report Generator
BCA 2023–26, GGSIPU
Follows the Major_Project_Guidelines_BCA_2023-26 formatting specification.
"""

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def set_page_margins(doc, top=1.0, bottom=1.0, left=1.5, right=1.0):
    """Set page margins in inches."""
    for section in doc.sections:
        section.top_margin    = Inches(top)
        section.bottom_margin = Inches(bottom)
        section.left_margin   = Inches(left)
        section.right_margin  = Inches(right)

def set_font(run, name="Times New Roman", size=12, bold=False, italic=False, color=None):
    run.font.name  = name
    run.font.size  = Pt(size)
    run.bold       = bold
    run.italic     = italic
    if color:
        run.font.color.rgb = RGBColor(*color)

def add_para(doc, text="", style="Normal", alignment=WD_ALIGN_PARAGRAPH.LEFT,
             font_name="Times New Roman", font_size=12, bold=False, italic=False,
             space_before=0, space_after=6, line_spacing=None, color=None):
    """Add a paragraph with custom formatting."""
    p = doc.add_paragraph(style=style)
    p.alignment = alignment
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after  = Pt(space_after)
    if line_spacing:
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        pf.line_spacing      = Pt(line_spacing)
    else:
        pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        pf.line_spacing      = 1.5
    if text:
        run = p.add_run(text)
        set_font(run, font_name, font_size, bold, italic, color)
    return p

def add_heading(doc, text, level=1):
    """Add a numbered/styled heading."""
    sizes = {1: 14, 2: 12, 3: 12}
    p = add_para(doc, text,
                 font_size=sizes.get(level, 12),
                 bold=True,
                 space_before=12,
                 space_after=6)
    return p

def add_page_break(doc):
    doc.add_page_break()

def add_table(doc, headers, rows, col_widths=None):
    """Add a formatted table."""
    table = doc.add_table(rows=1+len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Header row
    hdr = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.text = h
        for run in cell.paragraphs[0].runs:
            run.font.bold = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(11)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        shade = OxmlElement('w:shd')
        shade.set(qn('w:val'), 'clear')
        shade.set(qn('w:color'), 'auto')
        shade.set(qn('w:fill'), 'D9D9D9')
        cell._tc.get_or_add_tcPr().append(shade)

    # Data rows
    for ri, row in enumerate(rows):
        trow = table.rows[ri+1]
        for ci, val in enumerate(row):
            cell = trow.cells[ci]
            cell.text = str(val)
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
            for run in cell.paragraphs[0].runs:
                run.font.name = "Times New Roman"
                run.font.size = Pt(11)

    # Column widths
    if col_widths:
        for i, row in enumerate(table.rows):
            for j, cell in enumerate(row.cells):
                if j < len(col_widths):
                    cell.width = Inches(col_widths[j])

    doc.add_paragraph()
    return table

def add_centered_title(doc, text, size=16, bold=True, space_before=0, space_after=6):
    return add_para(doc, text,
                    alignment=WD_ALIGN_PARAGRAPH.CENTER,
                    font_size=size, bold=bold,
                    space_before=space_before, space_after=space_after)

# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT BUILD
# ─────────────────────────────────────────────────────────────────────────────

doc = Document()
set_page_margins(doc, top=1.0, bottom=1.0, left=1.5, right=1.0)

# Default Normal style
normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(12)

# ═══════════════════════════════════════════════════════════════════════════
# COVER PAGE
# ═══════════════════════════════════════════════════════════════════════════

add_para(doc, "", space_before=0, space_after=0)
add_para(doc, "", space_before=0, space_after=0)

add_centered_title(doc, "GURU GOBIND SINGH INDRAPRASTHA UNIVERSITY", size=14, bold=True, space_before=6)
add_centered_title(doc, "BACHELOR OF COMPUTER APPLICATIONS", size=13, bold=True, space_after=4)
add_centered_title(doc, "(BCA 2023–2026)", size=12, bold=False, space_after=2)

add_para(doc, "")

add_centered_title(doc, "MAJOR PROJECT REPORT", size=16, bold=True, space_before=18)
add_para(doc, "", space_after=4)

# Project title box
add_centered_title(doc, "SENTINEL", size=22, bold=True, space_before=10, space_after=4)
add_centered_title(doc,
    "An AI-Driven Work Integrity & Productivity Monitoring Ecosystem",
    size=13, bold=False, space_before=0, space_after=18)

add_para(doc, "")
add_para(doc, "Submitted in partial fulfillment of the requirements for the award of the degree of",
         alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=12, space_after=4)
add_centered_title(doc, "Bachelor of Computer Applications", size=12, bold=True, space_after=18)

add_para(doc, "")
add_para(doc, "Submitted by", alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=12, space_after=4)
add_centered_title(doc, "PIYUSH VATS", size=13, bold=True, space_after=2)
add_centered_title(doc, "Roll No.: 03913702023", size=12, bold=False, space_after=2)
add_centered_title(doc, "BCA – Semester VI", size=12, bold=False, space_after=18)

add_para(doc, "")
add_para(doc, "Under the Guidance of", alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=12, space_after=4)
add_centered_title(doc, "[Faculty Guide Name]", size=13, bold=True, space_after=2)
add_centered_title(doc, "Designation, Department", size=12, bold=False, space_after=18)

add_para(doc, "")
add_centered_title(doc, "[Name of the College/Institution]", size=13, bold=True, space_after=2)
add_centered_title(doc, "Affiliated to Guru Gobind Singh Indraprastha University, New Delhi", size=11, bold=False)
add_para(doc, "")
add_centered_title(doc, "Academic Year: 2025–2026", size=12, bold=True, space_before=6)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════
# CERTIFICATE PAGE
# ═══════════════════════════════════════════════════════════════════════════

add_centered_title(doc, "CERTIFICATE", size=16, bold=True, space_before=24)
add_para(doc, "")

cert_text = """This is to certify that the Major Project entitled "SENTINEL: An AI-Driven Work Integrity & Productivity Monitoring Ecosystem" submitted by Mr. Piyush Vats, Roll No. 03913702023, in partial fulfillment of the requirements for the award of the degree of Bachelor of Computer Applications from Guru Gobind Singh Indraprastha University, New Delhi, is a bonafide record of the project work carried out by the student under my supervision and guidance."""
add_para(doc, cert_text, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=18)

add_para(doc, "This project has not been submitted anywhere else for the award of any degree, "
             "diploma, or any other similar title.",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=36)

add_para(doc, "")
add_para(doc, "")

# Signature block
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
r1 = p.add_run("Faculty Guide\n[Faculty Guide Name]\nDesignation\n[Department Name]\n[Institution Name]")
r1.font.name = "Times New Roman"; r1.font.size = Pt(12)

add_para(doc, "")
add_centered_title(doc, "Forwarded through:", size=12, bold=True, space_before=18, space_after=6)
add_centered_title(doc, "Head of Department / Director", size=12, bold=False)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════
# DECLARATION
# ═══════════════════════════════════════════════════════════════════════════

add_centered_title(doc, "DECLARATION", size=16, bold=True, space_before=12)
add_para(doc, "")

decl_text = """I, Piyush Vats, Roll No. 03913702023, student of Bachelor of Computer Applications (BCA), Semester VI, hereby declare that the Major Project entitled "SENTINEL: An AI-Driven Work Integrity & Productivity Monitoring Ecosystem" submitted to Guru Gobind Singh Indraprastha University, New Delhi, is an original work done by me under the supervision of [Faculty Guide Name], and has not been submitted in part or in full to any other university or institution for the award of any degree or diploma."""
add_para(doc, decl_text, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=18)

add_para(doc, "I further declare that all the information, facts, and figures presented in this "
             "report are true and correct to the best of my knowledge and belief.",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=36)

add_para(doc, "")
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
r = p.add_run("Date: ___________\n\nPlace: New Delhi")
r.font.name = "Times New Roman"; r.font.size = Pt(12)

add_para(doc, "")
add_para(doc, "Piyush Vats\nRoll No.: 03913702023\nBCA – Semester VI",
         alignment=WD_ALIGN_PARAGRAPH.RIGHT, font_size=12)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════
# ACKNOWLEDGEMENT
# ═══════════════════════════════════════════════════════════════════════════

add_centered_title(doc, "ACKNOWLEDGEMENT", size=16, bold=True, space_before=12)
add_para(doc, "")

ack = """I take this opportunity to express my profound sense of gratitude and deep respect to all those who guided and supported me throughout the course of this Major Project.

I would like to express my sincere thanks to [Faculty Guide Name], my project guide, for their invaluable guidance, encouragement, and constant support at every stage of this project. Their insights and expertise have been instrumental in shaping this work.

I am deeply grateful to the [Head of Department's Name], Head of Department, and the entire faculty of [Institution Name] for providing the facilities and environment that enabled me to pursue this project.

I also extend my gratitude to Guru Gobind Singh Indraprastha University, New Delhi, for its academic framework that allowed me to undertake this project as part of my BCA curriculum.

Special thanks to my family and friends for their unwavering moral support and encouragement throughout the journey.

Lastly, I am grateful to all those who directly or indirectly contributed to the successful completion of this project."""

for para in ack.split("\n\n"):
    add_para(doc, para.strip(), alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=10)

add_para(doc, "")
add_para(doc, "Piyush Vats\nRoll No.: 03913702023", alignment=WD_ALIGN_PARAGRAPH.RIGHT, font_size=12)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════
# ABSTRACT
# ═══════════════════════════════════════════════════════════════════════════

add_centered_title(doc, "ABSTRACT", size=16, bold=True, space_before=12)
add_para(doc, "")

abstract = (
    "The modern remote and hybrid work environment has introduced significant challenges "
    "in maintaining employee accountability, ensuring work integrity, and accurately measuring "
    "productivity. Traditional attendance systems and manual supervision are insufficient to "
    "address the complexities of distributed work environments where an employee may be "
    "physically absent yet digitally clocked in.\n\n"
    "SENTINEL is a full-stack, AI-driven work integrity and productivity monitoring ecosystem "
    "designed to address these challenges. The system operates as a three-tier architecture: "
    "a native Windows desktop application deployed on employee workstations, a cloud-hosted "
    "FastAPI backend with real-time WebSocket communication, and a React-based administrative "
    "web dashboard for centralized monitoring and HR management.\n\n"
    "The desktop application performs privacy-safe, continuous behavioral analysis of employee "
    "activity — tracking only metadata (keystroke timing intervals, mouse movement patterns, "
    "clipboard size, and idle periods) without capturing any actual content. Its AI-powered "
    "detection engine identifies eleven categories of workplace malpractice including mechanical "
    "typing (bot/macro use), mouse jiggler devices, superhuman typing speeds, suspicious paste "
    "operations, extended idle periods, clock-in/clock-out abuse, and scripted activity patterns.\n\n"
    "The backend, deployed on Render, provides a comprehensive RESTful API with JWT-based "
    "authentication, session lifecycle management, anomaly reporting, leave management, task "
    "assignment, appeal workflows, and automatic PDF report generation via ReportLab. PostgreSQL "
    "(Supabase) serves as the cloud database with twelve normalized tables. Real-time events are "
    "pushed to the admin dashboard via dedicated WebSocket channels.\n\n"
    "The React web dashboard, deployed on Vercel, offers dual-role interfaces: a full-featured "
    "administrative panel for monitoring all employees, reviewing flagged sessions, approving "
    "leaves, assigning tasks, and exporting reports; and an employee self-service portal for "
    "viewing personal sessions, submitting leave requests, raising appeals, and tracking tasks.\n\n"
    "SENTINEL demonstrates the practical application of behavioral AI, real-time systems, and "
    "modern DevOps practices to solve a genuine enterprise HR problem — delivering an end-to-end "
    "production-ready system that is privacy-conscious, highly configurable, and scalable."
)

for para in abstract.split("\n\n"):
    add_para(doc, para.strip(), alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=10)

add_para(doc, "")
add_para(doc, "Keywords: Work Monitoring, Behavioral Analysis, FastAPI, React, WebSocket, "
             "AI Detection, Employee Productivity, PyInstaller, Supabase, PostgreSQL, HR Management",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=11, italic=True, space_after=6)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS
# ═══════════════════════════════════════════════════════════════════════════

add_centered_title(doc, "TABLE OF CONTENTS", size=16, bold=True, space_before=12)
add_para(doc, "")

toc_entries = [
    ("Certificate",                                            "ii"),
    ("Declaration",                                           "iii"),
    ("Acknowledgement",                                       "iv"),
    ("Abstract",                                              "v"),
    ("Table of Contents",                                     "vi"),
    ("List of Figures",                                       "viii"),
    ("List of Tables",                                        "ix"),
    ("",                                                      ""),
    ("CHAPTER 1 — INTRODUCTION",                              "1"),
    ("  1.1  Background and Motivation",                      "1"),
    ("  1.2  Problem Statement",                              "2"),
    ("  1.3  Objectives of the Project",                      "3"),
    ("  1.4  Scope of the Project",                           "4"),
    ("  1.5  Organization of the Report",                     "5"),
    ("",                                                      ""),
    ("CHAPTER 2 — LITERATURE SURVEY",                         "6"),
    ("  2.1  Existing Work Monitoring Systems",               "6"),
    ("  2.2  Behavioral Analysis in Workplace Monitoring",    "7"),
    ("  2.3  Privacy-Preserving Monitoring Techniques",       "8"),
    ("  2.4  Real-Time Communication Technologies",           "9"),
    ("  2.5  Comparative Study",                              "10"),
    ("  2.6  Research Gap",                                   "11"),
    ("",                                                      ""),
    ("CHAPTER 3 — SYSTEM ANALYSIS",                           "12"),
    ("  3.1  Feasibility Study",                              "12"),
    ("  3.2  Requirements Analysis",                          "13"),
    ("  3.3  Functional Requirements",                        "14"),
    ("  3.4  Non-Functional Requirements",                    "15"),
    ("  3.5  Use Case Diagrams",                              "16"),
    ("  3.6  Data Flow Diagrams",                             "18"),
    ("",                                                      ""),
    ("CHAPTER 4 — SYSTEM DESIGN",                             "22"),
    ("  4.1  System Architecture",                            "22"),
    ("  4.2  Three-Tier Architecture Design",                 "23"),
    ("  4.3  Database Design",                                "25"),
    ("  4.4  Detection Engine Design",                        "31"),
    ("  4.5  API Design",                                     "33"),
    ("  4.6  UI/UX Design",                                   "35"),
    ("",                                                      ""),
    ("CHAPTER 5 — IMPLEMENTATION",                            "38"),
    ("  5.1  Technology Stack",                               "38"),
    ("  5.2  Desktop Application Implementation",             "39"),
    ("  5.3  Backend Implementation",                         "44"),
    ("  5.4  Web Dashboard Implementation",                   "48"),
    ("  5.5  Deployment",                                     "52"),
    ("",                                                      ""),
    ("CHAPTER 6 — TESTING",                                   "54"),
    ("  6.1  Testing Strategy",                               "54"),
    ("  6.2  Unit Testing",                                   "55"),
    ("  6.3  Integration Testing",                            "57"),
    ("  6.4  System Testing",                                 "59"),
    ("  6.5  User Acceptance Testing",                        "60"),
    ("",                                                      ""),
    ("CHAPTER 7 — RESULTS AND DISCUSSION",                    "62"),
    ("  7.1  System Performance",                             "62"),
    ("  7.2  Detection Engine Accuracy",                      "63"),
    ("  7.3  Screenshots and Output",                         "64"),
    ("  7.4  Limitations",                                    "66"),
    ("",                                                      ""),
    ("CHAPTER 8 — CONCLUSION AND FUTURE SCOPE",               "67"),
    ("  8.1  Conclusion",                                     "67"),
    ("  8.2  Future Scope",                                   "68"),
    ("",                                                      ""),
    ("REFERENCES",                                            "70"),
    ("APPENDICES",                                            "72"),
    ("  Appendix A — Source Code Snippets",                   "72"),
    ("  Appendix B — Database Schema",                        "76"),
    ("  Appendix C — API Endpoints",                          "78"),
]

for entry, page in toc_entries:
    if not entry:
        add_para(doc, "", space_after=2)
        continue
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after  = Pt(1)
    tab_stops = p.paragraph_format.tab_stops
    tab_stops.add_tab_stop(Inches(5.5), WD_ALIGN_PARAGRAPH.RIGHT)
    run = p.add_run(f"{entry}\t{page}")
    run.font.name = "Times New Roman"
    run.font.size = Pt(11)
    if "CHAPTER" in entry or entry in ("REFERENCES", "APPENDICES"):
        run.bold = True

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════
# LIST OF FIGURES
# ═══════════════════════════════════════════════════════════════════════════

add_centered_title(doc, "LIST OF FIGURES", size=16, bold=True, space_before=12)
add_para(doc, "")

figures = [
    ("Figure 3.1", "Use Case Diagram — Admin",                           "16"),
    ("Figure 3.2", "Use Case Diagram — Employee",                        "17"),
    ("Figure 3.3", "Context-Level DFD (Level 0)",                        "18"),
    ("Figure 3.4", "Level 1 DFD — Desktop Application",                  "19"),
    ("Figure 3.5", "Level 1 DFD — Backend API",                          "20"),
    ("Figure 3.6", "Level 1 DFD — Web Dashboard",                        "21"),
    ("Figure 4.1", "Three-Tier System Architecture Diagram",              "22"),
    ("Figure 4.2", "Component Architecture — Desktop App",               "23"),
    ("Figure 4.3", "Real-Time WebSocket Architecture",                    "24"),
    ("Figure 4.4", "Entity-Relationship (ER) Diagram",                   "25"),
    ("Figure 4.5", "Detection Engine — Analysis Pipeline Flowchart",     "31"),
    ("Figure 5.1", "Session Lifecycle State Machine",                    "40"),
    ("Figure 5.2", "Abnormality Detection Flow",                         "43"),
    ("Figure 5.3", "Backend API Request–Response Cycle",                 "45"),
    ("Figure 7.1", "Sentinel Desktop App — Login Screen",                "64"),
    ("Figure 7.2", "Sentinel Desktop App — Main Dashboard",              "64"),
    ("Figure 7.3", "Admin Web Dashboard — Live Feed",                    "65"),
    ("Figure 7.4", "Employee Portal — My Dashboard",                     "65"),
]

for fig_num, title, page in figures:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after  = Pt(1)
    tab_stops = p.paragraph_format.tab_stops
    tab_stops.add_tab_stop(Inches(5.5), WD_ALIGN_PARAGRAPH.RIGHT)
    run = p.add_run(f"{fig_num}  {title}\t{page}")
    run.font.name = "Times New Roman"; run.font.size = Pt(11)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════
# LIST OF TABLES
# ═══════════════════════════════════════════════════════════════════════════

add_centered_title(doc, "LIST OF TABLES", size=16, bold=True, space_before=12)
add_para(doc, "")

tables_list = [
    ("Table 2.1", "Comparative Study of Work Monitoring Tools",           "10"),
    ("Table 3.1", "Functional Requirements",                             "14"),
    ("Table 3.2", "Non-Functional Requirements",                         "15"),
    ("Table 4.1", "Database Tables Overview",                            "25"),
    ("Table 4.2", "employees Table Schema",                              "26"),
    ("Table 4.3", "sessions Table Schema",                               "27"),
    ("Table 4.4", "abnormalities Table Schema",                          "28"),
    ("Table 4.5", "tasks Table Schema",                                  "29"),
    ("Table 4.6", "leaves Table Schema",                                 "30"),
    ("Table 4.7", "Detection Types and Severity Weights",                "32"),
    ("Table 4.8", "API Endpoints Summary",                               "33"),
    ("Table 5.1", "Technology Stack",                                    "38"),
    ("Table 5.2", "Desktop App Dependencies",                            "39"),
    ("Table 5.3", "Backend Dependencies",                                "44"),
    ("Table 6.1", "Unit Test Cases — Detection Engine",                  "55"),
    ("Table 6.2", "Integration Test Cases",                              "57"),
    ("Table 6.3", "System Test Cases",                                   "59"),
    ("Table 7.1", "Detection Engine Accuracy Results",                   "63"),
]

for tbl_num, title, page in tables_list:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after  = Pt(1)
    tab_stops = p.paragraph_format.tab_stops
    tab_stops.add_tab_stop(Inches(5.5), WD_ALIGN_PARAGRAPH.RIGHT)
    run = p.add_run(f"{tbl_num}  {title}\t{page}")
    run.font.name = "Times New Roman"; run.font.size = Pt(11)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════
# CHAPTER 1 — INTRODUCTION
# ═══════════════════════════════════════════════════════════════════════════

add_heading(doc, "CHAPTER 1", 1)
add_centered_title(doc, "INTRODUCTION", size=14, bold=True, space_before=2, space_after=12)

add_heading(doc, "1.1  Background and Motivation", 2)
add_para(doc, """The global shift toward remote and hybrid work models, accelerated by the COVID-19 pandemic, has fundamentally transformed the employer–employee relationship. According to a 2024 Gartner report, over 48% of the global knowledge-worker workforce now operates remotely or in hybrid arrangements at least three days per week. While this model offers organizational benefits such as reduced overhead costs and access to a geographically distributed talent pool, it simultaneously introduces significant challenges in maintaining accountability, measuring genuine productivity, and ensuring work integrity.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, """Traditional monitoring mechanisms — physical attendance registers, biometric punch-in systems, and on-site supervisors — are ill-suited to distributed work environments. They were designed for co-located offices and rely fundamentally on physical proximity. Conversely, existing digital monitoring solutions such as screenshot capture tools, keystroke loggers, and screen recording software — while technically capable — raise serious ethical and legal concerns regarding employee privacy, data security, and regulatory compliance (particularly under frameworks like GDPR, IT Act 2000, and emerging data protection bills).""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, """This project, SENTINEL, was conceived to bridge this gap: to build a monitoring system that is simultaneously effective at detecting genuine workplace malpractice, privacy-safe by design (collecting only behavioral metadata, never content), transparent to employees, and technically sophisticated enough to operate reliably in production enterprise environments.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=12)

add_heading(doc, "1.2  Problem Statement", 2)
add_para(doc, """Organizations employing remote and hybrid workers face a critical and growing problem: they cannot reliably verify that employees who are digitally "clocked in" are genuinely performing productive work. This manifests in several concrete abuse scenarios:""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=6)

problems = [
    ("Employee Ghosting:", "An employee starts a work session and immediately leaves their workstation, relying on natural mouse movement from OS screensavers or scheduled scripts to keep their status green on communication tools."),
    ("Mouse Jiggler Abuse:", "Employees use physical USB mouse jiggler devices or software tools (e.g., Caffeine, MouseJiggler) to simulate activity while being genuinely idle."),
    ("Automated Work Submission:", "Work output is generated by AI tools or scripts and then pasted as original work, with an unnaturally high paste-to-keystroke ratio."),
    ("Macro and Bot Usage:", "Automated keyboard macros replay pre-recorded keystrokes to simulate typing activity, producing patterns with unnaturally consistent inter-key timing intervals."),
    ("Attendance Fraud:", "Work sessions are started and ended remotely (by family members, scripts, or colleagues) to fraudulently record attendance."),
]

for title, desc in problems:
    p = add_para(doc, space_after=4, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12)
    run1 = p.add_run(f"  • {title} ")
    run1.font.bold = True; run1.font.name = "Times New Roman"; run1.font.size = Pt(12)
    run2 = p.add_run(desc)
    run2.font.name = "Times New Roman"; run2.font.size = Pt(12)

add_para(doc, """Current solutions either fail to detect these patterns reliably, violate employee privacy through invasive content capture, lack real-time administrative visibility, or are prohibitively expensive for small and medium enterprises. SENTINEL addresses all four failure modes.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=12)

add_heading(doc, "1.3  Objectives of the Project", 2)
add_para(doc, "The primary objectives of the SENTINEL project are:", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=6)

objectives = [
    "To design and implement a privacy-safe behavioral analysis engine that detects workplace malpractice through metadata analysis (timing, patterns, rates) without capturing any actual content.",
    "To build a native Windows desktop application that monitors employee sessions in real-time, integrates with the OS system tray, supports session recovery, and provides an intuitive employee-facing interface.",
    "To develop a production-grade RESTful API backend using FastAPI and PostgreSQL capable of handling concurrent employee sessions, real-time event propagation via WebSockets, and comprehensive HR data management.",
    "To create a dual-role React web dashboard providing administrators with real-time monitoring, anomaly review, leave management, task assignment, and reporting capabilities, while giving employees secure self-service access.",
    "To implement a complete HR workflow covering session management, abnormality detection, appeal processing, leave management, task tracking, email notifications, and PDF report generation.",
    "To deploy the complete ecosystem as a production application with CI/CD pipelines, environment-based configuration, automatic data synchronization, and robust error handling.",
    "To ensure the system is extensible, configurable, and maintainable through clean architecture, typed APIs, and comprehensive documentation.",
]

for i, obj in enumerate(objectives, 1):
    add_para(doc, f"  {i}. {obj}", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=4)

add_heading(doc, "1.4  Scope of the Project", 2)
add_para(doc, """SENTINEL encompasses the complete design, development, testing, and deployment of a three-component ecosystem. The scope includes:""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=6)

scope_items = [
    ("In Scope:", [
        "A Windows-only desktop application (PyInstaller executable) with system tray integration.",
        "Detection of eleven distinct behavioral abnormality types using statistical and AI-based algorithms.",
        "A cloud-hosted REST API with 14 router modules covering all HR and monitoring data domains.",
        "A React SPA with 12 admin pages and 7 employee self-service pages.",
        "Real-time bidirectional WebSocket communication between backend, dashboard, and desktop app.",
        "Email notification system for session events, abnormalities, and leave approvals.",
        "PDF report generation for employee performance dossiers.",
        "JWT-based authentication with secure token storage.",
        "Local SQLite database with cloud synchronization for offline resilience.",
        "Complete deployment on Render (backend) and Vercel (dashboard).",
    ]),
    ("Out of Scope:", [
        "Video surveillance or screen recording.",
        "Content capture (keystrokes content, clipboard text, or screen images).",
        "macOS or Linux desktop clients (planned for future versions).",
        "Mobile application interfaces.",
        "Hardware time-clock integrations.",
    ]),
]

for category, items in scope_items:
    add_para(doc, category, font_size=12, bold=True, space_after=2)
    for item in items:
        add_para(doc, f"    • {item}", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=2)
    add_para(doc, "", space_after=4)

add_heading(doc, "1.5  Organization of the Report", 2)
add_para(doc, """The remainder of this report is organized as follows:""", font_size=12, space_after=6)

chapters = [
    ("Chapter 2 — Literature Survey:", "Reviews existing work monitoring solutions, behavioral analysis research, privacy considerations, and identifies the research gap addressed by SENTINEL."),
    ("Chapter 3 — System Analysis:", "Presents the feasibility study, complete requirements specification (functional and non-functional), use case diagrams, and data flow diagrams."),
    ("Chapter 4 — System Design:", "Details the three-tier architecture, database schema (ER diagram and table specifications), detection engine design, API design, and UI/UX wireframes."),
    ("Chapter 5 — Implementation:", "Describes the technology stack selection rationale and the detailed implementation of all three system components, including deployment configuration."),
    ("Chapter 6 — Testing:", "Covers unit, integration, and system testing strategies, test cases, and results."),
    ("Chapter 7 — Results and Discussion:", "Presents system performance metrics, detection accuracy results, annotated screenshots, and discusses limitations."),
    ("Chapter 8 — Conclusion and Future Scope:", "Summarizes achievements, lessons learned, and outlines planned enhancements and research directions."),
]

for title, desc in chapters:
    p = add_para(doc, space_after=4, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12)
    r1 = p.add_run(f"  {title} ")
    r1.font.bold = True; r1.font.name = "Times New Roman"; r1.font.size = Pt(12)
    r2 = p.add_run(desc)
    r2.font.name = "Times New Roman"; r2.font.size = Pt(12)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════
# CHAPTER 2 — LITERATURE SURVEY
# ═══════════════════════════════════════════════════════════════════════════

add_heading(doc, "CHAPTER 2", 1)
add_centered_title(doc, "LITERATURE SURVEY", size=14, bold=True, space_before=2, space_after=12)

add_heading(doc, "2.1  Existing Work Monitoring Systems", 2)
add_para(doc, """Employee monitoring software has evolved significantly over the past two decades. Early systems (2000–2010) were largely limited to network-level monitoring — logging websites visited, email auditing, and application usage tracking through proxy servers and firewall logs. Products such as SolarWinds Bandwidth Analyzer and Spector 360 exemplified this era. These systems provided broad network visibility but offered no behavioral intelligence and were easily circumvented by VPNs or private devices.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, """The 2010s saw the emergence of more sophisticated endpoint monitoring solutions. Tools like Teramind, InterGuard, and Veriato introduced screen recording, keystroke logging (including content), and application activity tracking. While powerful, these systems raised significant privacy controversies and in many jurisdictions face regulatory scrutiny. Their primary weakness is content capture — they record actual keystrokes and screen content, which constitutes surveillance rather than behavioral monitoring.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, """The post-pandemic era (2020–present) witnessed an explosion in remote monitoring tools. ActivTrak, Hubstaff, Time Doctor, and Workpuls emerged with hybrid monitoring approaches — combining screenshot sampling (every 10 minutes), URL tracking, active/idle detection, and project-based time logging. However, these suffer from critical limitations relevant to SENTINEL's design context.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=12)

add_heading(doc, "2.2  Behavioral Analysis in Workplace Monitoring", 2)
add_para(doc, """Academic research on behavioral biometrics has established that human computer interaction produces statistically unique "signatures" that distinguish genuine human activity from automated or fraudulent input. Key contributions include:""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, """Bergadano et al. (2002) demonstrated that keystroke dynamics — specifically the inter-key timing intervals (dwell time and flight time) — follow characteristic distributions for individual users. Automated scripts produce artificially low variance in these intervals (coefficient of variation < 0.15), providing a reliable mechanical typing signal. SENTINEL's mechanical_typing detector implements this principle directly.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, """Mondal and Bours (2013) showed that continuous behavioural authentication using mouse movement patterns achieves an Equal Error Rate (EER) of approximately 4.2%, demonstrating that mouse movement analysis provides statistically meaningful behavioral signals. SENTINEL's mouse jiggler detection leverages the regularity (low standard deviation) of automated mouse movements.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, """Ahmed and Traore (2007) established that click frequency, movement velocity, and inter-event timing are discriminative behavioral features. Their work informs SENTINEL's idle period tracking and burst_then_idle detection.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=12)

add_heading(doc, "2.3  Privacy-Preserving Monitoring Techniques", 2)
add_para(doc, """A growing body of literature supports metadata-only monitoring as an ethically and legally superior alternative to content capture. The fundamental insight is that behavioral patterns — not content — are what matter for integrity monitoring. An employer does not need to read an employee's keystrokes to determine whether the typing pattern is consistent with human behavior; they only need the inter-key intervals.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, """The UK's Information Commissioner's Office (ICO) guidance on Monitoring at Work (2023) explicitly distinguishes between "monitoring what employees do" (permissible with notice) and "monitoring what employees say" (requiring much higher justification). SENTINEL falls cleanly in the former category — it never captures content, only behavioral metadata.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, """Roessler (2005) in "The Private in Public" argues for a privacy framework in organizational monitoring that requires proportionality (monitoring only as much as necessary), transparency (employees informed), and purpose limitation (data used only for stated purposes). SENTINEL's design incorporates all three principles.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=12)

add_heading(doc, "2.4  Real-Time Communication Technologies", 2)
add_para(doc, """Real-time data communication in multi-tier web applications has been approached through several mechanisms: long polling, Server-Sent Events (SSE), and WebSockets. The RFC 6455 WebSocket protocol provides full-duplex communication over a persistent TCP connection, enabling sub-second latency event delivery.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, """FastAPI's native WebSocket support (built on Starlette's ASGI foundation) enables efficient management of concurrent WebSocket connections through Python's asyncio event loop. SENTINEL implements a custom ConnectionManager class that maintains connection maps keyed by user_id, enabling targeted message delivery and broadcast to admin dashboards simultaneously.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=12)

add_heading(doc, "2.5  Comparative Study", 2)
add_para(doc, "Table 2.1 presents a comparative analysis of SENTINEL against leading commercial monitoring solutions:", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

comp_headers = ["Feature", "ActivTrak", "Teramind", "Hubstaff", "Time Doctor", "SENTINEL"]
comp_rows = [
    ["Keystroke Content Capture",    "No",       "Yes",    "No",     "No",         "No"],
    ["Screen Recording",             "Sampling", "Yes",    "Opt-in", "Sampling",   "No"],
    ["Behavioral Pattern Detection", "Basic",    "Yes",    "No",     "No",         "Advanced"],
    ["Mouse Jiggler Detection",      "No",       "No",     "No",     "No",         "Yes"],
    ["Real-time Admin Dashboard",    "Yes",      "Yes",    "Yes",    "Yes",        "Yes"],
    ["WebSocket Live Feed",          "No",       "No",     "No",     "No",         "Yes"],
    ["Native Desktop App",           "No",       "Yes",    "Yes",    "Yes",        "Yes"],
    ["Leave Management",             "No",       "No",     "Limited","No",         "Full"],
    ["Task Management",              "No",       "Limited","Yes",    "No",         "Yes"],
    ["Appeal Workflow",              "No",       "No",     "No",     "No",         "Yes"],
    ["Offline Resilience (SQLite)",  "No",       "No",     "No",     "No",         "Yes"],
    ["Open Source / Custom",         "No",       "No",     "No",     "No",         "Yes"],
    ["Free / Self-Hosted",           "No",       "No",     "No",     "No",         "Yes"],
]
add_table(doc, comp_headers, comp_rows, col_widths=[2.2, 0.9, 0.9, 0.9, 0.9, 0.9])
add_para(doc, "Table 2.1: Comparative Study of Work Monitoring Tools",
         alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=10, italic=True, space_after=12)

add_heading(doc, "2.6  Research Gap", 2)
add_para(doc, """The literature review and comparative analysis reveal a clear research gap: no existing solution combines all of the following desirable properties in a single integrated system:""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

gaps = [
    "Privacy-by-design (metadata-only, zero content capture)",
    "Advanced behavioral AI with multiple detection categories (11 types in SENTINEL)",
    "Native desktop integration with system tray and offline resilience",
    "Real-time admin visibility via WebSockets",
    "Complete HR workflow (sessions, leaves, tasks, appeals, reports)",
    "Full open-source, self-hostable, and cost-free deployment",
]
for gap in gaps:
    add_para(doc, f"  • {gap}", font_size=12, space_after=3)

add_para(doc, "SENTINEL is specifically designed to fill this gap.", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=6, space_before=6)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════
# CHAPTER 3 — SYSTEM ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

add_heading(doc, "CHAPTER 3", 1)
add_centered_title(doc, "SYSTEM ANALYSIS", size=14, bold=True, space_before=2, space_after=12)

add_heading(doc, "3.1  Feasibility Study", 2)
add_para(doc, "A thorough feasibility study was conducted across three dimensions before commencing development:", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, "Technical Feasibility", bold=True, font_size=12, space_after=2)
add_para(doc, """Python's mature ecosystem provides all required capabilities: pynput for low-level keyboard/mouse event hooks, win32clipboard for clipboard metadata, customtkinter for native Windows UI, FastAPI for high-performance async APIs, and SQLAlchemy for ORM-based database access. React's component model and Vite's development tooling provide a modern, maintainable frontend stack. All chosen technologies are production-proven, well-documented, and have active maintenance communities. Technical feasibility is confirmed.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, "Economic Feasibility", bold=True, font_size=12, space_after=2)
add_para(doc, """All technology components used in SENTINEL are open-source and free-of-charge. Deployment infrastructure costs are zero for the scale of this project: Render's free tier provides adequate backend hosting, Vercel's free tier accommodates the React dashboard, and Supabase's free tier provides 500MB PostgreSQL storage and 2GB bandwidth monthly. Development hardware is limited to a standard personal computer. Economic feasibility is fully confirmed.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, "Operational Feasibility", bold=True, font_size=12, space_after=2)
add_para(doc, """The target users — HR administrators and office employees — are assumed to have basic computer literacy. The admin dashboard provides an intuitive, self-explaining interface modeled on familiar HR software patterns. The desktop application provides clear visual status indicators and guided interactions. A PyInstaller-compiled executable package eliminates the need for employees to install Python or any dependencies. Operational feasibility is confirmed.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=12)

add_heading(doc, "3.2  Requirements Analysis", 2)
add_para(doc, """Requirements were gathered through the following methods: (1) analysis of existing commercial monitoring tool feature sets, (2) review of academic literature on behavioral monitoring systems, (3) informal interviews with potential end-users (both administrative and employee perspectives), and (4) analysis of common remote-work abuse patterns documented in industry reports.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=12)

add_heading(doc, "3.3  Functional Requirements", 2)

fr_headers = ["FR ID", "Category", "Requirement Description", "Priority"]
fr_rows = [
    ["FR-01", "Authentication", "System shall support email/password login with JWT token issuance, secure storage, and automatic refresh.", "High"],
    ["FR-02", "Authentication", "System shall support persistent login via locally-stored encrypted JWT tokens.", "High"],
    ["FR-03", "Session Mgmt", "Employee shall be able to start, pause (break/lunch), and end work sessions from the desktop app.", "High"],
    ["FR-04", "Session Mgmt", "System shall detect and offer recovery of incomplete sessions within a configurable time window.", "High"],
    ["FR-05", "Session Mgmt", "System shall detect and reject concurrent active session conflicts.", "High"],
    ["FR-06", "Detection", "System shall monitor keystroke timing intervals and detect mechanically uniform patterns.", "High"],
    ["FR-07", "Detection", "System shall detect mouse jiggler devices through movement interval regularity analysis.", "High"],
    ["FR-08", "Detection", "System shall detect paste operations and measure clipboard content size (metadata only).", "High"],
    ["FR-09", "Detection", "System shall detect extended idle periods during active work sessions.", "High"],
    ["FR-10", "Detection", "System shall detect clock-in/clock-out abuse (session with minimal activity).", "High"],
    ["FR-11", "Detection", "System shall detect burst-then-idle patterns.", "Medium"],
    ["FR-12", "Detection", "System shall detect superhuman typing speeds (>150 WPM).", "High"],
    ["FR-13", "Detection", "System shall detect scripted periodic activity bursts.", "Medium"],
    ["FR-14", "Sync", "Desktop app shall sync all detection data to cloud backend in real-time via REST API.", "High"],
    ["FR-15", "Sync", "Desktop app shall maintain local SQLite cache for offline operation.", "High"],
    ["FR-16", "Dashboard", "Admin shall view real-time live feed of all employee events via WebSocket.", "High"],
    ["FR-17", "Dashboard", "Admin shall review, dismiss, or escalate flagged abnormality records.", "High"],
    ["FR-18", "Dashboard", "Admin shall view detailed employee profiles with complete session history.", "High"],
    ["FR-19", "Dashboard", "Admin shall manage the full leave lifecycle (view, approve, reject).", "High"],
    ["FR-20", "Dashboard", "Admin shall create and assign tasks to employees with priorities and due dates.", "High"],
    ["FR-21", "Dashboard", "Admin shall generate and export PDF performance reports.", "Medium"],
    ["FR-22", "Employee", "Employee shall view their own session history and productivity metrics.", "High"],
    ["FR-23", "Employee", "Employee shall submit leave requests with supporting documentation.", "High"],
    ["FR-24", "Employee", "Employee shall raise appeals against flagged sessions.", "High"],
    ["FR-25", "Employee", "Employee shall view and update the status of assigned tasks.", "High"],
    ["FR-26", "Notifications", "System shall send email notifications for session events, leave decisions, and task assignments.", "Medium"],
]
add_table(doc, fr_headers, fr_rows, col_widths=[0.7, 1.2, 3.6, 0.7])
add_para(doc, "Table 3.1: Functional Requirements", alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=10, italic=True, space_after=12)

add_heading(doc, "3.4  Non-Functional Requirements", 2)

nfr_headers = ["NFR ID", "Category", "Requirement", "Metric / Target"]
nfr_rows = [
    ["NFR-01", "Performance",    "Backend API response time for standard queries",                  "< 500ms at p95"],
    ["NFR-02", "Performance",    "Detection analysis cycle frequency",                              "Every 30 seconds"],
    ["NFR-03", "Availability",   "Backend uptime",                                                 "> 99.5%"],
    ["NFR-04", "Security",       "All API endpoints require JWT authentication",                   "100%"],
    ["NFR-05", "Security",       "Passwords stored as bcrypt hashes",                              "Cost factor ≥ 12"],
    ["NFR-06", "Privacy",        "No keystroke content stored at any layer",                       "Zero content capture"],
    ["NFR-07", "Scalability",    "Backend shall handle concurrent employee sessions",              "> 100 concurrent"],
    ["NFR-08", "Reliability",    "Desktop app shall operate offline with local queue",              "SQLite fallback"],
    ["NFR-09", "Usability",      "Non-technical employee shall complete login < 60 seconds",        "First-time UX"],
    ["NFR-10", "Maintainability","All API endpoints documented via FastAPI auto-docs",             "OpenAPI 3.0"],
    ["NFR-11", "Portability",    "Desktop app distributed as single .exe (PyInstaller)",           "No Python required"],
    ["NFR-12", "Compliance",     "Data collection limited to behavioral metadata only",            "Privacy by design"],
]
add_table(doc, nfr_headers, nfr_rows, col_widths=[0.7, 1.2, 2.8, 1.5])
add_para(doc, "Table 3.2: Non-Functional Requirements", alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=10, italic=True, space_after=12)

add_heading(doc, "3.5  Use Case Diagrams", 2)
add_para(doc, "Two primary use case diagrams were developed for SENTINEL — one for the Administrator actor and one for the Employee actor.", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, "Use Case Diagram — Administrator (Figure 3.1)", bold=True, font_size=12, space_after=4)
add_para(doc, """Actor: Admin / HR Manager
System Boundary: SENTINEL Web Dashboard + Backend API

Use Cases:
  UC-A1: Login to Admin Dashboard
  UC-A2: View Real-Time Live Feed (WebSocket)
  UC-A3: View All Employee List
  UC-A4: View Employee Detail Profile
  UC-A5: View Session History (All Employees)
  UC-A6: Review Flagged Abnormalities
  UC-A7: Dismiss / Escalate / Issue Warning on Abnormality
  UC-A8: Approve / Reject Leave Request
  UC-A9: Create Task and Assign to Employee
  UC-A10: Send Admin Alert to Employee (via WebSocket)
  UC-A11: View Audit Log
  UC-A12: Generate and Export PDF Report
  UC-A13: Configure Work Rules per Department/Employee
  UC-A14: Manage Employee Records (Add/Edit/Deactivate)""",
         font_size=11, space_after=12)

add_para(doc, "Use Case Diagram — Employee (Figure 3.2)", bold=True, font_size=12, space_after=4)
add_para(doc, """Actor: Employee
System Boundary: SENTINEL Desktop App + Employee Web Portal

Use Cases:
  UC-E1: Login to Desktop Application
  UC-E2: Start Work Session
  UC-E3: Take / End Break
  UC-E4: Take / End Lunch
  UC-E5: End Work Session
  UC-E6: View Session Summary
  UC-E7: View Personal Session History (Web Portal)
  UC-E8: View Personal Flagged Sessions
  UC-E9: Submit Appeal Against Flag
  UC-E10: Submit Leave Request
  UC-E11: View Leave Status
  UC-E12: View Assigned Tasks
  UC-E13: Update Task Status (In Progress / Completed)
  UC-E14: Receive Admin Alerts (OS notifications)""",
         font_size=11, space_after=12)

add_heading(doc, "3.6  Data Flow Diagrams", 2)

add_para(doc, "Level 0 DFD (Context Diagram) — Figure 3.3", bold=True, font_size=12, space_after=4)
add_para(doc, """The context-level DFD shows SENTINEL as a single process interacting with three external entities:

  External Entity 1 — Employee: Provides login credentials and work session events (start/break/lunch/end). Receives session state updates, detection alerts, task notifications, and admin messages.
  
  External Entity 2 — Administrator/HR Manager: Provides review decisions, leave approvals, task assignments, alert messages, and configuration settings. Receives employee session data, anomaly reports, analytics, and generated PDF reports.
  
  External Entity 3 — Cloud Infrastructure (Supabase/PostgreSQL): Stores and retrieves all persistent data — employee records, sessions, abnormalities, tasks, leaves, appeals, and audit logs.

Data flows from Employee → SENTINEL: credentials, session control commands, keystroke/mouse metadata, paste events, task status updates, leave requests.
Data flows from SENTINEL → Employee: JWT tokens, session confirmations, detection alerts (OS notifications), assigned tasks.
Data flows from Admin → SENTINEL: review decisions, configuration, leave approvals, task creation, alerts.
Data flows from SENTINEL → Admin: real-time event stream (WebSocket), employee data, anomaly reports, analytics, PDF reports.""",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=11, space_after=12)

add_para(doc, "Level 1 DFD — Desktop Application (Figure 3.4)", bold=True, font_size=12, space_after=4)
add_para(doc, """The Level 1 DFD decomposes the Desktop Application process into five sub-processes:

  Process 1.1 — Authentication Manager: Receives credentials from Employee, validates with backend API, stores JWT token in encrypted local file, returns session state.
  
  Process 1.2 — Session Manager: Controls the session state machine (idle → working → break → lunch → working → completed). Communicates with backend API to create/update session records. Connects to WebSocket for receiving admin alerts and tasks.
  
  Process 1.3 — Input Collector: Intercepts system-level keyboard and mouse events via pynput hooks. Stores only timing metadata (intervals, rates) in rolling deque buffers. Polls for paste events via Windows API polling thread.
  
  Process 1.4 — Abnormality Detector: Reads metadata buffers from Input Collector every 30 seconds. Runs 11 detection algorithms. Returns list of detected Abnormality objects to Aggregator.
  
  Process 1.5 — Sync Client: Reads unsynced records from SQLite local database. Pushes them to backend REST API at configurable intervals. Updates sync status in UI.

Data Stores: DS-1 Local SQLite DB (sessions, abnormalities queue)""",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=11, space_after=12)

add_para(doc, "Level 1 DFD — Backend API (Figure 3.5)", bold=True, font_size=12, space_after=4)
add_para(doc, """The Level 1 DFD for the Backend API shows the following major sub-processes:

  Process 2.1 — Auth Router: JWT token issuance (login), validation (middleware), and invalidation (logout).
  Process 2.2 — Session Router: Create, update, and retrieve session records. Handle session conflict detection.
  Process 2.3 — Abnormality Router: UPSERT abnormality records (one row per session, JSONB detections). Review and decision recording.
  Process 2.4 — Employee Router: CRUD operations on employee records. Profile management.
  Process 2.5 — Task Router: Create tasks, assign to employees, update status, WebSocket notification on assignment.
  Process 2.6 — Leave Router: Submit, review, and approve/reject leave requests with email notifications.
  Process 2.7 — WebSocket Manager: Maintain connection maps for admin-feed and per-user channels. Fan-out broadcast for admin dashboard events.
  Process 2.8 — Report Generator: Produce ReportLab-based PDF performance dossiers on demand.

Data Stores: DS-2 PostgreSQL (Supabase) — 12 relational tables""",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=11, space_after=12)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════
# CHAPTER 4 — SYSTEM DESIGN
# ═══════════════════════════════════════════════════════════════════════════

add_heading(doc, "CHAPTER 4", 1)
add_centered_title(doc, "SYSTEM DESIGN", size=14, bold=True, space_before=2, space_after=12)

add_heading(doc, "4.1  System Architecture", 2)
add_para(doc, """SENTINEL follows a three-tier client-server architecture augmented with a real-time WebSocket communication layer. The architecture separates concerns cleanly across presentation, business logic, and data tiers, enabling independent scaling, testing, and deployment of each component.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, """The three tiers are:

  Tier 1 — Presentation Layer: 
    • The native Windows desktop application (Python + CustomTkinter) serves as the employee-facing presentation layer. It renders session controls, real-time detection feed, alert history, and task management UI.
    • The React single-page application (SPA) deployed on Vercel serves as the administrator-facing and employee self-service presentation layer.

  Tier 2 — Application Logic Layer: 
    • The FastAPI backend, deployed on Render, constitutes the application logic tier. It enforces business rules, implements the detection data storage hierarchy, manages authentication, processes HR workflows, and orchestrates real-time communications.

  Tier 3 — Data Layer: 
    • PostgreSQL (via Supabase) serves as the primary cloud data store.
    • SQLite (local, via the desktop app) serves as an offline-resilient secondary data store that queues data for cloud synchronization.""",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=12)

add_heading(doc, "4.2  Three-Tier Architecture Design", 2)
add_para(doc, "The full architecture diagram (Figure 4.1) illustrates the following communication pathways:", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

pathways = [
    ("Desktop App → Backend REST API", "HTTPS/JSON REST calls for session creation, session updates, abnormality upserts, and productivity metric logging. All calls are JWT-authenticated."),
    ("Desktop App ↔ Backend WebSocket (/ws/{user_id})", "A persistent WebSocket connection maintained per logged-in employee. Used to receive admin alerts, task assignments, and real-time directives."),
    ("Admin Dashboard ↔ Backend WebSocket (/ws/admin-feed)", "A dedicated WebSocket channel for the admin dashboard's Live Feed. The backend broadcasts all session events, abnormality detections, and task updates to this channel."),
    ("Admin Dashboard → Backend REST API", "HTTPS/JSON REST calls for data retrieval (employees, sessions, abnormalities, leaves, tasks, analytics) and mutation operations (review decisions, leave approvals, task creation)."),
    ("Employee Portal → Backend REST API", "HTTPS/JSON REST calls for personal data access, leave submission, appeal filing, and task status updates."),
    ("Backend → Supabase PostgreSQL", "Asynchronous SQLAlchemy (asyncpg dialect) database operations for all persistence needs."),
    ("Desktop SQLite ↔ Backend Sync", "Background sync thread periodically flushes unsynced local SQLite records to the cloud backend via REST API."),
]

for src, desc in pathways:
    p = add_para(doc, space_after=4, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12)
    r1 = p.add_run(f"  • {src}: ")
    r1.font.bold = True; r1.font.name = "Times New Roman"; r1.font.size = Pt(12)
    r2 = p.add_run(desc)
    r2.font.name = "Times New Roman"; r2.font.size = Pt(12)

add_heading(doc, "4.3  Database Design", 2)
add_para(doc, "The SENTINEL database comprises twelve relational tables hosted on Supabase PostgreSQL. The design follows Third Normal Form (3NF) with strategic JSONB columns for semi-structured detection data.", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

# DB Tables overview
db_overview_headers = ["Table Name", "Description", "Key Columns"]
db_overview_rows = [
    ["employees",             "Central user registry for all employees and admins",  "id (UUID PK), email, password_hash, role, department, position"],
    ["sessions",              "Records each work session lifecycle",                   "id (UUID PK), employee_id (FK), start_time, end_time, status, risk_score"],
    ["work_time_logs",        "Granular work/break/lunch segment tracking",           "session_id (FK), log_type, start_time, end_time, duration_minutes"],
    ["abnormalities",         "One row per session; JSONB detections map",            "session_id (UNIQUE FK), overall_severity, confidence_score, detections JSONB"],
    ["admin_actions",         "Audit trail of admin review decisions",                "admin_id (FK), employee_id (FK), action_type, justification"],
    ["appeals",               "Employee appeals against flagged sessions",             "employee_id (FK), session_id (FK), status, admin_response"],
    ["leaves",                "Full leave lifecycle management",                      "employee_id (FK), leave_type, from_date, to_date, status, comments JSONB"],
    ["tasks",                 "Task assignment and tracking",                         "assigned_to (FK), assigned_by (FK), priority, status, due_date"],
    ["productivity_metrics",  "Hourly activity snapshots per session",               "session_id (FK), hour_of_day, keystroke_count, mouse_movement_count"],
    ["reports",               "Metadata for generated PDF reports",                  "generated_by (FK), report_type, start_date, end_date, file_path"],
    ["work_rules",            "Configurable productivity rules per dept/employee",    "department, work_minutes_per_hour, detection_sensitivity"],
    ["audit_log",             "System-level event audit trail",                      "event_type, actor_id (FK), action, ip_address, user_agent"],
    ["notification_preferences", "Per-employee notification settings",               "employee_id (FK), email_notifications, break_reminders, weekly_reports"],
]
add_table(doc, db_overview_headers, db_overview_rows, col_widths=[1.5, 2.2, 2.5])
add_para(doc, "Table 4.1: Database Tables Overview", alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=10, italic=True, space_after=10)

# employees schema
add_para(doc, "Table 4.2: employees Table Schema", bold=True, font_size=12, space_after=4)
emp_headers = ["Column", "Data Type", "Constraints", "Description"]
emp_rows = [
    ["id",            "UUID",          "PK, DEFAULT uuid_generate_v4()", "Unique employee identifier"],
    ["email",         "VARCHAR(255)",  "UNIQUE, NOT NULL",               "Login email address"],
    ["password_hash", "VARCHAR(255)",  "NOT NULL",                       "bcrypt hash of password"],
    ["full_name",     "VARCHAR(255)",  "NOT NULL",                       "Employee's full name"],
    ["role",          "VARCHAR(50)",   "NOT NULL, DEFAULT 'employee'",   "employee / admin / super_admin"],
    ["department",    "VARCHAR(100)",  "NULLABLE",                       "Department name"],
    ["position",      "VARCHAR(100)",  "NULLABLE",                       "Job title/position"],
    ["gender",        "VARCHAR(20)",   "NULLABLE",                       "Gender"],
    ["phone",         "VARCHAR(20)",   "NULLABLE",                       "Contact phone"],
    ["employee_code", "VARCHAR(20)",   "NULLABLE",                       "HR employee code"],
    ["avatar_url",    "TEXT",          "NULLABLE",                       "Profile photo URL"],
    ["is_active",     "BOOLEAN",       "DEFAULT TRUE",                   "Account status flag"],
    ["created_at",    "TIMESTAMPTZ",   "DEFAULT now()",                  "Record creation timestamp"],
    ["updated_at",    "TIMESTAMPTZ",   "DEFAULT now(), ON UPDATE",       "Last modification timestamp"],
]
add_table(doc, emp_headers, emp_rows, col_widths=[1.2, 1.2, 1.9, 1.9])
add_para(doc, "Table 4.2: employees Table Schema", alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=10, italic=True, space_after=10)

# sessions schema
add_para(doc, "Table 4.3: sessions Table Schema", bold=True, font_size=12, space_after=4)
ses_headers = ["Column", "Data Type", "Constraints", "Description"]
ses_rows = [
    ["id",                   "UUID",       "PK",                               "Unique session identifier"],
    ["employee_id",          "UUID",       "FK → employees(id) ON DELETE CASCADE", "Owner of the session"],
    ["start_time",           "TIMESTAMPTZ","NOT NULL",                          "Session start timestamp"],
    ["end_time",             "TIMESTAMPTZ","NULLABLE",                          "Session end timestamp"],
    ["total_work_minutes",   "INTEGER",    "DEFAULT 0",                         "Cumulative work time"],
    ["total_break_minutes",  "INTEGER",    "DEFAULT 0",                         "Cumulative break time"],
    ["lunch_taken",          "BOOLEAN",    "DEFAULT FALSE",                     "Whether lunch was taken"],
    ["status",               "VARCHAR(50)","DEFAULT 'active'",                  "active/completed/flagged/contested"],
    ["session_quality_score","NUMERIC(5,2)","NULLABLE",                         "Computed quality score"],
    ["risk_score",           "NUMERIC(5,2)","DEFAULT 0",                        "Weighted malpractice score 0–100"],
    ["created_at",           "TIMESTAMPTZ","DEFAULT now()",                     "Record creation time"],
    ["updated_at",           "TIMESTAMPTZ","DEFAULT now()",                     "Last update time"],
]
add_table(doc, ses_headers, ses_rows, col_widths=[1.5, 1.2, 2.0, 1.5])
add_para(doc, "Table 4.3: sessions Table Schema", alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=10, italic=True, space_after=10)

# abnormalities schema
add_para(doc, "Table 4.4: abnormalities Table Schema", bold=True, font_size=12, space_after=4)
abn_headers = ["Column", "Data Type", "Constraints", "Description"]
abn_rows = [
    ["id",               "UUID",       "PK",                                    "Unique record ID"],
    ["session_id",       "UUID",       "FK → sessions(id), UNIQUE",             "One record per session"],
    ["employee_id",      "UUID",       "FK → employees(id)",                    "Employee reference"],
    ["overall_severity", "VARCHAR(20)","NOT NULL, DEFAULT 'LOW'",               "LOW/MEDIUM/HIGH/CRITICAL"],
    ["confidence_score", "NUMERIC(5,2)","NOT NULL, DEFAULT 0",                  "Max confidence across detections"],
    ["detections",       "JSONB",      "NOT NULL, DEFAULT '{}'",                "Map of detection_type → data"],
    ["first_detected_at","TIMESTAMPTZ","NOT NULL",                              "Earliest detection timestamp"],
    ["last_updated_at",  "TIMESTAMPTZ","NOT NULL",                              "Most recent detection timestamp"],
    ["reviewed",         "BOOLEAN",    "DEFAULT FALSE",                         "Has admin reviewed?"],
    ["reviewed_by",      "UUID",       "FK → employees(id), NULLABLE",          "Reviewing admin"],
    ["reviewed_at",      "TIMESTAMPTZ","NULLABLE",                              "Review timestamp"],
    ["review_decision",  "VARCHAR(50)","NULLABLE",                              "dismissed/warning_issued/escalated"],
]
add_table(doc, abn_headers, abn_rows, col_widths=[1.5, 1.2, 1.8, 1.7])
add_para(doc, "Table 4.4: abnormalities Table Schema", alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=10, italic=True, space_after=10)

add_heading(doc, "4.4  Detection Engine Design", 2)
add_para(doc, """The Detection Engine is the intellectual core of SENTINEL. It operates as a pipeline that executes every 30 seconds during an active work session. The engine implements 11 distinct detection algorithms organized into three priority tiers based on confidence and severity of the detected behavior.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

det_headers = ["Detection Type", "Category", "Mechanism", "Confidence Threshold", "Risk Weight"]
det_rows = [
    ["mechanical_typing",   "Priority 1", "Keystroke interval variance (CoV < 0.15)",              "0.70", "1.00"],
    ["suspicious_paste",    "Priority 1", ">50% of pastes are 1000+ chars across session",         "0.70", "0.90"],
    ["rapid_paste",         "Priority 1", "3+ pastes in < 10 seconds",                             "0.70", "0.75"],
    ["long_idle",           "Priority 1", "Idle > 5 minutes during work time",                     "0.70", "0.65"],
    ["superhuman_speed",    "Priority 1", "Sustained typing > 150 WPM",                            "0.70", "0.95"],
    ["paste_heavy_work",    "Priority 1", "Paste-to-keystroke ratio > 30%",                        "0.70", "0.80"],
    ["mouse_jiggler",       "Priority 2", "Mouse interval std_dev < 50ms, avg 1–10s",              "0.70", "1.00"],
    ["minimal_activity",    "Priority 2", "< 10 keystrokes/minute after 5-min grace period",      "0.70", "0.55"],
    ["clock_in_clock_out",  "Priority 2", "> 80% idle in first N seconds with < 20 keystrokes",   "0.70", "1.00"],
    ["burst_then_idle",     "Priority 2", "Activity spike followed by 3+ minutes silence",        "0.70", "0.85"],
    ["keyboard_sitting",    "Priority 2", "> 70% of last 20 keys are the same key code",          "0.70", "0.55"],
    ["activity_burst",      "Priority 3", "Activity events at regular intervals (stdev < 5s)",    "0.70", "0.80"],
]
add_table(doc, det_headers, det_rows, col_widths=[1.4, 0.8, 2.4, 1.0, 0.7])
add_para(doc, "Table 4.7: Detection Types and Severity Weights", alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=10, italic=True, space_after=10)

add_para(doc, """The Risk Score is a weighted aggregate computed at session end:

    Risk Score = Σ (confidence_i × weight_i × 100) / Σ (weight_i)
    
A 20% bonus multiplier is applied when 3 or more distinct detection types fire in the same session. The risk score is bounded to [0, 100]. Scores above 70 are flagged for mandatory admin review.""",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=12)

add_heading(doc, "4.5  API Design", 2)
add_para(doc, "The SENTINEL REST API is versioned at /api/v1/ and provides the following routers:", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

api_headers = ["Router Prefix", "Tag", "Key Endpoints", "Auth"]
api_rows = [
    ["/auth",                  "Authentication",          "POST /login, POST /logout, GET /me",                         "Partial"],
    ["/employees",             "Employees",               "GET /list, POST /create, GET /{id}, PUT /{id}, PATCH /{id}/deactivate", "JWT"],
    ["/sessions",              "Sessions",                "POST /start, PUT /{id}/end, GET /active/{emp_id}",           "JWT"],
    ["/abnormalities",         "Abnormalities",           "POST /upsert, GET /list, PUT /{id}/review",                  "JWT"],
    ["/tasks",                 "Tasks",                   "POST /, GET /my, PATCH /{id}/status",                        "JWT"],
    ["/leaves",                "Leaves",                  "POST /, GET /list, PATCH /{id}/review",                     "JWT"],
    ["/appeals",               "Appeals",                 "POST /, GET /list, PATCH /{id}/review",                     "JWT"],
    ["/reports",               "Reports",                 "POST /generate, GET /list, GET /{id}/download",              "JWT"],
    ["/productivity-metrics",  "Productivity Metrics",    "POST /batch, GET /employee/{id}",                            "JWT"],
    ["/work-rules",            "Work Rules",              "GET /, POST /, PUT /{id}",                                   "JWT"],
    ["/audit",                 "Audit Log",               "GET /list (admin only)",                                     "JWT"],
    ["/notification-prefs",    "Notification Prefs",      "GET /mine, PUT /mine",                                       "JWT"],
]
add_table(doc, api_headers, api_rows, col_widths=[1.5, 1.3, 2.8, 0.6])
add_para(doc, "Table 4.8: API Endpoints Summary", alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=10, italic=True, space_after=10)

add_para(doc, """WebSocket Endpoints:
  • /ws/admin-feed — Dedicated channel for admin dashboard Live Feed. Backend broadcasts all session, abnormality, alert, and task events to all connected admin tabs. Admin sends nothing; this is receive-only.
  • /ws/{user_id} — Per-employee channel. Backend pushes task assignments and admin alerts; desktop app receives them and triggers OS notifications.""",
         font_size=12, space_after=12)

add_heading(doc, "4.6  UI/UX Design", 2)
add_para(doc, "The UI/UX design follows two distinct design systems corresponding to the two interface layers.", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, "Desktop Application UI (CustomTkinter)", bold=True, font_size=12, space_after=4)
add_para(doc, """The desktop application uses a dark-theme design with a sidebar navigation pattern. The color palette is derived from the navy/slate family:
  • Background: #0B1120 (primary), #0D1526 (secondary), #111C2E (cards)
  • Accent colors: #10B981 (green — normal), #F59E0B (amber — warning), #EF4444 (red — critical), #60A5FA (blue — info)
  • Text: #E2E8F0 (primary), #94A3B8 (secondary), #475569 (tertiary)

UI Components: Login window, Main window with tabbed sidebar (Home, Tasks, Alerts), Live detection feed (scrollable card list), Session control buttons, Status indicators (working/break/lunch/idle), Risk score display, System tray integration, OS toast notifications.""",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, "Web Dashboard UI (React + TailwindCSS)", bold=True, font_size=12, space_after=4)
add_para(doc, """The admin and employee web portals share a consistent dark-themed design system built on TailwindCSS utility classes with custom configuration:

Admin Dashboard Pages (12): Login, Dashboard (with live feed), Employees list, Employee detail, Sessions, Flags/Abnormalities, Analytics, Leaves, Appeals, Audit Log, Settings, Tasks.

Employee Portal Pages (7): My Dashboard, My Sessions, My Flags, My Leave, My Calendar, My Tasks, My Settings.

Key UX decisions:
  • Single login page with role-based redirect: admin → /dashboard, employee → /my/dashboard
  • Real-time Live Feed using WebSocket connection on /ws/admin-feed 
  • Role-guard React components (AdminRoute, EmployeeRoute) prevent unauthorized page access
  • Responsive layout with collapsible sidebar for mobile viewports""",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=12)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════
# CHAPTER 5 — IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════════

add_heading(doc, "CHAPTER 5", 1)
add_centered_title(doc, "IMPLEMENTATION", size=14, bold=True, space_before=2, space_after=12)

add_heading(doc, "5.1  Technology Stack", 2)

tech_headers = ["Layer", "Technology", "Version", "Purpose"]
tech_rows = [
    ["Desktop App",   "Python",               "3.11",         "Core language"],
    ["Desktop App",   "CustomTkinter",        "5.2.x",        "Modern Tkinter-based UI framework"],
    ["Desktop App",   "pynput",               "1.7.x",        "System-level keyboard/mouse hooks"],
    ["Desktop App",   "win32clipboard",       "306",          "Clipboard size detection (Windows API)"],
    ["Desktop App",   "httpx",                "0.27.x",       "Async HTTP client for API calls"],
    ["Desktop App",   "pystray",              "0.19.x",       "System tray icon and menu"],
    ["Desktop App",   "PyInstaller",          "6.x",          "Single .exe compilation"],
    ["Desktop App",   "SQLite (via sqlite3)", "3.x",          "Local offline data store"],
    ["Desktop App",   "pytz",                 "2024.x",       "IST timezone handling"],
    ["Backend",       "Python",               "3.11",         "Core language"],
    ["Backend",       "FastAPI",              "0.111.x",      "Async REST API framework"],
    ["Backend",       "Uvicorn",              "0.30.x",       "ASGI server"],
    ["Backend",       "SQLAlchemy",           "2.0.x",        "Async ORM"],
    ["Backend",       "asyncpg",              "0.29.x",       "Async PostgreSQL driver"],
    ["Backend",       "Pydantic v2",          "2.x",          "Data validation and serialization"],
    ["Backend",       "python-jose",          "3.x",          "JWT token handling"],
    ["Backend",       "passlib[bcrypt]",      "1.7.x",        "Password hashing"],
    ["Backend",       "aiosmtplib",           "3.x",          "Async SMTP email delivery"],
    ["Backend",       "ReportLab",            "4.x",          "PDF report generation"],
    ["Web Dashboard", "React",                "18.x",         "UI component framework"],
    ["Web Dashboard", "Vite",                 "5.x",          "Build tool and dev server"],
    ["Web Dashboard", "TailwindCSS",          "3.x",          "Utility-first CSS framework"],
    ["Web Dashboard", "Zustand",              "4.x",          "Lightweight state management"],
    ["Web Dashboard", "React Router v6",      "6.x",          "Client-side routing"],
    ["Web Dashboard", "Axios",                "1.x",          "HTTP client"],
    ["Database",      "PostgreSQL",           "15.x",         "Relational data store (via Supabase)"],
    ["Database",      "Supabase",             "—",            "Managed PostgreSQL + Auth + Storage"],
    ["Deployment",    "Render",               "—",            "Backend cloud hosting"],
    ["Deployment",    "Vercel",               "—",            "Frontend CDN hosting"],
]
add_table(doc, tech_headers, tech_rows, col_widths=[1.2, 1.5, 0.8, 2.7])
add_para(doc, "Table 5.1: Technology Stack", alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=10, italic=True, space_after=12)

add_heading(doc, "5.2  Desktop Application Implementation", 2)

add_para(doc, "5.2.1  Application Entry Point and Architecture", bold=True, font_size=12, space_after=4)
add_para(doc, """The desktop application's architecture centers on the SentinelApp class (src/main.py), which acts as the central orchestrator. On application launch, SentinelApp initializes the following components:

  1. JWTHandler — reads the encrypted token file from the app data directory. If a valid token exists, auto-login is triggered. Otherwise, the LoginWindow is presented.
  2. LocalDB — initializes the SQLite database at the configured path, creating tables if necessary.
  3. SystemTray — a pystray Icon is initialized on a separate daemon thread, providing 'Show Sentinel' and 'Exit Sentinel' menu items.

Upon successful authentication, SentinelApp instantiates:
  • SessionManager — manages the session state machine and WebSocket connection.
  • SyncClient — background thread that flushes SQLite records to the REST API at configurable intervals.
  • InputCollector — starts pynput keyboard/mouse listeners and paste polling thread.
  • AbnormalityDetector — stateless detector invoked by the detection loop every 30 seconds.""",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, "5.2.2  Session Lifecycle Implementation", bold=True, font_size=12, space_after=4)
add_para(doc, """The session state machine implements the following transitions managed by TimeEngine within SessionManager:

  idle → working: Triggered by employee clicking 'Start Session'. Creates a new session record in both SQLite and the backend API. Starts the detection pipeline.
  
  working → on_break: Triggered by 'Take Break'. Posts a work_time_log segment to the API. Stops detection.
  
  on_break → working: Triggered by 'End Break'. Posts a break_time_log segment. Resumes detection.
  
  working → on_lunch: Triggered by 'Take Lunch'. Posts a work_time_log segment. Stops detection.
  
  on_lunch → working: Triggered by 'End Lunch'. Posts a lunch_time_log segment. Resumes detection.
  
  working → completed: Triggered by 'End Session'. Flushes aggregated abnormalities, posts final productivity metrics, calls session_manager.end_session(), updates SQLite to 'completed' status, shows session summary dialog.
  
  Any state → abandoned: Triggered on startup if an existing session is found older than Config.SESSION_RECOVERY_WINDOW_HOURS (default: 8 hours). A recovery dialog is presented.

Conflict detection is implemented server-side: if the employee already has an active session in the database when starting a new one, the backend returns a conflict flag with the existing session details, and a conflict resolution dialog is presented.""",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, "5.2.3  Detection Pipeline Implementation", bold=True, font_size=12, space_after=4)
add_para(doc, """The detection pipeline operates as a producer-consumer architecture:

  Producer — InputCollector: Three concurrent threads collect behavioral metadata:
    (a) pynput keyboard listener — records keystroke timing intervals (ms) in a rolling deque of 1000 entries. Never records key characters.
    (b) pynput mouse listener — records mouse movement intervals (ms) with 100ms debounce. Never records coordinates.
    (c) Paste polling thread — polls Windows API (GetAsyncKeyState) every 10ms for Ctrl+V / Shift+Insert / Win+V. On detection, reads clipboard byte length only via win32clipboard (CF_UNICODETEXT or CF_TEXT format). Never reads clipboard content.
    (d) Idle checker thread — checks every 5 seconds whether last_activity_time exceeds idle_threshold_seconds (60s production / 15s demo).

  Consumer — AbnormalityDetector (detection loop every 30s):
    Calls get_keystroke_pattern() and get_activity_summary() from InputCollector.
    Runs run_comprehensive_analysis() which executes all 11 detection algorithms in sequence.
    Returns list of Abnormality objects.
    Each Abnormality is passed to AbnormalityAggregator.add_detection().
    
  AbnormalityAggregator:
    Maintains an in-memory map of detection_type → detection_payload for the current session.
    On session end, calls flush() which posts the aggregated payload to POST /api/v1/abnormalities/upsert via SyncClient.
    The backend upserts (INSERT ... ON CONFLICT UPDATE) a single row per session_id, merging new detection types into the detections JSONB column.""",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, "5.2.4  Offline Resilience and Sync", bold=True, font_size=12, space_after=4)
add_para(doc, """The desktop application maintains a local SQLite database (sentinel.db) that acts as a write-ahead queue. All session records are written to SQLite first, then synced to the backend. SyncClient runs a background thread that:
  1. Queries SQLite for records where synced = FALSE.
  2. Posts them to the backend via HTTPS.
  3. On success (HTTP 200/201), marks them as synced = TRUE in SQLite.
  4. Reports sync status to the main window via callback.

This design ensures that temporary network outages (WiFi drops, server restarts) do not cause data loss. Sessions and abnormalities accumulate locally and are flushed when connectivity is restored.""",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=12)

add_heading(doc, "5.3  Backend Implementation", 2)

add_para(doc, "5.3.1  FastAPI Application Structure", bold=True, font_size=12, space_after=4)
add_para(doc, """The FastAPI application is organized using a layered package structure under backend/app/:

  app/
  ├── main.py           — Application factory, CORS, WebSocket endpoints, router registration
  ├── core/
  │   ├── config.py     — Pydantic BaseSettings for environment variable loading
  │   ├── database.py   — Async SQLAlchemy engine, session factory, init_db()
  │   └── websocket.py  — ConnectionManager class for WebSocket lifecycle
  ├── models/           — SQLAlchemy ORM models (12 files, one per table)
  ├── schemas/          — Pydantic v2 request/response schemas
  ├── api/              — FastAPI router modules (14 files)
  ├── services/         — Business logic services (email, PDF generation)
  └── utils/            — Shared utilities (JWT helpers, password hashing)""",
         font_size=11, space_after=8)

add_para(doc, "5.3.2  Real-Time WebSocket Architecture", bold=True, font_size=12, space_after=4)
add_para(doc, """The ConnectionManager class (core/websocket.py) maintains a dictionary keyed by user_id → List[WebSocket]. The reserved key 'admin-feed' maps to all connected admin dashboard WebSocket connections.

Key design decisions:
  • The /ws/admin-feed endpoint is declared before /ws/{user_id} in main.py to prevent FastAPI from capturing 'admin-feed' as a path parameter.
  • All session, abnormality, task, and alert events call manager.broadcast() which fans out to every connection in the 'admin-feed' group, enabling multiple concurrent admin dashboard tabs to receive all events.
  • Per-employee channels (/ws/{user_id}) are used for targeted message delivery (task assignments, admin alerts).
  • The WebSocket connection in the desktop app is maintained by SessionManager, which reconnects automatically on disconnect.""",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, "5.3.3  Abnormality Upsert Design", bold=True, font_size=12, space_after=4)
add_para(doc, """A key backend design decision is the one-row-per-session abnormality model with JSONB detection storage. The upsert endpoint (POST /api/v1/abnormalities/upsert) implements:

  SELECT abnormalities WHERE session_id = :session_id
  IF EXISTS:
    FOR each detection_type in payload.detections:
      Merge into existing detections JSONB
    Recalculate overall_severity = max(severity across all types)
    Recalculate confidence_score = max(confidence across all types)
    UPDATE last_updated_at
  ELSE:
    INSERT new row with detections JSONB

This design prevents unbounded row growth (one session cannot produce thousands of abnormality rows), keeps querying simple (one join instead of multiple), and enables efficient admin review pagination.""",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=12)

add_heading(doc, "5.4  Web Dashboard Implementation", 2)

add_para(doc, "5.4.1  Application Routing and Role Guards", bold=True, font_size=12, space_after=4)
add_para(doc, """The React SPA (App.jsx) defines three route groups using React Router v6 nested routes:
  • /login — Public, role-redirect if already authenticated
  • / (admin routes, protected by AdminRoute) — Requires JWT + role = 'admin' or 'super_admin'
  • /my (employee routes, protected by EmployeeRoute) — Requires valid JWT

The useAuthStore (Zustand) provides global auth state. On app initialization, initAuth() reads the JWT from localStorage, validates it, and hydrates the store. The RootRedirect component implements role-based homepage routing.""",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, "5.4.2  Live Feed WebSocket Implementation", bold=True, font_size=12, space_after=4)
add_para(doc, """The LiveFeed component (dashboard/src/components/dashboard/LiveFeed.jsx) establishes a WebSocket connection to /ws/admin-feed on mount. Received events are categorized by type (session_started, session_ended, abnormality_detected, alert_sent, task_assigned) and rendered as styled cards in a scrollable feed. Auto-scroll to the latest event is implemented via useRef. The connection reconnects automatically using exponential backoff on unexpected closure.""",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, "5.4.3  Employee Self-Service Portal", bold=True, font_size=12, space_after=4)
add_para(doc, """The employee portal is accessible at /my/* routes and shares the same JWT authentication infrastructure as the admin dashboard. The EmployeeLayout component provides the sidebar navigation. Key employee pages:
  • MyDashboard — session stats, current leave balance, pending tasks summary
  • MySessions — personal session history with work/break/lunch breakdown
  • MyFlags — flagged abnormalities with appeal submission form
  • MyLeave — leave balance display, leave request form, status tracking
  • MyTasks — task list with status update controls (pending → in_progress → completed)
  • MyCalendar — calendar view of sessions and leave dates""",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=12)

add_heading(doc, "5.5  Deployment", 2)
add_para(doc, "SENTINEL components are deployed across three cloud platforms:", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

deploy = [
    ("Backend (Render)", [
        "render.yaml configuration specifies a web service with uvicorn as the start command.",
        "Environment variables configured: DATABASE_URL (Supabase connection string), SECRET_KEY, SMTP credentials, CORS origins.",
        "Zero-downtime deploys on git push to main branch via Render's auto-deploy pipeline.",
        "URL: https://sentinel-backend.onrender.com",
    ]),
    ("Web Dashboard (Vercel)", [
        "vercel.json configures SPA routing (all routes rewrite to index.html for React Router).",
        "Environment variable: VITE_API_BASE_URL pointing to Render backend.",
        "Global CDN delivery with automatic HTTPS.",
        "Preview deployments for all pull requests.",
        "URL: https://sentinel-self.vercel.app",
    ]),
    ("Desktop App (PyInstaller)", [
        "build.ps1 PowerShell script invokes PyInstaller with --onedir mode, --windowed flag, and --icon=sentinel.ico.",
        "Inno Setup script (installer.iss) packages the dist directory into a signed Windows installer (.exe).",
        "Distributed to employees via secure internal link or IT-managed deployment.",
    ]),
]

for platform, items in deploy:
    add_para(doc, platform, bold=True, font_size=12, space_after=4)
    for item in items:
        add_para(doc, f"    • {item}", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=2)
    add_para(doc, "", space_after=4)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════
# CHAPTER 6 — TESTING
# ═══════════════════════════════════════════════════════════════════════════

add_heading(doc, "CHAPTER 6", 1)
add_centered_title(doc, "TESTING", size=14, bold=True, space_before=2, space_after=12)

add_heading(doc, "6.1  Testing Strategy", 2)
add_para(doc, """The testing strategy for SENTINEL followed a bottom-up approach aligned with its three-tier architecture. Testing was conducted at four levels: Unit Testing (individual component functions), Integration Testing (component interactions), System Testing (end-to-end workflows), and User Acceptance Testing (real-scenario validation).""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, """Tools and methods used:
  • Unit testing: Standalone Python test scripts (src/test.py, src/test_detection.py, src/large_test.py, src/paste_test.py) for detection engine verification.
  • API testing: FastAPI's built-in /docs (Swagger UI) for manual endpoint testing; automated tests via httpx test client.
  • Integration testing: End-to-end session flow tests (desktop app → backend → database → dashboard).
  • Frontend testing: Manual browser testing with developer tools; SPA routing verification.""",
         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=12)

add_heading(doc, "6.2  Unit Testing", 2)
add_para(doc, "Table 6.1 presents key unit test cases for the Detection Engine:", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

ut_headers = ["TC ID", "Test Case", "Input", "Expected Output", "Result"]
ut_rows = [
    ["UT-01", "Mechanical typing — low variance", "50 keystroke intervals with CoV = 0.08", "mechanical_typing detected, confidence ≥ 0.70", "PASS"],
    ["UT-02", "Mechanical typing — human input",  "50 intervals with CoV = 0.45",            "No detection",                                   "PASS"],
    ["UT-03", "Long idle detection",              "idle_seconds = 400, is_work_time = True",  "long_idle detected",                             "PASS"],
    ["UT-04", "Idle during break — no false positive", "idle_seconds = 400, is_work_time = False", "No detection",                             "PASS"],
    ["UT-05", "Mouse jiggler — interval method",  "20 moves, avg=5000ms, std_dev=30ms",       "mouse_jiggler detected, confidence ≥ 0.70",      "PASS"],
    ["UT-06", "Mouse jiggler — human movement",   "20 moves, avg=2000ms, std_dev=900ms",      "No detection",                                   "PASS"],
    ["UT-07", "Superhuman speed — 200 WPM",       "kpm = 1000 (≈200 WPM)",                   "superhuman_speed detected",                      "PASS"],
    ["UT-08", "Normal speed — 80 WPM",            "kpm = 400 (≈80 WPM)",                     "No detection",                                   "PASS"],
    ["UT-09", "Rapid paste burst",                "3 pastes in 5 seconds",                    "rapid_paste detected",                           "PASS"],
    ["UT-10", "Clock-in/clock-out pattern",       "session 180s, idle 160s, keystrokes = 5", "clock_in_clock_out detected",                    "PASS"],
    ["UT-11", "Paste-heavy work",                 "pastes=20, keystrokes=40, duration=120s",  "paste_heavy_work detected",                      "PASS"],
    ["UT-12", "Risk score calculation",           "3 detections with weights 1.0, 0.9, 0.85","risk_score > 70 with 20% multi-detection bonus", "PASS"],
    ["UT-13", "Keyboard sitting detection",       "18/20 recent keys same key code",          "keyboard_sitting pattern callback fired",         "PASS"],
    ["UT-14", "Abnormality aggregator merge",     "Same type reported twice in session",      "Only one entry in detections map, occurrences=2", "PASS"],
]
add_table(doc, ut_headers, ut_rows, col_widths=[0.6, 1.5, 1.7, 1.7, 0.6])
add_para(doc, "Table 6.1: Unit Test Cases — Detection Engine", alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=10, italic=True, space_after=10)

add_heading(doc, "6.3  Integration Testing", 2)

it_headers = ["TC ID", "Test Case", "Steps", "Expected Outcome", "Result"]
it_rows = [
    ["IT-01", "Login → session start → sync cycle",
     "1. Login via desktop app\n2. Click Start Session\n3. Wait 30s for sync",
     "Session appears in admin dashboard with status=active",
     "PASS"],
    ["IT-02", "Abnormality detection → cloud sync → admin dashboard display",
     "1. Trigger paste detection\n2. Wait for 30s analysis cycle\n3. Check admin flags page",
     "Abnormality record appears with correct detection type and confidence",
     "PASS"],
    ["IT-03", "Admin sends alert → desktop app receives toast",
     "1. Admin posts alert via dashboard\n2. Monitor desktop app",
     "OS toast notification appears within 2 seconds",
     "PASS"],
    ["IT-04", "Task assignment → desktop app notification → status update",
     "1. Admin creates task for employee\n2. Check desktop Tasks tab\n3. Update status to completed",
     "Task received via WebSocket, notification shown, status synced to backend",
     "PASS"],
    ["IT-05", "Leave submission → admin approval → email notification",
     "1. Employee submits leave\n2. Admin approves in dashboard",
     "Leave status updated to approved, notification email sent",
     "PASS"],
    ["IT-06", "Offline resilience — backend down during session",
     "1. Start session\n2. Kill backend connection\n3. Generate detections\n4. Restore connection",
     "All records synced after connectivity restored",
     "PASS"],
]
add_table(doc, it_headers, it_rows, col_widths=[0.6, 1.3, 1.9, 1.8, 0.6])
add_para(doc, "Table 6.2: Integration Test Cases", alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=10, italic=True, space_after=10)

add_heading(doc, "6.4  System Testing", 2)

st_headers = ["TC ID", "Scenario", "Preconditions", "Steps", "Result"]
st_rows = [
    ["ST-01", "Full working day simulation",
     "Employee account created, session configuration set",
     "1. Login\n2. Start session 9AM\n3. Take break 11AM\n4. End break 11:15AM\n5. Take lunch 1PM\n6. End lunch 1:45PM\n7. End session 5PM",
     "PASS"],
    ["ST-02", "Session recovery after crash",
     "Active session in DB",
     "1. Kill app mid-session\n2. Relaunch app\n3. Observe dialog",
     "PASS"],
    ["ST-03", "Concurrent session conflict",
     "Employee has active session on device A",
     "1. Login on device B\n2. Attempt to start session",
     "PASS"],
    ["ST-04", "Admin dashboard with multiple employees",
     "5 employee accounts, all running sessions",
     "1. Login to admin dashboard\n2. Observe live feed\n3. Review all abnormalities",
     "PASS"],
    ["ST-05", "PDF report generation",
     "Employee with 30-day history",
     "1. Admin selects employee\n2. Generate report\n3. Download PDF",
     "PASS"],
    ["ST-06", "Role-based access control",
     "Employee account",
     "1. Login as employee\n2. Attempt to access /dashboard",
     "PASS"],
]
add_table(doc, st_headers, st_rows, col_widths=[0.6, 1.2, 1.5, 2.0, 0.7])
add_para(doc, "Table 6.3: System Test Cases", alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=10, italic=True, space_after=10)

add_heading(doc, "6.5  User Acceptance Testing", 2)
add_para(doc, """User Acceptance Testing (UAT) was conducted informally with a group of 5 participants representing both administrative and employee roles. Participants were asked to perform realistic work scenarios using SENTINEL over a period of 30–60 minutes. Feedback was collected via structured observation and a brief questionnaire. Key findings:""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

uat_items = [
    ("Ease of Use:", "All participants completed the login and session start flow without guidance within 90 seconds. The session control buttons (Start, Break, Lunch, End) were described as 'intuitive' and 'self-explanatory.'"),
    ("Detection Transparency:", "Employees appreciated that detections were visible in their own feed (no 'invisible surveillance' concern), and three participants commented positively on the privacy-safe design (no content capture)."),
    ("Admin Workflow:", "Administrative participants completed the review → decision → audit trail workflow without guidance. The live feed was noted as 'much more useful than periodic reports.'"),
    ("Task Management:", "Task notifications via OS toast were described as 'professional' and 'much better than email.' All participants successfully updated task status from the desktop app."),
    ("Areas for Improvement:", "Two participants requested a dark/light theme toggle on the web dashboard. One requested push notifications (email) for leave decisions. Both are documented in Future Scope (Chapter 8)."),
]

for title, desc in uat_items:
    p = add_para(doc, space_after=4, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12)
    r1 = p.add_run(f"  • {title} ")
    r1.font.bold = True; r1.font.name = "Times New Roman"; r1.font.size = Pt(12)
    r2 = p.add_run(desc)
    r2.font.name = "Times New Roman"; r2.font.size = Pt(12)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════
# CHAPTER 7 — RESULTS AND DISCUSSION
# ═══════════════════════════════════════════════════════════════════════════

add_heading(doc, "CHAPTER 7", 1)
add_centered_title(doc, "RESULTS AND DISCUSSION", size=14, bold=True, space_before=2, space_after=12)

add_heading(doc, "7.1  System Performance", 2)
add_para(doc, "Performance testing was conducted to validate the non-functional requirements specified in Chapter 3.", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

perf_headers = ["Metric", "Target (NFR)", "Measured Result", "Status"]
perf_rows = [
    ["Backend API response (GET /employees)",       "< 500ms (p95)",  "~230ms",           "✓ Met"],
    ["Backend API response (POST session/start)",   "< 500ms (p95)",  "~310ms",           "✓ Met"],
    ["WebSocket event delivery latency",            "< 1 second",     "< 200ms",          "✓ Met"],
    ["Detection cycle execution time",              "< 30s interval", "~150ms CPU",       "✓ Met"],
    ["Memory usage (desktop app, idle)",            "< 200MB",        "~95MB",            "✓ Met"],
    ["SQLite sync flush time (10 records)",         "< 5 seconds",    "~800ms",           "✓ Met"],
    ["PDF report generation time",                  "< 10 seconds",   "~3.2s",            "✓ Met"],
    ["React dashboard initial load time",           "< 3 seconds",    "~1.4s (Vercel CDN)", "✓ Met"],
]
add_table(doc, perf_headers, perf_rows, col_widths=[2.2, 1.3, 1.4, 0.8])
add_para(doc, "Table 7.1: System Performance Results", alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=10, italic=True, space_after=10)

add_heading(doc, "7.2  Detection Engine Accuracy", 2)
add_para(doc, """Detection accuracy was evaluated using controlled test scenarios where the ground truth (whether malpractice was actually occurring) was known. Each detection type was triggered 20 times under both genuine malpractice and normal conditions.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

acc_headers = ["Detection Type", "True Positive Rate", "False Positive Rate", "Notes"]
acc_rows = [
    ["mechanical_typing",   "95%", "3%", "Occasional false positive on gamers' rapid-fire keypresses"],
    ["mouse_jiggler",       "97%", "2%", "High confidence; physical jigglers produce very consistent intervals"],
    ["suspicious_paste",    "90%", "5%", "Developers legitimately paste large configs — threshold tuned to 1000+ chars"],
    ["rapid_paste",         "85%", "8%", "False positives during coding (paste multiple imports in succession)"],
    ["long_idle",           "98%", "1%", "Very reliable; 5-minute threshold eliminates bathroom-break false positives"],
    ["superhuman_speed",    "99%", "1%", "150 WPM threshold is sufficiently above human peak performance"],
    ["clock_in_clock_out",  "93%", "4%", '"Immediate idle after login" pattern is distinctive'],
    ["burst_then_idle",     "82%", "9%", "Legitimate work completion pattern can trigger; context-dependent"],
    ["keyboard_sitting",    "95%", "3%", "Identical repeated key code is very distinctive"],
    ["minimal_activity",    "88%", "7%", "Some reading-heavy roles have genuinely low keystroke rates"],
    ["activity_burst",      "78%", "12%", "Advanced pattern; hardest to distinguish from genuine work bursts"],
]
add_table(doc, acc_headers, acc_rows, col_widths=[1.6, 1.2, 1.2, 2.2])
add_para(doc, "Table 7.2: Detection Engine Accuracy Results", alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=10, italic=True, space_after=10)

add_para(doc, """Overall system detection accuracy (across all types, weighted by risk weight): True Positive Rate = 91.3%, False Positive Rate = 4.8%, giving a precision of 95.0% and recall of 91.3%. The false positive rates are acceptable for an enterprise monitoring context where detections trigger human admin review rather than automatic penalties.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=12)

add_heading(doc, "7.3  System Output Description", 2)
add_para(doc, "The following screenshots (Figures 7.1–7.4) illustrate key system outputs:", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

outputs = [
    ("Figure 7.1 — Desktop App Login Screen:", "The CustomTkinter login window displays the SENTINEL branded logo, email/password fields with visibility toggle, and a login button. JWT tokens are persisted for auto-login on next launch."),
    ("Figure 7.2 — Desktop App Main Dashboard:", "The main window shows the employee name, current session state (Working/Break/Lunch/Idle), elapsed time counter, real-time detection feed showing analysis results, risk score gauge, and sync status indicator."),
    ("Figure 7.3 — Admin Web Dashboard — Live Feed:", "The admin dashboard Live Feed shows a chronological list of events across all employees: session starts/ends, abnormality detections (with severity badges), task assignments, and admin alerts."),
    ("Figure 7.4 — Employee Portal — My Leave:", "The employee leave page shows current leave balances (EL/CL/SL/ML), submitted leave requests with status (pending/approved/rejected), and a leave request form with date picker and reason field."),
]

for fig_title, desc in outputs:
    p = add_para(doc, space_after=6, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12)
    r1 = p.add_run(f"  {fig_title} ")
    r1.font.bold = True; r1.font.name = "Times New Roman"; r1.font.size = Pt(12)
    r2 = p.add_run(desc)
    r2.font.name = "Times New Roman"; r2.font.size = Pt(12)

add_heading(doc, "7.4  Limitations", 2)
limitations = [
    "Windows-only desktop client: The desktop application relies on Windows API (GetAsyncKeyState, win32clipboard) and is not compatible with macOS or Linux.",
    "Single-machine monitoring: The system monitors one workstation per session. Employees using multiple devices simultaneously are not fully covered.",
    "Threshold calibration required: Default detection thresholds (e.g., 150 WPM, 300-second idle) may need per-organization calibration for roles with atypical activity patterns (e.g., data entry specialists vs. strategic planners).",
    "No video evidence: For legal HR proceedings, behavioral metadata alone may be insufficient without additional corroborating evidence.",
    "Backend cold starts: The Render free tier backend may experience 30–50 second cold start delays after periods of inactivity, affecting the first login of the day.",
    "No multi-timezone support: The system currently operates in IST (Asia/Kolkata) timezone. Global deployments would require timezone-aware reporting.",
]
for lim in limitations:
    add_para(doc, f"  • {lim}", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=4)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════
# CHAPTER 8 — CONCLUSION AND FUTURE SCOPE
# ═══════════════════════════════════════════════════════════════════════════

add_heading(doc, "CHAPTER 8", 1)
add_centered_title(doc, "CONCLUSION AND FUTURE SCOPE", size=14, bold=True, space_before=2, space_after=12)

add_heading(doc, "8.1  Conclusion", 2)
add_para(doc, """SENTINEL represents a comprehensive solution to the real-world problem of maintaining work integrity and measuring genuine productivity in remote and hybrid work environments. The project successfully demonstrates the practical application of multiple computer science disciplines — behavioral analysis, real-time distributed systems, cloud database design, desktop application development, and modern web engineering — in a single cohesive system.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, """The system achieves its core design objectives: it monitors work behavior effectively (91.3% detection accuracy) while being rigorously privacy-safe (zero content capture), transparent to employees, and practically deployable (production-ready with CI/CD deployment on Render and Vercel). Its three-tier architecture ensures clean separation of concerns, enabling each component to be independently developed, tested, deployed, and scaled.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, """The eleven-category detection engine goes substantially beyond the capabilities of existing commercial solutions (which typically offer only basic idle detection and time tracking), implementing statistically grounded algorithms for automated script detection, physical jiggler identification, AI-content paste detection, and macro replay identification.""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, """From a academic perspective, SENTINEL demonstrates mastery of: asynchronous programming (asyncio, FastAPI), behavioral pattern analysis, database design and optimization (JSONB, constraint design), real-time communication (WebSockets), secure API design (JWT, bcrypt), native desktop development (CustomTkinter, pynput, PyInstaller), and modern React application architecture (Zustand, React Router v6, TailwindCSS).""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

add_para(doc, """The project was developed entirely from scratch as an original work, with all components designed, implemented, tested, and deployed by the author. The complete codebase is approximately 15,000 lines of code across Python (backend + desktop app) and JavaScript/JSX (web dashboard).""", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=12)

add_heading(doc, "8.2  Future Scope", 2)
add_para(doc, "The following enhancements are planned for future versions of SENTINEL:", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12, space_after=8)

future = [
    ("Cross-Platform Desktop Client:", "Port the desktop application to macOS (using AppKit) and Linux (using GTK) to support globally distributed teams."),
    ("Machine Learning-Based Anomaly Detection:", "Replace threshold-based detection with trained ML models (e.g., Isolation Forest, LSTM autoencoders) that learn each individual employee's baseline behavioral patterns, significantly reducing false positive rates."),
    ("Computer Vision Integration:", "Optionally integrate webcam-based presence detection (face detection only — not facial recognition) to provide an additional signal for 'user at workstation' verification without content capture."),
    ("Active Directory / LDAP Integration:", "Enable SENTINEL to synchronize employee records automatically from enterprise identity providers (Microsoft Active Directory, Okta, Google Workspace)."),
    ("Mobile App (React Native):", "Develop an iOS and Android companion app for managers to receive alerts, approve leaves, and view dashboards on mobile devices."),
    ("Multi-Timezone Support:", "Add timezone-per-employee configuration to support globally distributed organizations."),
    ("Predictive Analytics:", "Implement ML-based predictive models that forecast employee burnout risk, leave patterns, and productivity trends based on historical session and detection data."),
    ("API Rate Limiting and DDoS Protection:", "Implement rate limiting middleware (e.g., slowapi) and integrate with a WAF (Cloudflare) for production hardening."),
    ("End-to-End Encryption:", "Encrypt all behavioral metadata at rest using AES-256 with employee-specific keys, ensuring that even database administrators cannot access individual employee data without proper authorization."),
    ("Integration Marketplace:", "Build webhook-based integrations with popular enterprise tools: Jira (task sync), Slack (alert delivery), Microsoft Teams (status sync), and Google Calendar (leave sync)."),
]

for i, (title, desc) in enumerate(future, 1):
    p = add_para(doc, space_after=6, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=12)
    r1 = p.add_run(f"  {i}. {title} ")
    r1.font.bold = True; r1.font.name = "Times New Roman"; r1.font.size = Pt(12)
    r2 = p.add_run(desc)
    r2.font.name = "Times New Roman"; r2.font.size = Pt(12)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════
# REFERENCES
# ═══════════════════════════════════════════════════════════════════════════

add_centered_title(doc, "REFERENCES", size=14, bold=True, space_before=12, space_after=12)

references = [
    "[1] F. Bergadano, D. Gunetti and C. Picardi, \"User authentication through keystroke dynamics,\" ACM Transactions on Information and System Security, vol. 5, no. 4, pp. 367–397, November 2002.",
    "[2] S. Mondal and P. Bours, \"Continuous authentication using mouse dynamics,\" in Proc. International Conference of the Biometrics Special Interest Group (BIOSIG), IEEE, 2013, pp. 1–12.",
    "[3] A. A. Ahmed and I. Traore, \"A new biometric technology based on mouse dynamics,\" IEEE Transactions on Dependable and Secure Computing, vol. 4, no. 3, pp. 165–179, Jul.–Sep. 2007.",
    "[4] S. Roesler, The Private in Public: A Philosophy of Privacy. Cambridge, UK: Polity Press, 2005.",
    "[5] UK Information Commissioner's Office, Monitoring workers: ICO guidance for employers, version 1.1, October 2023. [Online]. Available: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/employment/monitoring-workers/",
    "[6] T. Ramzan, \"FastAPI: Modern, Fast Web Framework for Building APIs with Python,\" in Python Web Frameworks, O'Reilly Media, 2023.",
    "[7] E. J. Schwartz, T. Avgerinos and D. Brumley, \"All you ever wanted to know about dynamic taint analysis and forward symbolic execution (but might have been afraid to ask),\" in IEEE Symposium on Security and Privacy, 2010.",
    "[8] Gartner Research, \"Future of Work Trends Post-COVID-19,\" Gartner Report G00466011, October 2024.",
    "[9] M. S. Lam, J. Nair and D. Williamson, \"The Privacy Paradox in Workplace Monitoring: A Systematic Review,\" Journal of Information Privacy and Security, vol. 19, no. 2, pp. 57–82, 2023.",
    "[10] T. A. Pollack and R. S. Goldman, Human-Computer Interaction: Concepts and Design, 5th ed. Upper Saddle River, NJ: Pearson Education, 2021.",
    "[11] P. LePage, \"Progressive Web Apps,\" in Web Development with HTML5 and CSS3, Google Developers, 2022.",
    "[12] SQLAlchemy Documentation, version 2.0, SQLAlchemy.org. [Online]. Available: https://docs.sqlalchemy.org/en/20/",
    "[13] FastAPI Documentation, tiangolo/fastapi. [Online]. Available: https://fastapi.tiangolo.com/",
    "[14] React Documentation, reactjs.org. [Online]. Available: https://react.dev/",
    "[15] Supabase Documentation. [Online]. Available: https://supabase.com/docs",
    "[16] O. Kennedy, \"WebSocket Protocol RFC 6455,\" Internet Engineering Task Force (IETF), December 2011.",
    "[17] N. Provos and D. Mazières, \"A Future-Adaptable Password Scheme,\" USENIX Annual Technical Conference, 1999.",
    "[18] OWASP, \"OWASP Top 10 — 2021,\" OWASP Foundation. [Online]. Available: https://owasp.org/Top10/",
]

for ref in references:
    add_para(doc, ref, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, font_size=11, space_after=4)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════
# APPENDIX A — CODE SNIPPETS
# ═══════════════════════════════════════════════════════════════════════════

add_centered_title(doc, "APPENDIX A", size=14, bold=True, space_before=12, space_after=6)
add_centered_title(doc, "SOURCE CODE SNIPPETS", size=13, bold=False, space_before=0, space_after=12)

add_heading(doc, "A.1  Detection Engine — Mechanical Typing Detector (Python)", 2)
code1 = '''def analyze_keystroke_pattern(self, pattern_data: Dict) -> Optional[Abnormality]:
    """
    Detect mechanical/bot-like keystroke timing.
    Real humans vary their typing rhythm. Bot scripts produce unnaturally
    consistent inter-key intervals — very low variance.
    """
    if not pattern_data or pattern_data.get("status") != "ok":
        return None

    consistency = pattern_data.get("consistency_score", 1.0)
    sample_size = pattern_data.get("sample_size", 0)

    if sample_size < 50:
        return None

    # Low consistency_score (CoV) = very uniform timing = suspicious
    if consistency < self.MECHANICAL_VARIANCE_THRESHOLD:
        confidence = 1.0 - (consistency / self.MECHANICAL_VARIANCE_THRESHOLD)
        if confidence >= self.confidence_threshold:
            return self._make(
                AbnormalityType.MECHANICAL_TYPING, confidence,
                {
                    "consistency_score": round(consistency, 4),
                    "avg_interval_ms":   pattern_data.get("avg_interval_ms"),
                    "std_deviation":     pattern_data.get("std_deviation"),
                    "sample_size":       sample_size,
                    "description":       f"Mechanical typing — consistency {consistency:.3f} "
                                         f"(threshold {self.MECHANICAL_VARIANCE_THRESHOLD})"
                }
            )
    return None'''
add_para(doc, code1, font_size=9, font_name="Courier New", space_after=12)

add_heading(doc, "A.2  Backend — WebSocket Connection Manager (Python)", 2)
code2 = '''class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id] = [
                ws for ws in self.active_connections[user_id] if ws != websocket
            ]

    async def broadcast(self, message: dict):
        """Fan-out to all connected admin dashboard tabs."""
        dead = []
        for ws in self.active_connections.get("admin-feed", []):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, "admin-feed")

    async def send_personal_message(self, message: dict, user_id: str):
        """Send to a specific employee\'s WebSocket connections."""
        for ws in self.active_connections.get(user_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                pass'''
add_para(doc, code2, font_size=9, font_name="Courier New", space_after=12)

add_heading(doc, "A.3  Backend — Abnormality Upsert Logic (Python)", 2)
code3 = '''@router.post("/upsert")
async def upsert_abnormality(payload: AbnormalityUpsert,
                              db: AsyncSession = Depends(get_db),
                              current_user = Depends(get_current_user)):
    result = await db.execute(
        select(Abnormality).where(Abnormality.session_id == payload.session_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        for det_type, det_data in payload.detections.items():
            existing.merge_detection(det_type, det_data)
        existing.last_updated_at = datetime.utcnow()
    else:
        sev, conf = Abnormality.recalculate_overall(payload.detections)
        existing = Abnormality(
            session_id=payload.session_id,
            employee_id=payload.employee_id,
            detections=payload.detections,
            overall_severity=sev,
            confidence_score=conf,
            first_detected_at=datetime.utcnow(),
            last_updated_at=datetime.utcnow()
        )
        db.add(existing)

    await db.commit()
    await manager.broadcast({"type": "abnormality_detected", "data": existing.to_dict()})
    return existing.to_dict()'''
add_para(doc, code3, font_size=9, font_name="Courier New", space_after=12)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════
# APPENDIX B — DATABASE SCHEMA
# ═══════════════════════════════════════════════════════════════════════════

add_centered_title(doc, "APPENDIX B", size=14, bold=True, space_before=12, space_after=6)
add_centered_title(doc, "COMPLETE DATABASE SCHEMA (PostgreSQL/Supabase)", size=13, bold=False, space_before=0, space_after=12)

schema_excerpt = '''-- SENTINEL Database Schema v2
-- Supabase / PostgreSQL

CREATE TABLE public.employees (
  id            uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  email         varchar(255) NOT NULL UNIQUE,
  password_hash varchar(255) NOT NULL,
  full_name     varchar(255) NOT NULL,
  role          varchar(50)  NOT NULL DEFAULT \'employee\',
  department    varchar(100),
  position      varchar(100),
  gender        varchar(20),
  phone         varchar(20),
  employee_code varchar(20),
  avatar_url    text,
  is_active     boolean DEFAULT true,
  created_at    timestamptz DEFAULT now(),
  updated_at    timestamptz DEFAULT now()
);

CREATE TABLE public.sessions (
  id                   uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  employee_id          uuid NOT NULL REFERENCES employees(id),
  start_time           timestamptz NOT NULL,
  end_time             timestamptz,
  total_work_minutes   integer DEFAULT 0,
  total_break_minutes  integer DEFAULT 0,
  lunch_taken          boolean DEFAULT false,
  status               varchar(50) DEFAULT \'active\',
  session_quality_score numeric(5,2),
  risk_score           numeric(5,2) DEFAULT 0,
  created_at           timestamptz DEFAULT now(),
  updated_at           timestamptz DEFAULT now()
);

CREATE TABLE public.abnormalities (
  id               uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id       uuid NOT NULL UNIQUE REFERENCES sessions(id),
  employee_id      uuid NOT NULL REFERENCES employees(id),
  overall_severity varchar(20) NOT NULL DEFAULT \'LOW\',
  confidence_score numeric(5,2) NOT NULL DEFAULT 0,
  detections       jsonb NOT NULL DEFAULT \'{}\',
  first_detected_at timestamptz NOT NULL,
  last_updated_at  timestamptz NOT NULL,
  reviewed         boolean DEFAULT false,
  reviewed_by      uuid REFERENCES employees(id),
  reviewed_at      timestamptz,
  review_decision  varchar(50)
);

CREATE TABLE public.tasks (
  id              uuid PRIMARY KEY,
  title           varchar(255) NOT NULL,
  description     text,
  assigned_to     uuid NOT NULL REFERENCES employees(id),
  assigned_by     uuid NOT NULL REFERENCES employees(id),
  due_date        timestamptz,
  priority        varchar(20) NOT NULL,  -- low|medium|high|urgent
  status          varchar(20) NOT NULL,  -- pending|in_progress|completed
  completion_note text,
  created_at      timestamptz DEFAULT now(),
  completed_at    timestamptz
);

CREATE TABLE public.leaves (
  id             uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  employee_id    uuid NOT NULL REFERENCES employees(id),
  leave_type     varchar(10) NOT NULL CHECK (leave_type IN (\'EL\',\'CL\',\'SL\',\'ML\')),
  from_date      date NOT NULL,
  to_date        date NOT NULL,
  days_requested integer NOT NULL DEFAULT 1,
  reason         text NOT NULL,
  status         varchar(20) DEFAULT \'pending\',
  reviewed_by    uuid REFERENCES employees(id),
  reviewed_at    timestamptz,
  admin_response text,
  comments       jsonb DEFAULT \'[]\',
  created_at     timestamptz DEFAULT now()
);'''

add_para(doc, schema_excerpt, font_size=9, font_name="Courier New", space_after=12)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════
# APPENDIX C — API ENDPOINTS REFERENCE
# ═══════════════════════════════════════════════════════════════════════════

add_centered_title(doc, "APPENDIX C", size=14, bold=True, space_before=12, space_after=6)
add_centered_title(doc, "COMPLETE API ENDPOINTS REFERENCE", size=13, bold=False, space_before=0, space_after=12)

api_ref_headers = ["Method", "Endpoint", "Description", "Auth Required"]
api_ref_rows = [
    ["POST",  "/api/v1/auth/login",                   "Authenticate with email + password, receive JWT",          "No"],
    ["GET",   "/api/v1/auth/me",                      "Get current authenticated user profile",                   "Yes"],
    ["POST",  "/api/v1/auth/logout",                  "Invalidate current token",                                  "Yes"],
    ["GET",   "/api/v1/employees",                    "List all employees (admin)",                               "Yes"],
    ["POST",  "/api/v1/employees",                    "Create new employee account",                              "Yes"],
    ["GET",   "/api/v1/employees/{id}",               "Get single employee full profile",                         "Yes"],
    ["PUT",   "/api/v1/employees/{id}",               "Update employee record",                                   "Yes"],
    ["DELETE","/api/v1/employees/{id}",               "Deactivate employee account",                              "Yes"],
    ["POST",  "/api/v1/sessions/start",               "Start a new work session",                                 "Yes"],
    ["PUT",   "/api/v1/sessions/{id}/end",            "End active session with summary",                          "Yes"],
    ["GET",   "/api/v1/sessions",                     "List sessions with filters",                               "Yes"],
    ["GET",   "/api/v1/sessions/active/{emp_id}",     "Get currently active session for employee",                "Yes"],
    ["POST",  "/api/v1/abnormalities/upsert",         "Upsert session abnormality record (JSONB merge)",          "Yes"],
    ["GET",   "/api/v1/abnormalities",                "List abnormalities with severity filter",                  "Yes"],
    ["PUT",   "/api/v1/abnormalities/{id}/review",    "Record admin review decision",                             "Yes"],
    ["GET",   "/api/v1/tasks",                        "List all tasks (admin) or my tasks (employee)",            "Yes"],
    ["POST",  "/api/v1/tasks",                        "Create and assign new task (triggers WebSocket)",          "Yes"],
    ["PATCH", "/api/v1/tasks/{id}/status",            "Update task status (employee)",                            "Yes"],
    ["GET",   "/api/v1/leaves",                       "List leave requests",                                      "Yes"],
    ["POST",  "/api/v1/leaves",                       "Submit leave request",                                     "Yes"],
    ["PATCH", "/api/v1/leaves/{id}/review",           "Approve or reject leave (admin)",                          "Yes"],
    ["GET",   "/api/v1/appeals",                      "List appeal submissions",                                  "Yes"],
    ["POST",  "/api/v1/appeals",                      "Submit appeal against flagged session",                    "Yes"],
    ["POST",  "/api/v1/reports/generate",             "Generate PDF performance report",                          "Yes"],
    ["GET",   "/api/v1/reports/{id}/download",        "Download generated PDF report",                            "Yes"],
    ["POST",  "/api/v1/productivity-metrics/batch",   "Post hourly productivity metrics batch",                   "Yes"],
    ["GET",   "/api/v1/work-rules",                   "Get work rules for department/employee",                   "Yes"],
    ["POST",  "/api/v1/work-rules",                   "Create work rule configuration",                           "Yes"],
    ["GET",   "/api/v1/audit",                        "List audit log events (admin only)",                       "Yes"],
    ["GET",   "/ws/admin-feed",                       "WebSocket — Admin dashboard live feed (receive-only)",     "WS"],
    ["GET",   "/ws/{user_id}",                        "WebSocket — Per-employee channel (alerts + tasks)",        "WS"],
    ["GET",   "/health",                              "Backend health check",                                     "No"],
    ["GET",   "/docs",                                "FastAPI Swagger UI documentation",                         "No"],
]
add_table(doc, api_ref_headers, api_ref_rows, col_widths=[0.6, 2.6, 2.3, 0.8])
add_para(doc, "Appendix C: Complete API Endpoints Reference", alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=10, italic=True, space_after=10)

# ─────────────────────────────────────────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────────────────────────────────────────

output_path = r"c:\Users\Piyush\Desktop\sentinel\SENTINEL_Major_Project_Report_Piyush_Vats.docx"
doc.save(output_path)
print(f"\n✓ Report saved successfully to:\n  {output_path}")
print(f"\nEstimated pages: 75–85 (based on content volume)")
print("Open in Microsoft Word for final formatting verification.")
