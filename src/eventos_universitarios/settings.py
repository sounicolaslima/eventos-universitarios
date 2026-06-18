from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ==========================
# SEGURANÇA / DEBUG
# ==========================

# Em desenvolvimento, garanta DEBUG=True caso não exista no .env
DEBUG = config('DEBUG', default=True, cast=bool)

SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-ci-key-change-me'
)

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# ==========================
# INSTALLED APPS
# ==========================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_bootstrap5',

    'eventos',
    'usuarios',
]

# ==========================
# MIDDLEWARE
# ==========================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'eventos_universitarios.urls'

# ==========================
# TEMPLATES (corrigido)
# ==========================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        # só usa se a pasta existir
        'DIRS': [BASE_DIR / 'src' / 'templates'],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'eventos_universitarios.wsgi.application'

# ==========================
# DATABASE
# ==========================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ==========================
# VALIDADORES
# ==========================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==========================
# INTERNACIONALIZAÇÃO
# ==========================

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# ==========================
# STATIC
# ==========================

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'src' / 'static'
]

STATIC_ROOT = BASE_DIR / 'src' / 'staticfiles'

# ==========================
# MEDIA
# ==========================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'src' / 'media'

# ==========================
# LOGIN
# ==========================

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'

# ==========================
# CELERY
# ==========================

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# ==========================
# EMAIL (DEV)
# ==========================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ==========================
# AUTO FIELD
# ==========================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'