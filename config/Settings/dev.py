import os

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS += ['debug_toolbar']

MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

INTERNAL_IPS = ['127.0.0.1']

# Disable password validation in development for convenience
AUTH_PASSWORD_VALIDATORS = []

# The production architecture remains PostgreSQL. SQLite is an opt-in local
# fallback for a single-user workstation when Docker/PostgreSQL is unavailable.
if os.environ.get('USE_SQLITE', '').lower() in {'1', 'true', 'yes'}:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
