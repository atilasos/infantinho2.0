from django.apps import AppConfig


class PersonalizacaoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'personalizacao'
    verbose_name = 'Personalização'

    def ready(self):
        import personalizacao.signals
