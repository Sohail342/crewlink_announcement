from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.announcements.views import AnnouncementRecipientViewSet, AnnouncementViewSet

router = DefaultRouter()
router.register("announcements", AnnouncementViewSet, basename="announcement")
router.register("recipients", AnnouncementRecipientViewSet, basename="recipient")

urlpatterns = [
    path(
        "announcements/ai-draft/",
        AnnouncementViewSet.as_view({"post": "draft"}),
        name="announcement-ai-draft",
    ),
] + router.urls
