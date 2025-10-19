"""
Celery tasks for background processing
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@shared_task
def check_burnout_alerts():
    """
    Check for burnout patterns and create alerts for team leads
    Runs periodically (e.g., daily)
    """
    from .models import Employee, MoodCheckin, BurnoutAlert, Team, TeamLead
    
    # Get all employees
    employees = Employee.objects.all()
    
    for employee in employees:
        if not employee.team:
            continue
        
        # Check mood check-ins for the last 7 days
        week_ago = timezone.now() - timedelta(days=7)
        recent_moods = MoodCheckin.objects.filter(
            employee=employee,
            timestamp__gte=week_ago
        )
        
        # Count burnout moods
        burnout_count = recent_moods.filter(mood='burnout').count()
        stressed_count = recent_moods.filter(mood='stressed').count()
        
        # Determine severity
        severity = 'low'
        alert_message = ""
        
        if burnout_count >= 3:
            severity = 'critical'
            alert_message = f"{employee.user.get_full_name() or employee.user.username} has reported burnout {burnout_count} times in the past week. Immediate intervention needed."
        elif burnout_count >= 2:
            severity = 'high'
            alert_message = f"{employee.user.get_full_name() or employee.user.username} has reported burnout {burnout_count} times in the past week. High risk detected."
        elif stressed_count >= 4:
            severity = 'medium'
            alert_message = f"{employee.user.get_full_name() or employee.user.username} has been stressed {stressed_count} times this week. Monitor closely."
        
        # Create alert if needed
        if alert_message:
            # Get team leads for this team
            team_leads = employee.team.team_leads.all()
            
            for team_lead in team_leads:
                # Check if similar alert already exists (avoid duplicates)
                existing_alert = BurnoutAlert.objects.filter(
                    employee=employee,
                    team_lead=team_lead,
                    created_at__gte=week_ago,
                    is_acknowledged=False
                ).exists()
                
                if not existing_alert:
                    alert = BurnoutAlert.objects.create(
                        employee=employee,
                        team=employee.team,
                        team_lead=team_lead,
                        alert_message=alert_message,
                        severity=severity
                    )
                    
                    # Send real-time notification
                    send_notification_to_user.delay(team_lead.user.id, 'burnout_alert', alert_message)
    
    return f"Checked {employees.count()} employees for burnout alerts"


@shared_task
def send_notification_to_user(user_id, notification_type, message):
    """
    Send real-time notification to a user via WebSocket
    """
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        f'notifications_{user_id}',
        {
            'type': 'send_notification',
            'notification_type': notification_type,
            'message': message,
            'timestamp': timezone.now().isoformat()
        }
    )


@shared_task
def sync_calendar_tasks():
    """
    Sync tasks to user calendars (Google Calendar & Outlook)
    Runs periodically to keep calendars updated
    """
    from .models import CalendarSync, Task
    
    active_syncs = CalendarSync.objects.filter(is_active=True, sync_enabled=True)
    
    for sync in active_syncs:
        try:
            user = sync.user
            
            # Get user's tasks (if employee)
            if hasattr(user, 'employee_profile'):
                employee = user.employee_profile
                tasks = employee.tasks.filter(status__in=['pending', 'in_progress'])
                
                if sync.provider == 'google':
                    sync_to_google_calendar(sync, tasks)
                elif sync.provider == 'outlook':
                    sync_to_outlook_calendar(sync, tasks)
                
                # Update last synced time
                sync.last_synced = timezone.now()
                sync.save()
        
        except Exception as e:
            print(f"Error syncing calendar for {sync.user.username}: {e}")
    
    return f"Synced {active_syncs.count()} calendars"


def sync_to_google_calendar(sync, tasks):
    """
    Sync tasks to Google Calendar
    """
    from .utils.calendar_utils import GoogleCalendarService
    
    try:
        calendar_service = GoogleCalendarService(sync)
        
        for task in tasks:
            calendar_service.create_or_update_event(task)
    
    except Exception as e:
        print(f"Google Calendar sync error: {e}")


def sync_to_outlook_calendar(sync, tasks):
    """
    Sync tasks to Outlook Calendar
    """
    from .utils.calendar_utils import OutlookCalendarService
    
    try:
        calendar_service = OutlookCalendarService(sync)
        
        for task in tasks:
            calendar_service.create_or_update_event(task)
    
    except Exception as e:
        print(f"Outlook Calendar sync error: {e}")


@shared_task
def analyze_task_priorities():
    """
    Use AI to analyze and suggest task priority adjustments
    """
    from .models import Task, TaskPrioritySuggestion
    from .utils.ai_utils import TaskPrioritizer
    
    # Get active tasks
    active_tasks = Task.objects.filter(status__in=['pending', 'in_progress'])
    
    prioritizer = TaskPrioritizer()
    suggestions_created = 0
    
    for task in active_tasks:
        suggestion = prioritizer.analyze_task(task)
        
        if suggestion and suggestion['suggested_priority'] != task.priority:
            # Create suggestion
            TaskPrioritySuggestion.objects.create(
                task=task,
                suggested_priority=suggestion['suggested_priority'],
                current_priority=task.priority,
                reason=suggestion['reason'],
                confidence_score=suggestion['confidence_score']
            )
            suggestions_created += 1
    
    return f"Created {suggestions_created} priority suggestions"


@shared_task
def send_task_reminders():
    """
    Send reminders for tasks due soon
    """
    from .models import Task
    
    # Get tasks due in the next 24 hours
    tomorrow = timezone.now() + timedelta(days=1)
    today = timezone.now()
    
    upcoming_tasks = Task.objects.filter(
        status__in=['pending', 'in_progress'],
        due_date__gte=today.date(),
        due_date__lte=tomorrow.date()
    )
    
    for task in upcoming_tasks:
        user = task.assigned_to.user
        
        # Check user preferences
        if hasattr(user, 'preferences') and user.preferences.task_reminders:
            message = f"Reminder: Task '{task.title}' is due on {task.due_date.strftime('%B %d, %Y')}"
            send_notification_to_user.delay(user.id, 'task_reminder', message)
    
    return f"Sent reminders for {upcoming_tasks.count()} tasks"
