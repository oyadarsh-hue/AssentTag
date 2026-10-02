"""Local development server with expiry cleanup even when all chats are closed."""
import logging
import threading

from django.contrib.staticfiles.management.commands.runserver import Command as RunServer
from django.db import close_old_connections
from django.utils import timezone
from register.models import Message


class Command(RunServer):
    help = 'Run the local development website with a 30-second expiry cleanup worker.'

    def inner_run(self, *args, **options):
        stop = threading.Event()

        def cleanup():
            while not stop.is_set():
                try:
                    close_old_connections()
                    Message.objects.filter(expires_at__lte=timezone.now()).delete()
                except Exception as exc:
                    logging.getLogger(__name__).warning('Message cleanup failed: %s', type(exc).__name__)
                finally:
                    close_old_connections()
                stop.wait(30)

        worker = threading.Thread(target=cleanup, name='chat-expiry-cleanup', daemon=True)
        worker.start()
        try:
            return super().inner_run(*args, **options)
        finally:
            stop.set()
            worker.join(timeout=2)
