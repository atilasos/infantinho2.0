"""
Django settings for infantinho project.

Generated by 'django-admin startproject' using Django 5.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=Csv())


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.flatpages',
    'accounts',
    'pit',
    'tea',
    'gestao_cooperada',
    'khanmigo_clone',
    'blog',
    'ai_core',
    'frontend',
    'microsoft_auth',
    'crispy_forms',
    'crispy_bootstrap5',
    'listas_verificacao',
    'taggit',
    'exportacao_backup',
    'personalizacao',
    'debug_toolbar',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.microsoft',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

# Django Debug Toolbar
INTERNAL_IPS = [
    '127.0.0.1',
]

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
}

ROOT_URLCONF = 'infantinho.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]

WSGI_APPLICATION = 'infantinho.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='infantinho'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,  # 10 minutos
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'pt'

TIME_ZONE = 'Atlantic/Madeira'

USE_I18N = True
USE_L10N = True
USE_TZ = True

# Locale paths
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configurações de arquivos de backup e exportação
BACKUP_ROOT = os.path.join(BASE_DIR, 'backups')
EXPORT_ROOT = os.path.join(BASE_DIR, 'exports')

# Criar diretórios se não existirem
os.makedirs(BACKUP_ROOT, exist_ok=True)
os.makedirs(EXPORT_ROOT, exist_ok=True)

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Site ID for sitemap
SITE_ID = 1

# Login/Logout URLs
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/accounts/login/'

# Email settings
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Show emails in console during development
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    # SMTP settings below are only used when DEBUG is False

EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)

# Site URL for email links
SITE_URL = config('SITE_URL', default='http://localhost:8000')

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Configurações de Sessão
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Mudando para usar o banco de dados em vez do Redis
SESSION_CACHE_ALIAS = 'default'

# Authentication Backend settings
AUTHENTICATION_BACKENDS = [
    'accounts.views.DemoAuthenticationBackend',  # Custom backend for demo accounts
    'django.contrib.auth.backends.ModelBackend',  # Default Django backend
    'allauth.account.auth_backends.AuthenticationBackend',  # Allauth backend
    'microsoft_auth.backends.MicrosoftAuthenticationBackend',  # Microsoft backend
]

# CSRF settings
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'https://login.microsoftonline.com',
    'https://login.microsoft.com'
]

# Ollama settings
OLLAMA_HOST = config('OLLAMA_HOST', default='http://localhost:11434')
OLLAMA_MODEL = config('OLLAMA_MODEL', default='gemma3')

# Configurações do Microsoft Auth
MICROSOFT_AUTH_CLIENT_ID = config('MICROSOFT_CLIENT_ID')
MICROSOFT_AUTH_CLIENT_SECRET = config('MICROSOFT_SECRET')
MICROSOFT_AUTH_LOGIN_TYPE = 'ma'  # Microsoft authentication (inclui Microsoft Accounts, Office 365 Enterprise e Azure AD)

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# AI Agent Configuration
AI_AGENT_CONFIG = {
    'max_tokens': 2000,
    'temperature': 0.7,
    'model': OLLAMA_MODEL,
    'language': 'pt-PT',
    'target_audience': 'children',
    'age_range': '6-12'
}

# Configuração do CustomUser
AUTH_USER_MODEL = 'accounts.CustomUser'

# Configurações de Arquivos Estáticos
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Configurações de Compressão
COMPRESS_ENABLED = True
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.rCSSMinFilter',
]
COMPRESS_JS_FILTERS = [
    'compressor.filters.jsmin.JSMinFilter',
]

# Configurações de Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Criar diretório de logs se não existir
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Configurações do Sentry
SENTRY_DSN = os.environ.get('SENTRY_DSN', '')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
VERSION = '1.0.0'

# Inicializa o Sentry se o DSN estiver configurado
if SENTRY_DSN:
    from .sentry import init_sentry
    init_sentry()

# Configurações do Debug Toolbar
if DEBUG:
    from .debug_toolbar import configure_debug_toolbar
    configure_debug_toolbar()

    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
    ]

# Configurações do WhiteNoise
from .whitenoise import configure_whitenoise
configure_whitenoise()

# Configurações do django-allauth
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Para demonstração, não requer verificação de email
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[Infantinho 2.0] '
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 5
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_SIGNUP_FORM_CLASS = None
ACCOUNT_USERNAME_MIN_LENGTH = 3
ACCOUNT_USERNAME_MAX_LENGTH = 30
ACCOUNT_USERNAME_BLACKLIST = ['admin', 'administrator', 'root', 'user', 'test', 'demo']
ACCOUNT_PASSWORD_MIN_LENGTH = 8
ACCOUNT_PASSWORD_MAX_LENGTH = 128
ACCOUNT_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
