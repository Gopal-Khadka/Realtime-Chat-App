"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

# for making sure that connection is only allowed for host listed in settings.ALLOWED_HOSTS
from channels.security.websocket import AllowedHostsOriginValidator

# middleware to handle django authentication system
from channels.auth import AuthMiddlewareStack


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

django_asgi_application = get_asgi_application()

from chat_site import routing # import it after django_asgi_application
application = ProtocolTypeRouter(
    {
        "http": django_asgi_application,  # django asgi for http requests
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(routing.websocket_urlpatterns))
        ),
    }
)
