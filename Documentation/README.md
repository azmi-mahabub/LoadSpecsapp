# LoadSpecs - AI-Driven Workload Dashboard

LoadSpecs is an AI-driven dashboard designed to help organizations detect workload bottlenecks, burnout risks, and team performance issues.

## Features
- User authentication with role-based access (Team Lead & Employee)
- Team management and member assignment
- Task tracking with priority and status management
- Daily mood check-ins for burnout detection
- Visual analytics and reports
- Beautiful, responsive UI

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. Create a superuser:
```bash
python manage.py createsuperuser
```

5. Run the development server:
```bash
python manage.py runserver
```

6. Access the application at: http://127.0.0.1:8000

## Default Login
- Create your account via the signup page
- Choose your role: Team Lead or Employee

## Technology Stack
- Backend: Django 4.2
- Frontend: HTML, CSS, Bootstrap
- Database: SQLite (default)
- Charts: Matplotlib

## Project Structure
```
LoadSpecs2/
├── LoadSpecs/          # Project settings
├── LoadSpecsApp/       # Main application
├── templates/          # HTML templates
├── static/            # Static files (CSS, images)
├── media/             # User uploads
└── manage.py          # Django management script
```
