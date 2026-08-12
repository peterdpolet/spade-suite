"""
backend/labels/models.py

Label and IssueLabel models — Module 7. Per
Spadework_Tier2_Kanban_Spec_v1.md: simple tagging, no colour-coding
system beyond basics. Labels are board-scoped (not global), matching
how Status/Team already scope to a board's context.
"""
from django.db import models

from boards.models import Board
from issues.models import Issue


class Label(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='labels')
    name = models.CharField(max_length=50)

    class Meta:
        unique_together = [('board', 'name')]

    def __str__(self):
        return self.name


class IssueLabel(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='issue_labels')
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='issue_labels')

    class Meta:
        unique_together = [('issue', 'label')]
