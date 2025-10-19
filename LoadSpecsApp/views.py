from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from datetime import timedelta, datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import json
from .models import (
    User, Team, TeamLead, Employee, Task, MoodCheckin, InsightReport,
    Message, Announcement, BurnoutAlert, CalendarSync, TaskPrioritySuggestion, UserPreference
)
from .forms import (
    SignUpForm, LoginForm, ProfileUpdateForm, TeamCreateForm,
    JoinTeamForm, TaskCreateForm, TaskUpdateForm, MoodCheckinForm
)


def signup_view(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Send welcome email
            send_welcome_email(user)
            
            login(request, user)
            messages.success(request, f'Welcome to LoadSpecs, {user.first_name} {user.last_name}! Your account has been created successfully.')
            return redirect('home')
    else:
        form = SignUpForm()
    
    return render(request, 'LoadSpecsHTML/registration/signup.html', {'form': form})


def send_welcome_email(user):
    """Send welcome email to new users"""
    subject = f'Welcome to LoadSpecs, {user.first_name}!'
    message = f"""
Hello {user.first_name} {user.last_name},

Welcome to LoadSpecs! 🎉

Your account has been successfully created.

Username: {user.username}
Email: {user.email}
Role: {user.role}

You can now:
- {"Create and manage teams" if user.is_team_lead else "Join teams and collaborate"}
- {"Assign tasks to team members" if user.is_team_lead else "View and update your tasks"}
- {"Monitor team performance and burnout" if user.is_team_lead else "Submit mood check-ins"}
- Track progress and generate reports

Get started by logging in at: http://127.0.0.1:8000

If you have any questions, feel free to reach out.

Best regards,
The LoadSpecs Team
    """
    
    try:
        send_mail(
            subject,
            message,
            'noreply@loadspecs.com',
            [user.email],
            fail_silently=True,
        )
    except Exception as e:
        # Log error but don't fail registration
        print(f"Failed to send welcome email: {e}")


def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('home')
    else:
        form = LoginForm()
    
    return render(request, 'LoadSpecsHTML/registration/login.html', {'form': form})


@login_required
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
def home_view(request):
    """Home/Dashboard view with search functionality"""
    user = request.user
    search_query = request.GET.get('search', '').strip()
    
    context = {
        'user': user,
        'search_query': search_query,
    }
    
    # Handle search
    if search_query:
        # Search for users, teams, and tasks
        users_results = User.objects.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        ).exclude(id=user.id)[:10]
        
        teams_results = Team.objects.filter(
            Q(team_name__icontains=search_query) |
            Q(description__icontains=search_query)
        )[:10]
        
        tasks_results = Task.objects.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )[:10]
        
        context['search_results'] = {
            'users': users_results,
            'teams': teams_results,
            'tasks': tasks_results,
            'query': search_query
        }
        
        return render(request, 'LoadSpecsHTML/search_results.html', context)
    
    if user.is_team_lead:
        # Team Lead Dashboard
        try:
            team_lead = user.teamlead_profile
            teams = team_lead.teams.all()
            context['teams'] = teams
            context['total_teams'] = teams.count()
            
            # Get all employees across all teams
            all_employees = Employee.objects.filter(team__in=teams)
            context['total_employees'] = all_employees.count()
            
            # Get recent mood check-ins
            recent_moods = MoodCheckin.objects.filter(team__in=teams).order_by('-timestamp')[:10]
            context['recent_moods'] = recent_moods
            
        except TeamLead.DoesNotExist:
            TeamLead.objects.create(user=user)
            context['teams'] = []
    
    elif user.is_employee:
        # Employee Dashboard
        try:
            employee = user.employee_profile
            context['employee'] = employee
            context['team'] = employee.team
            
            if employee.team:
                # Get employee's tasks
                tasks = employee.tasks.all()
                context['tasks'] = tasks
                context['pending_tasks'] = tasks.filter(status='pending')
                context['in_progress_tasks'] = tasks.filter(status='in_progress')
                context['completed_tasks'] = tasks.filter(status='completed')
                
                # Get recent mood check-ins
                recent_moods = employee.mood_checkins.all()[:5]
                context['recent_moods'] = recent_moods
        
        except Employee.DoesNotExist:
            Employee.objects.create(user=user)
    
    return render(request, 'LoadSpecsHTML/home.html', context)


@login_required
def team_view(request):
    """Team management view"""
    user = request.user
    context = {}
    
    if user.is_team_lead:
        try:
            team_lead = user.teamlead_profile
            teams = team_lead.teams.all()
            context['teams'] = teams
            context['is_team_lead'] = True
        except TeamLead.DoesNotExist:
            TeamLead.objects.create(user=user)
            context['teams'] = []
            context['is_team_lead'] = True
    
    elif user.is_employee:
        try:
            employee = user.employee_profile
            context['team'] = employee.team
            context['is_employee'] = True
            
            if employee.team:
                context['team_members'] = employee.team.employees.all()
        except Employee.DoesNotExist:
            Employee.objects.create(user=user)
    
    return render(request, 'LoadSpecsHTML/team.html', context)


