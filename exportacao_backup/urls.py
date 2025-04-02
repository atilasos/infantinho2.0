from django.urls import path
from . import views

app_name = 'exportacao_backup'

urlpatterns = [
    # URLs de Backup
    path('backups/', views.lista_backups, name='lista_backups'),
    path('backups/criar/', views.criar_backup, name='criar_backup'),
    path('backups/<int:backup_id>/download/', views.download_backup, name='download_backup'),
    path('backups/<int:backup_id>/restaurar/', views.restaurar_backup, name='restaurar_backup'),
    
    # URLs de Exportação
    path('exportacoes/', views.lista_exportacoes, name='lista_exportacoes'),
    path('exportacoes/criar/', views.criar_exportacao, name='criar_exportacao'),
    path('exportacoes/<int:exportacao_id>/download/', views.download_exportacao, name='download_exportacao'),
    
    # URLs de Configuração
    path('configuracao/backup/', views.configuracao_backup, name='configuracao_backup'),
    path('configuracao/exportacao/', views.configuracao_exportacao, name='configuracao_exportacao'),
] 