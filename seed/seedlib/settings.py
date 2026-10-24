"""Minimal Django settings: just enough to use the backend's `base` models."""
from backend.database import get_databases  # resolved through ATB_BACKEND_PATH

SECRET_KEY = 'seed-tool-not-a-secret'
DEBUG = False
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'base.apps.BaseConfig',
]
DATABASES = get_databases()
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
USE_TZ = True