@login_required
def create_team_view(request):
    """Create a new team"""
    if not request.user.is_team_lead:
        messages.error(request, 'Only team leads can create teams.')
        return redirect('home')
    
    if request.method == 'POST':
        form = TeamCreateForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.created_by = request.user
            team.save()
            
            # Add team to team lead's teams
            team_lead = request.user.teamlead_profile
            team_lead.teams.add(team)
            
            messages.success(request, f'Team "{team.team_name}" created successfully! Join Code: {team.join_code}')
            return redirect('team')
    else:
        form = TeamCreateForm()
    
    return render(request, 'LoadSpecsHTML/create_team.html', {'form': form})


@login_required
def join_team_view(request):
    """Employee joins a team"""
    if not request.user.is_employee:
        messages.error(request, 'Only employees can join teams.')
        return redirect('home')
    
    if request.method == 'POST':
        form = JoinTeamForm(request.POST)
        if form.is_valid():
            join_code = form.cleaned_data['join_code']
            try:
                team = Team.objects.get(join_code=join_code)
                employee = request.user.employee_profile
                employee.team = team
                employee.save()
                
                messages.success(request, f'You have joined team "{team.team_name}"!')
                return redirect('team')
            except Team.DoesNotExist:
                messages.error(request, 'Invalid join code.')
    else:
        form = JoinTeamForm()
    
    return render(request, 'LoadSpecsHTML/join_team.html', {'form': form})


@login_required
def tasks_view(request):
    """Tasks view"""
    user = request.user
    context = {}
    
    if user.is_team_lead:
        try:
            team_lead = user.teamlead_profile
            teams = team_lead.teams.all()
            
            # Get all tasks from all teams
            all_tasks = Task.objects.filter(team__in=teams)
            context['tasks'] = all_tasks
            context['is_team_lead'] = True
            context['teams'] = teams
            
            # Group tasks by employee
            employees_with_tasks = []
            for team in teams:
                for employee in team.employees.all():
                    employee_tasks = employee.tasks.all()
                    if employee_tasks:
                        employees_with_tasks.append({
                            'employee': employee,
                            'tasks': employee_tasks,
                            'team': team
                        })
            
            context['employees_with_tasks'] = employees_with_tasks
            
        except TeamLead.DoesNotExist:
            TeamLead.objects.create(user=user)
    
    elif user.is_employee:
        try:
            employee = user.employee_profile
            tasks = employee.tasks.all()
            context['tasks'] = tasks
            context['is_employee'] = True
            context['employee'] = employee
        except Employee.DoesNotExist:
            Employee.objects.create(user=user)
    
    return render(request, 'LoadSpecsHTML/tasks.html', context)


@login_required
def create_task_view(request):
    """Create a new task"""
    if not request.user.is_team_lead:
        messages.error(request, 'Only team leads can create tasks.')
        return redirect('tasks')
    
    team_lead = request.user.teamlead_profile
    teams = team_lead.teams.all()
    
    if request.method == 'POST':
        form = TaskCreateForm(request.POST)
        
        # Filter form's assigned_to field to only show employees from team lead's teams
        form.fields['assigned_to'].queryset = Employee.objects.filter(team__in=teams)
        
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.team = task.assigned_to.team
            task.save()
            
            messages.success(request, f'Task "{task.title}" created successfully!')
            return redirect('tasks')
    else:
        form = TaskCreateForm()
        form.fields['assigned_to'].queryset = Employee.objects.filter(team__in=teams)
    
    return render(request, 'LoadSpecsHTML/create_task.html', {'form': form})


@login_required
def update_task_view(request, task_id):
    """Update/Edit task - Team leads can edit all fields, employees can only update status"""
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions
    if request.user.is_employee and task.assigned_to.user != request.user:
        messages.error(request, 'You can only update your own tasks.')
        return redirect('tasks')
    
    if not request.user.is_team_lead and not request.user.is_employee:
        messages.error(request, 'You do not have permission to edit tasks.')
        return redirect('tasks')
    
    if request.method == 'POST':
        if request.user.is_team_lead:
            # Team leads can edit everything using TaskCreateForm
            form = TaskCreateForm(request.POST, instance=task)
            if form.is_valid():
                form.save()
                messages.success(request, 'Task updated successfully!')
                return redirect('tasks')
        else:
            # Employees can only update status
            form = TaskUpdateForm(request.POST, instance=task)
            if form.is_valid():
                form.save()
                messages.success(request, 'Task status updated successfully!')
                return redirect('tasks')
    else:
        if request.user.is_team_lead:
            # Team leads see full edit form
            form = TaskCreateForm(instance=task)
            # Set queryset for assigned_to field
            team_lead = request.user.teamlead_profile
            teams = team_lead.teams.all()
            form.fields['assigned_to'].queryset = Employee.objects.filter(team__in=teams)
        else:
            # Employees see limited form
            form = TaskUpdateForm(instance=task)
    
    context = {
        'form': form,
        'task': task,
        'is_team_lead': request.user.is_team_lead
    }
    return render(request, 'LoadSpecsHTML/update_task.html', context)


