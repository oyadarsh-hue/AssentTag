import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
pdf_path = os.path.join(downloads_dir, "AssentTag_Malayalam_Presentation_Reference.pdf")

doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
styles = getSampleStyleSheet()
title_style = styles["Title"]
h1_style = styles["Heading1"]
normal_style = styles["Normal"]

explanation_style = ParagraphStyle(
    "ExplStyle", parent=styles["Normal"], fontSize=11, leading=15, textColor=colors.black, spaceBefore=5, spaceAfter=15
)

Story = []
Story.append(Paragraph("AssentTag - Malayalam Panel Presentation Guide", title_style))
Story.append(Paragraph("This reference guide translates the core concepts of the AssentTag presentation into easy-to-explain Malayalam suitable for addressing the project panel, bypassing complex PDF Unicode rendering issues by providing clear speech guidelines.", normal_style))
Story.append(Spacer(1, 20))

sections = [
    ("1. Introduction (Aamukham)",
     "Project Overview: 'AssentTag oru secure aaya social platform aanu. Nammude anuvaadam illathe nammude photo mattullavar upload cheyyunnathu thadayan aanu ithu main aayi upayogikkunnath. Deep Learning (ResNet-128D) vazhiyanu ithil face detect cheyyunnath.'"),
     
    ("2. Existing Systems (Nila-vilulla Systems)",
     "'Nilavilulla Facebook/Instagram pole ulla platforms-il nammude permission illathe aarkkum nammude face ulla group photos post cheyyam. Athu privacy-kku oru valiya issue aanu. Engane varunna fake accounts thadayan avarkku pattunnilla.'"),

    ("3. Proposed System & Security",
     "'Ee project-il, nammal Biometric Registration aanu use cheyyunnath. Account undakkumbol ulla photo-um live webcam-um match aayaal mathrame account create aavu (d <= 0.60). Pinne, aarenkilum photo upload cheyyumbol avarude face aa photo-il undo ennu check cheyyum; illenkil upload aavilla. Ithu vazhi fake accounts-um unauthorized uploads-um block aavum.'"),

    ("4. Privacy & Dynamic Blurring",
     "'Oru photo upload cheythu kazhinjal, athil ulla uploader ozhike mattu ella faces-um automatically blur aayirikkum. Aarkkokke aano tag vannirikunnath, avar notification vazhi Approve cheythaal mathrame avarude face clear aayi kaanikkukayullu. Ee blurring server-te RAM-il aanu nadakkunnath, athukond storage kalayunnilla.'"),

    ("5. Logic & Exceptions",
     "'Approve cheyyanum nammal live face verification nadathum. Hacker password kandupidichal polum nammude mukham illathe blur maattan pattilla. Duplicate account check cheyyunath database scan cheythittalla, static folder-il photos directly compare cheythittaanu (d <= 0.42). Ithu speed kootum.'"),

    ("6. Conclusion (Upasamharam)",
     "'Churukkathil paranjal, AssentTag nammude digital privacy thirichu tharunnu. Fake accounts thadayari, anavashya photo uploads block cheythu, RAM-based dynamic blurring vazhi nammude security urappu varuthunnu.'")
]

for heading, text in sections:
    Story.append(Paragraph(heading, h1_style))
    Story.append(Paragraph(text, explanation_style))
    Story.append(Spacer(1, 10))

try:
    doc.build(Story)
    print(f"Malayalam Reference PDF built successfully at {pdf_path}")
except Exception as e:
    print(f"Error generating PDF: {str(e)}")
