"""
backend/issues/models.py

Issue model — Module 5. Per Spadework_Tier2_Kanban_Spec_v1.md: priority
tier is fixed (not user-configurable), assignee must belong to the
assigned team if both are set (enforced in the serializer, not here —
`clean()` isn't called automatically by DRF), actual_completion_date
auto-captures on transition to Done (editable afterward if the
auto-capture needs correcting). `order` field included now as a
placeholder string — the actual fractional-key generation logic is
Module 8; adding the column now avoids a second migration later.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

from boards.models import Board, Status
from teams.models import Team


class Issue(models.Model):
    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='issues')
    status = models.ForeignKey(Status, on_delete=models.PROTECT, related_name='issues')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    team = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='issues'
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_issues',
    )
    target_completion_date = models.DateField(null=True, blank=True)
    actual_completion_date = models.DateField(null=True, blank=True)
    order = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-capture actual_completion_date the moment status becomes
        # Done — only sets it if not already set, so a manual correction
        # afterward isn't silently overwritten on the next save.
        if self.status_id and self.status.name == 'Done' and not self.actual_completion_date:
            self.actual_completion_date = timezone.now().date()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
