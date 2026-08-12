from rest_framework import viewsets
from .models import Comment
from .serializers import CommentSerializer


# PLANTED BUG (Module 10, deliberate — see
# Spadework_Tier2_Kanban_Spec_v1.md "Planted teaching bugs" — the
# simpler/earlier example of the concurrency-bug class before the
# harder drag-drop race): comments are NOT wired into the Module 9
# realtime broadcast at all. Two people viewing the same issue never
# see each other's comments live — only a manual refetch reveals them.
# If two people post near-simultaneously, whichever comment a given
# client happens to fetch/refresh first determines what order they
# perceive, even though the server's actual created_at ordering is the
# single source of truth. Lower stakes than the drag-drop race (no data
# collision, just a perception/timing gap), but the same underlying
# class of bug: client-side state silently diverging from server state
# during a window neither the client nor the person notices.
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related('author')
    serializer_class = CommentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        issue_id = self.request.query_params.get('issue')
        if issue_id:
            queryset = queryset.filter(issue_id=issue_id)
        return queryset

    def perform_create(self, serializer):
        # author is always the requesting user — never client-supplied,
        # otherwise anyone could post a comment as someone else.
        serializer.save(author=self.request.user)
