from rest_framework.routers import DefaultRouter

from apps.accounts.views import AuthViewSet

router = DefaultRouter()
router.register("auth", AuthViewSet, basename="auth")

urlpatterns = router.urls
