"""
Django settings for debby project.

Generated by 'django-admin startproject' using Django 1.10.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os

from linebot import LineBotApi
from linebot import WebhookHandler
import environ

root = environ.Path(__file__) - 2
env = environ.Env()

# read the django-environ file.
env_file = os.path.join(os.path.dirname(__file__), 'settings.env')
if os.path.exists(env_file):
    environ.Env.read_env(str(env_file))

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = root()
PROJECT_DIR = os.path.dirname(BASE_DIR)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

SECURE_SSL_REDIRECT = env('SECURE_SSL_REDIRECT')

ALLOWED_HOSTS = [
    env('NGROK_URL'),
    'localhost',
    'debby.metology.com.tw',
    '140.114.71.167',  # server ip for hsnl@NCHU
]

# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'corsheaders',
    'django_extensions',
    'django_celery_beat',
    'grappelli',
]

BUILD_APPS = [
    'line.apps.LineConfig',
    'user.apps.UserConfig',
    'bg_record.apps.BgRecordConfig',
    'exercise_record.apps.ExerciseRecordConfig',
    'food_record.apps.FoodRecordConfig',
    'drug_ask.apps.DrugAskConfig',
    'chat.apps.ChatConfig',
    'consult_food.apps.ConsultFoodConfig',
    'reminder.apps.ReminderConfig',
]

INSTALLED_APPS = THIRD_PARTY_APPS + BUILD_APPS + DJANGO_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # CROS middleware
    'corsheaders.middleware.CorsMiddleware',
]

ROOT_URLCONF = 'debby.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'debby.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': env.db()
}

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Taipei'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')

# Custom user model
AUTH_USER_MODEL = 'user.CustomUserModel'

# CROS settings.
CORS_ORIGIN_WHITELIST = (

)

# Celery settings
CELERY_BROKER_URL = 'amqp://'
CELERY_RESULT_BACKEND = 'amqp://'
CELERY_TIMEZONE = TIME_ZONE
CELERY_DEFAULT_EXCHANGE_TYPE = 'direct'
CELERY_IGNORE_RESULT = True

MEDIA_ROOT = os.path.join(PROJECT_DIR, 'media')

MEDIA_URL = '/media/'

# Caches
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    }
}

LINE_BOT_API = LineBotApi(env('LINE_WEBHOOK_TOKEN'))
HANDLER = WebhookHandler(env('LINE_WEBHOOK_SECRET'))
