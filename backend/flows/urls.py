from rest_framework.routers import DefaultRouter

from .views import DiagramViewSet, EdgeViewSet, NodeViewSet

router = DefaultRouter()
router.register('diagrams', DiagramViewSet, basename='diagram')
router.register('nodes', NodeViewSet, basename='node')
router.register('edges', EdgeViewSet, basename='edge')

urlpatterns = router.urls