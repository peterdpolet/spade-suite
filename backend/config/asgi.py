import os
from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django_asgi_app = get_asgi_application()
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from issues.routing import websocket_urlpatterns as issues_websocket_urlpatterns  # noqa: E402
from flows.routing import websocket_urlpatterns as flows_websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': URLRouter(issues_websocket_urlpatterns + flows_websocket_urlpatterns),
})