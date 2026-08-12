from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Activity, ActivityDependency, ActivityIssue, ScheduleBaseline, BaselineActivitySchedule, DecisionNode
from .serializers import (
    ActivitySerializer, ActivityDependencySerializer, ActivityIssueSerializer,
    ScheduleBaselineSerializer, DecisionNodeSerializer,
)
from .scheduling import compute_schedule, CycleDetectedError


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        board_id = self.request.query_params.get('board')
        if board_id:
            queryset = queryset.filter(board_id=board_id)
        return queryset


class ActivityDependencyViewSet(viewsets.ModelViewSet):
    queryset = ActivityDependency.objects.all()
    serializer_class = ActivityDependencySerializer


class ActivityIssueViewSet(viewsets.ModelViewSet):
    queryset = ActivityIssue.objects.all()
    serializer_class = ActivityIssueSerializer


class ScheduleBaselineViewSet(viewsets.ReadOnlyModelViewSet):
    # Read-only — baselines are never edited directly, only ever
    # CREATED (as a side effect of a DecisionNode, see below).
    queryset = ScheduleBaseline.objects.prefetch_related('schedule__activity')
    serializer_class = ScheduleBaselineSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        board_id = self.request.query_params.get('board')
        if board_id:
            queryset = queryset.filter(board_id=board_id)
        return queryset


class DecisionNodeViewSet(viewsets.ModelViewSet):
    """
    Creating a DecisionNode is the ONLY way a new ScheduleBaseline gets
    created (design confirmed with Peter): validate the dependency
    graph is a DAG, run the forward/backward pass against CURRENT
    Activity durations, snapshot the result into a new
    BaselineActivitySchedule row per activity, deactivate the
    previously-active baseline for this board, activate the new one —
    all inside one atomic transaction, so a mid-way failure can't leave
    two baselines simultaneously active or a half-written snapshot.
    """
    queryset = DecisionNode.objects.select_related('resulting_baseline')
    serializer_class = DecisionNodeSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        board_id = self.request.query_params.get('board')
        if board_id:
            queryset = queryset.filter(board_id=board_id)
        return queryset

    def create(self, request, *args, **kwargs):
        board_id = request.data.get('board')
        rationale = request.data.get('rationale', '')
        label = request.data.get('label', 'Baseline')

        if not board_id:
            return Response({'board': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)
        if not rationale:
            return Response({'rationale': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)

                # Only LEAF activities participate in the CPM pass — a
        # container/parent activity (one that has children) is never
        # independently scheduled; its displayed span is always a
        # roll-up of its children, computed client-side. Including it
        # here would let it be scheduled as if it were real, isolated
        # work with its own (essentially meaningless) planned_duration.
        parent_ids_with_children = set(
            Activity.objects.filter(board_id=board_id, parent__isnull=False).values_list('parent_id', flat=True)
        )
        activities = list(
            Activity.objects.filter(board_id=board_id)
            .exclude(id__in=parent_ids_with_children)
            .values('id', 'planned_duration')
        )
        leaf_ids = {a['id'] for a in activities}
        dependencies = list(
            ActivityDependency.objects.filter(
                predecessor__board_id=board_id,
                predecessor_id__in=leaf_ids,
                successor_id__in=leaf_ids,
            ).values('predecessor', 'successor')
        )

        try:
            schedule = compute_schedule(activities, dependencies)
        except CycleDetectedError as e:
            return Response(
                {'detail': str(e), 'involved_activity_ids': e.involved_ids},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            previous_active = ScheduleBaseline.objects.filter(board_id=board_id, is_active=True).first()
            if previous_active:
                previous_active.is_active = False
                previous_active.save()

            new_baseline = ScheduleBaseline.objects.create(
                board_id=board_id,
                label=label,
                based_on=previous_active,
                is_active=True,
            )

            duration_of = {a['id']: a['planned_duration'] for a in activities}
            for activity_id, computed in schedule.items():
                BaselineActivitySchedule.objects.create(
                    baseline=new_baseline,
                    activity_id=activity_id,
                    planned_duration_at_baseline=duration_of[activity_id],
                    early_start=computed['early_start'],
                    early_finish=computed['early_finish'],
                    late_start=computed['late_start'],
                    late_finish=computed['late_finish'],
                    float=computed['float'],
                )

            decision_node = DecisionNode.objects.create(
                board_id=board_id,
                triggered_by=request.user,
                rationale=rationale,
                resulting_baseline=new_baseline,
            )

        return Response(DecisionNodeSerializer(decision_node).data, status=status.HTTP_201_CREATED)