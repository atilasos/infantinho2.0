from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import (
    DominioAprendizagem, ObjetivoAprendizagem, StatusObjetivo, 
    RegistroAvaliacao, Turma
)
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.urls import reverse

User = get_user_model()

@login_required
def lista_objetivos(request):
    """View para exibir a lista de objetivos organizados por domínio"""
    dominios = DominioAprendizagem.objects.all()
    status_objetivos = StatusObjetivo.objects.filter(aluno=request.user)
    
    # Criar um dicionário para mapear objetivos para seus status
    status_map = {so.objetivo_id: so for so in status_objetivos}
    
    context = {
        'dominios': dominios,
        'status_map': status_map,
    }
    return render(request, 'listas_verificacao/lista_objetivos.html', context)

@login_required
def detalhe_objetivo(request, objetivo_id):
    """View para exibir detalhes de um objetivo específico"""
    objetivo = get_object_or_404(ObjetivoAprendizagem, id=objetivo_id)
    status = StatusObjetivo.objects.filter(aluno=request.user, objetivo=objetivo).first()
    avaliacoes = RegistroAvaliacao.objects.filter(status_objetivo=status) if status else []
    
    context = {
        'objetivo': objetivo,
        'status': status,
        'avaliacoes': avaliacoes,
    }
    return render(request, 'listas_verificacao/detalhe_objetivo.html', context)

@login_required
@require_POST
def atualizar_status(request, objetivo_id):
    """View para atualizar o status de um objetivo"""
    objetivo = get_object_or_404(ObjetivoAprendizagem, id=objetivo_id)
    novo_status = request.POST.get('status')
    
    if novo_status not in dict(StatusObjetivo.STATUS_CHOICES):
        return JsonResponse({'error': 'Status inválido'}, status=400)
    
    status, created = StatusObjetivo.objects.get_or_create(
        aluno=request.user,
        objetivo=objetivo,
        defaults={'status': novo_status}
    )
    
    if not created:
        status.status = novo_status
        status.save()
    
    return JsonResponse({
        'status': status.status,
        'data_atualizacao': status.data_atualizacao.strftime('%Y-%m-%d %H:%M:%S')
    })

@login_required
def registrar_avaliacao(request, objetivo_id):
    """View para registrar uma avaliação de um objetivo"""
    if not request.user.is_staff:
        messages.error(request, 'Apenas professores podem registrar avaliações.')
        return redirect('detalhe_objetivo', objetivo_id=objetivo_id)
    
    objetivo = get_object_or_404(ObjetivoAprendizagem, id=objetivo_id)
    aluno_id = request.POST.get('aluno_id')
    aluno = get_object_or_404(User, id=aluno_id)
    
    status, _ = StatusObjetivo.objects.get_or_create(
        aluno=aluno,
        objetivo=objetivo,
        defaults={'status': 'nao_iniciado'}
    )
    
    resultado = request.POST.get('resultado') == 'true'
    comentarios = request.POST.get('comentarios', '')
    evidencias = request.POST.get('evidencias', '')
    
    avaliacao = RegistroAvaliacao.objects.create(
        status_objetivo=status,
        avaliador=request.user,
        resultado=resultado,
        comentarios=comentarios,
        evidencias=evidencias
    )
    
    if resultado:
        status.status = 'validado'
        status.validado_por = request.user
        status.save()
    
    messages.success(request, 'Avaliação registrada com sucesso!')
    return redirect('detalhe_objetivo', objetivo_id=objetivo_id)

@login_required
def lista_aluno(request):
    """View para exibir a lista de objetivos do aluno"""
    if request.user.profile.user_type != 'student':
        messages.error(request, 'Acesso restrito a alunos.')
        return redirect('lista_objetivos')
    
    dominios = DominioAprendizagem.objects.all()
    status_objetivos = StatusObjetivo.objects.filter(aluno=request.user)
    
    # Criar um dicionário para mapear objetivos para seus status
    status_map = {so.objetivo_id: so for so in status_objetivos}
    
    context = {
        'dominios': dominios,
        'status_map': status_map,
    }
    return render(request, 'listas_verificacao/lista_aluno.html', context)

