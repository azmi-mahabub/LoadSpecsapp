"""
WebSocket consumers for real-time chat and notifications
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class TeamChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for team chat rooms"""
    
    async def connect(self):
        self.team_id = self.scope['url_route']['kwargs']['team_id']
        self.room_group_name = f'team_chat_{self.team_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = text_data_json['username']
        user_id = text_data_json['user_id']
        
        # Save message to database
        await self.save_team_message(user_id, self.team_id, message)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
                'user_id': user_id,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp']
        }))
    
    @database_sync_to_async
    def save_team_message(self, user_id, team_id, message):
        from .models import Message, User, Team
        user = User.objects.get(id=user_id)
        team = Team.objects.get(id=team_id)
        Message.objects.create(sender=user, team=team, content=message)


class TaskChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for task-based discussion rooms"""
    
    async def connect(self):
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.room_group_name = f'task_chat_{self.task_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = text_data_json['username']
        user_id = text_data_json['user_id']
        
        await self.save_task_message(user_id, self.task_id, message)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
                'user_id': user_id,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp']
        }))
    
    @database_sync_to_async
    def save_task_message(self, user_id, task_id, message):
        from .models import Message, User, Task
        user = User.objects.get(id=user_id)
        task = Task.objects.get(id=task_id)
        Message.objects.create(sender=user, task=task, content=message)


class DirectChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for direct messages between users"""
    
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        current_user_id = self.scope['user'].id
        
        # Create a unique room name for direct messages
        room_ids = sorted([int(current_user_id), int(self.user_id)])
        self.room_group_name = f'direct_chat_{room_ids[0]}_{room_ids[1]}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = text_data_json['username']
        user_id = text_data_json['user_id']
        
        await self.save_direct_message(user_id, self.user_id, message)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
                'user_id': user_id,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp']
        }))
    
    @database_sync_to_async
    def save_direct_message(self, sender_id, recipient_id, message):
        from .models import Message, User
        sender = User.objects.get(id=sender_id)
        recipient = User.objects.get(id=recipient_id)
        Message.objects.create(sender=sender, recipient=recipient, content=message)


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications"""
    
    async def connect(self):
        self.user_id = self.scope['user'].id
        self.notification_group_name = f'notifications_{self.user_id}'
        
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.notification_group_name,
            self.channel_name
        )
    
    async def send_notification(self, event):
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': event['notification_type'],
            'message': event['message'],
            'timestamp': event['timestamp']
        }))
