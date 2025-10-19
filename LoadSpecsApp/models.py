from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


class User(AbstractUser):
    """Custom User model extending AbstractUser"""
    is_employee = models.BooleanField(default=False)
    is_team_lead = models.BooleanField(default=False)
    company_name = models.CharField(max_length=200, blank=True, null=True)
    joined_date = models.DateTimeField(default=timezone.now)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        default='default_profile.png'
    )
    
    def __str__(self):
        return self.username
    
    @property
    def role(self):
        if self.is_team_lead:
            return "Team Lead"
        elif self.is_employee:
            return "Employee"
        return "No Role"
    
    @property
    def full_name(self):
        """Return user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    @property
    def profile_completion(self):
        """Calculate profile completion percentage"""
        fields = [
            self.first_name,
            self.last_name,
            self.email,
            self.bio,
            self.profile_picture and self.profile_picture.name != 'default_profile.png'
        ]
        completed = sum(1 for field in fields if field)
        return int((completed / len(fields)) * 100)


class Team(models.Model):
    """Team model for managing teams"""
    team_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teams_created'
    )
    created_at = models.DateTimeField(default=timezone.now)
    join_code = models.CharField(max_length=10, unique=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.join_code:
            self.join_code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.team_name
    
    @property
    def member_count(self):
        return self.employees.count()
    
    @property
    def total_tasks(self):
        return self.tasks.count()
    
    @property
    def completed_tasks(self):
        return self.tasks.filter(status='completed').count()
    
    @property
    def pending_tasks(self):
        return self.tasks.filter(status='pending').count()
    
    @property
    def in_progress_tasks(self):
        return self.tasks.filter(status='in_progress').count()
    
    @property
    def progress_percentage(self):
        total = self.total_tasks
        if total == 0:
            return 0
        return int((self.completed_tasks / total) * 100)


class TeamLead(models.Model):
    """Team Lead profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teamlead_profile')
    teams = models.ManyToManyField(Team, related_name='team_leads', blank=True)
    
    def __str__(self):
        return f"Team Lead: {self.user.username}"


