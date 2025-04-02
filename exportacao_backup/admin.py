from django.contrib import admin
from .models import Backup, Exportacao, ConfiguracaoBackup, ConfiguracaoExportacao

@admin.register(Backup)
class BackupAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo', 'data_criacao', 'status', 'tamanho')
    list_filter = ('tipo', 'status', 'data_criacao')
    search_fields = ('usuario__username', 'descricao')
    readonly_fields = ('data_criacao', 'data_conclusao', 'tamanho')
    ordering = ('-data_criacao',)

@admin.register(Exportacao)
class ExportacaoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'formato', 'data_criacao', 'status', 'tamanho')
    list_filter = ('formato', 'status', 'data_criacao')
    search_fields = ('usuario__username', 'descricao')
    readonly_fields = ('data_criacao', 'data_conclusao', 'tamanho')
    ordering = ('-data_criacao',)

@admin.register(ConfiguracaoBackup)
class ConfiguracaoBackupAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'ativo', 'frequencia', 'hora_execucao', 'manter_backups')
    list_filter = ('ativo', 'frequencia')
    search_fields = ('usuario__username',)
    ordering = ('usuario__username',)

@admin.register(ConfiguracaoExportacao)
class ConfiguracaoExportacaoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'formato_padrao', 'incluir_cabecalho', 'separador', 'encoding')
    list_filter = ('formato_padrao', 'incluir_cabecalho', 'compressao')
    search_fields = ('usuario__username',)
    ordering = ('usuario__username',)
