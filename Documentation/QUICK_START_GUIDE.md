# 🚀 QUICK START GUIDE - LoadSpecs New Features

## ✅ What's Been Done

All 9 features are fully implemented:
1. ✅ Calendar & Deadline Sync
2. ✅ Internal Messaging/Chat
3. ✅ Team Announcements  
4. ✅ AI Task Prioritizer
5. ✅ AI Report Generator (Enhanced)
6. ✅ Performance Dashboard
7. ✅ Enhanced User Profiles
8. ✅ Automated Burnout Alerts
9. ✅ Dark Mode/Theme Switcher

## 📦 Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Django Channels (WebSockets)
- Celery (Background tasks)
- Redis (Message broker)
- Google Calendar API
- Microsoft Graph API
- Scikit-learn (AI/ML)
- And more...

## 🗄️ Step 2: Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

This creates the new database tables for all features.

## 🎨 Step 3: Start the Development Server

```bash
python manage.py runserver
```

The app will be available at: http://127.0.0.1:8000/

## 🌐 Step 4: Access New Features

### For Team Leads:
- **Dashboard:** http://127.0.0.1:8000/dashboard/
- **Calendar:** http://127.0.0.1:8000/calendar/
- **Chat:** http://127.0.0.1:8000/chat/
- **Announcements:** http://127.0.0.1:8000/announcements/
- **Burnout Alerts:** http://127.0.0.1:8000/alerts/
- **Search Employees:** http://127.0.0.1:8000/team/search-employees/
- **Task Prioritizer:** http://127.0.0.1:8000/tasks/analyze-priority/

### For Employees:
- **Dashboard:** http://127.0.0.1:8000/dashboard/
- **Calendar:** http://127.0.0.1:8000/calendar/
- **Chat:** http://127.0.0.1:8000/chat/
- **Announcements:** http://127.0.0.1:8000/announcements/
- **Edit Skills:** http://127.0.0.1:8000/profile/edit-skills/
- **Task Prioritizer:** http://127.0.0.1:8000/tasks/analyze-priority/

## 🎯 Step 5: Test the Features

### Test Dark Mode:
1. Click the moon icon in the navigation bar
2. Theme switches between light and dark
3. Preference is saved automatically

### Test Calendar:
1. Go to /calendar/
2. View all your tasks with deadlines
3. Click "Setup Sync" to configure Google/Outlook integration

### Test Chat:
1. Go to /chat/
2. Select a team chat
3. Send messages in real-time
4. Try direct messaging with other users

### Test Announcements:
1. Team leads: Go to /announcements/
2. Click "Create Announcement"
3. Fill in title, content, and type
4. Pin important announcements

### Test Dashboard:
1. Go to /dashboard/
2. View task completion stats
3. See interactive charts (requires Chart.js)
4. Compare team performance

### Test Employee Search:
1. Team leads: Go to /team/search-employees/
2. Search by skills: "Python", "Django", etc.
3. View employee profiles with skills and experience

### Test Burnout Alerts:
1. Team leads: Go to /alerts/
2. View unacknowledged burnout alerts
3. Click "Acknowledge" to mark as handled

## ⚙️ Optional: Enable Real-Time Features

### For WebSocket Chat (Optional):
```bash
# 1. Install and start Redis
redis-server

# 2. Uncomment in settings.py:
# 'daphne',  # Line ~24
# 'channels',  # Line ~33

# 3. Run with Daphne instead:
daphne -b 127.0.0.1 -p 8000 LoadSpecs.asgi:application
```

### For Automated Tasks (Optional):
```bash
# Terminal 1: Start Celery worker
celery -A LoadSpecs worker -l info

# Terminal 2: Start Celery beat (scheduler)
celery -A LoadSpecs beat -l info
```

## 🎨 UI Elements You'll See

- Modern cards with shadows
- Color-coded badges (priority, status, type)
- Interactive charts on dashboard
- Real-time chat interface
- Skill badges on profiles
- Pin indicators on announcements
- Severity badges on alerts
- Theme switcher in navbar

## 🔍 Navigation

All features are accessible from the left sidebar:
- 🏠 Home
- 👥 Team
- ✅ Tasks  
- 📊 Reports
- 📈 Dashboard *(NEW)*
- 📅 Calendar *(NEW)*
- 💬 Chat *(NEW)*
- 📢 Announcements *(NEW)*
- ⚠️ Alerts *(NEW - Team Leads Only)*
- 😊 Mood Check
- 👤 Profile
- 🚪 Logout

Plus theme switcher (moon/sun icon) in the top navigation bar!

## 📱 Mobile Responsive

All templates are mobile-friendly with Bootstrap 5.

## 🎉 You're All Set!

Everything is ready to use. Just:
1. Run migrations
2. Start the server
3. Login and explore!

For detailed documentation, see `NEW_FEATURES_COMPLETE.md`

---

**Questions? Issues?**
- Check `NEW_FEATURES_COMPLETE.md` for full documentation
- Review `NEW_FEATURES_SETUP.md` for implementation details
- All models registered in Django admin for easy data management
