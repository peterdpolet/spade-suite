from rest_framework import serializers
from .models import Issue


class IssueSerializer(serializers.ModelSerializer):
    labels = serializers.SerializerMethodField()

    class Meta:
        model = Issue
        fields = [
            'id', 'board', 'status', 'title', 'description', 'priority',
            'team', 'assignee', 'target_completion_date',
            'actual_completion_date', 'order', 'labels', 'created_at',
            'updated_at',
        ]
        read_only_fields = ['actual_completion_date', 'order']

    def get_labels(self, obj):
        # Avoids a circular import at module load time (labels app
        # imports Issue from here) — imported lazily, inside the method.
        from labels.serializers import LabelSerializer
        return LabelSerializer(
            [il.label for il in obj.issue_labels.select_related('label')], many=True
        ).data

    def validate(self, data):
        team = data.get('team', getattr(self.instance, 'team', None))
        assignee = data.get('assignee', getattr(self.instance, 'assignee', None))

        if team and assignee:
            if not team.memberships.filter(user=assignee).exists():
                raise serializers.ValidationError(
                    {'assignee': 'Assignee must be a member of the assigned team.'}
                )
        return data
