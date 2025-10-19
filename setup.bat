@echo off
echo ====================================
echo LoadSpecs Setup Script
echo ====================================
echo.

echo Creating virtual environment...
python -m venv venv
echo.

echo Activating virtual environment...
call venv\Scripts\activate
echo.

echo Installing dependencies...
pip install -r requirements.txt
echo.

echo Running migrations...
python manage.py makemigrations
python manage.py migrate
echo.

echo.
echo ====================================
echo Setup Complete!
echo ====================================
echo.
echo Next steps:
echo 1. Create a superuser: python manage.py createsuperuser
echo 2. Run the server: python manage.py runserver
echo.
pause
