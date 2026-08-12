from rest_framework.routers import DefaultRouter
from .views import ActivityViewSet, ActivityDependencyViewSet, ActivityIssueViewSet, ScheduleBaselineViewSet, DecisionNodeViewSet

router = DefaultRouter()
router.register('activities', ActivityViewSet, basename='activity')
router.register('activity-dependencies', ActivityDependencyViewSet, basename='activity-dependency')
router.register('activity-issues', ActivityIssueViewSet, basename='activity-issue')
router.register('baselines', ScheduleBaselineViewSet, basename='baseline')
router.register('decision-nodes', DecisionNodeViewSet, basename='decision-node')

urlpatterns = router.urls