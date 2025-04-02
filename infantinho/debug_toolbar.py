from django.conf import settings

def configure_debug_toolbar():
    """Configura o Django Debug Toolbar com as configurações apropriadas."""
    if settings.DEBUG:
        INSTALLED_APPS = settings.INSTALLED_APPS
        MIDDLEWARE = settings.MIDDLEWARE
        
        # Adiciona o Debug Toolbar aos apps instalados
        if 'debug_toolbar' not in INSTALLED_APPS:
            INSTALLED_APPS += ['debug_toolbar']
        
        # Adiciona o middleware do Debug Toolbar
        if 'debug_toolbar.middleware.DebugToolbarMiddleware' not in MIDDLEWARE:
            MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
        
        # Configurações do Debug Toolbar
        DEBUG_TOOLBAR_CONFIG = {
            'SHOW_TOOLBAR_CALLBACK': lambda request: True,
            'INTERCEPT_REDIRECTS': False,
            'HIDE_DJANGO_SQL': False,
            'ENABLE_STACKTRACES': True,
            'SHOW_TEMPLATE_CONTEXT': True,
            'SQL_WARNING_THRESHOLD': 100,  # ms
            'SHOW_COLLAPSED': True,
            'PRETTIFY_SQL': True,
            'RENDER_PANELS': True,
        }
        
        # Configurações de painéis
        DEBUG_TOOLBAR_PANELS = [
            'debug_toolbar.panels.versions.VersionsPanel',
            'debug_toolbar.panels.timer.TimerPanel',
            'debug_toolbar.panels.settings.SettingsPanel',
            'debug_toolbar.panels.headers.HeadersPanel',
            'debug_toolbar.panels.request.RequestPanel',
            'debug_toolbar.panels.sql.SQLPanel',
            'debug_toolbar.panels.staticfiles.StaticFilesPanel',
            'debug_toolbar.panels.templates.TemplatesPanel',
            'debug_toolbar.panels.cache.CachePanel',
            'debug_toolbar.panels.signals.SignalsPanel',
            'debug_toolbar.panels.logging.LoggingPanel',
            'debug_toolbar.panels.redirects.RedirectsPanel',
            'debug_toolbar.panels.profiling.ProfilingPanel',
        ]
        
        # Atualiza as configurações
        settings.INSTALLED_APPS = INSTALLED_APPS
        settings.MIDDLEWARE = MIDDLEWARE
        settings.DEBUG_TOOLBAR_CONFIG = DEBUG_TOOLBAR_CONFIG
        settings.DEBUG_TOOLBAR_PANELS = DEBUG_TOOLBAR_PANELS 