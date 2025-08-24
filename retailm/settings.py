import os
from pathlib import Path
from datetime import timedelta  # for JWT token lifetime

# ----------------------------------------------------
# BASE DIR
# ----------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ----------------------------------------------------
# SECURITY
# ----------------------------------------------------
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-your-secret-key-here")
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if not DEBUG else ["*"]

# ----------------------------------------------------
# CUSTOM USER MODEL
# ----------------------------------------------------
AUTH_USER_MODEL = "api.CustomUser"  # ✅ custom user

# ----------------------------------------------------
# INSTALLED APPS
# ----------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",  # ✅ JWT
    "corsheaders",               # ✅ CORS

    # Local apps
    "api",
]

# ----------------------------------------------------
# MIDDLEWARE
# ----------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # "whitenoise.middleware.WhiteNoiseMiddleware",  # enable in prod if needed
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",       # ✅ enable CORS
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ----------------------------------------------------
# URLS / WSGI
# ----------------------------------------------------
ROOT_URLCONF = "retailm.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "retailm.wsgi.application"

# ----------------------------------------------------
# DATABASE
# ----------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ----------------------------------------------------
# PASSWORD VALIDATORS
# ----------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ----------------------------------------------------
# LANGUAGE / TIMEZONE
# ----------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ----------------------------------------------------
# STATIC FILES
# ----------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Only add static/ if it exists
STATICFILES_DIRS = []
if (BASE_DIR / "static").exists():
    STATICFILES_DIRS.append(BASE_DIR / "static")

# Whitenoise compression (for deployment)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ----------------------------------------------------
# DEFAULT PRIMARY KEY
# ----------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ----------------------------------------------------
# DJANGO REST FRAMEWORK + JWT
# ----------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
}

# JWT settings (tokens lifetime)
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# ----------------------------------------------------
# CORS
# ----------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",   # ✅ React local dev
]
CORS_ALLOW_CREDENTIALS = True  # allow cookies/session

# ----------------------------------------------------
# LOGGING CONFIG (Auto-create logs folder)
# ----------------------------------------------------
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "django.log",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["file", "console"],
        "level": "INFO",
    },
}
