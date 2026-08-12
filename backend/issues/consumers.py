"""
backend/issues/consumers.py

BoardConsumer — Module 9. Server-authoritative: clients only ever
RECEIVE broadcasts here, they never send board mutations over the
socket (all writes still go through the REST API, which is what
actually enforces validation like the team/assignee check). The
consumer's only job is: join a per-board group on connect, relay
whatever gets broadcast to that group.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class BoardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.board_id = self.scope['url_route']['kwargs']['board_id']
        self.group_name = f'board_{self.board_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Called when something is broadcast to this board's group (see
    # broadcast_board_event in issues/realtime.py) — relays it straight
    # to the connected browser as JSON.
    async def board_event(self, event):
        await self.send(text_data=json.dumps(event['payload']))
