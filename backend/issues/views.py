from rest_framework import viewsets, status as http_status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Issue
from .serializers import IssueSerializer
from .ordering import key_between
from .realtime import broadcast_board_event


class IssueViewSet(viewsets.ModelViewSet):
    queryset = Issue.objects.select_related('status', 'team', 'assignee').prefetch_related(
        'issue_labels__label'
    )
    serializer_class = IssueSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(team__memberships__user=self.request.user).distinct()
        board_id = self.request.query_params.get('board')
        if board_id:
            queryset = queryset.filter(board_id=board_id)
        status_id = self.request.query_params.get('status')
        if status_id:
            queryset = queryset.filter(status_id=status_id)
        assignee_id = self.request.query_params.get('assignee')
        if assignee_id:
            queryset = queryset.filter(assignee_id=assignee_id)
        label_id = self.request.query_params.get('label')
        if label_id:
            queryset = queryset.filter(issue_labels__label_id=label_id)
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
        return queryset.distinct()

    def perform_create(self, serializer):
        status_id = serializer.validated_data['status'].id
        last = Issue.objects.filter(status_id=status_id).order_by('-order').first()
        order = key_between(last.order if last else '', '')
        issue = serializer.save(order=order)
        broadcast_board_event(issue.board_id, 'created', IssueSerializer(issue).data)

    def perform_update(self, serializer):
        issue = serializer.save()
        broadcast_board_event(issue.board_id, 'updated', IssueSerializer(issue).data)

    def perform_destroy(self, instance):
        board_id = instance.board_id
        issue_id = instance.id
        instance.delete()
        broadcast_board_event(board_id, 'deleted', {'id': issue_id})

    @action(detail=True, methods=['post'], url_path='reorder')
    def reorder(self, request, pk=None):
        """
        PLANTED BUG (Module 10, deliberate — see
        Spadework_Tier2_Kanban_Spec_v1.md "Planted teaching bugs"):
        this read-then-write is NOT wrapped in a transaction or
        select_for_update(). Two near-simultaneous reorder requests
        moving different cards into the same gap both read the SAME
        before/after neighbour keys, both compute the SAME midpoint via
        key_between(), and both write it — the second write silently
        overwrites the first's `order`, and depending on timing both
        issues can end up with colliding or inconsistent order values.
        This is the exact "drag-drop race" scenario the spec calls out
        as a target for the EPC tracer content — genuinely reproducible
        with concurrent requests, not a contrived example. DO NOT fix
        with select_for_update()/atomic here without updating the
        Module 10 planted-bugs log entry — fixing this quietly defeats
        its teaching purpose.
        """
        issue = self.get_object()
        new_status_id = request.data.get('status', issue.status_id)
        before_id = request.data.get('before_id')
        after_id = request.data.get('after_id')

        before_order = ''
        after_order = ''
        if before_id:
            try:
                before_order = Issue.objects.get(pk=before_id).order
            except Issue.DoesNotExist:
                return Response({'before_id': ['Issue not found.']}, status=http_status.HTTP_400_BAD_REQUEST)
        if after_id:
            try:
                after_order = Issue.objects.get(pk=after_id).order
            except Issue.DoesNotExist:
                return Response({'after_id': ['Issue not found.']}, status=http_status.HTTP_400_BAD_REQUEST)

        issue.status_id = new_status_id
        issue.order = key_between(before_order, after_order)
        issue.save()
        data = IssueSerializer(issue).data
        broadcast_board_event(issue.board_id, 'updated', data)
        return Response(data)

    @action(detail=True, methods=['post'], url_path='labels')
    def add_label(self, request, pk=None):
        from labels.models import Label, IssueLabel
        issue = self.get_object()
        label_id = request.data.get('label')
        if not label_id:
            return Response({'label': ['This field is required.']}, status=http_status.HTTP_400_BAD_REQUEST)
        try:
            label = Label.objects.get(pk=label_id)
        except Label.DoesNotExist:
            return Response({'label': ['Label not found.']}, status=http_status.HTTP_404_NOT_FOUND)

        _, created = IssueLabel.objects.get_or_create(issue=issue, label=label)
        if not created:
            return Response({'detail': 'Label already attached.'}, status=http_status.HTTP_400_BAD_REQUEST)
        data = IssueSerializer(issue).data
        broadcast_board_event(issue.board_id, 'updated', data)
        return Response(data, status=http_status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='labels/(?P<label_id>[^/.]+)')
    def remove_label(self, request, pk=None, label_id=None):
        from labels.models import IssueLabel
        issue = self.get_object()
        deleted, _ = IssueLabel.objects.filter(issue=issue, label_id=label_id).delete()
        if not deleted:
            return Response({'detail': 'Label not attached to this issue.'}, status=http_status.HTTP_404_NOT_FOUND)
        broadcast_board_event(issue.board_id, 'updated', IssueSerializer(issue).data)
        return Response(status=http_status.HTTP_204_NO_CONTENT)