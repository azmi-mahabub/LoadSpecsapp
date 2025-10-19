from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Team, TeamLead, Employee, Task, MoodCheckin, InsightReport,
    Message, Announcement, BurnoutAlert, CalendarSync, TaskPrioritySuggestion, UserPreference
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'is_employee', 'is_team_lead', 'joined_date']
    list_filter = ['is_employee', 'is_team_lead', 'is_staff']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role Information', {'fields': ('is_employee', 'is_team_lead', 'bio', 'profile_picture')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('is_employee', 'is_team_lead')}),
    )


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['team_name', 'created_by', 'created_at', 'join_code', 'member_count']
    list_filter = ['created_at']
    search_fields = ['team_name', 'join_code']
    readonly_fields = ['join_code', 'created_at']


@admin.register(TeamLead)
class TeamLeadAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_teams']
    
    def get_teams(self, obj):
        return ", ".join([team.team_name for team in obj.teams.all()])
    get_teams.short_description = 'Teams'


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['user', 'team', 'assigned_tasks', 'completed_tasks']
    list_filter = ['team']
    search_fields = ['user__username', 'user__email']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'assigned_to', 'team', 'status', 'priority', 'due_date', 'created_at']
    list_filter = ['status', 'priority', 'team', 'due_date']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MoodCheckin)
class MoodCheckinAdmin(admin.ModelAdmin):
    list_display = ['employee', 'team', 'mood', 'timestamp']
    list_filter = ['mood', 'team', 'timestamp']
    search_fields = ['employee__user__username', 'notes']
    readonly_fields = ['timestamp']


@admin.register(InsightReport)
class InsightReportAdmin(admin.ModelAdmin):
    list_display = ['team', 'report_type', 'generated_by', 'created_at']
    list_filter = ['report_type', 'team', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'team', 'task', 'timestamp', 'is_read']
    list_filter = ['is_read', 'timestamp', 'team']
    search_fields = ['sender__username', 'recipient__username', 'content']
    readonly_fields = ['timestamp']


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'team', 'created_by', 'announcement_type', 'is_pinned', 'created_at']
    list_filter = ['announcement_type', 'is_pinned', 'team', 'created_at']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at']


@admin.register(BurnoutAlert)
class BurnoutAlertAdmin(admin.ModelAdmin):
    list_display = ['employee', 'team', 'severity', 'is_acknowledged', 'created_at']
    list_filter = ['severity', 'is_acknowledged', 'team', 'created_at']
    readonly_fields = ['created_at']


@admin.register(CalendarSync)
class CalendarSyncAdmin(admin.ModelAdmin):
    list_display = ['user', 'provider', 'is_active', 'sync_enabled', 'last_synced']
    list_filter = ['provider', 'is_active', 'sync_enabled']
    readonly_fields = ['last_synced']


@admin.register(TaskPrioritySuggestion)
class TaskPrioritySuggestionAdmin(admin.ModelAdmin):
    list_display = ['task', 'current_priority', 'suggested_priority', 'confidence_score', 'is_applied', 'created_at']
    list_filter = ['suggested_priority', 'is_applied', 'created_at']
    readonly_fields = ['created_at']


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'theme', 'email_notifications', 'burnout_alerts', 'task_reminders', 'chat_notifications']
    list_filter = ['theme', 'email_notifications']
