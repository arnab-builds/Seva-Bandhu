from django.urls import re_path
from . import consumers

websocket_urlpatterns = [

    re_path(
        r'^ws/requests/$',
        consumers.RequestConsumer.as_asgi()
    ),

    re_path(
        r'^ws/tracking/(?P<id>\d+)/$',
        consumers.RequestConsumer.as_asgi()
    ),

    re_path(
        r'^ws/chat/(?P<request_id>\d+)/$',
        consumers.ChatConsumer.as_asgi()
    ),
    re_path(
        r'^ws/support/technician/(?P<ticket_id>\d+)/$',
        consumers.TechnicianSupportConsumer.as_asgi()
    ),
]