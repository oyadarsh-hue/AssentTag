import getpass
import os

print("\n" + "="*60)
print("     ASSENTTAG HIGH-SECURITY SMTP CONFIGURATION UTILITY     ")
print("="*60 + "\n")
print("This setup will permanently activate the Live Internet Email Delivery.")
print("Otps will now arrive directly in your Inbox, completely bypassing Failsafe Mode.\n")

print("IMPORTANT: The password you are about to enter MUST be a 16-character")
print("App Password generated specifically from your Google Account Security Settings.")
print("Do NOT enter your regular Google login password.\n")

email_address = input("1. Enter your real Gmail Address: ").strip()

print("\n(Note: As you type the App Password, the letters will become invisible.")
print("This absolutely prevents the AI from seeing your true credentials.)")
app_password = getpass.getpass("2. Enter your 16-character App Password (invisibly): ").strip()

# Format validations
app_password = app_password.replace(" ", "")

if "@" not in email_address or not email_address.endswith("gmail.com"):
    print("\n[!] Error: The email must be a valid @gmail.com address!")
    exit(1)

if len(app_password) != 16:
    print(f"\n[!] Error: You entered {len(app_password)} characters. Google App Passwords must be exactly 16 letters long.")
    print("Example: abcd efgh ijkl mnop")
    exit(1)

# Write credentials silently to the environment file
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
with open(env_path, "w") as f:
    f.write(f"EMAIL_HOST_USER={email_address}\n")
    f.write(f"EMAIL_HOST_PASSWORD={app_password}\n")

print("\n" + "="*60)
print("[+] SUCCESS: Credentials safely archived to the root `.env` system.")
print("[+] Live Internet Mail Engine is now ACTIVE!")
print("="*60)
print("\nNext Steps:")
print("Go back to your running Django Server terminal and restart it")
print("(Ctrl+C, then `python manage.py runserver`).")
print("Test the application by triggering an OTP — it will now automatically arrive in your real Inbox!")
