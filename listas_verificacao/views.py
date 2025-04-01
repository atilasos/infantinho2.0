from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from .models import (
    Turma, ListaVerificacao, ProgressoAluno, Objetivo,
    CategoriaObjetivo, ObjetivoPredefinido, Disciplina,
    Domínio, Subdomínio, AprendizagemEssencial, Notificacao,
    ConfiguracaoNotificacao
)
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone
from .forms import (
    ListaVerificacaoForm, TurmaForm, ObjetivoForm,
    CategoriaObjetivoForm, ObjetivoPredefinidoForm,
    ImportarAprendizagensForm, AprendizagemEssencialForm,
    ConfiguracaoNotificacaoForm
)
import json
import csv
import io
import re
from django.core.paginator import Paginator
import itertools

User = get_user_model()

@login_required
def lista_aluno(request):
    if not request.user.is_student:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    # Buscar todas as listas de verificação do aluno
    listas = ListaVerificacao.objects.filter(
        Q(turma__alunos=request.user) | 
        Q(turma__isnull=True)
    ).distinct()
    
    # Buscar o progresso do aluno para cada lista
    progresso = {}
    
    for lista in listas:
        # Ordenar aprendizagens por código
        aprendizagens = lista.aprendizagens.all().order_by('codigo')
        
        progressos = ProgressoAluno.objects.filter(
            aluno=request.user,
            lista_verificacao=lista
        )
        
        if progressos.exists():
            progresso[lista.id] = {
                'aprendizagens_concluidas': progressos.filter(estado='concluido').count(),
                'progressos': {p.aprendizagem_id: p for p in progressos},
                'aprendizagens': aprendizagens
            }
        else:
            # Inicializar com progresso vazio para listas sem progresso
            progresso[lista.id] = {
                'aprendizagens_concluidas': 0,
                'progressos': {},
                'aprendizagens': aprendizagens
            }
    
    context = {
        'listas': listas,
        'progresso': progresso,
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
    if not request.user.is_student:
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
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turmas = Turma.objects.filter(professor=request.user)
    
    context = {
        'turmas': turmas,
    }
    return render(request, 'listas_verificacao/dashboard_professor.html', context)

@login_required
def lista_turmas(request):
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turmas = Turma.objects.filter(professor=request.user)
    
    context = {
        'turmas': turmas,
    }
    return render(request, 'listas_verificacao/lista_turmas.html', context)

@login_required
def criar_turma(request):
    if not request.user.is_teacher:
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
    if not request.user.is_teacher:
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
    if not request.user.is_teacher:
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
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    
    if request.method == 'POST':
        aluno_id = request.POST.get('aluno_id')
        aluno = get_object_or_404(User, id=aluno_id)
        
        if not aluno.is_student:
            messages.error(request, 'O usuário selecionado não é um aluno.')
            return redirect('listas_verificacao:dashboard_turma', turma_id=turma.id)
        
        turma.alunos.add(aluno)
        messages.success(request, f'Aluno {aluno.get_full_name()} adicionado à turma com sucesso!')
        return redirect('listas_verificacao:dashboard_turma', turma_id=turma.id)
    
    # Buscar alunos que não estão na turma
    alunos_disponiveis = User.objects.filter(
        groups__name='student'
    ).exclude(
        turmas_aluno=turma
    ).distinct()
    
    context = {
        'turma': turma,
        'alunos_disponiveis': alunos_disponiveis,
    }
    return render(request, 'listas_verificacao/adicionar_aluno.html', context)

@login_required
def remover_aluno(request, turma_id, aluno_id):
    if not request.user.is_teacher:
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
    if not request.user.is_student:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    lista = get_object_or_404(ListaVerificacao, id=lista_id)
    
    if request.method == 'POST':
        # Iterar sobre todas as aprendizagens da lista
        for aprendizagem in lista.aprendizagens.all():
            estado = request.POST.get(f'estado_{aprendizagem.id}')
            if estado:
                # Criar ou atualizar o progresso
                progresso, created = ProgressoAluno.objects.update_or_create(
                    aluno=request.user,
                    lista_verificacao=lista,
                    aprendizagem=aprendizagem,
                    defaults={'estado': estado}
                )
                print(f"Progresso {'criado' if created else 'atualizado'} para {aprendizagem.codigo}: {estado}")
        
        messages.success(request, 'Progresso registrado com sucesso!')
        return redirect('listas_verificacao:lista_aluno')
    
    # Buscar progresso existente
    progresso = {}
    progressos_existentes = ProgressoAluno.objects.filter(
        aluno=request.user,
        lista_verificacao=lista
    )
    for p in progressos_existentes:
        progresso[p.aprendizagem_id] = p
    
    context = {
        'lista': lista,
        'progresso': progresso,
        'estados': ProgressoAluno.ESTADOS,
    }
    return render(request, 'listas_verificacao/registrar_progresso.html', context)

@login_required
def dashboard_turma(request, turma_id):
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    
    # Buscar todas as listas da turma
    listas = ListaVerificacao.objects.filter(turma=turma)
    
    # Buscar todos os alunos da turma
    alunos = turma.alunos.all()
    total_alunos = alunos.count()
    
    # Calcular progresso para cada lista
    progresso_listas = []
    for lista in listas:
        progressos = ProgressoAluno.objects.filter(
            lista_verificacao=lista,
            aluno__in=alunos
        )
        
        # Calcular progresso médio da lista
        if total_alunos > 0:
            total_aprendizagens = lista.aprendizagens.count()
            if total_aprendizagens > 0:
                progresso_medio = 0
                for aluno in alunos:
                    progressos_aluno = progressos.filter(aluno=aluno)
                    aprendizagens_concluidas = progressos_aluno.filter(estado='concluido').count()
                    progresso_medio += (aprendizagens_concluidas / total_aprendizagens) * 100
                progresso_medio = progresso_medio / total_alunos
            else:
                progresso_medio = 0
        else:
            progresso_medio = 0
        
        progresso_listas.append({
            'lista': lista,
            'progresso_medio': round(progresso_medio, 1),
            'total_alunos': total_alunos,
            'alunos_concluidos': progressos.filter(estado='concluido').count()
        })
    
    # Calcular progresso geral da turma
    if total_alunos > 0 and listas.exists():
        total_aprendizagens = sum(lista.aprendizagens.count() for lista in listas)
        if total_aprendizagens > 0:
            progresso_geral = 0
            for aluno in alunos:
                progressos_aluno = ProgressoAluno.objects.filter(
                    aluno=aluno,
                    lista_verificacao__in=listas
                )
                aprendizagens_concluidas = progressos_aluno.filter(estado='concluido').count()
                progresso_geral += (aprendizagens_concluidas / total_aprendizagens) * 100
            progresso_geral = progresso_geral / total_alunos
        else:
            progresso_geral = 0
    else:
        progresso_geral = 0
    
    context = {
        'turma': turma,
        'listas': progresso_listas,
        'total_alunos': total_alunos,
        'progresso_geral': round(progresso_geral, 1),
    }
    return render(request, 'listas_verificacao/dashboard_turma.html', context)

@login_required
def gerenciar_categorias(request):
    if not request.user.is_teacher:
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
    if not request.user.is_teacher:
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
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    # Obter a turma do parâmetro GET se existir
    turma_id = request.GET.get('turma')
    turma = None
    if turma_id:
        turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    
    if request.method == 'POST':
        form = ListaVerificacaoForm(request.POST)
        if form.is_valid():
            lista = form.save()
            messages.success(request, 'Lista de verificação criada com sucesso!')
            if lista.turma:
                return redirect('listas_verificacao:dashboard_turma', turma_id=lista.turma.id)
            return redirect('listas_verificacao:dashboard_professor')
    else:
        form = ListaVerificacaoForm(initial={'turma': turma} if turma else None)
    
    context = {
        'form': form,
        'titulo': 'Criar Nova Lista de Verificação',
        'turma': turma,
    }
    return render(request, 'listas_verificacao/form_lista_verificacao.html', context)

@login_required
def editar_lista_verificacao(request, lista_id):
    if not request.user.is_teacher:
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
    if not request.user.is_teacher:
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
    if not request.user.is_teacher:
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
    if not request.user.is_teacher:
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
    if not request.user.is_teacher:
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
    if not request.user.is_teacher:
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

def extrair_codigo_dominio(codigo_aprendizagem):
    """Extrai o código do domínio do código da aprendizagem essencial"""
    match = re.match(r'([A-Z]+)\d+', codigo_aprendizagem)
    if match:
        return match.group(1)
    return None

@login_required
def importar_aprendizagens(request):
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    if request.method == 'POST':
        form = ImportarAprendizagensForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                disciplina = form.cleaned_data['disciplina']
                ano_escolar = form.cleaned_data['ano_escolar']
                arquivo_csv = request.FILES['arquivo_csv']
                
                # Ler o arquivo CSV
                csv_file = io.TextIOWrapper(arquivo_csv, encoding='iso-8859-1')
                csv_reader = csv.reader(csv_file)
                
                # Criar ou obter domínios
                dominios = {}
                for row in csv_reader:
                    if not row:  # Pular linhas vazias
                        continue
                    
                    codigo_aprendizagem = row[0].strip()
                    descricao = row[1].strip()
                    
                    # Extrair código do domínio
                    codigo_dominio = extrair_codigo_dominio(codigo_aprendizagem)
                    if not codigo_dominio:
                        continue
                    
                    # Criar ou obter domínio
                    dominio, _ = Domínio.objects.get_or_create(
                        codigo=codigo_dominio,
                        disciplina=disciplina,
                        defaults={'nome': f'Domínio {codigo_dominio}'}
                    )
                    
                    # Criar aprendizagem essencial
                    AprendizagemEssencial.objects.create(
                        codigo=codigo_aprendizagem,
                        descricao=descricao,
                        disciplina=disciplina,
                        dominio=dominio,
                        ano_escolar=ano_escolar
                    )
                
                messages.success(request, 'Aprendizagens essenciais importadas com sucesso!')
                return redirect('listas_verificacao:gerenciar_aprendizagens')
            
            except Exception as e:
                messages.error(request, f'Erro ao importar aprendizagens: {str(e)}')
    else:
        form = ImportarAprendizagensForm()
    
    context = {
        'form': form,
        'titulo': 'Importar Aprendizagens Essenciais'
    }
    return render(request, 'listas_verificacao/importar_aprendizagens.html', context)

@login_required
def gerenciar_aprendizagens(request):
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    disciplinas = Disciplina.objects.all()
    aprendizagens = AprendizagemEssencial.objects.all().order_by('disciplina', 'ano_escolar', 'ordem')
    
    context = {
        'disciplinas': disciplinas,
        'aprendizagens': aprendizagens,
    }
    return render(request, 'listas_verificacao/gerenciar_aprendizagens.html', context)

@login_required
def editar_aprendizagem(request, aprendizagem_id):
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    aprendizagem = get_object_or_404(AprendizagemEssencial, id=aprendizagem_id)
    
    if request.method == 'POST':
        form = AprendizagemEssencialForm(request.POST, instance=aprendizagem)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aprendizagem essencial atualizada com sucesso!')
            return redirect('listas_verificacao:gerenciar_aprendizagens')
    else:
        form = AprendizagemEssencialForm(instance=aprendizagem)
    
    context = {
        'form': form,
        'aprendizagem': aprendizagem,
        'titulo': 'Editar Aprendizagem Essencial'
    }
    return render(request, 'listas_verificacao/form_aprendizagem.html', context)

@login_required
def excluir_aprendizagem(request, aprendizagem_id):
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    aprendizagem = get_object_or_404(AprendizagemEssencial, id=aprendizagem_id)
    
    if request.method == 'POST':
        aprendizagem.delete()
        messages.success(request, 'Aprendizagem essencial excluída com sucesso!')
        return redirect('listas_verificacao:gerenciar_aprendizagens')
    
    context = {
        'aprendizagem': aprendizagem,
    }
    return render(request, 'listas_verificacao/confirmar_exclusao_aprendizagem.html', context)

@login_required
def lista_notificacoes(request):
    """Lista todas as notificações do usuário logado."""
    notificacoes = Notificacao.objects.filter(destinatario=request.user).order_by('-data_criacao')
    
    # Paginação
    paginator = Paginator(notificacoes, 10)  # 10 notificações por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notificacoes': page_obj,
        'tipos_notificacao': Notificacao.TIPOS,
        'is_paginated': True,
        'page_obj': page_obj,
    }
    
    return render(request, 'listas_verificacao/notificacoes/lista_notificacoes.html', context)

