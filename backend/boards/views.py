from rest_framework import viewsets
from .models import Board
from .serializers import BoardSerializer


class BoardViewSet(viewsets.ReadOnlyModelViewSet):
    # Read-only: Board/Status are fixed at seed time, not user-editable
    # (Spadework_Tier2_Kanban_Spec_v1.md — single board, fixed columns).
    queryset = Board.objects.prefetch_related('statuses')
    serializer_class = BoardSerializer