@login_required
def dashboard_professor(request):
    """View para exibir o dashboard do professor com o progresso dos alunos"""
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso restrito a professores.')
        return redirect('lista_objetivos')
    
    alunos = User.objects.filter(profile__user_type='student')  # Ajuste conforme seu modelo de usuário
    dominios = DominioAprendizagem.objects.all()
    
    # Criar um dicionário com o progresso de cada aluno por domínio
    progresso_alunos = {}
    for aluno in alunos:
        progresso_alunos[aluno.id] = {}
        for dominio in dominios:
            objetivos_dominio = ObjetivoAprendizagem.objects.filter(dominio=dominio)
            status_aluno = StatusObjetivo.objects.filter(
                aluno=aluno,
                objetivo__in=objetivos_dominio
            )
            
            total_objetivos = objetivos_dominio.count()
            objetivos_validados = status_aluno.filter(status='validado').count()
            
            progresso_alunos[aluno.id][dominio.codigo] = {
                'total': total_objetivos,
                'validados': objetivos_validados,
                'percentual': (objetivos_validados / total_objetivos * 100) if total_objetivos > 0 else 0
            }
    
    context = {
        'alunos': alunos,
        'dominios': dominios,
        'progresso_alunos': progresso_alunos,
    }
    return render(request, 'listas_verificacao/dashboard_professor.html', context)

@login_required
def lista_turmas(request):
    """View para listar as turmas do professor"""
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso restrito a professores.')
        return redirect('lista_objetivos')
    
    turmas = Turma.objects.filter(professor=request.user, ativa=True)
    context = {
        'turmas': turmas,
    }
    return render(request, 'listas_verificacao/lista_turmas.html', context)

@login_required
def criar_turma(request):
    """View para criar uma nova turma"""
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso restrito a professores.')
        return redirect('lista_objetivos')
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        ano_escolar = request.POST.get('ano_escolar')
        disciplina = request.POST.get('disciplina')
        
        try:
            turma = Turma.objects.create(
                nome=nome,
                professor=request.user,
                ano_escolar=ano_escolar,
                disciplina=disciplina
            )
            messages.success(request, 'Turma criada com sucesso!')
            return redirect('listas_verificacao:lista_turmas')
        except Exception as e:
            messages.error(request, f'Erro ao criar turma: {str(e)}')
    
    return render(request, 'listas_verificacao/criar_turma.html')

@login_required
def gerenciar_turma(request, turma_id):
    """View para gerenciar uma turma específica"""
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso restrito a professores.')
        return redirect('lista_objetivos')
    
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    
    if request.method == 'POST':
        if 'remover_alunos' in request.POST:
            alunos_ids = request.POST.getlist('alunos')
            turma.alunos.remove(*alunos_ids)
            messages.success(request, 'Alunos removidos com sucesso!')
        elif 'adicionar_alunos' in request.POST:
            alunos_ids = request.POST.getlist('alunos')
            turma.alunos.add(*alunos_ids)
            messages.success(request, 'Alunos adicionados com sucesso!')
    
    # Buscar alunos disponíveis (que não estão na turma)
    alunos_disponiveis = User.objects.filter(
        profile__user_type='student'
    ).exclude(
        id__in=turma.alunos.values_list('id', flat=True)
    )
    
    context = {
        'turma': turma,
        'alunos_disponiveis': alunos_disponiveis,
    }
    return render(request, 'listas_verificacao/gerenciar_turma.html', context)

@login_required
def dashboard_turma(request, turma_id):
    """View para exibir o dashboard de uma turma específica"""
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso restrito a professores.')
        return redirect('lista_objetivos')
    
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    dominios = DominioAprendizagem.objects.all()
    
    # Criar um dicionário com o progresso de cada aluno por domínio
    progresso_alunos = {}
    for aluno in turma.alunos.all():
        progresso_alunos[aluno.id] = {}
        for dominio in dominios:
            objetivos_dominio = ObjetivoAprendizagem.objects.filter(dominio=dominio)
            status_aluno = StatusObjetivo.objects.filter(
                aluno=aluno,
                objetivo__in=objetivos_dominio
            )
            
            total_objetivos = objetivos_dominio.count()
            objetivos_validados = status_aluno.filter(status='validado').count()
            
            progresso_alunos[aluno.id][dominio.codigo] = {
                'total': total_objetivos,
                'validados': objetivos_validados,
                'percentual': (objetivos_validados / total_objetivos * 100) if total_objetivos > 0 else 0
            }
    
    context = {
        'turma': turma,
        'dominios': dominios,
        'progresso_alunos': progresso_alunos,
        'tem_alunos': turma.alunos.exists(),  # Adicionar flag para verificar se há alunos
    }
    return render(request, 'listas_verificacao/dashboard_turma.html', context)
