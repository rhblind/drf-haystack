# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tests'))

SECRET_KEY = 'NOBODY expects the Spanish Inquisition!'
DEBUG = True

ALLOWED_HOSTS = ["*"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'test.db'),
    }
}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',

    'haystack',
    'rest_framework',

    'tests.mockapp',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {'debug': True},
        'APP_DIRS': True,
    },
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    )
}

ROOT_URLCONF = 'tests.urls'
WSGI_APPLICATION = 'tests.wsgi.application'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATIC_URL = '/static/'

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200/'),
        'INDEX_NAME': 'drf-haystack-test',
        'INCLUDE_SPELLING': True,
        'TIMEOUT': 300,
    },
}

DEFAULT_LOG_DIR = os.path.join(BASE_DIR, 'logs')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'console_handler': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'file_handler': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(DEFAULT_LOG_DIR, 'tests.log'),
        },
    },
    'loggers': {
        'default': {
            'handlers': ['file_handler'],
            'level': 'INFO',
            'propagate': True,
        },
        'elasticsearch': {
            'handlers': ['file_handler'],
            'level': 'ERROR',
            'propagate': True,
        },
        'elasticsearch.trace': {
            'handlers': ['file_handler'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

try:
    import elasticsearch
    if (2, ) <= elasticsearch.VERSION <= (3, ):
        HAYSTACK_CONNECTIONS['default'].update({
            'ENGINE': 'haystack.backends.elasticsearch2_backend.Elasticsearch2SearchEngine'
        })
except ImportError as e:
    del HAYSTACK_CONNECTIONS['default']  # This will intentionally cause everything to break!
