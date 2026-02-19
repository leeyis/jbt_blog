from .settings import *  # noqa


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
