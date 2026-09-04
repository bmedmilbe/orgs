from .dev import *

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]


CACHES["default"]["BACKEND"] = "django.core.cache.backends.locmem.LocMemCache"

WHITENOISE_AUTOREFRESH = True

DATABASES["default"]["TEST"] = {"SERIALIZE": False}

DATABASES = {
    'default': {
        'ENGINE': "django_tenants.postgresql_backend",
        'USER': 'postgres',
        'HOST': 'orgsdbtest',
        'PASSWORD': 'postgres',
        'NAME': 'orgsdbtest',
        'PORT': '5432',
    }
}
