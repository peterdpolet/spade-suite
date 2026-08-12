from rest_framework.routers import DefaultRouter
from .views import LabelViewSet

router = DefaultRouter()
router.register('labels', LabelViewSet, basename='label')

urlpatterns = router.urls
