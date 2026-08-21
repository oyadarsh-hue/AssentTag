import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Path for the PDF
pdf_name = "Project_Features_Code_Summary.pdf"
local_pdf_path = os.path.join(os.getcwd(), pdf_name)
downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
final_pdf_path = os.path.join(downloads_dir, pdf_name)

doc = SimpleDocTemplate(
    local_pdf_path,
    pagesize=letter,
    rightMargin=30,
    leftMargin=30,
    topMargin=30,
    bottomMargin=30
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
    fontSize=7,
    leading=9,
    textColor=colors.darkblue,
    leftIndent=15,
    spaceBefore=4,
    spaceAfter=4
)

story = []

# Title
story.append(Paragraph("AssentTag - Complete Feature Guide & Source Code", title_style))
story.append(Spacer(1, 12))

# 1. np.linalg
story.append(Paragraph("1. NumPy Linear Algebra (np.linalg)", h1_style))
story.append(Paragraph("np.linalg is the core mathematical engine for biometric verification. It calculates the 128D Euclidean distance between faces.", normal_style))
story.append(Spacer(1, 10))

# 2. OTP Security (6-Digit PIN)
story.append(Paragraph("2. Financial Override PIN (6-Digit OTP)", h1_style))
story.append(Paragraph("<b>Source File:</b> login/views.py", h2_style))
story.append(Paragraph("This logic monitors chat for keywords like 'transfer' or 'pay' and intercepts them with a PIN requirement.", normal_style))
story.append(Paragraph("def chat(request, user_id):<br/>    # ... keyword detection ...<br/>    if is_financial:<br/>        otp = '123456' # HARDCODED PIN FOR DEMO<br/>        request.session['financial_otp'] = otp<br/>        # ... sends failsafe email to d:/AssentTag/emails/ ...", code_style))
story.append(Spacer(1, 10))

# 3. Tap to Hold (Ghost Text)
story.append(Paragraph("3. Tap to Hold (Ghost Text Decryption)", h1_style))
story.append(Paragraph("<b>Source File (Template):</b> temp/templates/temp/dashboard.html", h2_style))
story.append(Paragraph("<b>Source File (Logic):</b> temp/views.py", h2_style))
story.append(Paragraph("Ghost text is only visible while the user holds their finger/mouse on the screen. This prevents unauthorized screenshots.", normal_style))
story.append(Paragraph("&lt;div class='ghost-text-container' <br/>     onmousedown='decryptGhostText(this, ...)' <br/>     onmouseup='encryptGhostText(this)' <br/>     ontouchstart='decryptGhostText(this, ...)'&gt;<br/>     &lt;h2&gt;SECURE DECRYPT: HOLD TO READ&lt;/h2&gt;<br/>&lt;/div&gt;", code_style))
story.append(Spacer(1, 10))

# 4. Complaint & Admin Reply
story.append(Paragraph("4. Complaint & Admin Reply System", h1_style))
story.append(Paragraph("<b>Source File:</b> complaint/views.py", h2_style))
story.append(Paragraph("def add_reply(request, idd):<br/>    if request.method == 'POST':<br/>        obj = Complaint.objects.get(complaint_id=idd)<br/>        obj.reply = request.POST.get('admin_reply')<br/>        obj.save()", code_style))
story.append(Spacer(1, 10))

# 5. Explore Feed
story.append(Paragraph("5. Explore Feed (User Discovery)", h1_style))
story.append(Paragraph("<b>Source File:</b> temp/views.py", h2_style))
story.append(Paragraph("def explore_feed(request):<br/>    # Exclude self and hibernated users<br/>    all_users = Register.objects.exclude(register_id=ss).exclude(status='hibernated')<br/>    return render(request, 'temp/explore_feed.html', {'all_users': all_users})", code_style))
story.append(Spacer(1, 10))

# 6. Messaging (Chat)
story.append(Paragraph("6. Messaging (Chat Protocol)", h1_style))
story.append(Paragraph("<b>Source File:</b> login/views.py", h2_style))
story.append(Paragraph("class Message(models.Model):<br/>    content = models.TextField()<br/>    is_disappearing = models.BooleanField(default=False)<br/>    receiver = models.ForeignKey('Register', models.DO_NOTHING)", code_style))
story.append(Spacer(1, 10))

# 7. Story Persistence (24 Hours)
story.append(Paragraph("7. Story Persistence (24 Hour Filter)", h1_style))
story.append(Paragraph("<b>Source File:</b> temp/views.py", h2_style))
story.append(Paragraph("if current_time - s_dt <= timedelta(hours=24):<br/>    if s.register_id not in stories_dict:<br/>        stories_dict[s.register_id] = s", code_style))
story.append(Spacer(1, 10))

# 8. Followers & Mutuals
story.append(Paragraph("8. Followers & Mutual Verification", h1_style))
story.append(Paragraph("<b>Source File:</b> register/models.py", h2_style))
story.append(Paragraph("class Follower(models.Model):<br/>    follower_user = models.ForeignKey('Register', ...)<br/>    user = models.ForeignKey('Register', ...)", code_style))

try:
    doc.build(story)
    import shutil
    shutil.copy2(local_pdf_path, final_pdf_path)
    print(f"Full Feature PDF with Ghost Text details updated at: {final_pdf_path}")
except Exception as e:
    print(f"Error: {e}")
