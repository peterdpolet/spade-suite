from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from .models import Diagram, Edge, Node
from .serializers import DiagramSerializer, EdgeSerializer, NodeSerializer
from teams.models import TeamMembership



from rest_framework.exceptions import PermissionDenied

from teams.models import TeamMembership
from .realtime import broadcast_diagram_event


class DiagramViewSet(viewsets.ModelViewSet):
    queryset = Diagram.objects.select_related('team', 'created_by')
    serializer_class = DiagramSerializer

    def get_queryset(self):
        return super().get_queryset().filter(
            team__memberships__user=self.request.user
        ).distinct()

    def perform_create(self, serializer):
        team = serializer.validated_data['team']
        if not TeamMembership.objects.filter(team=team, user=self.request.user).exists():
            raise PermissionDenied("You are not a member of this team.")
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        if instance.created_by != self.request.user:
            raise PermissionDenied("Only the diagram's creator can delete it.")
        instance.delete()


class NodeViewSet(viewsets.ModelViewSet):
    queryset = Node.objects.select_related('diagram', 'parent_node')
    serializer_class = NodeSerializer

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            diagram__team__memberships__user=self.request.user
        ).distinct()
        diagram_id = self.request.query_params.get('diagram')
        if diagram_id:
            queryset = queryset.filter(diagram_id=diagram_id)

        parent_id = self.request.query_params.get('parent')
        if parent_id is not None:
            if parent_id == '':
                queryset = queryset.filter(parent_node__isnull=True)
            else:
                queryset = queryset.filter(parent_node_id=parent_id)
        else:
            queryset = queryset.filter(parent_node__isnull=True)

        return queryset

    def perform_create(self, serializer):
        diagram = serializer.validated_data['diagram']
        if not TeamMembership.objects.filter(team=diagram.team, user=self.request.user).exists():
            raise PermissionDenied("You are not a member of this diagram's team.")
        node = serializer.save()
        broadcast_diagram_event(node.diagram_id, 'created', 'node', NodeSerializer(node).data)

    def perform_update(self, serializer):
        """
        PLANTED BUG (Module 9, deliberate — see miniFlow build notes):
        perform_create broadcasts a 'created' event, but this
        perform_update does NOT broadcast an 'updated' event. Moving a
        node (dragging it to a new position) saves correctly to the
        database and the dragging user sees it move — but every OTHER
        connected browser session never receives any notification, so
        their canvas silently drifts out of sync with the real position
        until they manually refresh. This is a "JWT/auth"-adjacent but
        really more of an "incomplete feature" category bug: the
        real-time story only covers creation, not the full CRUD
        lifecycle. Fix: mirror perform_create's broadcast call here,
        with event_type='updated' instead of 'created'.
        """
        node = serializer.save()

    def perform_destroy(self, instance):
        """
        PLANTED BUG (Module 9, deliberate — see miniFlow build notes):
        same gap as perform_update above — deleting a node removes it
        from the database for everyone, but only the deleting user's own
        browser removes it from their canvas (via their own local Vue
        state). Every other connected session keeps showing a node that
        no longer exists in the backend at all — clicking it or trying
        to connect to it will start failing with 404s that look like a
        totally unrelated bug, when the real cause is simply "this
        broadcast was never wired up." Fix: broadcast a 'deleted' event
        (with just the id, since the object no longer exists to
        serialize) before or after instance.delete().
        """
        node_id = instance.id
        diagram_id = instance.diagram_id
        instance.delete()
    

class EdgeViewSet(viewsets.ModelViewSet):
    queryset = Edge.objects.select_related('diagram', 'source_node', 'target_node')
    serializer_class = EdgeSerializer

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            diagram__team__memberships__user=self.request.user
        ).distinct()
        diagram_id = self.request.query_params.get('diagram')
        if diagram_id:
            queryset = queryset.filter(diagram_id=diagram_id)
        return queryset

    def perform_create(self, serializer):
        diagram = serializer.validated_data['diagram']
        if not TeamMembership.objects.filter(team=diagram.team, user=self.request.user).exists():
            raise PermissionDenied("You are not a member of this diagram's team.")
        edge = serializer.save()
        broadcast_diagram_event(edge.diagram_id, 'created', 'edge', EdgeSerializer(edge).data)

    def perform_update(self, serializer):
        """
        PLANTED BUG (Module 9, deliberate — see miniFlow build notes):
        perform_create broadcasts a 'created' event, but this
        perform_update does NOT broadcast an 'updated' event. Moving a
        node (dragging it to a new position) saves correctly to the
        database and the dragging user sees it move — but every OTHER
        connected browser session never receives any notification, so
        their canvas silently drifts out of sync with the real position
        until they manually refresh. This is a "JWT/auth"-adjacent but
        really more of an "incomplete feature" category bug: the
        real-time story only covers creation, not the full CRUD
        lifecycle. Fix: mirror perform_create's broadcast call here,
        with event_type='updated' instead of 'created'.
        """
        node = serializer.save()

    def perform_destroy(self, instance):
        """
        PLANTED BUG (Module 9, deliberate — see miniFlow build notes):
        same gap as perform_update above — deleting a node removes it
        from the database for everyone, but only the deleting user's own
        browser removes it from their canvas (via their own local Vue
        state). Every other connected session keeps showing a node that
        no longer exists in the backend at all — clicking it or trying
        to connect to it will start failing with 404s that look like a
        totally unrelated bug, when the real cause is simply "this
        broadcast was never wired up." Fix: broadcast a 'deleted' event
        (with just the id, since the object no longer exists to
        serialize) before or after instance.delete().
        """
        node_id = instance.id
        diagram_id = instance.diagram_id
        instance.delete()