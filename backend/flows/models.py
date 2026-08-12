from django.conf import settings
from django.db import models

from teams.models import Team


class Diagram(models.Model):
    title = models.CharField(max_length=200)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="diagrams")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Node(models.Model):
    class NodeType(models.TextChoices):
        EVENT = "event", "Event"
        FUNCTION = "function", "Function"
        ORG_UNIT = "org_unit", "Organizational Unit"
        DATA_OBJECT = "data_object", "Data Object"
        GENERIC_RECT = "generic_rect", "Generic — Rectangle"
        GENERIC_DIAMOND = "generic_diamond", "Generic — Diamond"

    diagram = models.ForeignKey(Diagram, on_delete=models.CASCADE, related_name="nodes")
    node_type = models.CharField(max_length=20, choices=NodeType.choices)
    label = models.CharField(max_length=200)
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    parent_node = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )

    def __str__(self):
        return f"{self.get_node_type_display()}: {self.label}"


class Edge(models.Model):
    diagram = models.ForeignKey(Diagram, on_delete=models.CASCADE, related_name="edges")
    source_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="outgoing_edges")
    target_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="incoming_edges")

    def __str__(self):
        return f"{self.source_node_id} → {self.target_node_id}"