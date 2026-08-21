import os
import time
import re

# Path to the emails directory
email_dir = r"d:\AssentTag\emails"

def get_latest_otp():
    if not os.path.exists(email_dir):
        return "Emails directory not found."
    
    files = [os.path.join(email_dir, f) for f in os.listdir(email_dir) if f.endswith('.html')]
    if not files:
        return "No OTP files found."
    
    # Get the latest file by modification time
    latest_file = max(files, key=os.path.getmtime)
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        content = f.read()
        # Find 6 digit number inside h1 tag
        match = re.search(r'>(\d{6})</h1>', content)
        if match:
            return match.group(1)
    return "OTP not found in file."

print("=== AssentTag OTP Watcher ===")
print(f"Monitoring folder: {email_dir}")
print("Waiting for new security codes...")

last_otp = None
try:
    while True:
        current_otp = get_latest_otp()
        if current_otp != last_otp:
            print(f"\n[!] NEW SECURITY PIN DETECTED: {current_otp}")
            print(f"Timestamp: {time.strftime('%H:%M:%S')}")
            last_otp = current_otp
        time.sleep(1)
except KeyboardInterrupt:
    print("\nWatcher stopped.")
