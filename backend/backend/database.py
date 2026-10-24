"""Database configuration shared by the Django project and the seed tool.

Postgres is used when DB_NAME is set; otherwise SQLite (DB_SQLITE_PATH, default
<project>/db.sqlite3).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def get_databases():
    if os.environ.get('DB_NAME'):
        return {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ['DB_NAME'],
                'USER': os.environ.get('DB_USER', ''),
                'PASSWORD': os.environ.get('DB_PASSWORD', ''),
                'HOST': os.environ.get('DB_HOST', 'localhost'),
                'PORT': os.environ.get('DB_PORT', ''),
            }
        }
    return {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.environ.get('DB_SQLITE_PATH', BASE_DIR / 'db.sqlite3'),
        }
    }
