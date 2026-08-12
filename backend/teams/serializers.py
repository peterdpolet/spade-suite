from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Team, TeamMembership

User = get_user_model()


class TeamMembershipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = TeamMembership
        fields = ['id', 'user', 'username', 'email', 'joined_at']
        read_only_fields = ['joined_at']


class TeamSerializer(serializers.ModelSerializer):
    memberships = TeamMembershipSerializer(many=True, read_only=True)

    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'memberships', 'created_at']
