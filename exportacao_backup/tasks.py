from django.utils import timezone
from django.core.files.storage import default_storage
from .models import Backup, ConfiguracaoBackup
from .services import BackupService

def executar_backups_automaticos():
    """Executa backups automáticos para todos os usuários com configuração ativa."""
    configuracoes = ConfiguracaoBackup.objects.filter(ativo=True)
    
    for config in configuracoes:
        # Verifica se é hora de executar o backup
        if _deve_executar_backup(config):
            # Cria e executa o backup
            backup = Backup.objects.create(
                usuario=config.usuario,
                tipo='automatico',
                descricao=f'Backup automático - {timezone.now().strftime("%d/%m/%Y %H:%M")}'
            )
            
            # Executa o backup
            BackupService.executar_backup(backup)
            
            # Remove backups antigos se necessário
            _limpar_backups_antigos(config)

def _deve_executar_backup(config):
    """Verifica se deve executar o backup baseado na frequência e horário configurados."""
    agora = timezone.now()
    ultimo_backup = Backup.objects.filter(
        usuario=config.usuario,
        tipo='automatico'
    ).order_by('-data_criacao').first()
    
    if not ultimo_backup:
        return True
    
    diferenca = agora - ultimo_backup.data_criacao
    
    if config.frequencia == 'diario':
        return diferenca.days >= 1
    elif config.frequencia == 'semanal':
        return diferenca.days >= 7
    elif config.frequencia == 'mensal':
        return diferenca.days >= 30
    
    return False

def _limpar_backups_antigos(config):
    """Remove backups antigos mantendo apenas o número configurado."""
    backups = Backup.objects.filter(
        usuario=config.usuario,
        tipo='automatico'
    ).order_by('-data_criacao')
    
    # Mantém apenas o número configurado de backups
    if backups.count() > config.numero_backups:
        for backup in backups[config.numero_backups:]:
            backup.delete() 