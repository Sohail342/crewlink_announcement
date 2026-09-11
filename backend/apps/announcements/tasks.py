from celery import shared_task

from apps.announcements.models import Announcement
from apps.announcements.services import process_announcement_send


@shared_task
def send_announcement(announcement_id):
    announcement = Announcement.objects.get(pk=announcement_id)
    process_announcement_send(announcement)
    return announcement.pk
