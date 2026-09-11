from django.contrib import admin

from apps.announcements.models import Announcement, AnnouncementRecipient


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "local", "status", "needs_ack", "created_at")
    list_filter = ("status", "needs_ack", "local")
    search_fields = ("title",)


@admin.register(AnnouncementRecipient)
class AnnouncementRecipientAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "announcement",
        "member",
        "delivery_status",
        "read_at",
        "acknowledged_at",
    )
    list_filter = ("delivery_status",)
