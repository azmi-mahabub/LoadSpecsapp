"""
WebSocket URL routing for real-time features
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/team/(?P<team_id>\d+)/$', consumers.TeamChatConsumer.as_asgi()),
    re_path(r'ws/chat/task/(?P<task_id>\d+)/$', consumers.TaskChatConsumer.as_asgi()),
    re_path(r'ws/chat/direct/(?P<user_id>\d+)/$', consumers.DirectChatConsumer.as_asgi()),
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
]
