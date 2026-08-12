from django.contrib import admin
from .models import Board, Status


class StatusInline(admin.TabularInline):
    model = Status
    extra = 0


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    inlines = [StatusInline]
