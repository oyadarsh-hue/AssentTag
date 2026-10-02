from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = 'Check SMTP configuration; optionally send a delivery test to an explicit address.'

    def add_arguments(self, parser):
        parser.add_argument('--send-to', help='Send a test email to this address.')

    def handle(self, *args, **options):
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            raise CommandError('Gmail credentials are missing. Run python setup_email.py locally.')
        if not settings.EMAIL_BACKEND.endswith('smtp.EmailBackend'):
            raise CommandError('An SMTP email backend is required to verify real delivery.')
        self.stdout.write('SMTP credentials are configured. No passwords are displayed.')
        recipient = options['send_to']
        if not recipient:
            self.stdout.write('Delivery not tested. Use --send-to with an explicit test address.')
            return
        try:
            validate_email(recipient)
        except ValidationError:
            raise CommandError('Enter a valid recipient email address.')
        try:
            count = send_mail('AssentTag email delivery test',
                              'AssentTag SMTP setup is working. This is a delivery test, not an OTP.',
                              settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)
        except Exception:
            raise CommandError('SMTP delivery failed. Check the Gmail App Password, 2-Step Verification, and network access.')
        if count != 1:
            raise CommandError('The SMTP backend did not accept the message.')
        self.stdout.write(self.style.SUCCESS('SMTP accepted the test message. Check the recipient inbox and spam folder.'))
