# OTP inbox delivery and activation

## Implemented behavior

1. A financial-keyword message stays pending until its sender verifies their registered email.
2. Django generates a random six-digit code and sends it through authenticated Gmail SMTP (TLS).
3. Only successful SMTP acceptance creates an active challenge. Its five-minute expiry starts after acceptance, so SMTP latency does not consume the user's validity period.
4. The session stores a keyed digest, never the plaintext code. Verification binds the code to the sender, email, recipient, message, and disappearing-message setting.
5. Resend is available after 60 seconds and replaces the previous code. Expired, reused, changed-message and five-times-incorrect codes are rejected by the server.
6. Missing configuration does not consume the resend quota. Actual send attempts are limited to five per session per hour.
7. A successful check rechecks the follow relationship and sends the pending message. Delivery failure never bypasses verification.

## Remaining activation step

The connected Codex Gmail plugin is not the running Django server's SMTP authorization. Its credentials cannot be exported into this project.

Enable Google 2-Step Verification and create an App Password for the sender account. Complete Google's account-authentication steps yourself. Enter the App Password only into the local hidden prompt:

```powershell
python setup_email.py --email adarsh22saji@gmail.com --test
```

This stores local configuration in `.env` and sends a delivery test. Restart each running Django server afterwards. Configure each local checkout privately; `.env` is intentionally excluded from both Git and project synchronization.

If this Google account cannot offer App Passwords, a separately configured Gmail OAuth application or a transactional email provider is needed. Both require their own account authorization/credentials; neither can be replaced with a fixed OTP or a simulated success response.

## Acceptance check

- Confirm receipt of the delivery test in the intended Gmail account. SMTP acceptance alone does not confirm inbox placement.
- Request an OTP from the application and confirm receipt, without logging or publishing its value.
- Verify that the intended pending message is sent only after the correct code.
- Confirm rejection after five minutes and after use; resend must accept only the replacement code.
- Inbox arrival time depends on the mail provider; five minutes is the server-enforced validity period, not a guaranteed delivery deadline.

Automated tests cover mail-backend failure, slow acceptance, expiry, resend, wrong attempts, message/email binding and sequential reuse. These tests do not claim live Gmail delivery or simultaneous-request race protection.

References: [Google App Passwords](https://support.google.com/accounts/answer/185833), [Django email](https://docs.djangoproject.com/en/4.2/topics/email/).
