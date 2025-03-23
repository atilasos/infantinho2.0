from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import (
    Turma, ListaVerificacao, ProgressoAluno, Objetivo,
    CategoriaObjetivo, ObjetivoPredefinido
)
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone
from .forms import (
    ListaVerificacaoForm, TurmaForm, ObjetivoForm,
    CategoriaObjetivoForm, ObjetivoPredefinidoForm
)
import json

User = get_user_model()

@login_required
def lista_aluno(request):
    if request.user.profile.user_type != 'student':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    # Buscar todas as listas de verificação do aluno
    listas = ListaVerificacao.objects.filter(
        Q(turma__alunos=request.user) | 
        Q(turma__isnull=True)
    ).distinct()
    
    # Buscar o progresso do aluno para cada lista
    progresso = {}
    status_map = {}
    
    for lista in listas:
        progresso_aluno = ProgressoAluno.objects.filter(
            aluno=request.user,
            lista_verificacao=lista
        ).first()
        
        if progresso_aluno:
            progresso[lista.id] = progresso_aluno
            # Converter os estados dos objetivos para o formato esperado
            for objetivo in lista.objetivos.all():
                status = progresso_aluno.get_estado_objetivo(objetivo.id)
                status_map[objetivo.id] = {
                    'status': status,
                    'get_status_display': dict(ProgressoAluno.ESTADOS).get(status, 'Não Iniciado')
                }
    
    context = {
        'listas': listas,
        'progresso': progresso,
        'status_map': status_map,
    }
    return render(request, 'listas_verificacao/lista_aluno.html', context)

@login_required
def detalhe_objetivo(request, objetivo_id):
    objetivo = get_object_or_404(Objetivo, id=objetivo_id)
    
    # Verificar se o aluno tem acesso ao objetivo
    if not (objetivo.lista_verificacao.turma and request.user in objetivo.lista_verificacao.turma.alunos.all()):
        messages.error(request, 'Você não tem acesso a este objetivo.')
        return redirect('listas_verificacao:lista_aluno')
    
    # Buscar o progresso do aluno
    progresso = ProgressoAluno.objects.filter(
        aluno=request.user,
        lista_verificacao=objetivo.lista_verificacao
    ).first()
    
    status = None
    if progresso:
        status_atual = progresso.get_estado_objetivo(objetivo.id)
        status = {
            'status': status_atual,
            'get_status_display': dict(ProgressoAluno.ESTADOS).get(status_atual, 'Não Iniciado'),
            'data_atualizacao': progresso.data_atualizacao
        }
    
    context = {
        'objetivo': objetivo,
        'status': status,
        'avaliacoes': []  # Implementar histórico de avaliações posteriormente
    }
    return render(request, 'listas_verificacao/detalhe_objetivo.html', context)

