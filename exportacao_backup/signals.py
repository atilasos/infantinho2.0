from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage
from .models import Backup, Exportacao

@receiver(pre_delete, sender=Backup)
def delete_backup_file(sender, instance, **kwargs):
    """Deleta o arquivo de backup quando o registro é excluído."""
    if instance.arquivo:
        try:
            default_storage.delete(instance.arquivo.path)
        except Exception:
            pass  # Ignora erros ao tentar deletar o arquivo

@receiver(pre_delete, sender=Exportacao)
def delete_exportacao_file(sender, instance, **kwargs):
    """Deleta o arquivo de exportação quando o registro é excluído."""
    if instance.arquivo:
        try:
            default_storage.delete(instance.arquivo.path)
        except Exception:
            pass  # Ignora erros ao tentar deletar o arquivo

@receiver(post_save, sender=Backup)
def execute_backup(sender, instance, created, **kwargs):
    """Executa o backup quando um novo registro é criado."""
    if created and instance.status == 'pendente':
        from .services import BackupService
        BackupService.executar_backup(instance)

@receiver(post_save, sender=Exportacao)
def execute_exportacao(sender, instance, created, **kwargs):
    """Executa a exportação quando um novo registro é criado."""
    if created and instance.status == 'pendente':
        from .services import ExportacaoService
        ExportacaoService.executar_exportacao(instance) 