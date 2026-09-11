from rest_framework.routers import DefaultRouter

from apps.locals.views import LocalViewSet, MemberViewSet

router = DefaultRouter()
router.register("locals", LocalViewSet, basename="local")
router.register("members", MemberViewSet, basename="member")

urlpatterns = router.urls