@login_required
@require_POST
def marcar_notificacao_lida(request, notificacao_id):
    """Marca uma notificação como lida."""
    try:
        notificacao = Notificacao.objects.get(
            id=notificacao_id,
            destinatario=request.user
        )
        notificacao.marcar_como_lida()
        return JsonResponse({'success': True})
    except Notificacao.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notificação não encontrada'}, status=404)

@login_required
def configurar_notificacoes(request):
    """
    View para configurar as preferências de notificação do usuário.
    """
    config, created = ConfiguracaoNotificacao.objects.get_or_create(usuario=request.user)
    
    if request.method == 'POST':
        form = ConfiguracaoNotificacaoForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configurações de notificação atualizadas com sucesso!')
            return redirect('listas_verificacao:configurar_notificacoes')
    else:
        form = ConfiguracaoNotificacaoForm(instance=config)
    
    return render(request, 'listas_verificacao/notificacoes/configurar_notificacoes.html', {
        'form': form,
        'config': config
    })

@login_required
def relatorio_progresso_turma(request, turma_id):
    """
    View para exibir o relatório detalhado de progresso de uma turma.
    """
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    
    # Gerar relatório
    from listas_verificacao.services.report_service import gerar_relatorio_progresso_turma
    relatorio = gerar_relatorio_progresso_turma(turma)
    
    context = {
        'relatorio': relatorio,
        'turma': turma,
    }
    
    return render(request, 'listas_verificacao/relatorios/progresso_turma.html', context)

