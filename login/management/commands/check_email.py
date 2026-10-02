from django.conf import settings
from django.core.mail import send_mail, get_connection
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = 'Check SMTP configuration; optionally send a delivery test to an explicit address.'

    def add_arguments(self, parser):
        parser.add_argument('--send-to', help='Send a test email to this address.')
        parser.add_argument('--connect', action='store_true', help='Check network, TLS and SMTP authentication without sending mail.')

    def handle(self, *args, **options):
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            raise CommandError('Gmail credentials are missing. Run python setup_email.py locally.')
        if not settings.EMAIL_BACKEND.endswith('smtp.EmailBackend'):
            raise CommandError('An SMTP email backend is required to verify real delivery.')
        self.stdout.write('SMTP credentials are configured. No passwords are displayed.')
        if options['connect']:
            try:
                with get_connection() as connection:
                    connection.open()
            except Exception as exc:
                raise CommandError(self.delivery_error(exc)) from None
            self.stdout.write(self.style.SUCCESS('SMTP connection, TLS and authentication succeeded.'))
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
        except Exception as exc:
            raise CommandError(self.delivery_error(exc)) from None
        if count != 1:
            raise CommandError('The SMTP backend did not accept the message.')
        self.stdout.write(self.style.SUCCESS('SMTP accepted the test message. Check the recipient inbox and spam folder.'))

    @staticmethod
    def delivery_error(exc):
        # Exception text can contain SMTP payloads: expose only safe diagnostics.
        if getattr(exc,'errno',None) in (13,10013):
            return 'SMTP network access is blocked for this process. Run the server in a normal local terminal with outbound Gmail SMTP access.'
        if getattr(exc,'smtp_code',None) == 535:
            return 'Gmail rejected SMTP authentication. Update the Gmail App Password using setup_email.py.'
        return ('SMTP delivery failed: '+type(exc).__name__+
                '. Check network access and run check_email --connect in the server environment.')
