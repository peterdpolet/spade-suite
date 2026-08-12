"""
backend/flows/consumers.py

DiagramConsumer — Module 7. Server-authoritative, same pattern as
issues/consumers.py's BoardConsumer: clients only ever RECEIVE
broadcasts here, they never send diagram mutations over the socket.
All writes still go through the REST API (which enforces the
team-membership permission checks). The consumer's only job is: join
a per-diagram group on connect, relay whatever gets broadcast to it.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class DiagramConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.diagram_id = self.scope['url_route']['kwargs']['diagram_id']
        self.group_name = f'diagram_{self.diagram_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Called when something is broadcast to this diagram's group (see
    # broadcast_diagram_event in flows/realtime.py) — relays it
    # straight to the connected browser as JSON.
    async def diagram_event(self, event):
        await self.send(text_data=json.dumps(event['payload']))