from rest_framework import serializers
from .models import Activity, ActivityDependency, ActivityIssue, ScheduleBaseline, BaselineActivitySchedule, DecisionNode


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ['id', 'board', 'name', 'planned_duration', 'actual_duration', 'parent', 'created_at']

    def validate_parent(self, value):
        # Mirrors Activity.clean() — DRF doesn't call model.clean()
        # automatically, so the one-level-only rule needs enforcing
        # here too, not just at the model layer.
        if value and value.parent_id:
            raise serializers.ValidationError(
                'Only one level of grouping is allowed — a parent activity cannot itself have a parent.'
            )
        return value


class ActivityDependencySerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityDependency
        fields = ['id', 'predecessor', 'successor']

    def validate(self, data):
        predecessor = data.get('predecessor', getattr(self.instance, 'predecessor', None))
        successor = data.get('successor', getattr(self.instance, 'successor', None))
        if predecessor and successor and predecessor.id == successor.id:
            raise serializers.ValidationError('An activity cannot depend on itself.')
        return data


class ActivityIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityIssue
        fields = ['id', 'activity', 'issue']


class BaselineActivityScheduleSerializer(serializers.ModelSerializer):
    activity_name = serializers.CharField(source='activity.name', read_only=True)

    class Meta:
        model = BaselineActivitySchedule
        fields = [
            'id', 'activity', 'activity_name', 'planned_duration_at_baseline',
            'early_start', 'early_finish', 'late_start', 'late_finish', 'float',
        ]


class ScheduleBaselineSerializer(serializers.ModelSerializer):
    schedule = BaselineActivityScheduleSerializer(many=True, read_only=True)

    class Meta:
        model = ScheduleBaseline
        fields = ['id', 'board', 'label', 'created_at', 'based_on', 'is_active', 'schedule']
        read_only_fields = ['is_active']


class DecisionNodeSerializer(serializers.ModelSerializer):
    resulting_baseline_detail = ScheduleBaselineSerializer(source='resulting_baseline', read_only=True)

    class Meta:
        model = DecisionNode
        fields = [
            'id', 'board', 'triggered_by', 'created_at', 'rationale',
            'resulting_baseline', 'resulting_baseline_detail',
        ]
        read_only_fields = ['triggered_by', 'resulting_baseline']