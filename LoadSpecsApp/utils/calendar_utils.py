"""
Calendar integration utilities for Google Calendar and Outlook
"""

from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone


class GoogleCalendarService:
    """
    Google Calendar API integration
    """
    
    def __init__(self, calendar_sync):
        self.calendar_sync = calendar_sync
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Calendar API service"""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            
            # Create credentials from stored tokens
            creds = Credentials(
                token=self.calendar_sync.access_token,
                refresh_token=self.calendar_sync.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=settings.GOOGLE_CALENDAR_CLIENT_ID,
                client_secret=settings.GOOGLE_CALENDAR_CLIENT_SECRET
            )
            
            # Build service
            self.service = build('calendar', 'v3', credentials=creds)
        
        except Exception as e:
            print(f"Failed to initialize Google Calendar service: {e}")
            self.service = None
    
    def create_or_update_event(self, task):
        """Create or update a calendar event for a task"""
        if not self.service:
            return None
        
        try:
            # Create event data
            event = {
                'summary': f'Task: {task.title}',
                'description': task.description or '',
                'start': {
                    'date': task.due_date.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'date': task.due_date.isoformat(),
                    'timeZone': 'UTC',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 60},
                    ],
                },
            }
            
            # Check if event already exists (using task ID in description or metadata)
            # For simplicity, we'll create a new event
            event_result = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return event_result.get('id')
        
        except Exception as e:
            print(f"Error creating Google Calendar event: {e}")
            return None
    
    def delete_event(self, event_id):
        """Delete a calendar event"""
        if not self.service:
            return False
        
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            return True
        
        except Exception as e:
            print(f"Error deleting Google Calendar event: {e}")
            return False


class OutlookCalendarService:
    """
    Microsoft Outlook/Graph API integration
    """
    
    def __init__(self, calendar_sync):
        self.calendar_sync = calendar_sync
        self.access_token = calendar_sync.access_token
    
    def _get_headers(self):
        """Get authorization headers"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def create_or_update_event(self, task):
        """Create or update an Outlook calendar event for a task"""
        try:
            import requests
            
            # Create event data
            event = {
                'subject': f'Task: {task.title}',
                'body': {
                    'contentType': 'HTML',
                    'content': task.description or ''
                },
                'start': {
                    'dateTime': f'{task.due_date}T09:00:00',
                    'timeZone': 'UTC'
                },
                'end': {
                    'dateTime': f'{task.due_date}T17:00:00',
                    'timeZone': 'UTC'
                },
                'reminderMinutesBeforeStart': 1440  # 24 hours
            }
            
            # Create event via Microsoft Graph API
            response = requests.post(
                'https://graph.microsoft.com/v1.0/me/events',
                headers=self._get_headers(),
                json=event
            )
            
            if response.status_code == 201:
                return response.json().get('id')
            else:
                print(f"Outlook API error: {response.text}")
                return None
        
        except Exception as e:
            print(f"Error creating Outlook event: {e}")
            return None
    
    def delete_event(self, event_id):
        """Delete an Outlook calendar event"""
        try:
            import requests
            
            response = requests.delete(
                f'https://graph.microsoft.com/v1.0/me/events/{event_id}',
                headers=self._get_headers()
            )
            
            return response.status_code == 204
        
        except Exception as e:
            print(f"Error deleting Outlook event: {e}")
            return False


def get_oauth_url(provider='google'):
    """
    Generate OAuth authorization URL for calendar providers
    """
    if provider == 'google':
        from google_auth_oauthlib.flow import Flow
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CALENDAR_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CALENDAR_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_CALENDAR_REDIRECT_URI]
                }
            },
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        
        flow.redirect_uri = settings.GOOGLE_CALENDAR_REDIRECT_URI
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        return authorization_url, state
    
    elif provider == 'outlook':
        import msal
        
        app = msal.PublicClientApplication(
            settings.MICROSOFT_CLIENT_ID,
            authority=settings.MICROSOFT_AUTHORITY
        )
        
        auth_url = app.get_authorization_request_url(
            settings.MICROSOFT_SCOPES,
            redirect_uri=settings.MICROSOFT_REDIRECT_URI
        )
        
        return auth_url, None
    
    return None, None
