from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Team, TeamMembership
from .serializers import TeamSerializer, TeamMembershipSerializer

User = get_user_model()


class TeamViewSet(viewsets.ModelViewSet):
    # Full CRUD — unlike Board/Status, Teams are genuinely user-managed
    # (Spadework_Tier2_Kanban_Spec_v1.md).
    queryset = Team.objects.prefetch_related('memberships__user')
    serializer_class = TeamSerializer

    @action(detail=True, methods=['post'], url_path='members')
    def add_member(self, request, pk=None):
        team = self.get_object()
        user_id = request.data.get('user')
        if not user_id:
            return Response({'user': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'user': ['User not found.']}, status=status.HTTP_404_NOT_FOUND)

        membership, created = TeamMembership.objects.get_or_create(team=team, user=user)
        if not created:
            return Response(
                {'detail': 'User is already a member of this team.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(TeamMembershipSerializer(membership).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='members/(?P<user_id>[^/.]+)')
    def remove_member(self, request, pk=None, user_id=None):
        team = self.get_object()
        deleted, _ = TeamMembership.objects.filter(team=team, user_id=user_id).delete()
        if not deleted:
            return Response({'detail': 'Membership not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