@login_required
def delete_task_view(request, task_id):
    """Delete a task"""
    task = get_object_or_404(Task, id=task_id)
    
    if not request.user.is_team_lead:
        messages.error(request, 'Only team leads can delete tasks.')
        return redirect('tasks')
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully!')
        return redirect('tasks')
    
    return render(request, 'LoadSpecsHTML/delete_task.html', {'task': task})


@login_required
def mood_checkin_view(request):
    """Mood check-in for employees"""
    if not request.user.is_employee:
        messages.error(request, 'Only employees can submit mood check-ins.')
        return redirect('home')
    
    employee = request.user.employee_profile
    
    if not employee.team:
        messages.error(request, 'You must join a team before submitting mood check-ins.')
        return redirect('join_team')
    
    if request.method == 'POST':
        form = MoodCheckinForm(request.POST)
        if form.is_valid():
            mood_checkin = form.save(commit=False)
            mood_checkin.employee = employee
            mood_checkin.team = employee.team
            mood_checkin.save()
            
            messages.success(request, 'Mood check-in submitted successfully!')
            return redirect('home')
    else:
        form = MoodCheckinForm()
    
    return render(request, 'LoadSpecsHTML/mood_checkin.html', {'form': form})


@login_required
def reports_view(request):
    """Reports and analytics view"""
    user = request.user
    context = {}
    
    if user.is_team_lead:
        try:
            team_lead = user.teamlead_profile
            teams = team_lead.teams.all()
            context['teams'] = teams
            context['is_team_lead'] = True
            
            # Generate some basic analytics
            if teams.exists():
                # Total statistics
                total_employees = Employee.objects.filter(team__in=teams).count()
                total_tasks = Task.objects.filter(team__in=teams).count()
                completed_tasks = Task.objects.filter(team__in=teams, status='completed').count()
                pending_tasks = Task.objects.filter(team__in=teams, status='pending').count()
                
                context['total_employees'] = total_employees
                context['total_tasks'] = total_tasks
                context['completed_tasks'] = completed_tasks
                context['pending_tasks'] = pending_tasks
                
                # Mood statistics
                recent_moods = MoodCheckin.objects.filter(team__in=teams, timestamp__gte=timezone.now() - timedelta(days=30))
                mood_counts = {
                    'happy': recent_moods.filter(mood='happy').count(),
                    'neutral': recent_moods.filter(mood='neutral').count(),
                    'stressed': recent_moods.filter(mood='stressed').count(),
                    'burnout': recent_moods.filter(mood='burnout').count(),
                }
                context['mood_counts'] = mood_counts
                
                # Generate chart
                context['chart'] = generate_mood_chart(mood_counts)
                
                # Get recent reports
                recent_reports = InsightReport.objects.filter(team__in=teams)[:5]
                context['recent_reports'] = recent_reports
        
        except TeamLead.DoesNotExist:
            TeamLead.objects.create(user=user)
    
    elif user.is_employee:
        employee = user.employee_profile
        context['is_employee'] = True
        context['employee'] = employee
        
        if employee.team:
            # Get employee's personal statistics
            context['my_tasks'] = employee.tasks.count()
            context['my_completed'] = employee.tasks.filter(status='completed').count()
            context['my_pending'] = employee.tasks.filter(status='pending').count()
            
            # Get mood history
            recent_moods = employee.mood_checkins.all()[:7]
            context['recent_moods'] = recent_moods
    
    return render(request, 'LoadSpecsHTML/reports.html', context)


def generate_mood_chart(mood_counts):
    """Generate a simple mood distribution chart"""
    labels = list(mood_counts.keys())
    sizes = list(mood_counts.values())
    
    if sum(sizes) == 0:
        return None
    
    colors = ['#4CAF50', '#FFC107', '#FF9800', '#F44336']
    
    plt.figure(figsize=(8, 6))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title('Mood Distribution (Last 30 Days)')
    plt.axis('equal')
    
    # Convert plot to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    graphic = base64.b64encode(image_png).decode('utf-8')
    return graphic


@login_required
def generate_report_view(request):
    """Generate an insight report"""
    if not request.user.is_team_lead:
        messages.error(request, 'Only team leads can generate reports.')
        return redirect('reports')
    
    if request.method == 'POST':
        team_id = request.POST.get('team_id')
        report_type = request.POST.get('report_type')
        download_pdf = request.POST.get('download_pdf') == 'true'
        
        team = get_object_or_404(Team, id=team_id)
        
        # Generate summary based on type
        if report_type == 'workload':
            summary = generate_workload_summary(team)
        elif report_type == 'burnout':
            summary = generate_burnout_analysis(team)
        elif report_type == 'performance':
            summary = generate_performance_report(team)
        else:
            summary = "Report generated successfully."
        
        # Create report
        report = InsightReport.objects.create(
            team=team,
            generated_by=request.user,
            summary_text=summary,
            report_type=report_type
        )
        
        # If PDF download requested, generate and return PDF
        if download_pdf:
            return generate_report_pdf(report, team)
        
        messages.success(request, 'Report generated successfully!')
        return redirect('reports')
    
    return redirect('reports')


