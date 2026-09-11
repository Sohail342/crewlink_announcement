from django.db import transaction

from apps.announcements.models import Announcement, AnnouncementRecipient
from apps.locals.models import Member


def queue_announcement(announcement, classification=None):
    members = Member.objects.filter(
        local_id=announcement.local_id,
        status=Member.Status.ACTIVE,
    )
    if classification:
        members = members.filter(classification=classification)

    with transaction.atomic():
        recipients = [
            AnnouncementRecipient(announcement=announcement, member=member)
            for member in members
        ]
        AnnouncementRecipient.objects.bulk_create(recipients, ignore_conflicts=True)
        announcement.status = Announcement.Status.QUEUED
        announcement.save(update_fields=["status"])

    return announcement
