import os

import dj_database_url

from .common import *

DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t")

SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-default-change-me-in-production"
)

# Defaulting split strings to empty lists or local defaults to avoid crashes
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost 127.0.0.1").split(" ")

DJANGO_SETTINGS_MODULE = os.environ.get(
    "DJANGO_SETTINGS_MODULE", "myproject.settings.local"
)

# --- DATABASE ---
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/dbname")

DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL, 
        conn_max_age=600,
    )
}

DATABASES["default"]["ENGINE"] = "django_tenants.postgresql_backend"

DATABASE_ROUTERS = (
    "django_tenants.routers.TenantSyncRouter",
)



# --- AWS S3 STORAGE ---
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "default_aws_key")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "default_aws_secret")
AWS_STORAGE_BUCKET_NAME = os.environ.get(
    "AWS_STORAGE_BUCKET_NAME", "default-bucket-name"
)
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"



# --- SECURITY & COOKIES ---
CORS_ALLOW_ALL_ORIGINS = True
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False

CSRF_TRUSTED_ORIGINS = os.environ.get(
    "CSRF_TRUSTED_ORIGINS", "http://localhost:8000 http://127.0.0.1:8000"
).split(" ")

