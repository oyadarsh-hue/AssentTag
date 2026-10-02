# AssentTag email verification

The financial-message verification flow sends a random six-digit code to the logged-in user's registered email when SMTP is configured. Codes expire after five minutes, can be used once, allow five attempts, and are tied to the exact sender, recipient, and pending message. A live countdown disables verification when the code expires. The resend button displays its remaining 60-second cooldown and becomes available automatically; resending invalidates the old code. Requests have a limit of five per session per hour. Failed delivery never authorizes a message or claims a code was sent. The server enforces expiry and cooldown even without JavaScript.

## Complete the local Gmail setup

For a masked desktop setup form, run `python setup_email.py --gui`. The form explains the one-time credential step, saves it locally, and automatically sends a test. OTPs themselves are then generated and emailed by the running application on demand.

1. Enable [Google 2-Step Verification](https://support.google.com/accounts/answer/185833?hl=en).
2. Create an App Password at [Google Account App Passwords](https://myaccount.google.com/apppasswords). Some managed accounts do not offer this option; consult your administrator in that case.
3. Run `python setup_email.py --email adarsh22saji@gmail.com --test` in this project. Enter the App Password privately at the terminal prompt. This fills in the sender address and automatically sends a delivery test after saving. Do not use your normal Google password and do not paste the App Password into chat. Use `python setup_email.py` if you prefer to choose another sender and test separately.
4. Restart the Django server so it reloads `.env`.
5. Run `python manage.py check_email --send-to adarsh22saji@gmail.com` and check Inbox and Spam. SMTP acceptance alone is not proof of inbox receipt.
6. Log in as a registered user, open a chat with a mutual follower, and send a message containing a financial keyword. Enter the code delivered to that user's registered email. A successful check sends the pending message once. The page also supports resend and cancel.

The Gmail connector used in Codex does not provide SMTP credentials to the running Django application. The application sends through Django's configured SMTP backend. OS environment variables take precedence over `.env`; `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and `DEFAULT_FROM_EMAIL` must match the intended sender.

The old fixed `123456` token, code logging, and disk email fallback have been removed. Registration's existing biometric enrollment and login behavior remain unchanged; this OTP verifies a financial-keyword message, not an actual money transfer.

Implementation reference: [Django email configuration](https://docs.djangoproject.com/en/4.2/topics/email/).
