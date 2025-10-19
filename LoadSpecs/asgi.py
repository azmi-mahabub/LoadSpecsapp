"""
ASGI config for LoadSpecs project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LoadSpecs.settings')

django_asgi_app = get_asgi_application()

# Try to import channels for WebSocket support
try:
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.auth import AuthMiddlewareStack
    from channels.security.websocket import AllowedHostsOriginValidator
    from LoadSpecsApp import routing

    application = ProtocolTypeRouter({
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(
                    routing.websocket_urlpatterns
                )
            )
        ),
    })
except ImportError:
    # Channels not installed - use standard ASGI application
    application = django_asgi_app