@login_required
def relatorio_progresso_aluno(request, turma_id, aluno_id):
    """
    View para exibir o relatório detalhado de progresso de um aluno.
    """
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    aluno = get_object_or_404(User, id=aluno_id)
    
    # Verificar se o aluno pertence à turma
    if aluno not in turma.alunos.all():
        messages.error(request, 'Este aluno não pertence à turma.')
        return redirect('listas_verificacao:dashboard_turma', turma_id=turma.id)
    
    # Gerar relatório
    from listas_verificacao.services.report_service import gerar_relatorio_progresso_aluno
    relatorio = gerar_relatorio_progresso_aluno(aluno, turma)
    
    context = {
        'relatorio': relatorio,
        'turma': turma,
        'aluno': aluno,
    }
    
    return render(request, 'listas_verificacao/relatorios/progresso_aluno.html', context)

@login_required
def relatorio_tempo_conclusao(request, turma_id):
    """
    View para exibir o relatório de tempo médio de conclusão das listas.
    """
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    
    # Gerar relatório
    from listas_verificacao.services.report_service import gerar_relatorio_tempo_conclusao
    relatorio = gerar_relatorio_tempo_conclusao(turma)
    
    context = {
        'relatorio': relatorio,
        'turma': turma,
    }
    
    return render(request, 'listas_verificacao/relatorios/tempo_conclusao.html', context)

