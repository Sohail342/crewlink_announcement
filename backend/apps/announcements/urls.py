from rest_framework.routers import DefaultRouter

from apps.announcements.views import AnnouncementRecipientViewSet, AnnouncementViewSet

router = DefaultRouter()
router.register("announcements", AnnouncementViewSet, basename="announcement")
router.register("recipients", AnnouncementRecipientViewSet, basename="recipient")

urlpatterns = router.urls
