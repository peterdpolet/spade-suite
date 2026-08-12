from rest_framework import serializers
from .models import Board, Status


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ['id', 'name', 'order']


class BoardSerializer(serializers.ModelSerializer):
    # Nested, read-only: statuses are fixed at seed time (Module 3 data
    # migration) and aren't created/edited through this API — Board/
    # Status are both read-only endpoints for the same reason.
    statuses = StatusSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'name', 'description', 'statuses', 'created_at']
