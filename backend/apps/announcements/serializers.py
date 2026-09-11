from rest_framework import serializers

from apps.announcements.models import Announcement, AnnouncementRecipient


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = (
            "id",
            "local",
            "created_by",
            "title",
            "body",
            "push_preview",
            "needs_ack",
            "status",
            "sent_at",
            "created_at",
        )
        read_only_fields = (
            "id",
            "local",
            "created_by",
            "status",
            "sent_at",
            "created_at",
        )


class SendAnnouncementSerializer(serializers.Serializer):
    classification = serializers.CharField(required=False, allow_blank=False)


class AnnouncementRecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnouncementRecipient
        fields = (
            "id",
            "announcement",
            "member",
            "delivery_status",
            "sent_at",
            "read_at",
            "acknowledged_at",
        )
        read_only_fields = (
            "id",
            "announcement",
            "member",
            "delivery_status",
            "sent_at",
            "read_at",
            "acknowledged_at",
        )