@login_required
def download_report_pdf(request, report_id):
    """Download existing report as PDF"""
    report = get_object_or_404(InsightReport, id=report_id)
    
    # Check permissions
    if request.user.is_team_lead:
        team_lead = request.user.teamlead_profile
        if report.team not in team_lead.teams.all():
            messages.error(request, 'You do not have permission to download this report.')
            return redirect('reports')
    else:
        messages.error(request, 'Only team leads can download reports.')
        return redirect('reports')
    
    return generate_report_pdf(report, report.team)


def generate_report_pdf(report, team):
    """Generate PDF for a report"""
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="LoadSpecs_Report_{team.team_name}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    
    # Create the PDF object
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#003135'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#00bcd4'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    elements.append(Paragraph(f"LoadSpecs Report - {team.team_name}", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Report Info
    elements.append(Paragraph(f"<b>Report Type:</b> {report.report_type.title()}", styles['Normal']))
    elements.append(Paragraph(f"<b>Generated By:</b> {report.generated_by.full_name}", styles['Normal']))
    elements.append(Paragraph(f"<b>Generated On:</b> {report.created_at.strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary
    elements.append(Paragraph("Summary", heading_style))
    for line in report.summary_text.split('\n'):
        if line.strip():
            elements.append(Paragraph(line.strip(), styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Team Statistics
    elements.append(Paragraph("Team Statistics", heading_style))
    
    # Tasks Table
    tasks = Task.objects.filter(team=team)
    if tasks.exists():
        elements.append(Paragraph("<b>Tasks Overview:</b>", styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        
        task_data = [['Task Title', 'Assigned To', 'Status', 'Priority', 'Due Date']]
        for task in tasks[:10]:  # Limit to 10 tasks
            task_data.append([
                task.title[:30],
                task.assigned_to.user.username,
                task.status.title(),
                task.priority.title(),
                task.due_date.strftime('%Y-%m-%d')
            ])
        
        task_table = Table(task_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1*inch, 1*inch])
        task_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003135')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(task_table)
        elements.append(Spacer(1, 0.3*inch))
    
    # Mood Statistics
    moods = MoodCheckin.objects.filter(team=team, timestamp__gte=timezone.now() - timedelta(days=30))
    if moods.exists():
        elements.append(Paragraph("<b>Recent Mood Check-ins (Last 30 Days):</b>", styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        
        mood_counts = {
            'Happy': moods.filter(mood='happy').count(),
            'Neutral': moods.filter(mood='neutral').count(),
            'Stressed': moods.filter(mood='stressed').count(),
            'Burnout': moods.filter(mood='burnout').count(),
        }
        
        mood_data = [['Mood', 'Count']]
        for mood, count in mood_counts.items():
            mood_data.append([mood, str(count)])
        
        mood_table = Table(mood_data, colWidths=[3*inch, 2*inch])
        mood_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00bcd4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(mood_table)
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("___", styles['Normal']))
    elements.append(Paragraph("Generated by LoadSpecs - Workload Management System", styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    return response


def generate_workload_summary(team):
    """Generate workload summary for a team"""
    total_tasks = team.tasks.count()
    completed = team.completed_tasks
    pending = team.pending_tasks
    in_progress = team.in_progress_tasks
    
    summary = f"""
    Workload Summary for {team.team_name}:
    
    Total Tasks: {total_tasks}
    Completed: {completed} ({(completed/total_tasks*100) if total_tasks > 0 else 0:.1f}%)
    In Progress: {in_progress}
    Pending: {pending}
    
    Team Members: {team.member_count}
    Average Tasks per Member: {total_tasks/team.member_count if team.member_count > 0 else 0:.1f}
    
    Status: {'On Track' if completed/total_tasks > 0.7 else 'Needs Attention' if total_tasks > 0 else 'No Tasks'}
    """
    
    return summary


def generate_burnout_analysis(team):
    """Generate burnout analysis for a team"""
    recent_moods = MoodCheckin.objects.filter(
        team=team,
        timestamp__gte=timezone.now() - timedelta(days=30)
    )
    
    total_checkins = recent_moods.count()
    burnout_count = recent_moods.filter(mood='burnout').count()
    stressed_count = recent_moods.filter(mood='stressed').count()
    
    risk_level = "Low"
    if burnout_count / total_checkins > 0.3 if total_checkins > 0 else False:
        risk_level = "High"
    elif stressed_count / total_checkins > 0.5 if total_checkins > 0 else False:
        risk_level = "Medium"
    
    summary = f"""
    Burnout Analysis for {team.team_name}:
    
    Total Mood Check-ins (30 days): {total_checkins}
    Burnout Reports: {burnout_count}
    Stressed Reports: {stressed_count}
    
    Risk Level: {risk_level}
    
    Recommendation: {'Immediate attention needed. Consider workload redistribution.' if risk_level == 'High' else 'Monitor team well-being regularly.' if risk_level == 'Medium' else 'Team morale is healthy.'}
    """
    
    return summary


def generate_performance_report(team):
    """Generate performance report for a team"""
    employees = team.employees.all()
    
    summary = f"Performance Report for {team.team_name}:\n\n"
    
    for emp in employees:
        total = emp.assigned_tasks
        completed = emp.completed_tasks
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        summary += f"{emp.user.username}: {completed}/{total} tasks completed ({completion_rate:.1f}%)\n"
    
    return summary


@login_required
def profile_view(request):
    """User profile view"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    context = {
        'form': form,
        'user': request.user
    }
    
    return render(request, 'LoadSpecsHTML/profile.html', context)


def password_reset_request(request):
    """Handle password reset request"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            
            # Generate token and UID
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset link
            current_site = get_current_site(request)
            reset_link = f"http://{current_site.domain}/password-reset-confirm/{uid}/{token}/"
            
            # Send email
            subject = "LoadSpecs - Password Reset Request"
            message = f"""
Hello {user.first_name or user.username},

You requested a password reset for your LoadSpecs account.

Click the link below to reset your password:
{reset_link}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
LoadSpecs Team
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    'noreply@loadspecs.com',
                    [email],
                    fail_silently=False,
                )
                
                # For development - print to console
                print("\n" + "="*60)
                print("PASSWORD RESET EMAIL")
                print("="*60)
                print(f"Subject: {subject}")
                print(f"To: {email}")
                print(f"Reset Link: {reset_link}")
                print("="*60 + "\n")
                
                messages.success(request, f'Password reset link has been sent to {email}! (Check your email or console in development mode)')
                return redirect('password_reset_done')
            except Exception as e:
                print(f"Email sending failed: {e}")
                messages.error(request, f'Failed to send email. Error: {str(e)}. Please check email configuration.')
                # Still show the link for development
                messages.info(request, f'Development Mode - Reset link: {reset_link}')
            
        except User.DoesNotExist:
            messages.error(request, 'No user found with that email address.')
    
    return render(request, 'LoadSpecsHTML/registration/password_reset.html')


def password_reset_done(request):
    """Password reset email sent confirmation"""
    return render(request, 'LoadSpecsHTML/registration/password_reset_done.html')


def password_reset_confirm(request, uidb64, token):
    """Handle password reset confirmation with token"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            if password1 and password1 == password2:
                user.set_password(password1)
                user.save()
                messages.success(request, 'Your password has been reset successfully! You can now log in.')
                return redirect('password_reset_complete')
            else:
                messages.error(request, 'Passwords do not match.')
        
        return render(request, 'LoadSpecsHTML/registration/password_reset_confirm.html', {
            'validlink': True,
            'uidb64': uidb64,
            'token': token
        })
    else:
        return render(request, 'LoadSpecsHTML/registration/password_reset_confirm.html', {
            'validlink': False
        })


def password_reset_complete(request):
    """Password reset complete confirmation"""
    return render(request, 'LoadSpecsHTML/registration/password_reset_complete.html')


@require_http_methods(["GET"])
def check_username(request):
    """Check if username is available (AJAX)"""
    username = request.GET.get('username', '')
    
    if not username:
        return JsonResponse({'available': False, 'message': 'Username is required'})
    
    if len(username) < 3:
        return JsonResponse({'available': False, 'message': 'Username must be at least 3 characters'})
    
    exists = User.objects.filter(username=username).exists()
    
    if exists:
        return JsonResponse({
            'available': False,
            'message': 'This username is already taken'
        })
    else:
        return JsonResponse({
            'available': True,
            'message': 'Username is available!'
        })


@require_http_methods(["GET"])
def check_email(request):
    """Check if email is already registered (AJAX)"""
    email = request.GET.get('email', '')
    
    if not email:
        return JsonResponse({'available': False, 'message': 'Email is required'})
    
    exists = User.objects.filter(email=email).exists()
    
    if exists:
        return JsonResponse({
            'available': False,
            'message': 'An account with this email already exists'
        })
    else:
        return JsonResponse({
            'available': True,
            'message': 'Email is available!'
        })


# ============================================
# NEW FEATURE VIEWS - All 9 Features
# ============================================

@login_required
def calendar_view(request):
    """Calendar view showing all tasks with deadlines"""
    user = request.user
    context = {'user': user}
    
    if user.is_employee:
        employee = user.employee_profile
        tasks = employee.tasks.all()
        context['tasks'] = tasks
    elif user.is_team_lead:
        team_lead = user.teamlead_profile
        teams = team_lead.teams.all()
        tasks = Task.objects.filter(team__in=teams)
        context['tasks'] = tasks
        context['teams'] = teams
    
    # Check if calendar sync is set up
    try:
        calendar_sync = CalendarSync.objects.get(user=user)
        context['calendar_sync'] = calendar_sync
    except CalendarSync.DoesNotExist:
        context['calendar_sync'] = None
    
    return render(request, 'LoadSpecsHTML/calendar.html', context)


@login_required
def calendar_sync_setup(request):
    """Set up calendar synchronization"""
    if request.method == 'POST':
        provider = request.POST.get('provider')
        
        calendar_sync, created = CalendarSync.objects.get_or_create(
            user=request.user,
            defaults={'provider': provider}
        )
        
        if not created:
            calendar_sync.provider = provider
            calendar_sync.save()
        
        messages.success(request, f'{provider.title()} Calendar integration configured!')
        return redirect('calendar')
    
    return render(request, 'LoadSpecsHTML/calendar_sync_setup.html')


@login_required
def google_calendar_callback(request):
    """Handle Google Calendar OAuth callback"""
    messages.success(request, 'Google Calendar connected successfully!')
    return redirect('calendar')


@login_required
def outlook_calendar_callback(request):
    """Handle Outlook Calendar OAuth callback"""
    messages.success(request, 'Outlook Calendar connected successfully!')
    return redirect('calendar')


# ============================================
# FEATURE 2: INTERNAL MESSAGING / CHAT
# ============================================

@login_required
def chat_view(request):
    """Main chat interface"""
    user = request.user
    context = {'user': user}
    
    if user.is_employee:
        employee = user.employee_profile
        if employee.team:
            context['teams'] = [employee.team]
    elif user.is_team_lead:
        team_lead = user.teamlead_profile
        context['teams'] = team_lead.teams.all()
    
    recent_messages = Message.objects.filter(
        Q(sender=user) | Q(recipient=user)
    ).order_by('-timestamp')[:50]
    
    context['recent_messages'] = recent_messages
    
    return render(request, 'LoadSpecsHTML/chat.html', context)


@login_required
def team_chat_view(request, team_id):
    """Team chat room"""
    team = get_object_or_404(Team, id=team_id)
    user = request.user
    
    is_member = False
    if user.is_employee:
        is_member = user.employee_profile.team == team
    elif user.is_team_lead:
        is_member = team in user.teamlead_profile.teams.all()
    
    if not is_member:
        messages.error(request, 'You do not have access to this team chat.')
        return redirect('chat')
    
    messages_list = Message.objects.filter(team=team).order_by('timestamp')
    
    context = {
        'team': team,
        'messages': messages_list,
        'user': user
    }
    
    return render(request, 'LoadSpecsHTML/team_chat.html', context)


@login_required
def task_chat_view(request, task_id):
    """Task-based discussion room"""
    task = get_object_or_404(Task, id=task_id)
    user = request.user
    
    has_access = False
    if user.is_employee:
        has_access = task.assigned_to.user == user
    elif user.is_team_lead:
        has_access = task.team in user.teamlead_profile.teams.all()
    
    if not has_access:
        messages.error(request, 'You do not have access to this task discussion.')
        return redirect('chat')
    
    messages_list = Message.objects.filter(task=task).order_by('timestamp')
    
    context = {
        'task': task,
        'messages': messages_list,
        'user': user
    }
    
    return render(request, 'LoadSpecsHTML/task_chat.html', context)


@login_required
def direct_chat_view(request, user_id):
    """Direct messaging between users"""
    other_user = get_object_or_404(User, id=user_id)
    user = request.user
    
    messages_list = Message.objects.filter(
        (Q(sender=user) & Q(recipient=other_user)) |
        (Q(sender=other_user) & Q(recipient=user))
    ).order_by('timestamp')
    
    context = {
        'other_user': other_user,
        'messages': messages_list,
        'user': user
    }
    
    return render(request, 'LoadSpecsHTML/direct_chat.html', context)


@login_required
@require_http_methods(["POST"])
def send_message_api(request):
    """API endpoint to send a message"""
    try:
        data = json.loads(request.body)
        message_type = data.get('type')
        content = data.get('content')
        target_id = data.get('target_id')
        
        if not content:
            return JsonResponse({'success': False, 'error': 'Message content is required'})
        
        message = Message.objects.create(sender=request.user, content=content)
        
        if message_type == 'team':
            team = Team.objects.get(id=target_id)
            message.team = team
        elif message_type == 'task':
            task = Task.objects.get(id=target_id)
            message.task = task
        elif message_type == 'direct':
            recipient = User.objects.get(id=target_id)
            message.recipient = recipient
        
        message.save()
        
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'timestamp': message.timestamp.isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def get_messages_api(request, chat_id):
    """API endpoint to get messages"""
    chat_type = request.GET.get('type')
    
    if chat_type == 'team':
        messages_list = Message.objects.filter(team_id=chat_id)
    elif chat_type == 'task':
        messages_list = Message.objects.filter(task_id=chat_id)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid chat type'})
    
    messages_data = [{
        'id': msg.id,
        'sender': msg.sender.username,
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat()
    } for msg in messages_list.order_by('timestamp')]
    
    return JsonResponse({'success': True, 'messages': messages_data})


# ============================================
# FEATURE 3: TEAM ANNOUNCEMENTS
# ============================================

@login_required
def announcements_view(request):
    """View all announcements"""
    user = request.user
    context = {'user': user}
    
    if user.is_employee:
        employee = user.employee_profile
        if employee.team:
            announcements = Announcement.objects.filter(team=employee.team).order_by('-created_at')
            context['announcements'] = announcements
            context['team'] = employee.team
    elif user.is_team_lead:
        team_lead = user.teamlead_profile
        teams = team_lead.teams.all()
        announcements = Announcement.objects.filter(team__in=teams).order_by('-created_at')
        context['announcements'] = announcements
        context['teams'] = teams
    
    return render(request, 'LoadSpecsHTML/announcements.html', context)


@login_required
def create_announcement_view(request):
    """Create a new announcement (team leads only)"""
    if not request.user.is_team_lead:
        messages.error(request, 'Only team leads can create announcements.')
        return redirect('announcements')
    
    team_lead = request.user.teamlead_profile
    teams = team_lead.teams.all()
    
    if request.method == 'POST':
        team_id = request.POST.get('team')
        title = request.POST.get('title')
        content = request.POST.get('content')
        announcement_type = request.POST.get('announcement_type', 'general')
        is_pinned = request.POST.get('is_pinned') == 'on'
        
        team = get_object_or_404(Team, id=team_id)
        
        if team not in teams:
            messages.error(request, 'You can only post to your own teams.')
            return redirect('announcements')
        
        Announcement.objects.create(
            team=team,
            created_by=request.user,
            title=title,
            content=content,
            announcement_type=announcement_type,
            is_pinned=is_pinned
        )
        
        messages.success(request, 'Announcement posted successfully!')
        return redirect('announcements')
    
    context = {'teams': teams}
    return render(request, 'LoadSpecsHTML/create_announcement.html', context)


@login_required
def delete_announcement_view(request, announcement_id):
    """Delete an announcement"""
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    if announcement.created_by != request.user:
        messages.error(request, 'You can only delete your own announcements.')
        return redirect('announcements')
    
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, 'Announcement deleted successfully!')
    
    return redirect('announcements')


@login_required
def pin_announcement_view(request, announcement_id):
    """Pin/unpin an announcement"""
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    if announcement.created_by != request.user:
        messages.error(request, 'You can only pin your own announcements.')
        return redirect('announcements')
    
    announcement.is_pinned = not announcement.is_pinned
    announcement.save()
    
    return redirect('announcements')


# ============================================
# FEATURE 4: AI TASK PRIORITIZER
# ============================================

@login_required
def analyze_task_priority_view(request):
    """View AI task priority suggestions"""
    user = request.user
    context = {'user': user}
    
    if user.is_employee:
        employee = user.employee_profile
        tasks = employee.tasks.filter(status__in=['pending', 'in_progress'])
        suggestions = TaskPrioritySuggestion.objects.filter(
            task__assigned_to=employee,
            is_applied=False
        )
        context['tasks'] = tasks
        context['suggestions'] = suggestions
    
    elif user.is_team_lead:
        team_lead = user.teamlead_profile
        teams = team_lead.teams.all()
        tasks = Task.objects.filter(team__in=teams, status__in=['pending', 'in_progress'])
        suggestions = TaskPrioritySuggestion.objects.filter(
            task__team__in=teams,
            is_applied=False
        )
        context['tasks'] = tasks
        context['suggestions'] = suggestions
        context['teams'] = teams
    
    return render(request, 'LoadSpecsHTML/task_priority_analyzer.html', context)


@login_required
def apply_priority_suggestion(request, suggestion_id):
    """Apply an AI priority suggestion"""
    suggestion = get_object_or_404(TaskPrioritySuggestion, id=suggestion_id)
    task = suggestion.task
    
    has_permission = False
    if request.user.is_team_lead:
        has_permission = task.team in request.user.teamlead_profile.teams.all()
    elif request.user.is_employee:
        has_permission = task.assigned_to.user == request.user
    
    if not has_permission:
        messages.error(request, 'You do not have permission to modify this task.')
        return redirect('analyze_task_priority')
    
    task.priority = suggestion.suggested_priority
    task.save()
    
    suggestion.is_applied = True
    suggestion.save()
    
    messages.success(request, f'Task priority updated to {suggestion.suggested_priority.upper()}!')
    return redirect('analyze_task_priority')


# ============================================
# FEATURE 5 & 6: PERFORMANCE DASHBOARD
# ============================================

@login_required
def performance_dashboard_view(request):
    """Performance dashboard with charts and analytics"""
    user = request.user
    context = {'user': user}
    
    if user.is_team_lead:
        team_lead = user.teamlead_profile
        teams = team_lead.teams.all()
        context['teams'] = teams
        context['is_team_lead'] = True
        
        if teams.exists():
            total_tasks = Task.objects.filter(team__in=teams).count()
            completed_tasks = Task.objects.filter(team__in=teams, status='completed').count()
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            context['total_tasks'] = total_tasks
            context['completed_tasks'] = completed_tasks
            context['completion_rate'] = round(completion_rate, 1)
    
    elif user.is_employee:
        employee = user.employee_profile
        context['is_employee'] = True
        context['employee'] = employee
        
        if employee.team:
            total_tasks = employee.tasks.count()
            completed_tasks = employee.completed_tasks
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            context['total_tasks'] = total_tasks
            context['completed_tasks'] = completed_tasks
            context['completion_rate'] = round(completion_rate, 1)
    
    return render(request, 'LoadSpecsHTML/performance_dashboard.html', context)


@login_required
def get_productivity_data(request):
    """API endpoint for productivity chart data"""
    user = request.user
    
    if user.is_team_lead:
        team_lead = user.teamlead_profile
        teams = team_lead.teams.all()
        
        data = []
        for i in range(6, -1, -1):
            date = timezone.now().date() - timedelta(days=i)
            completed = Task.objects.filter(
                team__in=teams,
                status='completed',
                updated_at__date=date
            ).count()
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'completed': completed
            })
        
        return JsonResponse({'success': True, 'data': data})
    
    return JsonResponse({'success': False, 'error': 'Unauthorized'})


@login_required
def get_mood_trends_data(request):
    """API endpoint for mood trends chart data"""
    user = request.user
    
    if user.is_team_lead:
        team_lead = user.teamlead_profile
        teams = team_lead.teams.all()
        
        data = []
        for i in range(3, -1, -1):
            start_date = timezone.now().date() - timedelta(weeks=i+1)
            end_date = timezone.now().date() - timedelta(weeks=i)
            
            moods = MoodCheckin.objects.filter(
                team__in=teams,
                timestamp__date__gte=start_date,
                timestamp__date__lt=end_date
            )
            
            data.append({
                'week': f'Week {4-i}',
                'happy': moods.filter(mood='happy').count(),
                'neutral': moods.filter(mood='neutral').count(),
                'stressed': moods.filter(mood='stressed').count(),
                'burnout': moods.filter(mood='burnout').count()
            })
        
        return JsonResponse({'success': True, 'data': data})
    
    return JsonResponse({'success': False, 'error': 'Unauthorized'})


@login_required
def get_team_comparison_data(request):
    """API endpoint for team comparison chart data"""
    user = request.user
    
    if user.is_team_lead:
        team_lead = user.teamlead_profile
        teams = team_lead.teams.all()
        
        data = []
        for team in teams:
            total = team.total_tasks
            completed = team.completed_tasks
            completion_rate = (completed / total * 100) if total > 0 else 0
            
            data.append({
                'team': team.team_name,
                'total': total,
                'completed': completed,
                'completion_rate': round(completion_rate, 1)
            })
        
        return JsonResponse({'success': True, 'data': data})
    
    return JsonResponse({'success': False, 'error': 'Unauthorized'})


# ============================================
# FEATURE 7: ENHANCED PROFILES
# ============================================

@login_required
def edit_skills_view(request):
    """Edit employee skills and profile"""
    if not request.user.is_employee:
        messages.error(request, 'This feature is for employees only.')
        return redirect('profile')
    
    employee = request.user.employee_profile
    
    if request.method == 'POST':
        skills = request.POST.get('skills', '')
        experience_years = request.POST.get('experience_years', 0)
        interests = request.POST.get('interests', '')
        department = request.POST.get('department', '')
        job_title = request.POST.get('job_title', '')
        
        employee.skills = skills
        employee.experience_years = int(experience_years) if experience_years else 0
        employee.interests = interests
        employee.department = department
        employee.job_title = job_title
        employee.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    context = {'employee': employee}
    return render(request, 'LoadSpecsHTML/edit_skills.html', context)


@login_required
def search_employees_view(request):
    """Search and filter employees by skills"""
    if not request.user.is_team_lead:
        messages.error(request, 'This feature is for team leads only.')
        return redirect('home')
    
    team_lead = request.user.teamlead_profile
    teams = team_lead.teams.all()
    
    employees = Employee.objects.filter(team__in=teams)
    
    search_query = request.GET.get('q', '')
    if search_query:
        employees = employees.filter(
            Q(skills__icontains=search_query) |
            Q(interests__icontains=search_query) |
            Q(department__icontains=search_query) |
            Q(job_title__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    context = {
        'employees': employees,
        'search_query': search_query,
        'teams': teams
    }
    
    return render(request, 'LoadSpecsHTML/search_employees.html', context)


# ============================================
# FEATURE 8: AUTOMATED BURNOUT ALERTS
# ============================================

@login_required
def burnout_alerts_view(request):
    """View burnout alerts"""
    if not request.user.is_team_lead:
        messages.error(request, 'This feature is for team leads only.')
        return redirect('home')
    
    team_lead = request.user.teamlead_profile
    
    alerts = BurnoutAlert.objects.filter(team_lead=team_lead)
    unacknowledged_alerts = alerts.filter(is_acknowledged=False)
    acknowledged_alerts = alerts.filter(is_acknowledged=True)
    
    context = {
        'unacknowledged_alerts': unacknowledged_alerts,
        'acknowledged_alerts': acknowledged_alerts,
        'alert_count': unacknowledged_alerts.count()
    }
    
    return render(request, 'LoadSpecsHTML/burnout_alerts.html', context)


@login_required
def acknowledge_alert(request, alert_id):
    """Acknowledge a burnout alert"""
    alert = get_object_or_404(BurnoutAlert, id=alert_id)
    
    if alert.team_lead.user != request.user:
        messages.error(request, 'You can only acknowledge your own alerts.')
        return redirect('burnout_alerts')
    
    alert.is_acknowledged = True
    alert.acknowledged_at = timezone.now()
    alert.save()
    
    messages.success(request, 'Alert acknowledged.')
    return redirect('burnout_alerts')


# ============================================
# FEATURE 9: DARK MODE / THEME SWITCHER
# ============================================

@login_required
@require_http_methods(["POST"])
def toggle_theme(request):
    """Toggle between light and dark mode"""
    data = json.loads(request.body)
    theme = data.get('theme', 'light')
    
    preferences, created = UserPreference.objects.get_or_create(
        user=request.user,
        defaults={'theme': theme}
    )
    
    if not created:
        preferences.theme = theme
        preferences.save()
    
    return JsonResponse({
        'success': True,
        'theme': theme
    })
