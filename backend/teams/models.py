"""
backend/teams/models.py

Team and TeamMembership models — Module 4. Per
Spadework_Tier2_Kanban_Spec_v1.md: a user can belong to more than one
team (TeamMembership is a genuine through table, not a simple FK on
User), since Issue allocation later needs "assignee must belong to the
assigned team" — that check requires querying membership, not a single
team field on the user.
"""
from django.conf import settings
from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class TeamMembership(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='team_memberships'
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('team', 'user')]

    def __str__(self):
        return f'{self.user} in {self.team.name}'
