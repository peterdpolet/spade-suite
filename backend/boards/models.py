"""
backend/boards/models.py

Board and Status models — Module 3. Per
Spadework_Tier2_Kanban_Spec_v1.md: single project/board for MVP (no
multi-project switching), fixed status columns (Todo / In Progress /
Blocked / Done — not user-editable). Status.order is fixed at seed time
via a data migration, not exposed for user reordering.
"""
from django.db import models


class Board(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Status(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='statuses')
    name = models.CharField(max_length=50)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['order']
        unique_together = [('board', 'order')]

    def __str__(self):
        return f'{self.board.name} — {self.name}'
