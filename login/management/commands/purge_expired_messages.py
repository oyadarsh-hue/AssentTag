from django.core.management.base import BaseCommand
from django.utils import timezone
from register.models import Message


class Command(BaseCommand):
    help = 'Permanently remove messages whose server expiry has passed.'

    def handle(self, *args, **options):
        count, _ = Message.objects.filter(expires_at__lte=timezone.now()).delete()
        self.stdout.write(f'Removed {count} expired messages.')
