"""
backend/accounts/models.py

Deliberately a separate copy from Riverside Club's accounts app, even
though both start from the same SimpleJWT + Djoser pattern — miniJira/
miniProject is a reusable tool, not tied to a specific project's auth.
See Spadework_Tier2_Kanban_Spec_v1.md, Open decisions (resolved).
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
