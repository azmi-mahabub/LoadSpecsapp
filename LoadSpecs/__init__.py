# This will make sure the app is always imported when Django starts
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery not installed yet - will be available after pip install
    pass
