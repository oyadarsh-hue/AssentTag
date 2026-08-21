import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Define the user's Downloads directory path based on Windows standard
downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
pdf_path = os.path.join(downloads_dir, "AssentTag_Logic_And_Exceptions.pdf")

doc = SimpleDocTemplate(
    pdf_path,
    pagesize=letter,
    rightMargin=40,
    leftMargin=40,
    topMargin=40,
    bottomMargin=40
)

styles = getSampleStyleSheet()
title_style = styles["Title"]
h1_style = styles["Heading1"]
h2_style = styles["Heading2"]
normal_style = styles["Normal"]

explanation_style = ParagraphStyle(
    "ExplStyle",
    parent=styles["Normal"],
    fontSize=10,
    leading=14,
    textColor=colors.black,
    spaceBefore=5,
    spaceAfter=15,
    bulletIndent=15,
    leftIndent=25
)

Story = []
Story.append(Paragraph("AssentTag - Registration, Upload & Consent Logic", title_style))
Story.append(Paragraph("This document outlines the core logic and exception handling for Biometric Registration, Photo Upload Gating, and the dynamic Consent (Approve/Reject) mechanism.", normal_style))
Story.append(Spacer(1, 20))

# SECTION 1: REGISTRATION BIOMETRICS
Story.append(Paragraph("1. Registration & Biometrics Logic", h1_style))
Story.append(Paragraph("The Registration module enforces strict 128-D Euclidean Distance verification prior to account creation to block fake and duplicate profiles.", normal_style))
Story.append(Spacer(1, 10))
Story.append(Paragraph("<b>Primary Process Loop:</b>", h2_style))
Story.append(Paragraph("• <b>Step 1:</b> User uploads a Profile Photo and captures a Live Webcam image.<br/>"
                       "• <b>Step 2:</b> ResNet AI computes the 128D descriptor distance ($d$) between both images.<br/>"
                       "• <b>Step 3:</b> The system then scans the `Static/Media/` directory directly, bypassing heavy database SQL queries.<br/>"
                       "• <b>Step 4:</b> The Live face is checked against all existing physical profile photos.", explanation_style))

Story.append(Paragraph("<b>Exception Handling & Restrictions:</b>", h2_style))
Story.append(Paragraph("• <b>Exception 1 ('No Face'):</b> If the Dlib engine fails to detect a face in either image, the registration is aborted immediately.<br/>"
                       "• <b>Exception 2 ('Mismatch'):</b> If the distance between the profile photo and the live webcam exceeds $d \leq 0.60$, the account is blocked (Spoof attempt).<br/>"
                       "• <b>Exception 3 ('Duplicate Account'):</b> If the live face matches an already existing photo in the Static folder ($d \leq 0.42$), the user is completely blocked from creating a second account.", explanation_style))
Story.append(Spacer(1, 20))

# SECTION 2: PHOTO UPLOAD
Story.append(Paragraph("2. Photo Upload & Identity Gating", h1_style))
Story.append(Paragraph("The Upload gate ensures that only physically verified individuals present inside the requested photograph can post it to the timeline.", normal_style))
Story.append(Spacer(1, 10))
Story.append(Paragraph("<b>Primary Process Loop:</b>", h2_style))
Story.append(Paragraph("• <b>Step 1:</b> The uploading user submits a group photo and takes a mandatory Live Webcam shot.<br/>"
                       "• <b>Step 2:</b> The AI maps all coordinates (X, Y, W, H) for every face detected in the group photo and embeds this JSON inside EXIF.<br/>"
                       "• <b>Step 3:</b> It checks if the Live Webcam descriptor matches *any* of the faces detected in the group photo.", explanation_style))

Story.append(Paragraph("<b>Exception Handling & Restrictions:</b>", h2_style))
Story.append(Paragraph("• <b>Exception 1 ('Absence Violation'):</b> If the uploader's live face is NOT found inside the boundary geometries of the uploaded photo ($d > 0.60$), the upload is instantly deleted to prevent non-consensual sharing of third-party photos.<br/>"
                       "• <b>Exception 2 ('Corrupted EXIF'):</b> If JSON generation for coordinates crashes, the upload fails safely without writing garbage to memory.", explanation_style))
Story.append(Spacer(1, 20))

# SECTION 3: CONSENT APPROVAL
Story.append(Paragraph("3. Consent Approval (Approve/Reject) Logic", h1_style))
Story.append(Paragraph("Approving a privacy notification requires severe live validation to prevent hijacked accounts from unblurring photos maliciously.", normal_style))
Story.append(Spacer(1, 10))
Story.append(Paragraph("<b>Primary Process Loop:</b>", h2_style))
Story.append(Paragraph("• <b>Step 1:</b> User clicks the notification leading to a live verification capture screen.<br/>"
                       "• <b>Step 2:</b> Live webcam snapshot is compared directly against the user’s original first-time Registration Photo from the static folder ($d \leq 0.60$).<br/>"
                       "• <b>Step 3:</b> A temporary, randomly hashed Session Key is injected to authorize the status change.<br/>"
                       "• <b>Step 4:</b> Target state shifts to 'approved', dropping their face coordinates from the Gaussian Blurring algorithm on the next real-time page render.", explanation_style))

Story.append(Paragraph("<b>Exception Handling & Restrictions:</b>", h2_style))
Story.append(Paragraph("• <b>Exception 1 ('Missing Session Key'):</b> If an attacker attempts to click 'Approve' via URL bypassing the webcam script, the missing temporal Session Key triggers an automatic HTTP 403 block.<br/>"
                       "• <b>Exception 2 ('Tag Mismatch'):</b> If the `tag_id` in the API payload does not strictly belong to the connected `User_ID`, the request is rejected.<br/>"
                       "• <b>Exception 3 ('Verification Failure'):</b> If the live face does not match the registration photo ($d > 0.60$), the approval process is locked.", explanation_style))


try:
    doc.build(Story)
    print(f"Logic PDF built successfully at {pdf_path}")
except Exception as e:
    print(f"Error generating PDF: {str(e)}")