@login_required
@require_POST
def atualizar_status_objetivo(request, objetivo_id):
    if request.user.profile.user_type != 'student':
        return JsonResponse({'error': 'Acesso não autorizado.'}, status=403)
    
    objetivo = get_object_or_404(Objetivo, id=objetivo_id)
    
    # Verificar se o aluno tem acesso ao objetivo
    if not (objetivo.lista_verificacao.turma and request.user in objetivo.lista_verificacao.turma.alunos.all()):
        return JsonResponse({'error': 'Você não tem acesso a este objetivo.'}, status=403)
    
    try:
        data = json.loads(request.body)
        novo_status = data.get('status')
        
        # Mapear os valores do prompt para os estados reais
        status_map = {
            '1': 'nao_iniciado',
            '2': 'em_progresso',
            '3': 'concluido'
        }
        
        novo_status = status_map.get(novo_status)
        if not novo_status:
            return JsonResponse({'error': 'Status inválido.'}, status=400)
        
        # Buscar ou criar o progresso do aluno
        progresso, created = ProgressoAluno.objects.get_or_create(
            aluno=request.user,
            lista_verificacao=objetivo.lista_verificacao
        )
        
        # Atualizar o estado do objetivo
        if progresso.set_estado_objetivo(objetivo.id, novo_status):
            return JsonResponse({
                'success': True,
                'status': novo_status,
                'status_display': dict(ProgressoAluno.ESTADOS).get(novo_status)
            })
        else:
            return JsonResponse({'error': 'Não foi possível atualizar o status.'}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Dados inválidos.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_professor(request):
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turmas = Turma.objects.filter(professor=request.user)
    
    context = {
        'turmas': turmas,
    }
    return render(request, 'listas_verificacao/dashboard_professor.html', context)

@login_required
def lista_turmas(request):
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turmas = Turma.objects.filter(professor=request.user)
    
    context = {
        'turmas': turmas,
    }
    return render(request, 'listas_verificacao/lista_turmas.html', context)

@login_required
def criar_turma(request):
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    if request.method == 'POST':
        form = TurmaForm(request.POST)
        if form.is_valid():
            turma = form.save(commit=False)
            turma.professor = request.user
            turma.save()
            messages.success(request, 'Turma criada com sucesso!')
            return redirect('listas_verificacao:lista_turmas')
    else:
        form = TurmaForm()
    
    context = {
        'form': form,
        'titulo': 'Criar Nova Turma',
    }
    return render(request, 'listas_verificacao/form_turma.html', context)

@login_required
def editar_turma(request, turma_id):
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    
    if request.method == 'POST':
        form = TurmaForm(request.POST, instance=turma)
        if form.is_valid():
            form.save()
            messages.success(request, 'Turma atualizada com sucesso!')
            return redirect('listas_verificacao:lista_turmas')
    else:
        form = TurmaForm(instance=turma)
    
    context = {
        'form': form,
        'titulo': 'Editar Turma',
        'turma': turma,
    }
    return render(request, 'listas_verificacao/form_turma.html', context)

@login_required
def excluir_turma(request, turma_id):
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    
    if request.method == 'POST':
        turma.delete()
        messages.success(request, 'Turma excluída com sucesso!')
        return redirect('listas_verificacao:lista_turmas')
    
    context = {
        'turma': turma,
    }
    return render(request, 'listas_verificacao/confirmar_exclusao_turma.html', context)

@login_required
def adicionar_aluno(request, turma_id):
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    
    if request.method == 'POST':
        aluno_id = request.POST.get('aluno_id')
        aluno = get_object_or_404(User, id=aluno_id)
        
        if aluno.profile.user_type != 'student':
            messages.error(request, 'O usuário selecionado não é um aluno.')
            return redirect('listas_verificacao:gerenciar_turma', turma_id=turma.id)
        
        turma.alunos.add(aluno)
        messages.success(request, f'Aluno {aluno.get_full_name()} adicionado à turma com sucesso!')
        return redirect('listas_verificacao:gerenciar_turma', turma_id=turma.id)
    
    # Buscar alunos que não estão na turma
    alunos_disponiveis = User.objects.filter(
        profile__user_type='student'
    ).exclude(
        turmas_aluno=turma
    )
    
    context = {
        'turma': turma,
        'alunos_disponiveis': alunos_disponiveis,
    }
    return render(request, 'listas_verificacao/adicionar_aluno.html', context)

@login_required
def remover_aluno(request, turma_id, aluno_id):
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    aluno = get_object_or_404(User, id=aluno_id)
    
    if request.method == 'POST':
        turma.alunos.remove(aluno)
        messages.success(request, f'Aluno {aluno.get_full_name()} removido da turma com sucesso!')
        return redirect('listas_verificacao:gerenciar_turma', turma_id=turma.id)
    
    context = {
        'turma': turma,
        'aluno': aluno,
    }
    return render(request, 'listas_verificacao/confirmar_remocao_aluno.html', context)

@login_required
def registrar_progresso(request, lista_id):
    if request.user.profile.user_type != 'student':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    lista = get_object_or_404(ListaVerificacao, id=lista_id)
    
    # Verificar se o aluno tem acesso à lista
    if not (lista.turma and request.user in lista.turma.alunos.all()):
        messages.error(request, 'Você não tem acesso a esta lista de verificação.')
        return redirect('listas_verificacao:lista_aluno')
    
    # Buscar ou criar o progresso do aluno
    progresso, created = ProgressoAluno.objects.get_or_create(
        aluno=request.user,
        lista_verificacao=lista,
        defaults={'objetivos_concluidos': []}
    )
    
    if request.method == 'POST':
        objetivos_concluidos = request.POST.getlist('objetivos_concluidos')
        progresso.objetivos_concluidos = objetivos_concluidos
        progresso.save()
        
        messages.success(request, 'Progresso registrado com sucesso!')
        return redirect('listas_verificacao:lista_aluno')
    
    context = {
        'lista': lista,
        'progresso': progresso,
    }
    return render(request, 'listas_verificacao/registrar_progresso.html', context)

@login_required
def dashboard_turma(request, turma_id):
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    listas = ListaVerificacao.objects.filter(turma=turma)
    
    # Calcular progresso geral da turma
    progresso_turma = {}
    for lista in listas:
        progressos = ProgressoAluno.objects.filter(lista_verificacao=lista)
        total_alunos = turma.alunos.count()
        if total_alunos > 0:
            progresso_medio = sum(p.porcentagem_conclusao for p in progressos) / total_alunos
            progresso_turma[lista.id] = {
                'lista': lista,
                'progresso_medio': progresso_medio,
                'total_alunos': total_alunos,
                'alunos_concluidos': sum(1 for p in progressos if p.porcentagem_conclusao == 100)
            }
    
    context = {
        'turma': turma,
        'listas': listas,
        'progresso_turma': progresso_turma,
    }
    return render(request, 'listas_verificacao/dashboard_turma.html', context)

@login_required
def gerenciar_categorias(request):
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    categorias = CategoriaObjetivo.objects.all()
    
    if request.method == 'POST':
        form = CategoriaObjetivoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoria criada com sucesso!')
            return redirect('listas_verificacao:gerenciar_categorias')
    else:
        form = CategoriaObjetivoForm()
    
    context = {
        'categorias': categorias,
        'form': form,
    }
    return render(request, 'listas_verificacao/gerenciar_categorias.html', context)

@login_required
def gerenciar_objetivos_predefinidos(request):
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    objetivos = ObjetivoPredefinido.objects.all()
    
    if request.method == 'POST':
        form = ObjetivoPredefinidoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Objetivo predefinido criado com sucesso!')
            return redirect('listas_verificacao:gerenciar_objetivos_predefinidos')
    else:
        form = ObjetivoPredefinidoForm()
    
    context = {
        'objetivos': objetivos,
        'form': form,
    }
    return render(request, 'listas_verificacao/gerenciar_objetivos_predefinidos.html', context)

@login_required
def criar_lista_verificacao(request):
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    if request.method == 'POST':
        form = ListaVerificacaoForm(request.POST)
        if form.is_valid():
            lista = form.save()
            messages.success(request, 'Lista de verificação criada com sucesso!')
            return redirect('listas_verificacao:dashboard_turma', turma_id=lista.turma.id)
    else:
        form = ListaVerificacaoForm()
    
    context = {
        'form': form,
        'titulo': 'Criar Nova Lista de Verificação',
    }
    return render(request, 'listas_verificacao/form_lista_verificacao.html', context)

@login_required
def editar_lista_verificacao(request, lista_id):
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    lista = get_object_or_404(ListaVerificacao, id=lista_id)
    
    if request.method == 'POST':
        form = ListaVerificacaoForm(request.POST, instance=lista)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lista de verificação atualizada com sucesso!')
            return redirect('listas_verificacao:dashboard_turma', turma_id=lista.turma.id)
    else:
        form = ListaVerificacaoForm(instance=lista)
    
    context = {
        'form': form,
        'titulo': 'Editar Lista de Verificação',
        'lista': lista,
    }
    return render(request, 'listas_verificacao/form_lista_verificacao.html', context)

@login_required
def excluir_lista_verificacao(request, lista_id):
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    lista = get_object_or_404(ListaVerificacao, id=lista_id)
    turma_id = lista.turma.id
    
    if request.method == 'POST':
        lista.delete()
        messages.success(request, 'Lista de verificação excluída com sucesso!')
        return redirect('listas_verificacao:dashboard_turma', turma_id=turma_id)
    
    context = {
        'lista': lista,
    }
    return render(request, 'listas_verificacao/confirmar_exclusao_lista.html', context)

@login_required
def editar_categoria(request, categoria_id):
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    categoria = get_object_or_404(CategoriaObjetivo, id=categoria_id)
    
    if request.method == 'POST':
        form = CategoriaObjetivoForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoria atualizada com sucesso!')
            return redirect('listas_verificacao:gerenciar_categorias')
    else:
        form = CategoriaObjetivoForm(instance=categoria)
    
    context = {
        'form': form,
        'categoria': categoria,
        'titulo': 'Editar Categoria',
    }
    return render(request, 'listas_verificacao/form_categoria.html', context)

@login_required
def excluir_categoria(request, categoria_id):
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    categoria = get_object_or_404(CategoriaObjetivo, id=categoria_id)
    
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, 'Categoria excluída com sucesso!')
        return redirect('listas_verificacao:gerenciar_categorias')
    
    context = {
        'categoria': categoria,
    }
    return render(request, 'listas_verificacao/confirmar_exclusao_categoria.html', context)

