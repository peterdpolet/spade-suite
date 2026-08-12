"""
backend/activities/models.py

Activity, ActivityDependency, ActivityIssue, ScheduleBaseline,
BaselineActivitySchedule, DecisionNode — Module 11, per
Spadework_miniProject_Spec_v1.md.

Design confirmed with Peter before building: Activity.planned_duration
is live/mutable (current best plan). A Decision Node is what actually
triggers the forward/backward pass AND creates the immutable baseline
snapshot, in one step — recalculation and baselining happen together,
gated by writing a rationale. BaselineActivitySchedule isn't literally
named in the spec, but is the necessary "snapshot the current state
immutably" mechanism the spec describes in its "revised scope
exclusion" section — it's what makes a ScheduleBaseline actually mean
something rather than just being a label.

Added 15 Jul 2026: Activity.parent — ONE additional level of grouping
(high-level vs. operational-level view), confirmed with Peter as
exactly one level, not arbitrary nesting. Deliberately does NOT change
the scheduling algorithm at all: the forward/backward pass still runs
only against leaf (operational) activities and their real dependencies.
A parent activity's "schedule" is always a roll-up (min early_start,
max early_finish across its children) computed on the READ side, never
an independently-scheduled node of its own — enforced by
validate_parent_depth below, which forbids a parent activity from
itself having a parent.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from boards.models import Board
from issues.models import Issue


class Activity(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='activities')
    name = models.CharField(max_length=200)
    planned_duration = models.PositiveIntegerField(help_text='Duration in days')
    actual_duration = models.PositiveIntegerField(null=True, blank=True)
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Enforces exactly ONE level of nesting — a parent activity
        # can't itself have a parent. Model-level clean(), not just
        # serializer validation, so this holds even for
        # admin/shell-created rows, not only API requests.
        if self.parent_id and self.parent.parent_id:
            raise ValidationError(
                'Only one level of grouping is allowed — a parent activity cannot itself have a parent.'
            )

    def __str__(self):
        return self.name


class ActivityDependency(models.Model):
    predecessor = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name='successor_links'
    )
    successor = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name='predecessor_links'
    )

    class Meta:
        unique_together = [('predecessor', 'successor')]

    def __str__(self):
        return f'{self.predecessor.name} -> {self.successor.name}'


class ActivityIssue(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='activity_issues')
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='activity_issues')

    class Meta:
        unique_together = [('activity', 'issue')]


class ScheduleBaseline(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='baselines')
    label = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    based_on = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='derived_baselines'
    )
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.label


class BaselineActivitySchedule(models.Model):
    baseline = models.ForeignKey(ScheduleBaseline, on_delete=models.CASCADE, related_name='schedule')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    planned_duration_at_baseline = models.PositiveIntegerField()
    early_start = models.IntegerField()
    early_finish = models.IntegerField()
    late_start = models.IntegerField()
    late_finish = models.IntegerField()
    float = models.IntegerField()

    class Meta:
        unique_together = [('baseline', 'activity')]


class DecisionNode(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='decision_nodes')
    triggered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    rationale = models.TextField()
    resulting_baseline = models.OneToOneField(ScheduleBaseline, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.triggered_by} — {self.created_at:%Y-%m-%d}'