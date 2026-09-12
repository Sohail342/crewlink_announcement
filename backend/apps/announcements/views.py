from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.permissions import (
    IsLeadership,
    IsLeadershipOrMember,
    IsMemberRole,
    LocalScopedQuerySetMixin,
)
from apps.announcements.models import Announcement, AnnouncementRecipient
from apps.announcements.serializers import (
    AnnouncementRecipientSerializer,
    AnnouncementSerializer,
    SendAnnouncementSerializer,
)
from apps.announcements.services import create_recipients
from apps.announcements.tasks import send_announcement
from apps.announcements.ai_draft import generate_announcement_draft, AINotConfigured


class AnnouncementViewSet(LocalScopedQuerySetMixin, viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    http_method_names = ["get", "post", "put", "patch", "head", "options"]
    local_filter_field = "local_id"
    lookup_value_regex = r"[0-9]+"

    def get_permissions(self):
        if self.action in (
            "create",
            "update",
            "partial_update",
            "send",
            "counts",
            "draft",
        ):
            return [IsLeadership()]
        return [IsLeadershipOrMember()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if getattr(user, "is_superuser", False):
            return queryset
        if getattr(user, "role", None) == User.Role.MEMBER:
            return queryset.filter(recipients__member__user=user).distinct()
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if not user.local_id:
            raise ValidationError({"local": "User is not assigned to a local."})
        serializer.save(
            local_id=user.local_id,
            created_by=user,
            status=Announcement.Status.DRAFT,
        )

    def update(self, request, *args, **kwargs):
        announcement = self.get_object()
        if announcement.status != Announcement.Status.DRAFT:
            return Response(
                {"detail": "Only draft announcements can be updated."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        announcement = self.get_object()
        if announcement.status not in (
            Announcement.Status.DRAFT,
            Announcement.Status.QUEUED,
        ):
            return Response(
                {"detail": "Only draft or queued announcements can be sent."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = SendAnnouncementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        announcement_id = announcement.id
        classification = serializer.validated_data.get("classification")

        with transaction.atomic():
            announcement.status = Announcement.Status.QUEUED
            announcement.save(update_fields=["status"])
            create_recipients(announcement, classification=classification)
            transaction.on_commit(lambda: send_announcement.delay(announcement_id))

        return Response(
            {"detail": "sending to members", "status": Announcement.Status.SENDING}
        )

    @action(detail=True, methods=["get"])
    def counts(self, request, pk=None):
        announcement = self.get_object()
        recipients = announcement.recipients.all()
        return Response(
            {
                "sent": recipients.filter(
                    delivery_status=AnnouncementRecipient.DeliveryStatus.SENT
                ).count(),
                "read": recipients.exclude(read_at__isnull=True).count(),
                "acknowledged": recipients.exclude(
                    acknowledged_at__isnull=True
                ).count(),
            }
        )

    @action(detail=False, methods=["post"])
    def draft(self, request):
        note = (request.data.get("note") or "").strip()
        if not note:
            return Response(
                {"detail": "Enter a leadership note before generating a draft."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            draft = generate_announcement_draft(note)
        except AINotConfigured:  # noqa
            return Response(
                {"detail": "AI not configured"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(draft)


class AnnouncementRecipientViewSet(
    LocalScopedQuerySetMixin, viewsets.ReadOnlyModelViewSet
):
    queryset = AnnouncementRecipient.objects.select_related("announcement", "member")
    serializer_class = AnnouncementRecipientSerializer
    local_filter_field = "announcement__local_id"

    def get_permissions(self):
        if self.action in ("read", "acknowledge"):
            return [IsMemberRole()]
        return [IsLeadershipOrMember()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if getattr(user, "is_superuser", False):
            return queryset
        if getattr(user, "role", None) == User.Role.MEMBER:
            return queryset.filter(member__user=user)
        return queryset

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        recipient = self.get_object()
        if recipient.read_at is None:
            recipient.read_at = timezone.now()
            recipient.save(update_fields=["read_at"])
        return Response(AnnouncementRecipientSerializer(recipient).data)

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        recipient = self.get_object()
        if not recipient.announcement.needs_ack:
            return Response(
                {"detail": "Acknowledgement is not required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if recipient.acknowledged_at is None:
            recipient.acknowledged_at = timezone.now()
            recipient.save(update_fields=["acknowledged_at"])
        return Response(AnnouncementRecipientSerializer(recipient).data)
