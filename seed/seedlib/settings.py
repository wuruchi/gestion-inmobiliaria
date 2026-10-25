"""Minimal Django settings: just enough to use the backend's `base` models."""
import os
from pathlib import Path

import backend.database as _backend_database
from backend.database import get_databases  # resolved through ATB_BACKEND_PATH

SECRET_KEY = 'seed-tool-not-a-secret'
DEBUG = False
INSTALLED_APPS = [
    # The admin, sessions and messages apps are here only so that `migrate` creates their tables: without them the
    # backend's /admin/ page fails on a database set up by this tool.
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'base.apps.BaseConfig',
]
DATABASES = get_databases()
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
USE_TZ = True
# Where the backend stores uploaded files (same rule as backend/settings.py); the fake offers copy their photos here.
MEDIA_ROOT = Path(os.environ.get('DJANGO_MEDIA_ROOT', Path(_backend_database.__file__).resolve().parent.parent / 'media'))
