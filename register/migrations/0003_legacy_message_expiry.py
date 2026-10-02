from datetime import timedelta
from django.db import migrations
from django.utils import timezone


def assign_legacy_expiry(apps, schema_editor):
    # Previously timed messages had no deadline and were deleted on first view.
    # Give those still present a full day from upgrade; do not erase old chats
    # as a side effect of installing the feature.
    Message = apps.get_model('register', 'Message')
    Message.objects.using(schema_editor.connection.alias).filter(
        is_disappearing=True, expires_at__isnull=True).update(
            disappearing_seconds=86400, expires_at=timezone.now() + timedelta(days=1))


class Migration(migrations.Migration):
    dependencies = [('register', '0002_message_disappearing_seconds_message_expires_at')]
    operations = [migrations.RunPython(assign_legacy_expiry, migrations.RunPython.noop)]
