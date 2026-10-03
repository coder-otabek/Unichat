from pathlib import Path
from datetime import timedelta
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG                         =(bool,  False),
    USE_SQLITE                    =(bool,  True),
    ALLOW_GUEST_CHAT              =(bool,  True),
    AUTO_TITLE_SESSIONS           =(bool,  True),
    USE_LOCAL_EMBEDDINGS          =(bool,  False),
    CORS_ALLOW_ALL_ORIGINS_IN_DEBUG=(bool, True),
    JWT_ROTATE_REFRESH            =(bool,  True),
    JWT_ACCESS_LIFETIME_DAYS      =(int,   7),
    JWT_REFRESH_LIFETIME_DAYS     =(int,   30),
    CHUNK_SIZE                    =(int,   800),
    CHUNK_OVERLAP                 =(int,   150),
    TOP_K                         =(int,   5),
    MAX_FILE_MB                   =(int,   50),
    LLM_TEMPERATURE               =(float, 0.7),
    LLM_MAX_TOKENS                =(int,   2000),
    EMBED_DIM                     =(int,   1536),
    MIN_SCORE                     =(float, 0.25),
    MAX_HISTORY_MESSAGES          =(int,   10),
    CHAT_RATE_LIMIT_PER_HOUR      =(int,   30),
    GUEST_RATE_LIMIT_PER_HOUR     =(int,   5),
)
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY    = env('SECRET_KEY', default='dev-secret-key-change-in-production')
DEBUG         = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])  # ngrok uchun '*' yetarli

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'apps.accounts',
    'apps.books',
    'apps.chat',
    'apps.core',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.AllowGoogleAvatarMiddleware',
]

ROOT_URLCONF     = 'unichat.urls'
AUTH_USER_MODEL  = 'accounts.User'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
WSGI_APPLICATION = 'unichat.wsgi.application'

TEMPLATES = [{
    'BACKEND' : 'django.template.backends.django.DjangoTemplates',
    'DIRS'    : [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS' : {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

# ── Database ──────────────────────────────────────────────────────────────────
if env('USE_SQLITE'):
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME'  : BASE_DIR / 'db.sqlite3',
    }}
else:
    _db_url = env('DATABASE_URL', default='')
    if _db_url:
        DATABASES = {'default': env.db_url('DATABASE_URL')}
    else:
        DATABASES = {'default': {
            'ENGINE'  : 'django.db.backends.postgresql',
            'NAME'    : env('DB_NAME',     default='unichat_db'),
            'USER'    : env('DB_USER',     default='unichat'),
            'PASSWORD': env('DB_PASSWORD', default=''),
            'HOST'    : env('DB_HOST',     default='localhost'),
            'PORT'    : env('DB_PORT',     default='5432'),
        }}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'uz'
TIME_ZONE     = 'Asia/Tashkent'
USE_I18N      = True
USE_TZ        = True

STATIC_URL          = '/static/'
STATICFILES_DIRS    = [BASE_DIR / 'static']
STATIC_ROOT         = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL           = '/media/'
MEDIA_ROOT          = BASE_DIR / 'media'

# ── DRF ──────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'DEFAULT_RENDERER_CLASSES'  : ['rest_framework.renderers.JSONRenderer'],
    'EXCEPTION_HANDLER'         : 'apps.core.exceptions.custom_exception_handler',
}

# ── JWT ───────────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME' : timedelta(days=env('JWT_ACCESS_LIFETIME_DAYS')),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=env('JWT_REFRESH_LIFETIME_DAYS')),
    'ROTATE_REFRESH_TOKENS' : env('JWT_ROTATE_REFRESH'),
    'UPDATE_LAST_LOGIN'     : True,
    'AUTH_HEADER_TYPES'     : ('Bearer',),
}

# ── CORS ─────────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS  = env('CORS_ALLOW_ALL_ORIGINS_IN_DEBUG', default=True)
CORS_ALLOWED_ORIGINS    = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_ALLOW_CREDENTIALS  = True


# ── CSRF (ngrok va boshqa tunnel uchun) ──────────────────────
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[
    'http://localhost:8000',
    'http://127.0.0.1:8000',
])
# ngrok ishlatilganda .env ga qo'shing:
# CSRF_TRUSTED_ORIGINS=https://xxxx-xx-xx.ngrok-free.app

# ── App-level settings ────────────────────────────────────────────────────────
LLM_PROVIDER        = env('LLM_PROVIDER',          default='groq')
LLM_MODEL           = env('LLM_MODEL',             default='gpt-4o-mini')
LLM_TEMPERATURE     = env('LLM_TEMPERATURE')
LLM_MAX_TOKENS      = env('LLM_MAX_TOKENS')
OPENAI_API_KEY      = env('OPENAI_API_KEY',         default='')
ANTHROPIC_API_KEY   = env('ANTHROPIC_API_KEY',      default='')
GROQ_API_KEY        = env('GROQ_API_KEY',           default='')
DEEPSEEK_API_KEY    = env('DEEPSEEK_API_KEY',       default='')
TOGETHER_API_KEY    = env('TOGETHER_API_KEY',       default='')
OPENROUTER_API_KEY  = env('OPENROUTER_API_KEY',     default='')
USE_LOCAL_EMBEDDINGS= env('USE_LOCAL_EMBEDDINGS', default=True)
LOCAL_EMBED_MODEL   = env('LOCAL_EMBED_MODEL',      default='paraphrase-multilingual-MiniLM-L12-v2')
EMBED_MODEL         = env('EMBED_MODEL',            default='text-embedding-3-small')
EMBED_DIM           = env('EMBED_DIM')
CHUNK_SIZE          = env('CHUNK_SIZE')
CHUNK_OVERLAP       = env('CHUNK_OVERLAP')
TOP_K               = env('TOP_K')
MIN_SCORE           = env('MIN_SCORE')
MAX_FILE_MB         = env('MAX_FILE_MB')
ALLOWED_EXTENSIONS  = env.list('ALLOWED_EXTENSIONS', default=['pdf','docx','txt','md','epub'])
ALLOW_GUEST_CHAT    = env('ALLOW_GUEST_CHAT')
AUTO_TITLE_SESSIONS = env('AUTO_TITLE_SESSIONS')
MAX_HISTORY_MESSAGES= env('MAX_HISTORY_MESSAGES')
SITE_TITLE          = env('SITE_TITLE',             default='UniChat')
SITE_DESCRIPTION    = env('SITE_DESCRIPTION',       default='AI yordamchi — bilim bazasidan javob beradi')
GOOGLE_CLIENT_ID       = env('GOOGLE_CLIENT_ID',          default='')

# ── Security headers ─────────────────────────────────────────
SECURE_CROSS_ORIGIN_OPENER_POLICY = None