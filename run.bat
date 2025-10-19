@echo off
echo Starting LoadSpecs Development Server...
echo.

call venv\Scripts\activate
python manage.py runserver

pause
