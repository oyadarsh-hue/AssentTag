from PIL import Image

try:
    img = Image.open('debug_frontend_img.jpg')
    img.verify()
    print("SUCCESS: Image is perfectly valid according to PIL.")
    print(f"Format: {img.format}, Size: {img.size}, Mode: {img.mode}")
except Exception as e:
    print(f"FAILED: Image is corrupted: {e}")
