from django.conf import settings

def configure_whitenoise():
    """Configura o WhiteNoise para servir arquivos estáticos."""
    MIDDLEWARE = settings.MIDDLEWARE
    
    # Adiciona o middleware do WhiteNoise
    if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
        MIDDLEWARE = [
            'whitenoise.middleware.WhiteNoiseMiddleware',
        ] + MIDDLEWARE
    
    # Configurações do WhiteNoise
    WHITENOISE_USE_FINDERS = True
    WHITENOISE_MANIFEST_STRICT = False
    WHITENOISE_ALLOW_ALL_ORIGINS = True
    WHITENOISE_INDEX_FILE = True
    WHITENOISE_ROOT = settings.STATIC_ROOT
    WHITENOISE_AUTOREFRESH = settings.DEBUG
    
    # Configurações de compressão
    WHITENOISE_COMPRESS = True
    WHITENOISE_COMPRESS_LEVEL = 6
    WHITENOISE_MAX_AGE = 60 * 60 * 24 * 365  # 1 ano
    
    # Configurações de cache
    WHITENOISE_CACHE_PREFIX = 'whitenoise:'
    WHITENOISE_CACHE_MAX_AGE = 60 * 60 * 24  # 1 dia
    
    # Configurações de segurança
    WHITENOISE_ALLOW_ALL_ORIGINS = False
    WHITENOISE_ALLOWED_ORIGINS = [
        'localhost',
        '127.0.0.1',
    ]
    
    # Atualiza as configurações
    settings.MIDDLEWARE = MIDDLEWARE
    settings.WHITENOISE_USE_FINDERS = WHITENOISE_USE_FINDERS
    settings.WHITENOISE_MANIFEST_STRICT = WHITENOISE_MANIFEST_STRICT
    settings.WHITENOISE_ALLOW_ALL_ORIGINS = WHITENOISE_ALLOW_ALL_ORIGINS
    settings.WHITENOISE_INDEX_FILE = WHITENOISE_INDEX_FILE
    settings.WHITENOISE_ROOT = WHITENOISE_ROOT
    settings.WHITENOISE_AUTOREFRESH = WHITENOISE_AUTOREFRESH
    settings.WHITENOISE_COMPRESS = WHITENOISE_COMPRESS
    settings.WHITENOISE_COMPRESS_LEVEL = WHITENOISE_COMPRESS_LEVEL
    settings.WHITENOISE_MAX_AGE = WHITENOISE_MAX_AGE
    settings.WHITENOISE_CACHE_PREFIX = WHITENOISE_CACHE_PREFIX
    settings.WHITENOISE_CACHE_MAX_AGE = WHITENOISE_CACHE_MAX_AGE
    settings.WHITENOISE_ALLOWED_ORIGINS = WHITENOISE_ALLOWED_ORIGINS 