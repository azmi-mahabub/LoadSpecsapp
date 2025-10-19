# LoadSpecs Installation Guide

## Quick Setup (Windows)

### Option 1: Automated Setup
1. Double-click `setup.bat`
2. Wait for installation to complete
3. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
4. Run the server:
   ```bash
   python manage.py runserver
   ```

### Option 2: Manual Setup

1. **Create Virtual Environment**
   ```bash
   python -m venv venv
   ```

2. **Activate Virtual Environment**
   ```bash
   venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create Superuser (Admin Account)**
   ```bash
   python manage.py createsuperuser
   ```
   Follow the prompts to create your admin account.

6. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

7. **Access the Application**
   - Open browser: http://127.0.0.1:8000
   - Admin panel: http://127.0.0.1:8000/admin

## First Time Usage

### For Team Leads:
1. Sign up at http://127.0.0.1:8000/signup/
2. Select "Team Lead" as your role
3. After login, create a team
4. Share the team join code with employees
5. Start assigning tasks

### For Employees:
1. Sign up at http://127.0.0.1:8000/signup/
2. Select "Employee" as your role
3. Join a team using the join code from your team lead
4. View and update your assigned tasks
5. Submit daily mood check-ins

## Features Overview

### Team Lead Features:
- ✅ Create and manage multiple teams
- ✅ Assign tasks to team members
- ✅ Track team progress and workload
- ✅ Monitor employee mood and burnout risks
- ✅ Generate analytics reports
- ✅ View team performance metrics

### Employee Features:
- ✅ Join teams via join code
- ✅ View assigned tasks
- ✅ Update task status and progress
- ✅ Submit daily mood check-ins
- ✅ View personal performance statistics
- ✅ Track task completion rates

## Default Images

The application includes placeholder SVG images for:
- Logo (`loadspecs_logo.svg`)
- Profile icon (`profile-icon.png`)
- Default profile (`default_profile.png`)

You can replace these with actual PNG/JPG images in the `static/Images/` folder.

## Troubleshooting

### Issue: "No module named 'LoadSpecsApp'"
**Solution:** Make sure you're in the project root directory and virtual environment is activated.

### Issue: Database errors
**Solution:** Delete `db.sqlite3` and run migrations again:
```bash
del db.sqlite3
python manage.py makemigrations
python manage.py migrate
```

### Issue: Static files not loading
**Solution:** Run collectstatic:
```bash
python manage.py collectstatic
```

### Issue: Image uploads not working
**Solution:** Ensure `media/` folder exists and has write permissions.

## Production Deployment

Before deploying to production:

1. **Update settings.py:**
   - Set `DEBUG = False`
   - Add your domain to `ALLOWED_HOSTS`
   - Generate a new `SECRET_KEY`
   - Use PostgreSQL instead of SQLite

2. **Configure static files:**
   ```bash
   python manage.py collectstatic
   ```

3. **Use environment variables for sensitive data**

4. **Set up proper web server (Gunicorn + Nginx)**

## Support

For issues or questions:
- Check Django documentation: https://docs.djangoproject.com/
- Review the README.md file
- Check the code comments for implementation details

## Tech Stack
- **Backend:** Django 4.2
- **Frontend:** Bootstrap 5, HTML5, CSS3
- **Database:** SQLite (development) / PostgreSQL (production)
- **Charts:** Matplotlib
- **Icons:** Font Awesome 6
