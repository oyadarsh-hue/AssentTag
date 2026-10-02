"""One-time email challenges bound to the exact pending message."""
import hashlib
import logging
import secrets
import time

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.html import escape

logger = logging.getLogger(__name__)
TTL = 300
MAX_ATTEMPTS = 5
RESEND_SECONDS = 60
CHALLENGE_KEY = 'financial_email_challenge'
PENDING_KEYS = ('pending_financial_msg', 'pending_financial_receiver', 'pending_is_disappearing')


def binding(session, user):
    payload = '|'.join((str(user.register_id), user.email.strip().lower(),
                        str(session.get('pending_financial_receiver', '')),
                        str(session.get('pending_financial_msg', '')),
                        str(session.get('pending_is_disappearing', False))))
    return hashlib.sha256(payload.encode()).hexdigest()


def clear_pending(session):
    for key in (*PENDING_KEYS, CHALLENGE_KEY, 'financial_otp'):
        session.pop(key, None)


def challenge_state(session, user):
    """Public countdown state; the server remains the authority on expiry."""
    now = int(time.time())
    challenge = session.get(CHALLENGE_KEY)
    expired = bool(challenge and challenge['expires'] <= now)
    if challenge and (expired or challenge['binding'] != binding(session, user)):
        session.pop(CHALLENGE_KEY, None)
        challenge = None
    remaining = max(0, challenge['expires'] - now) if challenge else 0
    last_sent = session.get('financial_email_rate', {}).get('last', 0)
    return {
        'code_sent': bool(challenge),
        'otp_remaining_seconds': remaining,
        'resend_remaining_seconds': max(0, RESEND_SECONDS - (now - last_sent)),
        'code_expired': expired,
    }


def issue_challenge(session, user):
    if settings.EMAIL_BACKEND.endswith('smtp.EmailBackend') and (
        not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD
        or settings.EMAIL_HOST_USER.startswith('YOUR_')
        or settings.EMAIL_HOST_PASSWORD.startswith('YOUR_')
    ):
        session.pop(CHALLENGE_KEY, None)
        return False, 'Email delivery is not configured. Please ask the administrator to complete Gmail setup.'
    now = int(time.time())
    rate = session.get('financial_email_rate', {})
    if now - rate.get('last', 0) < RESEND_SECONDS:
        wait = RESEND_SECONDS - (now - rate['last'])
        return False, f'Please wait {wait} seconds before requesting another code.'
    if now - rate.get('start', 0) >= 3600:
        rate = {'start': now, 'count': 0}
    if rate.get('count', 0) >= 5:
        return False, 'Too many email requests. Please try again in one hour.'
    rate.update(last=now, count=rate.get('count', 0) + 1)
    session['financial_email_rate'] = rate
    # Invalidate the previous token before attempting delivery of its replacement.
    session.pop(CHALLENGE_KEY, None)
    code = f'{secrets.randbelow(1000000):06d}'
    subject = 'AssentTag verification code'
    text = (f'Hello {user.first_name},\n\nYour AssentTag verification code is {code}. '
            'It expires in 5 minutes and authorizes only your pending message. '
            'Never share this code. If you did not request it, ignore this email.')
    html = (f'<div style="font-family:Arial;background:#111a30;color:#f4f5ff;padding:32px;border-radius:20px">'
            f'<h2 style="color:#aeb2ff">AssentTag · Verify your identity</h2>'
            f'<p>Hello {escape(user.first_name)},</p><p>Your one-time verification code:</p>'
            f'<p style="font-size:36px;letter-spacing:8px;color:#8deaf0">{code}</p>'
            '<p>Valid for 5 minutes, for your pending message only.</p>'
            '<p>Never share this code. If you did not request it, ignore this email.</p></div>')
    try:
        message = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, [user.email])
        message.attach_alternative(html, 'text/html')
        if message.send(fail_silently=False) != 1:
            raise RuntimeError('Email backend did not accept the message')
    except Exception as exc:
        # Do not expose SMTP credentials, codes, or message contents in logs.
        logger.warning('AssentTag verification email delivery failed: type=%s smtp_code=%s errno=%s',
                       type(exc).__name__, getattr(exc,'smtp_code',None), getattr(exc,'errno',None))
        return False, 'We could not send your verification email. Please retry or contact the administrator.'
    nonce = secrets.token_hex(16)
    # SMTP can take time: give the user five full minutes after acceptance.
    accepted_at = int(time.time())
    rate['last'] = accepted_at
    session['financial_email_rate'] = rate
    session[CHALLENGE_KEY] = {
        'digest': salted_hmac('assenttag.email-otp', nonce + code).hexdigest(),
        'nonce': nonce, 'binding': binding(session, user),
        'expires': accepted_at + TTL, 'attempts': 0,
    }
    return True, 'A new code was sent to your registered email. It expires in 5 minutes.'


def verify_challenge(session, user, code):
    challenge = session.get(CHALLENGE_KEY)
    if not challenge:
        return False, 'Request a new code before verifying.'
    if challenge['binding'] != binding(session, user):
        session.pop(CHALLENGE_KEY, None)
        return False, 'Your pending message changed. Request a new code.'
    if int(time.time()) >= challenge['expires']:
        session.pop(CHALLENGE_KEY, None)
        return False, 'This code expired. Request a new code.'
    challenge['attempts'] += 1
    session[CHALLENGE_KEY] = challenge
    candidate = salted_hmac('assenttag.email-otp', challenge['nonce'] + code).hexdigest()
    if len(code) == 6 and code.isascii() and code.isdigit() and constant_time_compare(candidate, challenge['digest']):
        session.pop(CHALLENGE_KEY, None)
        return True, ''
    if challenge['attempts'] >= MAX_ATTEMPTS:
        session.pop(CHALLENGE_KEY, None)
        return False, 'Too many incorrect attempts. Request a new code.'
    return False, f'Incorrect code. {MAX_ATTEMPTS - challenge["attempts"]} attempts remaining.'