class Employee(models.Model):
    """Employee profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )
    # Enhanced profile fields
    skills = models.TextField(blank=True, null=True, help_text="Comma-separated skills")
    experience_years = models.IntegerField(default=0, help_text="Years of experience")
    interests = models.TextField(blank=True, null=True, help_text="Professional interests")
    department = models.CharField(max_length=100, blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"Employee: {self.user.username}"
    
    def get_skills_list(self):
        """Return skills as a list"""
        if self.skills:
            return [skill.strip() for skill in self.skills.split(',')]
        return []
    
    @property
    def assigned_tasks(self):
        return self.tasks.count()
    
    @property
    def completed_tasks(self):
        return self.tasks.filter(status='completed').count()
    
    @property
    def pending_tasks(self):
        return self.tasks.filter(status='pending').count()
    
    @property
    def burnout_status(self):
        """
        Calculate burnout status based on the burnout score
        Returns: String representing risk level with emoji
        """
        score = self.calculate_burnout_score()
        
        if score >= 81:
            return "🔴 Critical Risk"
        elif score >= 61:
            return "🟠 High Risk"
        elif score >= 31:
            return "🟡 Moderate Risk"
        else:
            return "🟢 Low Risk"
    
    def get_burnout_description(self):
        """Get detailed description of burnout status"""
        score = self.calculate_burnout_score()
        
        if score >= 81:
            return "Burnout danger - Immediate intervention needed"
        elif score >= 61:
            return "Overload likely - Redistribute workload"
        elif score >= 31:
            return "Manageable stress - Monitor closely"
        else:
            return "Healthy balance - Good workload"
    
    def calculate_burnout_score(self):
        """
        Calculate burnout score (0-100) automatically based on assigned tasks
        Formula: burnout_score = (priority_score + deadline_pressure + workload_factor + pending_factor) / 4
        
        No manual input required - fully automatic calculation from task data.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Get all assigned tasks
        all_tasks = self.tasks.all()
        
        if not all_tasks.exists():
            return 10  # Minimal score if no tasks
        
        # Get active tasks (pending or in_progress)
        active_tasks = all_tasks.filter(status__in=['pending', 'in_progress'])
        
        # 1️⃣ PRIORITY SCORE (0-100)
        # Average priority across all assigned tasks
        priority_score = self._calculate_priority_score(all_tasks)
        
        # 2️⃣ DEADLINE PRESSURE (0-100)
        # Check clustering of high-priority deadlines
        deadline_pressure = self._calculate_deadline_pressure(active_tasks)
        
        # 3️⃣ WORKLOAD FACTOR (0-100)
        # Based on number of active tasks
        workload_factor = self._calculate_workload_factor(active_tasks)
        
        # 4️⃣ PENDING FACTOR (0-100)
        # Percentage of pending tasks
        pending_factor = self._calculate_pending_factor(all_tasks)
        
        # Final burnout score (average of all factors)
        burnout_score = (priority_score + deadline_pressure + workload_factor + pending_factor) / 4
        
        return min(int(burnout_score), 100)
    
    def _calculate_priority_score(self, tasks):
        """
        Calculate priority score based on task priorities
        High → 100, Medium → 60, Low → 30
        Returns average across all tasks
        """
        if not tasks.exists():
            return 10
        
        priority_values = {
            'high': 100,
            'medium': 60,
            'low': 30
        }
        
        total_priority = sum(priority_values.get(task.priority, 30) for task in tasks)
        return total_priority / tasks.count()
    
    def _calculate_deadline_pressure(self, active_tasks):
        """
        Calculate deadline pressure based on clustering of high-priority tasks
        - 2+ high-priority tasks within 20 days → 100 (high pressure)
        - Deadlines 20-40 days apart → 60 (medium pressure)
        - Otherwise → 30 (low pressure)
        """
        from django.utils import timezone
        
        if not active_tasks.exists():
            return 30
        
        now = timezone.now().date()
        
        # Get high-priority tasks with their deadlines
        high_priority_tasks = active_tasks.filter(priority='high')
        
        if high_priority_tasks.count() < 2:
            # Check if any task has near deadline
            for task in active_tasks:
                days_until = (task.due_date - now).days
                if days_until <= 20:
                    return 60  # Medium pressure
            return 30  # Low pressure
        
        # Check clustering of high-priority deadlines
        high_priority_deadlines = sorted([task.due_date for task in high_priority_tasks])
        
        # Check if 2+ high-priority tasks are within 20 days of each other
        for i in range(len(high_priority_deadlines) - 1):
            days_apart = (high_priority_deadlines[i + 1] - high_priority_deadlines[i]).days
            
            # Also check how far from now
            days_from_now = (high_priority_deadlines[i] - now).days
            
            if days_apart <= 20 and days_from_now <= 20:
                return 100  # High pressure - multiple high-priority tasks close together
        
        # Check if deadlines are 20-40 days apart
        for i in range(len(high_priority_deadlines) - 1):
            days_apart = (high_priority_deadlines[i + 1] - high_priority_deadlines[i]).days
            if 20 <= days_apart <= 40:
                return 60  # Medium pressure
        
        return 30  # Low pressure - deadlines well-spaced
    
    def _calculate_workload_factor(self, active_tasks):
        """
        Calculate workload factor based on number of active tasks
        - >5 tasks → 100
        - 3-5 tasks → 70
        - 1-2 tasks → 40
        - 0 tasks → 10
        """
        count = active_tasks.count()
        
        if count > 5:
            return 100
        elif count >= 3:
            return 70
        elif count >= 1:
            return 40
        else:
            return 10
    
    def _calculate_pending_factor(self, all_tasks):
        """
        Calculate pending factor as percentage of pending tasks
        pending_factor = (pending_tasks / total_tasks) * 100
        """
        if not all_tasks.exists():
            return 10
        
        total_tasks = all_tasks.count()
        pending_tasks = all_tasks.filter(status='pending').count()
        
        if total_tasks == 0:
            return 10
        
        return (pending_tasks / total_tasks) * 100


