from django.db import transaction
from django.utils import timezone

from apps.announcements.models import Announcement, AnnouncementRecipient
from apps.announcements.push import PushService
from apps.locals.models import Member


def create_recipients(announcement, classification=None):
    members = Member.objects.filter(
        local_id=announcement.local_id,
        status=Member.Status.ACTIVE,
    )
    if classification:
        members = members.filter(classification=classification)

    recipients = [
        AnnouncementRecipient(announcement=announcement, member=member)
        for member in members
    ]
    AnnouncementRecipient.objects.bulk_create(recipients, ignore_conflicts=True)
    return announcement


def deliver_pending_recipients(announcement):
    push_service = PushService()
    pending_ids = list(
        AnnouncementRecipient.objects.filter(
            announcement=announcement,
            delivery_status=AnnouncementRecipient.DeliveryStatus.PENDING,
        ).values_list("id", flat=True)
    )

    for recipient_id in pending_ids:
        with transaction.atomic():
            try:
                recipient = AnnouncementRecipient.objects.select_for_update().get(
                    pk=recipient_id,
                    delivery_status=AnnouncementRecipient.DeliveryStatus.PENDING,
                )
            except AnnouncementRecipient.DoesNotExist:
                continue

            sent = push_service.send(
                recipient.member_id,
                announcement.title,
                announcement.push_preview,
            )
            if sent:
                recipient.delivery_status = AnnouncementRecipient.DeliveryStatus.SENT
                recipient.sent_at = timezone.now()
                recipient.save(update_fields=["delivery_status", "sent_at"])

    announcement.status = Announcement.Status.SENT
    announcement.sent_at = timezone.now()
    announcement.save(update_fields=["status", "sent_at"])
    return announcement


def process_announcement_send(announcement):
    announcement.status = Announcement.Status.SENDING
    announcement.save(update_fields=["status"])
    return deliver_pending_recipients(announcement)
