"""
backend/flows/realtime.py

Broadcast helper — called from the views after a successful mutation
(create/update/delete on Node/Edge), never from inside a serializer
or model, so it's obvious at the call site exactly when a broadcast
fires. Mirrors issues/realtime.py's pattern.
"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_diagram_event(diagram_id, event_type, entity_type, data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'diagram_{diagram_id}',
        {
            'type': 'diagram_event',  # routes to DiagramConsumer.diagram_event
            'payload': {'event': event_type, 'entity': entity_type, 'data': data},
        },
    )