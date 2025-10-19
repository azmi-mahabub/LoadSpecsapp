from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    
    # Password Reset
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset-complete/', views.password_reset_complete, name='password_reset_complete'),
    
    # Main views
    path('home/', views.home_view, name='home'),
    path('team/', views.team_view, name='team'),
    path('tasks/', views.tasks_view, name='tasks'),
    path('reports/', views.reports_view, name='reports'),
    path('profile/', views.profile_view, name='profile'),
    
    # Team management
    path('team/create/', views.create_team_view, name='create_team'),
    path('team/join/', views.join_team_view, name='join_team'),
    
    # Task management
    path('tasks/create/', views.create_task_view, name='create_task'),
    path('tasks/update/<int:task_id>/', views.update_task_view, name='update_task'),
    path('tasks/delete/<int:task_id>/', views.delete_task_view, name='delete_task'),
    
    # Mood check-in
    path('mood-checkin/', views.mood_checkin_view, name='mood_checkin'),
    
    # Reports
    path('reports/generate/', views.generate_report_view, name='generate_report'),
    path('reports/download/<int:report_id>/', views.download_report_pdf, name='download_report_pdf'),
    
    # AJAX Endpoints
    path('api/check-username/', views.check_username, name='check_username'),
    path('api/check-email/', views.check_email, name='check_email'),
    
    # NEW FEATURES - Calendar
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/sync/', views.calendar_sync_setup, name='calendar_sync_setup'),
    path('calendar/oauth2callback/', views.google_calendar_callback, name='google_calendar_callback'),
    path('calendar/outlook/callback/', views.outlook_calendar_callback, name='outlook_calendar_callback'),
    
    # NEW FEATURES - Chat & Messaging
    path('chat/', views.chat_view, name='chat'),
    path('chat/team/<int:team_id>/', views.team_chat_view, name='team_chat'),
    path('chat/task/<int:task_id>/', views.task_chat_view, name='task_chat'),
    path('chat/direct/<int:user_id>/', views.direct_chat_view, name='direct_chat'),
    path('api/messages/send/', views.send_message_api, name='send_message_api'),
    path('api/messages/<int:chat_id>/', views.get_messages_api, name='get_messages_api'),
    
    # NEW FEATURES - Announcements
    path('announcements/', views.announcements_view, name='announcements'),
    path('announcements/create/', views.create_announcement_view, name='create_announcement'),
    path('announcements/<int:announcement_id>/delete/', views.delete_announcement_view, name='delete_announcement'),
    path('announcements/<int:announcement_id>/pin/', views.pin_announcement_view, name='pin_announcement'),
    
    # NEW FEATURES - AI Task Prioritizer
    path('tasks/analyze-priority/', views.analyze_task_priority_view, name='analyze_task_priority'),
    path('tasks/apply-suggestion/<int:suggestion_id>/', views.apply_priority_suggestion, name='apply_priority_suggestion'),
    
    # NEW FEATURES - Performance Dashboard
    path('dashboard/', views.performance_dashboard_view, name='performance_dashboard'),
    path('api/dashboard/productivity/', views.get_productivity_data, name='get_productivity_data'),
    path('api/dashboard/mood-trends/', views.get_mood_trends_data, name='get_mood_trends_data'),
    path('api/dashboard/team-comparison/', views.get_team_comparison_data, name='get_team_comparison_data'),
    
    # NEW FEATURES - Burnout Alerts
    path('alerts/', views.burnout_alerts_view, name='burnout_alerts'),
    path('alerts/<int:alert_id>/acknowledge/', views.acknowledge_alert, name='acknowledge_alert'),
    
    # NEW FEATURES - Enhanced Profiles
    path('profile/edit-skills/', views.edit_skills_view, name='edit_skills'),
    path('team/search-employees/', views.search_employees_view, name='search_employees'),
    
    # NEW FEATURES - Theme Switcher
    path('api/toggle-theme/', views.toggle_theme, name='toggle_theme'),
]