@login_required
def relatorio_objetivos_dificeis(request, turma_id):
    """
    View para exibir o relatório de objetivos mais difíceis.
    """
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    
    # Gerar relatório
    from listas_verificacao.services.report_service import gerar_relatorio_objetivos_dificeis
    relatorio = gerar_relatorio_objetivos_dificeis(turma)
    
    context = {
        'relatorio': relatorio,
        'turma': turma,
    }
    
    return render(request, 'listas_verificacao/relatorios/objetivos_dificeis.html', context)

@login_required
def relatorio_dificuldades_aluno(request, turma_id, aluno_id):
    """
    View para exibir o relatório de aprendizagens com dificuldade de um aluno.
    """
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    aluno = get_object_or_404(User, id=aluno_id)
    
    # Verificar se o aluno pertence à turma
    if aluno not in turma.alunos.all():
        messages.error(request, 'Este aluno não pertence à turma.')
        return redirect('listas_verificacao:dashboard_turma', turma_id=turma.id)
    
    # Gerar relatório
    from listas_verificacao.services.report_service import gerar_relatorio_dificuldades_aluno
    relatorio = gerar_relatorio_dificuldades_aluno(aluno, turma)
    
    context = {
        'relatorio': relatorio,
        'turma': turma,
        'aluno': aluno,
    }
    
    return render(request, 'listas_verificacao/relatorios/dificuldades_aluno.html', context)

@login_required
def relatorio_aprendizagens_pendentes(request, turma_id):
    """
    View para exibir o relatório de aprendizagens pendentes de confirmação.
    """
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    
    # Gerar relatório
    from listas_verificacao.services.report_service import gerar_relatorio_aprendizagens_pendentes
    relatorio = gerar_relatorio_aprendizagens_pendentes(turma)
    
    context = {
        'relatorio': relatorio,
        'turma': turma,
    }
    
    return render(request, 'listas_verificacao/relatorios/aprendizagens_pendentes.html', context)

@login_required
def relatorio_tendencias_progresso(request, turma_id):
    """
    View para exibir o relatório de tendências de progresso da turma.
    """
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    
    # Gerar relatório
    from listas_verificacao.services.report_service import gerar_relatorio_tendencias_progresso
    relatorio = gerar_relatorio_tendencias_progresso(turma)
    
    context = {
        'relatorio': relatorio,
        'turma': turma,
    }
    
    return render(request, 'listas_verificacao/relatorios/tendencias_progresso.html', context)

@login_required
def relatorio_analise_preditiva(request, turma_id):
    """
    View para exibir o relatório de análise preditiva de desempenho.
    """
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    
    # Gerar relatório
    from listas_verificacao.services.report_service import gerar_relatorio_analise_preditiva
    relatorio = gerar_relatorio_analise_preditiva(turma)
    
    context = {
        'relatorio': relatorio,
        'turma': turma,
    }
    
    return render(request, 'listas_verificacao/relatorios/analise_preditiva.html', context)

@login_required
def relatorio_engajamento(request, turma_id):
    """
    View para exibir o relatório de engajamento dos alunos.
    """
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    
    # Gerar relatório
    from listas_verificacao.services.report_service import gerar_relatorio_engajamento
    relatorio = gerar_relatorio_engajamento(turma)
    
    context = {
        'relatorio': relatorio,
        'turma': turma,
    }
    
    return render(request, 'listas_verificacao/relatorios/engajamento.html', context)

@login_required
def relatorio_cooperacao(request, turma_id):
    """
    View para exibir o relatório de cooperação e partilha de experiências.
    """
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    
    # Gerar relatório
    from listas_verificacao.services.report_service import gerar_relatorio_cooperacao
    relatorio = gerar_relatorio_cooperacao(turma)
    
    context = {
        'relatorio': relatorio,
        'turma': turma,
    }
    
    return render(request, 'listas_verificacao/relatorios/cooperacao.html', context)

