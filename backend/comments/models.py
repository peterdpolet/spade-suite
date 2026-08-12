"""
backend/comments/models.py

Comment model — Module 6. Per Spadework_Tier2_Kanban_Spec_v1.md: tied
to Issue, simple body + author. Ordering is chronological — the
"comment ordering under concurrent posts" planted teaching bug (Module
10) targets this model specifically, as the simpler/earlier example of
the concurrency-bug class before the harder drag-drop race.
"""
from django.conf import settings
from django.db import models

from issues.models import Issue


class Comment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author} on {self.issue.title}'
