from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from .models import Backup, Exportacao, ConfiguracaoBackup, ConfiguracaoExportacao
from .forms import BackupForm, ExportacaoForm, ConfiguracaoBackupForm, ConfiguracaoExportacaoForm
from .services import BackupService, ExportacaoService

@login_required
def lista_backups(request):
    """Lista todos os backups do usuário"""
    backups = Backup.objects.filter(usuario=request.user)
    return render(request, 'exportacao_backup/backups/lista.html', {
        'backups': backups
    })

@login_required
def criar_backup(request):
    """Cria um novo backup"""
    if request.method == 'POST':
        form = BackupForm(request.POST)
        if form.is_valid():
            backup = BackupService.criar_backup(
                usuario=request.user,
                tipo=form.cleaned_data['tipo'],
                descricao=form.cleaned_data['descricao']
            )
            try:
                BackupService.executar_backup(backup)
                messages.success(request, 'Backup criado com sucesso!')
                return redirect('exportacao_backup:lista_backups')
            except Exception as e:
                messages.error(request, f'Erro ao criar backup: {str(e)}')
    else:
        form = BackupForm()
    
    return render(request, 'exportacao_backup/backups/criar.html', {
        'form': form
    })

@login_required
def download_backup(request, backup_id):
    """Download do arquivo de backup"""
    backup = get_object_or_404(Backup, id=backup_id, usuario=request.user)
    
    if not backup.arquivo:
        messages.error(request, 'Arquivo de backup não encontrado')
        return redirect('exportacao_backup:lista_backups')
    
    response = HttpResponse(backup.arquivo, content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="{backup.arquivo.name}"'
    return response

@login_required
def restaurar_backup(request, backup_id):
    """Restaura um backup"""
    backup = get_object_or_404(Backup, id=backup_id, usuario=request.user)
    
    try:
        BackupService.restaurar_backup(backup)
        messages.success(request, 'Backup restaurado com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao restaurar backup: {str(e)}')
    
    return redirect('exportacao_backup:lista_backups')

@login_required
def lista_exportacoes(request):
    """Lista todas as exportações do usuário"""
    exportacoes = Exportacao.objects.filter(usuario=request.user)
    return render(request, 'exportacao_backup/exportacoes/lista.html', {
        'exportacoes': exportacoes
    })

@login_required
def criar_exportacao(request):
    """Cria uma nova exportação"""
    if request.method == 'POST':
        form = ExportacaoForm(request.POST)
        if form.is_valid():
            exportacao = ExportacaoService.criar_exportacao(
                usuario=request.user,
                formato=form.cleaned_data['formato'],
                filtros=form.cleaned_data['filtros'],
                descricao=form.cleaned_data['descricao']
            )
            try:
                ExportacaoService.executar_exportacao(exportacao)
                messages.success(request, 'Exportação criada com sucesso!')
                return redirect('exportacao_backup:lista_exportacoes')
            except Exception as e:
                messages.error(request, f'Erro ao criar exportação: {str(e)}')
    else:
        form = ExportacaoForm()
    
    return render(request, 'exportacao_backup/exportacoes/criar.html', {
        'form': form
    })

@login_required
def download_exportacao(request, exportacao_id):
    """Download do arquivo de exportação"""
    exportacao = get_object_or_404(Exportacao, id=exportacao_id, usuario=request.user)
    
    if not exportacao.arquivo:
        messages.error(request, 'Arquivo de exportação não encontrado')
        return redirect('exportacao_backup:lista_exportacoes')
    
    content_type = 'application/octet-stream'
    if exportacao.formato == 'csv':
        content_type = 'text/csv'
    elif exportacao.formato == 'excel':
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif exportacao.formato == 'pdf':
        content_type = 'application/pdf'
    
    response = HttpResponse(exportacao.arquivo, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{exportacao.arquivo.name}"'
    return response

@login_required
def configuracao_backup(request):
    """Configurações de backup do usuário"""
    config, created = ConfiguracaoBackup.objects.get_or_create(usuario=request.user)
    
    if request.method == 'POST':
        form = ConfiguracaoBackupForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configurações de backup atualizadas com sucesso!')
            return redirect('exportacao_backup:configuracao_backup')
    else:
        form = ConfiguracaoBackupForm(instance=config)
    
    return render(request, 'exportacao_backup/configuracao/backup.html', {
        'form': form
    })

@login_required
def configuracao_exportacao(request):
    """Configurações de exportação do usuário"""
    config, created = ConfiguracaoExportacao.objects.get_or_create(usuario=request.user)
    
    if request.method == 'POST':
        form = ConfiguracaoExportacaoForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configurações de exportação atualizadas com sucesso!')
            return redirect('exportacao_backup:configuracao_exportacao')
    else:
        form = ConfiguracaoExportacaoForm(instance=config)
    
    return render(request, 'exportacao_backup/configuracao/exportacao.html', {
        'form': form
    })
