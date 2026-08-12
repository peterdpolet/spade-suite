from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/diagram/(?P<diagram_id>\d+)/$', consumers.DiagramConsumer.as_asgi()),
]