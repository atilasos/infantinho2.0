from django.apps import AppConfig


class ExportacaoBackupConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'exportacao_backup'
    verbose_name = 'Exportação e Backup'

    def ready(self):
        import exportacao_backup.signals  # Importa os sinais do app