class Task(models.Model):
    """Task model for tracking work items"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks_created'
    )
    
    def __str__(self):
        return f"{self.title} - {self.assigned_to.user.username}"
    
    @property
    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.status != 'completed'
    
    class Meta:
        ordering = ['-created_at']


class MoodCheckin(models.Model):
    """Mood check-in model for tracking employee well-being"""
    MOOD_CHOICES = [
        ('happy', 'Happy'),
        ('neutral', 'Neutral'),
        ('stressed', 'Stressed'),
        ('burnout', 'Burnout'),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='mood_checkins'
    )
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='mood_checkins')
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES)
    notes = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.employee.user.username} - {self.mood} - {self.timestamp.date()}"
    
    class Meta:
        ordering = ['-timestamp']


class InsightReport(models.Model):
    """AI-generated insight reports"""
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='reports')
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    summary_text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    report_type = models.CharField(
        max_length=50,
        choices=[
            ('workload', 'Workload Summary'),
            ('burnout', 'Burnout Analysis'),
            ('performance', 'Performance Report'),
            ('productivity', 'Productivity Analysis'),
            ('team_balance', 'Team Balance Report'),
        ],
        default='workload'
    )
    # Enhanced report fields
    productivity_score = models.FloatField(default=0.0)
    burnout_prediction = models.TextField(blank=True, null=True)
    team_balance_data = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.team.team_name} - {self.report_type} - {self.created_at.date()}"
    
    class Meta:
        ordering = ['-created_at']


class Message(models.Model):
    """Real-time chat messages"""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    
    # For direct messages
    recipient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_messages',
        null=True,
        blank=True
    )
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"
    
    class Meta:
        ordering = ['timestamp']


class Announcement(models.Model):
    """Team announcements"""
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='announcements')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_pinned = models.BooleanField(default=False)
    
    ANNOUNCEMENT_TYPES = [
        ('general', 'General'),
        ('important', 'Important'),
        ('motivational', 'Motivational'),
        ('update', 'Update'),
    ]
    announcement_type = models.CharField(max_length=20, choices=ANNOUNCEMENT_TYPES, default='general')
    
    def __str__(self):
        return f"{self.team.team_name} - {self.title}"
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']


class BurnoutAlert(models.Model):
    """Automated burnout alerts for team leads"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='burnout_alerts')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='burnout_alerts')
    team_lead = models.ForeignKey(TeamLead, on_delete=models.CASCADE, related_name='received_alerts')
    alert_message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='medium')
    
    def __str__(self):
        return f"Alert: {self.employee.user.username} - {self.severity}"
    
    class Meta:
        ordering = ['-created_at']


class CalendarSync(models.Model):
    """Calendar synchronization settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='calendar_sync')
    
    PROVIDER_CHOICES = [
        ('google', 'Google Calendar'),
        ('outlook', 'Microsoft Outlook'),
    ]
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    
    # OAuth tokens (encrypted in production)
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    token_expiry = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    last_synced = models.DateTimeField(null=True, blank=True)
    sync_enabled = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.provider}"
    
    class Meta:
        verbose_name = 'Calendar Sync'
        verbose_name_plural = 'Calendar Syncs'


class TaskPrioritySuggestion(models.Model):
    """AI-generated task priority suggestions"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='priority_suggestions')
    suggested_priority = models.CharField(max_length=20, choices=Task.PRIORITY_CHOICES)
    current_priority = models.CharField(max_length=20)
    reason = models.TextField()
    confidence_score = models.FloatField(default=0.0)  # 0.0 to 1.0
    created_at = models.DateTimeField(default=timezone.now)
    is_applied = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Suggestion for {self.task.title}: {self.suggested_priority}"
    
    class Meta:
        ordering = ['-created_at']


class UserPreference(models.Model):
    """User preferences including theme"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    THEME_CHOICES = [
        ('light', 'Light Mode'),
        ('dark', 'Dark Mode'),
    ]
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    burnout_alerts = models.BooleanField(default=True)
    task_reminders = models.BooleanField(default=True)
    chat_notifications = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username} - Preferences"
