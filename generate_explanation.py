from fpdf import FPDF
import os

class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 16)
        self.cell(0, 10, 'AssentTag: Technical Explanation of EXIF & Dynamic Blurring', 0, 1, 'C')
        self.ln(10)

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Helvetica', '', 11)
        self.multi_cell(0, 8, body)
        self.ln()

    def code_block(self, code):
        self.set_font('Courier', '', 9)
        self.set_fill_color(240, 240, 240)
        self.multi_cell(0, 5, code, fill=True)
        self.ln()

pdf = PDF()
pdf.add_page()

# Section 1: Overview
pdf.chapter_title('1. Why EXIF and piexif are used')
explanation1 = (
    "In the AssentTag framework, 'EXIF' (Exchangeable Image File Format) is used as a metadata storage layer "
    "within the image file itself. The 'piexif' library is used to read and write this metadata without "
    "altering the visual pixels of the image.\n\n"
    "Key Advantages over a standard Database:\n"
    "- Speed: No need to run AI face detection every time an image is requested.\n"
    "- Portability: Privacy settings and coordinates stay physically attached to the image file.\n"
    "- Zero-Storage: Reduces database bloat by storing coordinate geometry in the files themselves."
)
pdf.chapter_body(explanation1)

# Section 2: Code Snippets
pdf.chapter_title('2. EXIF Implementation in views.py')

pdf.set_font('Helvetica', 'B', 11)
pdf.cell(0, 10, 'A. Metadata Injection (During Upload)', 0, 1)
upload_code = (
    "# Convert face locations to JSON and inject into UserComment\n"
    "json_payload = json.dumps(json_coords)\n"
    "exif_dict['Exif'][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(json_payload)\n"
    "exif_bytes = piexif.dump(exif_dict)\n"
    "piexif.insert(exif_bytes, filepath)"
)
pdf.code_block(upload_code)

pdf.set_font('Helvetica', 'B', 11)
pdf.cell(0, 10, 'B. Metadata Extraction (During Serving)', 0, 1)
serve_code = (
    "# Read hidden metadata to identify blur regions\n"
    "exif_dict = piexif.load(filepath)\n"
    "user_comment = exif_dict.get('Exif', {}).get(piexif.ExifIFD.UserComment)\n"
    "if user_comment:\n"
    "    json_string = piexif.helper.UserComment.load(user_comment)\n"
    "    json_coords = json.loads(json_string)"
)
pdf.code_block(serve_code)

# Section 3: Dynamic Blur Logic
pdf.chapter_title('3. Dynamic Gaussian Blur Logic')
explanation2 = (
    "The 'serve_dynamic_image' view applies blurs in real-time based on the viewer's identity:\n"
    "1. The system identifies the viewer using the session 'u_id'.\n"
    "2. It compares the viewer's ID against the 'authorized_ids' list (uploader and approved friends).\n"
    "3. For unauthorized faces, it uses OpenCV (cv2) to apply a deep pixelation followed by a heavy "
    "Gaussian Blur kernel (strength 99) and a circular mask."
)
pdf.chapter_body(explanation2)

# Section 4: Security Features
pdf.chapter_title('4. Steganographic Tracing')
explanation3 = (
    "To prevent screenshots, the system embeds a near-invisible watermark of the current viewer's ID into the "
    "pixels at 3% opacity. This enables 'Traitor Tracing' where leaked images can be traced back to the "
    "specific user who viewed them."
)
pdf.chapter_body(explanation3)

# Save the PDF
download_path = r'C:\Users\HP\Downloads\AssentTag_Exif_Explanation.pdf'
pdf.output(download_path)
print(f"Updated PDF successfully generated at: {download_path}")