@login_required
def visualizacao_progresso_turma(request, turma_id):
    """
    View para exibir a visualização do progresso da turma.
    """
    # Verificar se o usuário é um professor
    if not request.user.is_teacher:
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('listas_verificacao:lista_aluno')
    
    # Buscar a turma
    turma = get_object_or_404(Turma, professor=request.user, id=turma_id)
    
    # Buscar todas as listas da turma
    listas = ListaVerificacao.objects.filter(turma=turma)
    
    # Buscar todos os alunos da turma
    alunos = turma.alunos.all()
    
    # Preparar dados para o gráfico
    datas = []
    progresso_geral = []
    dificuldades = []
    conclusoes = []
    
    # Buscar progressos ordenados por data
    progressos = ProgressoAluno.objects.filter(
        lista_verificacao__in=listas,
        aluno__in=alunos,
        data_atualizacao__isnull=False
    ).order_by('data_atualizacao')
    
    if progressos.exists():
        # Agrupar por data
        progressos_por_data = {}
        for progresso in progressos:
            data = progresso.data_atualizacao.strftime('%Y-%m-%d')
            if data not in progressos_por_data:
                progressos_por_data[data] = {
                    'total': 0,
                    'dificuldades': 0,
                    'conclusoes': 0
                }
            
            progressos_por_data[data]['total'] += 1
            if progresso.estado == 'dificuldade':
                progressos_por_data[data]['dificuldades'] += 1
            elif progresso.estado == 'concluido':
                progressos_por_data[data]['conclusoes'] += 1
        
        # Calcular percentuais
        total_aprendizagens = sum(lista.aprendizagens.count() for lista in listas)
        total_alunos = alunos.count()
        total_possivel = total_aprendizagens * total_alunos
        
        for data, dados in progressos_por_data.items():
            datas.append(data)
            progresso_geral.append(round((dados['conclusoes'] / total_possivel) * 100, 1))
            dificuldades.append(round((dados['dificuldades'] / total_possivel) * 100, 1))
            conclusoes.append(round((dados['conclusoes'] / total_possivel) * 100, 1))
    
    context = {
        'turma': turma,
        'datas': datas,
        'progresso_geral': progresso_geral,
        'dificuldades': dificuldades,
        'conclusoes': conclusoes
    }
    
    return render(request, 'listas_verificacao/visualizacoes/progresso_turma.html', context)

