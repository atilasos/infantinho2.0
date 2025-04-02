import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from django.conf import settings

def init_sentry():
    """Inicializa o Sentry com as configurações apropriadas."""
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            RedisIntegration(),
            CeleryIntegration(),
            SqlalchemyIntegration(),
        ],
        # Configurações de performance
        traces_sample_rate=0.2,
        profiles_sample_rate=0.1,
        
        # Configurações de ambiente
        environment=settings.ENVIRONMENT,
        release=settings.VERSION,
        
        # Configurações de erro
        send_default_pii=True,
        max_breadcrumbs=50,
        
        # Configurações de sessão
        auto_session_tracking=True,
        session_mode="request",
        
        # Configurações de contexto
        _experiments={
            "profiles_sample_rate": 0.1,
        },
    )

    # Configurações adicionais
    sentry_sdk.set_tag("app", "infantinho")
    sentry_sdk.set_tag("version", settings.VERSION)
    
    # Configurações de contexto do usuário
    @sentry_sdk.inject_context
    def user_context(user):
        if user and user.is_authenticated:
            return {
                "id": user.id,
                "email": user.email,
                "username": user.username,
            }
        return None 