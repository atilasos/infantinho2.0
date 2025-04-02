from django import forms
from .models import Backup, Exportacao, ConfiguracaoBackup, ConfiguracaoExportacao

class BackupForm(forms.ModelForm):
    class Meta:
        model = Backup
        fields = ['descricao']

class ExportacaoForm(forms.ModelForm):
    class Meta:
        model = Exportacao
        fields = ['formato', 'filtros', 'descricao']
        widgets = {
            'filtros': forms.Textarea(attrs={'rows': 4}),
            'descricao': forms.Textarea(attrs={'rows': 4}),
        }

class ConfiguracaoBackupForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoBackup
        fields = ['ativo', 'frequencia', 'hora_execucao', 'manter_backups', 'incluir_media']
        widgets = {
            'hora_execucao': forms.TimeInput(attrs={'type': 'time'}),
        }

class ConfiguracaoExportacaoForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoExportacao
        fields = ['formato_padrao', 'incluir_cabecalho', 'separador', 'encoding', 'compressao'] 