"""
Django settings for Handwritten Notes Digitizer project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-change-me-in-production")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# ─── Applications ─────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    # Project apps
    "apps.accounts",
    "apps.admin_module",
    "apps.customer_module",
    "apps.ocr_engine",
    "apps.document_generator",
    "apps.notifications",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

# ─── Database ─────────────────────────────────────────────────────────────────

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ─── Custom User Model ────────────────────────────────────────────────────────

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─── Static & Media ───────────────────────────────────────────────────────────

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
UPLOAD_DIR = MEDIA_ROOT / "uploads"
OUTPUT_DIR = MEDIA_ROOT / "outputs"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── REST Framework ───────────────────────────────────────────────────────────

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

# ─── CORS ─────────────────────────────────────────────────────────────────────

CORS_ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",")
CORS_ALLOW_CREDENTIALS = True

# ─── Anthropic Claude API (AI layout analysis) ───────────────────────────────────

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
# Get a key at https://console.anthropic.com/
# If not set, the system falls back to regex-based layout detection.

# ─── OCR.space API ────────────────────────────────────────────────────────────

OCR_SPACE_API_KEY  = os.getenv("OCR_SPACE_API_KEY", "")
OCR_SPACE_ENGINE   = 3          # Engine 3: best handwriting support
OCR_SPACE_LANGUAGE = "eng"
OCR_SPACE_API_URL  = "https://api.ocr.space/parse/image"

# ─── Upload Constraints ───────────────────────────────────────────────────────

MAX_UPLOAD_SIZE_MB = 10
ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".pdf"]

# ─── Celery ───────────────────────────────────────────────────────────────────

CELERY_BROKER_URL      = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND  = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT  = ["json"]
CELERY_TIMEZONE        = TIME_ZONE

# ─── Email ────────────────────────────────────────────────────────────────────

EMAIL_BACKEND    = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@digitizer.local")

# ─── Document Style Templates ─────────────────────────────────────────────────

DOCUMENT_STYLE_TEMPLATES = {

    # ── Default ───────────────────────────────────────────────────────────────
    # Clean sans-serif, moderate spacing, dark navy text
    "default": {
        "font_family":         "Helvetica",
        "font_size":           12,
        "heading_size":        18,
        "line_spacing":        1.5,
        "margin_top":          72,
        "margin_bottom":       72,
        "margin_left":         72,
        "margin_right":        72,
        "primary_color":       "#2C3E50",
        "secondary_color":     "#7F8C8D",
        # Border
        "border_outer_width":  1.2,
        "border_inner_width":  0.5,
        "border_gap":          4,
        # Heading style: "underline" | "box" | "leftbar" | "plain" | "shaded"
        "heading_style":       "underline",
        "heading_underline_color": "#2C3E50",
        # Body paragraph alignment: 0=left 1=centre 2=right 4=justify
        "body_alignment":      4,
        # First-line indent for body paragraphs (points)
        "body_indent":         0,
        # Bullet style
        "bullet_char":         "•",
    },

    # ── Academic ──────────────────────────────────────────────────────────────
    # Times Roman serif, double-spaced, full justification, numbered-feel headings
    # Wide margins (like a printed thesis), underlined section headings
    "academic": {
        "font_family":         "Times-Roman",
        "font_size":           12,
        "heading_size":        14,
        "line_spacing":        2.0,
        "margin_top":          90,
        "margin_bottom":       90,
        "margin_left":         100,
        "margin_right":        100,
        "primary_color":       "#1A1A1A",
        "secondary_color":     "#555555",
        # Border — thin double line, traditional black
        "border_outer_width":  1.5,
        "border_inner_width":  0.5,
        "border_gap":          5,
        # Headings: underline rule beneath each section title
        "heading_style":       "underline",
        "heading_underline_color": "#1A1A1A",
        # Full justification like a journal paper
        "body_alignment":      4,
        # First-line indent (1.5 pica = 18pt) — classic academic indent
        "body_indent":         18,
        "bullet_char":         "-",
        # Extra academic-specific keys
        "heading_caps":        True,   # Section headings in SMALL CAPS style
        "first_para_indent":   False,  # First paragraph after heading has no indent
        "subheading_italic":   True,   # Subheadings in italic
    },

    # ── Notion-style ──────────────────────────────────────────────────────────
    # Modern minimal: Helvetica, generous whitespace, coloured heading accent bar,
    # warm off-white feel, emoji-friendly bullets, left-aligned everywhere
    "notion": {
        "font_family":         "Helvetica",
        "font_size":           11,
        "heading_size":        20,
        "line_spacing":        1.7,
        "margin_top":          70,
        "margin_bottom":       70,
        "margin_left":         85,
        "margin_right":        85,
        "primary_color":       "#37352F",
        "secondary_color":     "#9B9A97",
        # Border — very subtle warm grey
        "border_outer_width":  0.8,
        "border_inner_width":  0.3,
        "border_gap":          4,
        # Headings: thick left accent bar (Notion signature look)
        "heading_style":       "leftbar",
        "heading_bar_color":   "#E9E5DD",   # warm beige bar fill
        "heading_bar_accent":  "#37352F",   # dark left stripe
        # Left-aligned body — Notion never justifies
        "body_alignment":      0,
        "body_indent":         0,
        "bullet_char":         "→",
        # Extra notion-specific keys
        "heading_caps":        False,
        "subheading_italic":   False,
        "subheading_color":    "#787774",  # muted grey subheadings
        "body_color_override": "#37352F",
        "callout_style":       True,       # indent body under headings slightly
    },

    # ── Minimal ───────────────────────────────────────────────────────────────
    # Monospace Courier, compact spacing, typewriter feel
    "minimal": {
        "font_family":         "Courier",
        "font_size":           11,
        "heading_size":        13,
        "line_spacing":        1.2,
        "margin_top":          60,
        "margin_bottom":       60,
        "margin_left":         60,
        "margin_right":        60,
        "primary_color":       "#000000",
        "secondary_color":     "#666666",
        "border_outer_width":  1.0,
        "border_inner_width":  0.4,
        "border_gap":          3,
        "heading_style":       "plain",
        "body_alignment":      0,
        "body_indent":         0,
        "bullet_char":         "*",
        "heading_caps":        False,
        "subheading_italic":   False,
    },
}
