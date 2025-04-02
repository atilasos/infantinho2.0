from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import time
import os

User = get_user_model()

class Backup(models.Model):
    TIPOS_BACKUP = [
        ('auto', 'Automático'),
        ('manual', 'Manual'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
        ('erro', 'Erro'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='backups')
    tipo = models.CharField(max_length=10, choices=TIPOS_BACKUP, default='manual')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    arquivo = models.FileField(upload_to='backups/', null=True, blank=True)
    tamanho = models.BigIntegerField(null=True, blank=True)  # Tamanho em bytes
    descricao = models.TextField(blank=True)
    erro = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Backup'
        verbose_name_plural = 'Backups'
        ordering = ['-data_criacao']
    
    def __str__(self):
        return f"Backup {self.tipo} - {self.data_criacao.strftime('%d/%m/%Y %H:%M')}"
    
    def salvar_arquivo(self, arquivo):
        """Salva o arquivo de backup e atualiza o tamanho"""
        self.arquivo = arquivo
        self.tamanho = arquivo.size
        self.save()
    
    def deletar_arquivo(self):
        """Deleta o arquivo físico do backup"""
        if self.arquivo and os.path.isfile(self.arquivo.path):
            os.remove(self.arquivo.path)
            self.arquivo = None
            self.tamanho = None
            self.save()

class Exportacao(models.Model):
    FORMATOS_CHOICES = [
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('personalizado', 'Personalizado'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
        ('erro', 'Erro'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exportacoes')
    formato = models.CharField(max_length=20, choices=FORMATOS_CHOICES)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    arquivo = models.FileField(upload_to='exportacoes/', null=True, blank=True)
    tamanho = models.BigIntegerField(null=True, blank=True)  # Tamanho em bytes
    filtros = models.JSONField(default=dict, blank=True)  # Filtros aplicados na exportação
    descricao = models.TextField(blank=True)
    erro = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Exportação'
        verbose_name_plural = 'Exportações'
        ordering = ['-data_criacao']
    
    def __str__(self):
        return f"Exportação {self.formato} - {self.data_criacao.strftime('%d/%m/%Y %H:%M')}"
    
    def salvar_arquivo(self, arquivo):
        """Salva o arquivo de exportação e atualiza o tamanho"""
        self.arquivo = arquivo
        self.tamanho = arquivo.size
        self.save()
    
    def deletar_arquivo(self):
        """Deleta o arquivo físico da exportação"""
        if self.arquivo and os.path.isfile(self.arquivo.path):
            os.remove(self.arquivo.path)
            self.arquivo = None
            self.tamanho = None
            self.save()

class ConfiguracaoBackup(models.Model):
    """Configurações para backup automático"""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='configuracao_backup')
    ativo = models.BooleanField(default=True)
    frequencia = models.CharField(max_length=20, choices=[
        ('diario', 'Diário'),
        ('semanal', 'Semanal'),
        ('mensal', 'Mensal')
    ], default='diario')
    hora_execucao = models.TimeField(default=time(0, 0))  # Hora do dia para executar
    manter_backups = models.IntegerField(default=7)  # Número de backups a manter
    incluir_media = models.BooleanField(default=True)  # Incluir arquivos de mídia
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuração de Backup'
        verbose_name_plural = 'Configurações de Backup'
    
    def __str__(self):
        return f"Configuração de Backup - {self.usuario.username}"

class ConfiguracaoExportacao(models.Model):
    """Configurações padrão para exportações"""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='configuracao_exportacao')
    formato_padrao = models.CharField(max_length=20, choices=Exportacao.FORMATOS_CHOICES, default='csv')
    incluir_cabecalho = models.BooleanField(default=True)
    separador = models.CharField(max_length=1, default=',')
    encoding = models.CharField(max_length=20, default='utf-8')
    compressao = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Configuração de Exportação'
        verbose_name_plural = 'Configurações de Exportação'
    
    def __str__(self):
        return f"Configuração de Exportação - {self.usuario.username}"
