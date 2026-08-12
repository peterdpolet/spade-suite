"""
backend/issues/realtime.py

Broadcast helper — called from the views after a successful mutation
(create/update/reorder/delete), never from inside a serializer or
model, so it's obvious at the call site exactly when a broadcast fires.
"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_board_event(board_id, event_type, issue_data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'board_{board_id}',
        {
            'type': 'board_event',  # routes to BoardConsumer.board_event
            'payload': {'event': event_type, 'issue': issue_data},
        },
    )