@login_required
def editar_objetivo_predefinido(request, objetivo_id):
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    objetivo = get_object_or_404(ObjetivoPredefinido, id=objetivo_id)
    
    if request.method == 'POST':
        form = ObjetivoPredefinidoForm(request.POST, instance=objetivo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Objetivo predefinido atualizado com sucesso!')
            return redirect('listas_verificacao:gerenciar_objetivos_predefinidos')
    else:
        form = ObjetivoPredefinidoForm(instance=objetivo)
    
    context = {
        'form': form,
        'objetivo': objetivo,
        'titulo': 'Editar Objetivo Predefinido',
    }
    return render(request, 'listas_verificacao/form_objetivo_predefinido.html', context)

@login_required
def excluir_objetivo_predefinido(request, objetivo_id):
    if request.user.profile.user_type != 'teacher':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    objetivo = get_object_or_404(ObjetivoPredefinido, id=objetivo_id)
    
    if request.method == 'POST':
        objetivo.delete()
        messages.success(request, 'Objetivo predefinido excluído com sucesso!')
        return redirect('listas_verificacao:gerenciar_objetivos_predefinidos')
    
    context = {
        'objetivo': objetivo,
    }
    return render(request, 'listas_verificacao/confirmar_exclusao_objetivo.html', context)
