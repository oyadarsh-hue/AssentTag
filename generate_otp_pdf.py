import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Path for the PDF in Downloads
downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
pdf_path = os.path.join(downloads_dir, "OTP_Security_Logic.pdf")

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

code_style = ParagraphStyle(
    "CodeStyle",
    parent=styles["Normal"],
    fontName="Courier",
    fontSize=10,
    leading=14,
    textColor=colors.darkblue,
    leftIndent=20,
    spaceBefore=10,
    spaceAfter=10
)

story = []

story.append(Paragraph("AssentTag: 6-Digit OTP Security Protocol", title_style))
story.append(Spacer(1, 20))

story.append(Paragraph("Overview", h1_style))
story.append(Paragraph("The 6-digit number in the AssentTag project is a <b>One-Time Password (OTP)</b> or Security PIN used to authorize high-risk actions, specifically financial transfers attempted via the messaging system.", normal_style))
story.append(Spacer(1, 15))

story.append(Paragraph("1. Generation Mechanism", h1_style))
story.append(Paragraph("The OTP is generated dynamically using Python's random library. It produces a secure, non-predictable 6-digit integer between 100,000 and 999,999.", normal_style))
story.append(Paragraph("otp = str(random.randint(100000, 999999))", code_style))
story.append(Spacer(1, 15))

story.append(Paragraph("2. Storage and Persistence", h1_style))
story.append(Paragraph("To verify the user's input, the server must 'remember' the generated OTP. This is handled using Django Sessions:", normal_style))
story.append(Paragraph("request.session['financial_otp'] = otp", code_style))
story.append(Paragraph("This means the PIN is stored temporarily in the server's session memory (RAM or Database) and is linked specifically to the user's current login session.", normal_style))
story.append(Spacer(1, 15))

story.append(Paragraph("3. Delivery and Failsafes", h1_style))
story.append(Paragraph("• <b>Live Delivery:</b> If SMTP is configured, the PIN is sent to the user's registered email address.<br/>"
                       "• <b>Local Failsafe:</b> If the email server is offline, the system generates an HTML file in the <i>'emails/'</i> directory (parent folder of project) containing the PIN.<br/>"
                       "• <b>Console Log:</b> For developers, the PIN is printed to the server terminal: <i>print(f'[!] FAILSAFE OTP: {otp}')</i>", normal_style))
story.append(Spacer(1, 15))

story.append(Paragraph("4. Validation Logic", h1_style))
story.append(Paragraph("When the user enters the PIN on the verification screen, the server compares the submitted text with the value stored in the session:", normal_style))
story.append(Paragraph("if entered_otp == expected_otp:<br/>    # Authorize Action", code_style))

try:
    doc.build(story)
    print(f"OTP Security PDF built successfully at {pdf_path}")
except Exception as e:
    print(f"Error generating PDF: {str(e)}")
