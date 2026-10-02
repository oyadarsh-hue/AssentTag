"""Server-authoritative chat timers. Viewing never starts or cancels expiry."""
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from login.models import ConversationTimer
from register.models import Message, Follower


TIMER_CHOICES = ((0, 'Off'), (60, '1 minute'), (86400, '24 hours'),
                 (604800, '7 days'), (7776000, '90 days'))


def can_chat(user_id, other_id):
    return (str(user_id) != str(other_id)
            and Follower.objects.filter(follower_user_id=user_id, user_id=other_id).exists()
            and Follower.objects.filter(follower_user_id=other_id, user_id=user_id).exists())


def timer_for(user_id, other_id):
    low, high = sorted((int(user_id), int(other_id)))
    return ConversationTimer.objects.get_or_create(user_low_id=low, user_high_id=high)[0]


def timer_payload(timer):
    return {'duration': timer.duration, 'label': dict(TIMER_CHOICES)[timer.duration],
            'revision': timer.revision, 'updated_at': timer.updated_at.isoformat(),
            'updated_by': timer.updated_by_id}


def expiry_fields(seconds, now=None):
    if seconds not in dict(TIMER_CHOICES):
        raise ValueError('Unsupported disappearing-message duration')
    return {'is_disappearing': bool(seconds), 'disappearing_seconds': seconds,
            'expires_at': (now or timezone.now()) + timedelta(seconds=seconds) if seconds else None}


def create_message(sender_id, receiver_id, content, seconds):
    return Message.objects.create(sender_id=sender_id, receiver_id=receiver_id,
                                  content=content, **expiry_fields(seconds))


def conversation_messages(user_id, other_id, now=None):
    now = now or timezone.now()
    messages = Message.objects.filter(
        Q(sender_id=user_id, receiver_id=other_id) | Q(sender_id=other_id, receiver_id=user_id))
    messages.filter(expires_at__lte=now).delete()
    return messages.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now)).order_by('timestamp', 'message_id')


@transaction.atomic
def update_timer(timer, duration, revision, actor_id):
    timer = ConversationTimer.objects.select_for_update().get(pk=timer.pk)
    if timer.revision != revision:
        return timer, False
    if timer.duration != duration:
        timer.duration = duration
        timer.revision += 1
        timer.updated_by_id = actor_id
        timer.save(update_fields=['duration', 'revision', 'updated_by', 'updated_at'])
    return timer, True