@login_required
def visualizacao_heatmap_atividade(request, turma_id):
    """
    View para exibir o heatmap de atividade da turma.
    """
    # Verificar se o usuário é um professor
    if not request.user.is_teacher:
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('listas_verificacao:lista_aluno')
    
    # Buscar a turma
    turma = get_object_or_404(Turma, professor=request.user, id=turma_id)
    
    # Buscar todas as listas da turma
    listas = ListaVerificacao.objects.filter(turma=turma)
    
    # Buscar todos os alunos da turma
    alunos = turma.alunos.all()
    
    # Preparar dados para o heatmap
    dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    horas_dia = [str(h) + 'h' for h in range(24)]
    
    # Inicializar matriz de atividade
    atividade = {}
    for dia in dias_semana:
        atividade[dia] = {hora: 0 for hora in horas_dia}
    
    # Buscar progressos com data de atualização
    progressos = ProgressoAluno.objects.filter(
        lista_verificacao__in=listas,
        aluno__in=alunos,
        data_atualizacao__isnull=False
    )
    
    # Contar atividades por dia e hora
    for progresso in progressos:
        dia = progresso.data_atualizacao.strftime('%A')  # Nome do dia em inglês
        hora = progresso.data_atualizacao.strftime('%H') + 'h'
        
        # Mapear nome do dia em inglês para português
        dia_mapping = {
            'Monday': 'Segunda',
            'Tuesday': 'Terça',
            'Wednesday': 'Quarta',
            'Thursday': 'Quinta',
            'Friday': 'Sexta',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }
        
        if dia in dia_mapping:
            dia = dia_mapping[dia]
            atividade[dia][hora] += 1
    
    # Preparar datasets para o Chart.js
    datasets = []
    for dia in dias_semana:
        for hora in horas_dia:
            count = atividade[dia][hora]
            # Calcular intensidade baseada no número de atividades
            intensity = min(4, max(1, count // 5 + 1))  # 1-4 níveis de intensidade
            
            datasets.append({
                x: hora,
                y: dia,
                v: hora,
                c: count,
                backgroundColor: [
                    '#e8f5e9',  # Baixa atividade
                    '#c8e6c9',  # Média atividade
                    '#a5d6a7',  # Alta atividade
                    '#81c784'   # Muito alta atividade
                ][intensity - 1]
            })
    
    context = {
        'turma': turma,
        'dias_semana': dias_semana,
        'datasets': datasets
    }
    
    return render(request, 'listas_verificacao/visualizacoes/heatmap_atividade.html', context)

@login_required
def visualizacao_tendencias(request, turma_id):
    # Verificar se o usuário é um professor
    if not request.user.is_teacher:
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('listas_verificacao:lista_alunos')
    
    # Buscar a turma do professor logado
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    
    # Buscar todas as listas da turma
    listas = ListaVerificacao.objects.filter(turma=turma)
    
    # Buscar todos os alunos da turma
    alunos = turma.alunos.all()
    
    # Inicializar listas para os dados dos gráficos
    datas = []
    progresso_datasets = []
    dificuldades_datasets = []
    velocidade_datasets = []
    engajamento_datasets = []
    
    # Buscar todos os progressos ordenados por data
    progressos = ProgressoAluno.objects.filter(
        aluno__in=alunos,
        data_atualizacao__isnull=False
    ).order_by('data_atualizacao')
    
    if progressos.exists():
        # Agrupar dados por data
        dados_por_data = {}
        for progresso in progressos:
            data = progresso.data_atualizacao.strftime('%d/%m/%Y')
            if data not in dados_por_data:
                dados_por_data[data] = {
                    'total_progresso': 0,
                    'total_dificuldades': 0,
                    'total_velocidade': 0,
                    'total_engajamento': 0,
                    'count': 0
                }
            
            dados_por_data[data]['total_progresso'] += progresso.percentual_progresso
            dados_por_data[data]['total_dificuldades'] += progresso.percentual_dificuldades
            dados_por_data[data]['total_velocidade'] += progresso.velocidade_progresso
            dados_por_data[data]['total_engajamento'] += progresso.percentual_engajamento
            dados_por_data[data]['count'] += 1
        
        # Calcular médias e preparar datasets
        for data, dados in dados_por_data.items():
            datas.append(data)
            
            # Calcular médias
            media_progresso = dados['total_progresso'] / dados['count']
            media_dificuldades = dados['total_dificuldades'] / dados['count']
            media_velocidade = dados['total_velocidade'] / dados['count']
            media_engajamento = dados['total_engajamento'] / dados['count']
            
            # Adicionar aos datasets
            progresso_datasets.append({
                'label': 'Progresso Geral',
                'data': [media_progresso],
                'borderColor': 'rgb(75, 192, 192)',
                'tension': 0.1
            })
            
            dificuldades_datasets.append({
                'label': 'Dificuldades',
                'data': [media_dificuldades],
                'borderColor': 'rgb(255, 99, 132)',
                'tension': 0.1
            })
            
            velocidade_datasets.append({
                'label': 'Velocidade',
                'data': [media_velocidade],
                'borderColor': 'rgb(54, 162, 235)',
                'tension': 0.1
            })
            
            engajamento_datasets.append({
                'label': 'Engajamento',
                'data': [media_engajamento],
                'borderColor': 'rgb(153, 102, 255)',
                'tension': 0.1
            })
    
    context = {
        'turma': turma,
        'datas': json.dumps(datas),
        'progresso_datasets': json.dumps(progresso_datasets),
        'dificuldades_datasets': json.dumps(dificuldades_datasets),
        'velocidade_datasets': json.dumps(velocidade_datasets),
        'engajamento_datasets': json.dumps(engajamento_datasets)
    }
    
    return render(request, 'listas_verificacao/visualizacoes/tendencias.html', context)

@login_required
def dashboard_interativo(request, turma_id):
    # Verificar se o usuário é um professor
    if not hasattr(request.user, 'professor'):
        messages.error(request, 'Acesso negado. Apenas professores podem acessar esta página.')
        return redirect('listas_verificacao:lista_alunos')

    # Buscar a turma
    turma = get_object_or_404(Turma, professor=request.user.professor, id=turma_id)
    
    # Buscar todas as listas e alunos da turma
    listas = ListaVerificacao.objects.filter(turma=turma)
    alunos = turma.alunos.all()
    
    # Calcular métricas principais
    total_alunos = alunos.count()
    total_listas = listas.count()
    
    # Calcular progresso geral
    progressos = ProgressoAluno.objects.filter(aluno__in=alunos)
    if progressos.exists():
        total_aprendizados = sum(p.aprendizados.count() for p in progressos)
        total_objetivos = sum(l.objetivos.count() for l in listas)
        progresso_geral = round((total_aprendizados / total_objetivos) * 100) if total_objetivos > 0 else 0
    else:
        progresso_geral = 0
    
    # Calcular alunos ativos (com atividade nos últimos 7 dias)
    data_limite = timezone.now() - timezone.timedelta(days=7)
    alunos_ativos = alunos.filter(progressoaluno__data_atualizacao__gte=data_limite).distinct().count()
    percentual_alunos_ativos = round((alunos_ativos / total_alunos) * 100) if total_alunos > 0 else 0
    
    # Calcular listas concluídas
    listas_concluidas = sum(1 for l in listas if l.objetivos.filter(aprendizado__isnull=False).exists())
    percentual_listas_concluidas = round((listas_concluidas / total_listas) * 100) if total_listas > 0 else 0
    
    # Calcular engajamento médio
    engajamentos = [p.engajamento for p in progressos if p.engajamento is not None]
    engajamento_medio = round(sum(engajamentos) / len(engajamentos)) if engajamentos else 0
    
    # Preparar dados para os gráficos
    datas = []
    progresso_datasets = []
    dificuldades_datasets = []
    engajamento_datasets = []
    cooperacao_datasets = []
    
    # Buscar progressos ordenados por data
    progressos = progressos.filter(data_atualizacao__isnull=False).order_by('data_atualizacao')
    
    if progressos.exists():
        # Agrupar por data
        for data, grupo in itertools.groupby(progressos, key=lambda x: x.data_atualizacao.date()):
            datas.append(data.strftime('%d/%m/%Y'))
            grupo_list = list(grupo)
            
            # Calcular médias para cada métrica
            total_progresso = sum(p.aprendizados.count() for p in grupo_list)
            total_objetivos = sum(l.objetivos.count() for l in listas)
            media_progresso = round((total_progresso / total_objetivos) * 100) if total_objetivos > 0 else 0
            
            total_dificuldades = sum(p.dificuldades.count() for p in grupo_list)
            media_dificuldades = round((total_dificuldades / total_objetivos) * 100) if total_objetivos > 0 else 0
            
            engajamentos = [p.engajamento for p in grupo_list if p.engajamento is not None]
            media_engajamento = round(sum(engajamentos) / len(engajamentos)) if engajamentos else 0
            
            cooperacoes = [p.cooperacao for p in grupo_list if p.cooperacao is not None]
            media_cooperacao = round(sum(cooperacoes) / len(cooperacoes)) if cooperacoes else 0
            
            # Adicionar aos datasets
            progresso_datasets.append(media_progresso)
            dificuldades_datasets.append(media_dificuldades)
            engajamento_datasets.append(media_engajamento)
            cooperacao_datasets.append(media_cooperacao)
    
    # Calcular distribuição de progresso
    distribuicao_progresso = [0] * 5  # [0-20%, 21-40%, 41-60%, 61-80%, 81-100%]
    for progresso in progressos:
        total_aprendizados = progresso.aprendizados.count()
        total_objetivos = sum(l.objetivos.count() for l in listas)
        percentual = round((total_aprendizados / total_objetivos) * 100) if total_objetivos > 0 else 0
        
        if percentual <= 20:
            distribuicao_progresso[0] += 1
        elif percentual <= 40:
            distribuicao_progresso[1] += 1
        elif percentual <= 60:
            distribuicao_progresso[2] += 1
        elif percentual <= 80:
            distribuicao_progresso[3] += 1
        else:
            distribuicao_progresso[4] += 1
    
    # Preparar dados dos alunos para a tabela
    dados_alunos = []
    for aluno in alunos:
        progresso = progressos.filter(aluno=aluno).first()
        if progresso:
            total_aprendizados = progresso.aprendizados.count()
            total_objetivos = sum(l.objetivos.count() for l in listas)
            percentual_progresso = round((total_aprendizados / total_objetivos) * 100) if total_objetivos > 0 else 0
            
            total_dificuldades = progresso.dificuldades.count()
            percentual_dificuldades = round((total_dificuldades / total_objetivos) * 100) if total_objetivos > 0 else 0
            
            dados_alunos.append({
                'nome': aluno.get_full_name(),
                'progresso': percentual_progresso,
                'dificuldades': percentual_dificuldades,
                'engajamento': progresso.engajamento or 0,
                'ultima_atividade': progresso.data_atualizacao.strftime('%d/%m/%Y %H:%M') if progresso.data_atualizacao else 'Nunca'
            })
    
    context = {
        'turma': turma,
        'listas': listas,
        'alunos': alunos,
        'progresso_geral': progresso_geral,
        'alunos_ativos': alunos_ativos,
        'total_alunos': total_alunos,
        'percentual_alunos_ativos': percentual_alunos_ativos,
        'listas_concluidas': listas_concluidas,
        'total_listas': total_listas,
        'percentual_listas_concluidas': percentual_listas_concluidas,
        'engajamento_medio': engajamento_medio,
        'datas': json.dumps(datas),
        'progresso_datasets': json.dumps([{
            'label': 'Progresso',
            'data': progresso_datasets,
            'borderColor': 'rgb(75, 192, 192)',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'tension': 0.4
        }]),
        'dificuldades_datasets': json.dumps([{
            'label': 'Dificuldades',
            'data': dificuldades_datasets,
            'borderColor': 'rgb(255, 159, 64)',
            'backgroundColor': 'rgba(255, 159, 64, 0.5)',
            'tension': 0.4
        }]),
        'engajamento_datasets': json.dumps([{
            'label': 'Engajamento',
            'data': engajamento_datasets,
            'borderColor': 'rgb(54, 162, 235)',
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'tension': 0.4
        }]),
        'cooperacao_datasets': json.dumps([{
            'label': 'Cooperação',
            'data': cooperacao_datasets,
            'borderColor': 'rgb(153, 102, 255)',
            'backgroundColor': 'rgba(153, 102, 255, 0.5)',
            'tension': 0.4
        }]),
        'distribuicao_progresso': json.dumps(distribuicao_progresso),
        'dados_alunos': dados_alunos
    }
    
    return render(request, 'listas_verificacao/visualizacoes/dashboard_interativo.html', context)

@login_required
def dashboard_dados(request, turma_id):
    # Verificar se o usuário é um professor
    if not hasattr(request.user, 'professor'):
        return JsonResponse({'error': 'Acesso negado'}, status=403)
    
    # Buscar a turma
    turma = get_object_or_404(Turma, professor=request.user.professor, id=turma_id)
    
    # Obter parâmetros de filtro
    periodo = int(request.GET.get('periodo', 30))
    lista_id = request.GET.get('lista')
    aluno_id = request.GET.get('aluno')
    
    # Definir data limite
    data_limite = timezone.now() - timezone.timedelta(days=periodo)
    
    # Buscar listas e alunos
    listas = ListaVerificacao.objects.filter(turma=turma)
    if lista_id != 'todas':
        listas = listas.filter(id=lista_id)
    
    alunos = turma.alunos.all()
    if aluno_id != 'todos':
        alunos = alunos.filter(id=aluno_id)
    
    # Buscar progressos filtrados
    progressos = ProgressoAluno.objects.filter(
        aluno__in=alunos,
        data_atualizacao__gte=data_limite,
        data_atualizacao__isnull=False
    ).order_by('data_atualizacao')
    
    # Preparar dados para os gráficos
    datas = []
    progresso_datasets = []
    dificuldades_datasets = []
    engajamento_datasets = []
    cooperacao_datasets = []
    
    if progressos.exists():
        # Agrupar por data
        for data, grupo in itertools.groupby(progressos, key=lambda x: x.data_atualizacao.date()):
            datas.append(data.strftime('%d/%m/%Y'))
            grupo_list = list(grupo)
            
            # Calcular médias para cada métrica
            total_progresso = sum(p.aprendizados.count() for p in grupo_list)
            total_objetivos = sum(l.objetivos.count() for l in listas)
            media_progresso = round((total_progresso / total_objetivos) * 100) if total_objetivos > 0 else 0
            
            total_dificuldades = sum(p.dificuldades.count() for p in grupo_list)
            media_dificuldades = round((total_dificuldades / total_objetivos) * 100) if total_objetivos > 0 else 0
            
            engajamentos = [p.engajamento for p in grupo_list if p.engajamento is not None]
            media_engajamento = round(sum(engajamentos) / len(engajamentos)) if engajamentos else 0
            
            cooperacoes = [p.cooperacao for p in grupo_list if p.cooperacao is not None]
            media_cooperacao = round(sum(cooperacoes) / len(cooperacoes)) if cooperacoes else 0
            
            # Adicionar aos datasets
            progresso_datasets.append(media_progresso)
            dificuldades_datasets.append(media_dificuldades)
            engajamento_datasets.append(media_engajamento)
            cooperacao_datasets.append(media_cooperacao)
    
    # Calcular distribuição de progresso
    distribuicao_progresso = [0] * 5  # [0-20%, 21-40%, 41-60%, 61-80%, 81-100%]
    for progresso in progressos:
        total_aprendizados = progresso.aprendizados.count()
        total_objetivos = sum(l.objetivos.count() for l in listas)
        percentual = round((total_aprendizados / total_objetivos) * 100) if total_objetivos > 0 else 0
        
        if percentual <= 20:
            distribuicao_progresso[0] += 1
        elif percentual <= 40:
            distribuicao_progresso[1] += 1
        elif percentual <= 60:
            distribuicao_progresso[2] += 1
        elif percentual <= 80:
            distribuicao_progresso[3] += 1
        else:
            distribuicao_progresso[4] += 1
    
    # Preparar dados dos alunos para a tabela
    dados_alunos = []
    for aluno in alunos:
        progresso = progressos.filter(aluno=aluno).first()
        if progresso:
            total_aprendizados = progresso.aprendizados.count()
            total_objetivos = sum(l.objetivos.count() for l in listas)
            percentual_progresso = round((total_aprendizados / total_objetivos) * 100) if total_objetivos > 0 else 0
            
            total_dificuldades = progresso.dificuldades.count()
            percentual_dificuldades = round((total_dificuldades / total_objetivos) * 100) if total_objetivos > 0 else 0
            
            dados_alunos.append({
                'nome': aluno.get_full_name(),
                'progresso': percentual_progresso,
                'dificuldades': percentual_dificuldades,
                'engajamento': progresso.engajamento or 0,
                'ultima_atividade': progresso.data_atualizacao.strftime('%d/%m/%Y %H:%M') if progresso.data_atualizacao else 'Nunca'
            })
    
    return JsonResponse({
        'datas': datas,
        'datasets': [{
            'label': 'Progresso',
            'data': progresso_datasets,
            'borderColor': 'rgb(75, 192, 192)',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'tension': 0.4
        }],
        'distribuicao': distribuicao_progresso,
        'dados_alunos': dados_alunos
    })
