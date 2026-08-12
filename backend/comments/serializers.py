from rest_framework import serializers
from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'issue', 'author', 'author_username', 'body', 'created_at']
        read_only_fields = ['author']

    def create(self, validated_data):
        # author isn't submitted by the client — it's always the
        # requesting user, set in the view via perform_create.
        return Comment.objects.create(**validated_data)
