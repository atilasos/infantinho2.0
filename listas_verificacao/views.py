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
    ConfiguracaoNotificacao, AvaliacaoAprendizagem, ComentarioAprendizagem,
    Duvida, RespostaDuvida, DiarioAprendizagem, EntradaDiario, ComentarioEntrada, ConexaoAprendizagem,
    MetaAprendizagem, AlteracaoMeta, ReflexaoMeta, AcompanhamentoMeta, ConquistaMeta,
    ConquistaColetiva, ReconhecimentoContribuicao, ProjetoColaborativo, CircuitoComunicacao,
    Checklist, Item, Categoria, Meta
)
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone
from .forms import (
    ListaVerificacaoForm, TurmaForm, ObjetivoForm,
    CategoriaObjetivoForm, ObjetivoPredefinidoForm,
    ImportarAprendizagensForm, AprendizagemEssencialForm,
    ConfiguracaoNotificacaoForm, ConquistaColetivaForm, ReconhecimentoContribuicaoForm,
    ProjetoColaborativoForm, CircuitoComunicacaoForm,
    MetaAprendizagemForm, AlteracaoMetaForm, ReflexaoMetaForm, AcompanhamentoMetaForm,
    ChecklistForm, ItemForm, CategoriaForm, MetaForm
)
import json
import csv
import io
import re
from django.core.paginator import Paginator
import itertools
from django.core.exceptions import PermissionDenied

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
    
    # Verificar se o aluno tem acesso à lista
    if not (lista.turma and request.user in lista.turma.alunos.all()):
        messages.error(request, 'Você não tem acesso a esta lista de verificação.')
        return redirect('listas_verificacao:lista_aluno')
    
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('aprendizagem_'):
                aprendizagem_id = int(key.split('_')[1])
                aprendizagem = get_object_or_404(AprendizagemEssencial, id=aprendizagem_id)
                
                # Atualizar ou criar o progresso
                progresso, created = ProgressoAluno.objects.update_or_create(
                    aluno=request.user,
                    lista_verificacao=lista,
                    aprendizagem=aprendizagem,
                    defaults={'estado': value}
                )
        
        messages.success(request, 'Progresso registrado com sucesso!')
        return redirect('listas_verificacao:lista_aluno')
    
    # Buscar o progresso atual do aluno
    progressos = {
        p.aprendizagem_id: p.estado 
        for p in ProgressoAluno.objects.filter(
            aluno=request.user,
            lista_verificacao=lista
        )
    }
    
    context = {
        'lista': lista,
        'aprendizagens': lista.aprendizagens.all().order_by('codigo'),
        'progressos': progressos,
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
        if total_aprendizagens > 0:
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
    
    aprendizagens = AprendizagemEssencial.objects.all()
    
    context = {
        'aprendizagens': aprendizagens,
    }
    return render(request, 'listas_verificacao/gerenciar_aprendizagens.html', context)

@login_required
def criar_aprendizagem(request):
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    if request.method == 'POST':
        form = AprendizagemEssencialForm(request.POST)
        if form.is_valid():
            aprendizagem = form.save()
            messages.success(request, 'Aprendizagem criada com sucesso.')
            return redirect('listas_verificacao:gerenciar_aprendizagens')
    else:
        form = AprendizagemEssencialForm()
    
    context = {
        'form': form,
        'titulo': 'Criar Nova Aprendizagem',
    }
    return render(request, 'listas_verificacao/form_aprendizagem.html', context)

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

@login_required
def avaliar_aprendizagem(request, progresso_id):
    """
    View para avaliar uma aprendizagem específica.
    Permite que professores avaliem o progresso do aluno e alunos solicitem avaliação.
    """
    progresso = get_object_or_404(ProgressoAluno, id=progresso_id)
    avaliacao, created = AvaliacaoAprendizagem.objects.get_or_create(progresso=progresso)
    
    # Verificar permissões
    if request.user.is_student and request.user != progresso.aluno:
        messages.error(request, 'Você não tem permissão para avaliar esta aprendizagem.')
        return redirect('listas_verificacao:lista_aluno')
    
    if request.method == 'POST':
        novo_estado = request.POST.get('estado')
        observacoes = request.POST.get('observacoes', '')
        
        if request.user.is_student:
            # Aluno solicitando avaliação
            if novo_estado == 'aguardando_avaliacao':
                avaliacao.estado = novo_estado
                avaliacao.data_solicitacao_avaliacao = timezone.now()
                avaliacao.save()
                
                # Criar notificação para professores
                Notificacao.objects.create(
                    destinatario=progresso.lista_verificacao.turma.professor,
                    tipo='confirmacao_pendente',
                    titulo=f'Nova solicitação de avaliação - {progresso.aprendizagem.codigo}',
                    mensagem=f'O aluno {progresso.aluno.get_full_name()} solicitou avaliação para a aprendizagem {progresso.aprendizagem.codigo}.',
                    prioridade='media',
                    lista_verificacao=progresso.lista_verificacao,
                    aprendizagem=progresso.aprendizagem,
                    progresso=progresso
                )
                
                messages.success(request, 'Solicitação de avaliação enviada com sucesso!')
            else:
                avaliacao.estado = novo_estado
                avaliacao.save()
                messages.success(request, 'Estado atualizado com sucesso!')
        else:
            # Professor avaliando
            avaliacao.estado = novo_estado
            avaliacao.avaliador = request.user
            avaliacao.data_avaliacao = timezone.now()
            avaliacao.observacoes_avaliador = observacoes
            avaliacao.save()
            
            # Se aprovado, verificar se deve ser marcado como monitor
            if novo_estado == 'avaliado_aprovado':
                # Criar notificação para o aluno
                Notificacao.objects.create(
                    destinatario=progresso.aluno,
                    tipo='feedback',
                    titulo=f'Avaliação concluída - {progresso.aprendizagem.codigo}',
                    mensagem=f'Sua aprendizagem {progresso.aprendizagem.codigo} foi avaliada e aprovada.',
                    prioridade='media',
                    lista_verificacao=progresso.lista_verificacao,
                    aprendizagem=progresso.aprendizagem,
                    progresso=progresso
                )
            
            messages.success(request, 'Avaliação registrada com sucesso!')
        
        return redirect('listas_verificacao:detalhe_aprendizagem', progresso_id=progresso_id)
    
    context = {
        'progresso': progresso,
        'avaliacao': avaliacao,
        'estados': AvaliacaoAprendizagem.ESTADOS,
    }
    return render(request, 'listas_verificacao/avaliar_aprendizagem.html', context)

@login_required
def adicionar_comentario(request, progresso_id):
    """
    View para adicionar comentários em uma aprendizagem.
    Permite que alunos, professores e monitores adicionem comentários.
    """
    progresso = get_object_or_404(ProgressoAluno, id=progresso_id)
    
    # Verificar permissões
    if request.user.is_student and request.user != progresso.aluno:
        messages.error(request, 'Você não tem permissão para comentar nesta aprendizagem.')
        return redirect('listas_verificacao:lista_aluno')
    
    if request.method == 'POST':
        texto = request.POST.get('texto')
        tipo = request.POST.get('tipo')
        anexos = request.FILES.getlist('anexos')
        
        # Criar o comentário
        comentario = ComentarioAprendizagem.objects.create(
            progresso=progresso,
            autor=request.user,
            tipo=tipo,
            texto=texto
        )
        
        # Processar anexos
        for anexo in anexos:
            comentario.anexos.save(anexo.name, anexo)
        
        # Criar notificação apropriada
        if tipo == 'autoavaliacao':
            # Notificar professores
            Notificacao.objects.create(
                destinatario=progresso.lista_verificacao.turma.professor,
                tipo='feedback',
                titulo=f'Nova autoavaliação - {progresso.aprendizagem.codigo}',
                mensagem=f'O aluno {progresso.aluno.get_full_name()} fez uma autoavaliação na aprendizagem {progresso.aprendizagem.codigo}.',
                prioridade='media',
                lista_verificacao=progresso.lista_verificacao,
                aprendizagem=progresso.aprendizagem,
                progresso=progresso
            )
        elif tipo == 'feedback_professor':
            # Notificar aluno
            Notificacao.objects.create(
                destinatario=progresso.aluno,
                tipo='feedback',
                titulo=f'Novo feedback - {progresso.aprendizagem.codigo}',
                mensagem=f'Você recebeu um novo feedback na aprendizagem {progresso.aprendizagem.codigo}.',
                prioridade='media',
                lista_verificacao=progresso.lista_verificacao,
                aprendizagem=progresso.aprendizagem,
                progresso=progresso
            )
        
        messages.success(request, 'Comentário adicionado com sucesso!')
        return redirect('listas_verificacao:detalhe_aprendizagem', progresso_id=progresso_id)
    
    context = {
        'progresso': progresso,
        'tipos_comentario': ComentarioAprendizagem.TIPOS,
    }
    return render(request, 'listas_verificacao/adicionar_comentario.html', context)

@login_required
def detalhe_aprendizagem(request, progresso_id):
    """
    View para visualizar detalhes de uma aprendizagem específica,
    incluindo avaliações e comentários.
    """
    progresso = get_object_or_404(ProgressoAluno, id=progresso_id)
    avaliacao = AvaliacaoAprendizagem.objects.filter(progresso=progresso).first()
    comentarios = ComentarioAprendizagem.objects.filter(progresso=progresso).order_by('-data_criacao')
    
    context = {
        'progresso': progresso,
        'avaliacao': avaliacao,
        'comentarios': comentarios,
    }
    return render(request, 'listas_verificacao/detalhe_aprendizagem.html', context)

@login_required
def lista_duvidas(request):
    """Lista todas as dúvidas do usuário."""
    if request.user.is_teacher:
        duvidas = Duvida.objects.filter(turma__professor=request.user)
    else:
        duvidas = Duvida.objects.filter(Q(autor=request.user) | Q(turma__alunos=request.user)).distinct()
    
    # Filtros
    estado = request.GET.get('estado')
    categoria = request.GET.get('categoria')
    prioridade = request.GET.get('prioridade')
    
    if estado:
        duvidas = duvidas.filter(estado=estado)
    if categoria:
        duvidas = duvidas.filter(categoria=categoria)
    if prioridade:
        duvidas = duvidas.filter(prioridade=prioridade)
    
    # Ordenação
    duvidas = duvidas.order_by('-prioridade', '-data_criacao')
    
    # Buscar aprendizagens disponíveis para o aluno
    if request.user.is_student:
        aprendizagens = AprendizagemEssencial.objects.filter(
            listas_verificacao__turma__in=request.user.turmas_aluno.all()
        ).distinct()
    else:
        aprendizagens = []
    
    context = {
        'duvidas': duvidas,
        'estados': Duvida.ESTADOS,
        'categorias': Duvida.CATEGORIAS,
        'prioridades': Duvida.PRIORIDADES,
        'aprendizagens': aprendizagens,
    }
    return render(request, 'listas_verificacao/duvidas/lista_duvidas.html', context)

@login_required
def criar_duvida(request):
    """View para criar uma nova dúvida."""
    if not request.user.is_student:
        messages.error(request, 'Apenas alunos podem criar dúvidas.')
        return redirect('listas_verificacao:lista_duvidas')
    
    if request.method == 'POST':
        aprendizagem_id = request.POST.get('aprendizagem')
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        categoria = request.POST.get('categoria')
        prioridade = request.POST.get('prioridade')
        
        # Buscar a aprendizagem e a turma
        aprendizagem = get_object_or_404(AprendizagemEssencial, id=aprendizagem_id)
        turma = request.user.turmas_aluno.first()  # Pega a primeira turma do aluno
        
        conexao = ConexaoAprendizagem.objects.create(
            entrada=entrada,
            aprendizagem=aprendizagem,
            descricao=descricao
        )
        
        messages.success(request, 'Conexão adicionada com sucesso!')
        return redirect('listas_verificacao:detalhe_diario', diario_id=entrada.diario.id)
    
    # GET request
    aprendizagens = AprendizagemEssencial.objects.filter(
        listas_verificacao=entrada.diario.turma.lista_verificacao
    ).exclude(
        id__in=entrada.conexoes.values_list('aprendizagem_id', flat=True)
    )
    
    context = {
        'entrada': entrada,
        'aprendizagens': aprendizagens,
    }
    return render(request, 'listas_verificacao/diario/adicionar_conexao.html', context)

# Views do Sistema de Metas e Prazos
@login_required
def lista_metas(request):
    """Lista as metas do aluno ou da turma."""
    if request.user.is_teacher:
        # Professores veem metas de suas turmas
        turmas = Turma.objects.filter(professor=request.user)
        metas = MetaAprendizagem.objects.filter(turma__in=turmas)
    else:
        # Alunos veem suas próprias metas e as coletivas da turma
        metas = MetaAprendizagem.objects.filter(
            Q(aluno=request.user) | 
            Q(turma__in=request.user.turmas_aluno.all(), tipo='coletiva')
        ).distinct()
    
    context = {
        'metas': metas,
    }
    return render(request, 'listas_verificacao/metas/lista_metas.html', context)

@login_required
def criar_meta(request):
    """Cria uma nova meta de aprendizagem."""
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        tipo = request.POST.get('tipo')
        turma_id = request.POST.get('turma')
        aprendizagens_ids = request.POST.getlist('aprendizagens')
        participantes_ids = request.POST.getlist('participantes')
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        justificativa = request.POST.get('justificativa')
        plano_acao = request.POST.get('plano_acao')
        recursos_necessarios = request.POST.get('recursos_necessarios')
        
        turma = get_object_or_404(Turma, id=turma_id)
        
        # Verificar se o aluno pertence à turma
        if not request.user.is_teacher and request.user not in turma.alunos.all():
            messages.error(request, 'Você não tem permissão para criar uma meta nesta turma.')
            return redirect('listas_verificacao:lista_metas')
        
        meta = MetaAprendizagem.objects.create(
            aluno=request.user,
            titulo=titulo,
            descricao=descricao,
            tipo=tipo,
            turma=turma,
            data_inicio=data_inicio if data_inicio else None,
            data_fim=data_fim if data_fim else None,
            justificativa=justificativa,
            plano_acao=plano_acao,
            recursos_necessarios=recursos_necessarios
        )
        
        # Adicionar aprendizagens relacionadas
        if aprendizagens_ids:
            aprendizagens = AprendizagemEssencial.objects.filter(id__in=aprendizagens_ids)
            meta.aprendizagens.set(aprendizagens)
        
        # Adicionar participantes para metas coletivas
        if tipo in ['coletiva', 'projeto'] and participantes_ids:
            participantes = User.objects.filter(id__in=participantes_ids)
            meta.participantes.set(participantes)
        
        # Criar notificação para o professor
        if request.user.is_student:
            Notificacao.objects.create(
                destinatario=turma.professor,
                tipo='meta',
                titulo=f'Nova meta proposta - {meta.titulo}',
                mensagem=f'O aluno {request.user.get_full_name()} propôs uma nova meta.',
                prioridade='media',
                lista_verificacao=turma.lista_verificacao,
            )
        
        messages.success(request, 'Meta criada com sucesso!')
        return redirect('listas_verificacao:detalhe_meta', meta_id=meta.id)
    
    # GET request
    if request.user.is_teacher:
        turmas = Turma.objects.filter(professor=request.user)
    else:
        turmas = request.user.turmas.all()
    
    context = {
        'turmas': turmas,
        'tipos_meta': MetaAprendizagem.TIPOS_META,
    }
    return render(request, 'listas_verificacao/metas/criar_meta.html', context)

@login_required
def detalhe_meta(request, meta_id):
    """Visualiza os detalhes de uma meta específica."""
    meta = get_object_or_404(MetaAprendizagem, id=meta_id)
    
    # Verificar permissões
    if not request.user.is_teacher and request.user != meta.aluno and meta.tipo == 'individual':
        messages.error(request, 'Você não tem permissão para ver esta meta.')
        return redirect('listas_verificacao:lista_metas')
    
    context = {
        'meta': meta,
        'ajustes': meta.ajustes.all(),
        'reflexoes': meta.reflexoes.all(),
        'acompanhamentos': meta.acompanhamentos.all(),
        'conquistas': meta.conquistas.all(),
    }
    return render(request, 'listas_verificacao/metas/detalhe_meta.html', context)

@login_required
def solicitar_ajuste_meta(request, meta_id):
    """Solicita um ajuste em uma meta."""
    meta = get_object_or_404(MetaAprendizagem, id=meta_id)
    
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        descricao = request.POST.get('descricao')
        justificativa = request.POST.get('justificativa')
        
        ajuste = AlteracaoMeta.objects.create(
            meta=meta,
            tipo=tipo,
            descricao=descricao,
            justificativa=justificativa
        )
        
        # Notificar o professor
        Notificacao.objects.create(
            destinatario=meta.turma.professor,
            tipo='ajuste_meta',
            titulo=f'Solicitação de ajuste - {meta.titulo}',
            mensagem=f'{request.user.get_full_name()} solicitou um ajuste na meta.',
            prioridade='media',
            lista_verificacao=meta.turma.lista_verificacao,
        )
        
        messages.success(request, 'Solicitação de ajuste enviada com sucesso!')
        return redirect('listas_verificacao:detalhe_meta', meta_id=meta.id)
    
    context = {
        'meta': meta,
        'tipos_ajuste': AjusteMeta.TIPOS_AJUSTE,
    }
    return render(request, 'listas_verificacao/metas/solicitar_ajuste.html', context)

@login_required
def adicionar_reflexao(request, meta_id):
    """Adiciona uma reflexão sobre o progresso da meta."""
    meta = get_object_or_404(MetaAprendizagem, id=meta_id)
    
    if request.method == 'POST':
        conteudo = request.POST.get('conteudo')
        nivel_satisfacao = request.POST.get('nivel_satisfacao')
        dificuldades = request.POST.get('dificuldades_encontradas')
        estrategias = request.POST.get('estrategias_sucesso')
        sugestoes = request.POST.get('sugestoes_melhoria')
        
        reflexao = ReflexaoMeta.objects.create(
            meta=meta,
            autor=request.user,
            conteudo=conteudo,
            nivel_satisfacao=nivel_satisfacao,
            dificuldades_encontradas=dificuldades,
            estrategias_sucesso=estrategias,
            sugestoes_melhoria=sugestoes
        )
        
        # Notificar o professor se houver dificuldades
        if dificuldades and request.user.is_student:
            Notificacao.objects.create(
                destinatario=meta.turma.professor,
                tipo='reflexao_meta',
                titulo=f'Reflexão com dificuldades - {meta.titulo}',
                mensagem=f'O aluno {request.user.get_full_name()} reportou dificuldades na meta.',
                prioridade='alta',
                lista_verificacao=meta.turma.lista_verificacao,
            )
        
        messages.success(request, 'Reflexão adicionada com sucesso!')
        return redirect('listas_verificacao:detalhe_meta', meta_id=meta.id)
    
    return render(request, 'listas_verificacao/metas/adicionar_reflexao.html', {'meta': meta})

@login_required
def adicionar_acompanhamento(request, meta_id):
    """Adiciona um acompanhamento colaborativo da meta."""
    meta = get_object_or_404(MetaAprendizagem, id=meta_id)
    
    if request.method == 'POST':
        progresso = request.POST.get('progresso')
        observacoes = request.POST.get('observacoes')
        sugestoes = request.POST.get('sugestoes')
        recursos = request.POST.get('recursos_sugeridos')
        
        acompanhamento = AcompanhamentoMeta.objects.create(
            meta=meta,
            autor=request.user,
            progresso=progresso,
            observacoes=observacoes,
            sugestoes=sugestoes,
            recursos_sugeridos=recursos
        )
        
        # Notificar o autor da meta
        if request.user != meta.aluno:
            Notificacao.objects.create(
                destinatario=meta.aluno,
                tipo='acompanhamento_meta',
                titulo=f'Novo acompanhamento - {meta.titulo}',
                mensagem=f'{request.user.get_full_name()} adicionou um acompanhamento à sua meta.',
                prioridade='media',
                lista_verificacao=meta.turma.lista_verificacao,
            )
        
        messages.success(request, 'Acompanhamento adicionado com sucesso!')
        return redirect('listas_verificacao:detalhe_meta', meta_id=meta.id)
    
    return render(request, 'listas_verificacao/metas/adicionar_acompanhamento.html', {'meta': meta})

@login_required
def registrar_conquista(request, meta_id):
    """Registra uma conquista relacionada à meta."""
    meta = get_object_or_404(MetaAprendizagem, id=meta_id)
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        comentarios = request.POST.get('comentarios')
        evidencias = request.FILES.get('evidencias')
        
        conquista = ConquistaMeta.objects.create(
            meta=meta,
            titulo=titulo,
            descricao=descricao,
            comentarios=comentarios,
            evidencias=evidencias,
            reconhecido_por=request.user
        )
        
        # Notificar participantes da meta
        participantes = [meta.aluno] + list(meta.participantes.all())
        for participante in participantes:
            if participante != request.user:
                Notificacao.objects.create(
                    destinatario=participante,
                    tipo='conquista_meta',
                    titulo=f'Nova conquista - {meta.titulo}',
                    mensagem=f'{request.user.get_full_name()} registrou uma conquista na meta.',
                    prioridade='baixa',
                    lista_verificacao=meta.turma.lista_verificacao,
                )
        
        messages.success(request, 'Conquista registrada com sucesso!')
        return redirect('listas_verificacao:detalhe_meta', meta_id=meta.id)
    
    return render(request, 'listas_verificacao/metas/registrar_conquista.html', {'meta': meta})

@login_required
def lista_conquistas(request):
    """Lista as conquistas coletivas da turma do usuário."""
    if request.user.is_teacher:
        conquistas = ConquistaColetiva.objects.filter(turma__professor=request.user)
    else:
        conquistas = ConquistaColetiva.objects.filter(
            Q(turma__alunos=request.user) | Q(participantes=request.user)
        ).distinct()
    
    # Aplicar filtros
    tipo = request.GET.get('tipo')
    if tipo:
        conquistas = conquistas.filter(tipo=tipo)
    
    # Ordenar por data de criação mais recente
    conquistas = conquistas.order_by('-data_criacao')
    
    context = {
        'conquistas': conquistas,
        'tipos_conquista': ConquistaColetiva.TIPOS_CONQUISTA,
        'tipo_selecionado': tipo or '',  # Para manter o filtro selecionado no template
    }
    return render(request, 'listas_verificacao/conquistas/lista_conquistas.html', context)

@login_required
def criar_conquista(request):
    """Cria uma nova conquista coletiva."""
    if request.method == 'POST':
        form = ConquistaColetivaForm(request.POST, request.FILES)
        if form.is_valid():
            conquista = form.save(commit=False)
            conquista.criador = request.user
            conquista.save()
            form.save_m2m()  # Salva as relações many-to-many
            
            # Notifica os participantes
            for participante in conquista.participantes.all():
                if participante != request.user:
                    Notificacao.objects.create(
                        destinatario=participante,
                        remetente=request.user,
                        tipo='conquista',
                        titulo='Nova Conquista Coletiva',
                        mensagem=f'Você foi adicionado como participante na conquista "{conquista.titulo}"',
                        prioridade='media'
                    )
            
            messages.success(request, 'Conquista coletiva criada com sucesso!')
            return redirect('listas_verificacao:detalhe_conquista', conquista_id=conquista.id)
    else:
        form = ConquistaColetivaForm()
    
    context = {
        'form': form,
        'tipos_conquista': ConquistaColetiva.TIPOS_CONQUISTA,
        'tipos_impacto': ConquistaColetiva.IMPACTO,
    }
    return render(request, 'listas_verificacao/conquistas/criar_conquista.html', context)

@login_required
def detalhe_conquista(request, conquista_id):
    """Exibe os detalhes de uma conquista coletiva."""
    conquista = get_object_or_404(ConquistaColetiva, id=conquista_id)
    
    # Verifica permissões
    if not (request.user.is_teacher or 
            request.user in conquista.participantes.all() or 
            request.user in conquista.turma.alunos.all()):
        raise PermissionDenied
    
    context = {
        'conquista': conquista,
        'reconhecimentos': conquista.reconhecimentos.all(),
        'tipos_contribuicao': ReconhecimentoContribuicao.TIPOS_CONTRIBUICAO,
        'projetos_relacionados': ProjetoColaborativo.objects.filter(turma=conquista.turma)
    }
    return render(request, 'listas_verificacao/conquistas/detalhe_conquista.html', context)

@login_required
def validar_conquista(request, conquista_id):
    """Permite que um usuário valide uma conquista coletiva."""
    conquista = get_object_or_404(ConquistaColetiva, id=conquista_id)
    
    if request.method == 'POST':
        feedback = request.POST.get('feedback', '')
        conquista.validar(request.user, feedback)
        
        # Notifica o criador da conquista
        if request.user != conquista.criador:
            Notificacao.objects.create(
                destinatario=conquista.criador,
                remetente=request.user,
                tipo='conquista',
                titulo='Conquista Validada',
                mensagem=f'Sua conquista "{conquista.titulo}" foi validada por {request.user.get_full_name()}',
                prioridade='baixa'
            )
        
        messages.success(request, 'Conquista validada com sucesso!')
        return redirect('listas_verificacao:detalhe_conquista', conquista_id=conquista.id)
    
    return render(request, 'listas_verificacao/conquistas/validar_conquista.html', {'conquista': conquista})

@login_required
def registrar_reconhecimento(request):
    """Registra um reconhecimento de contribuição."""
    if request.method == 'POST':
        form = ReconhecimentoContribuicaoForm(request.POST, request.FILES)
        if form.is_valid():
            reconhecimento = form.save(commit=False)
            reconhecimento.reconhecido_por = request.user
            reconhecimento.save()
            
            # Notifica o contribuidor
            if request.user != reconhecimento.contribuidor:
                Notificacao.objects.create(
                    destinatario=reconhecimento.contribuidor,
                    remetente=request.user,
                    tipo='reconhecimento',
                    titulo='Nova Contribuição Reconhecida',
                    mensagem=f'Sua contribuição foi reconhecida por {request.user.get_full_name()}',
                    prioridade='media'
                )
            
            messages.success(request, 'Reconhecimento registrado com sucesso!')
            return redirect('listas_verificacao:detalhe_conquista', 
                          conquista_id=reconhecimento.conquista.id)
    else:
        form = ReconhecimentoContribuicaoForm()
    
    context = {
        'form': form,
        'tipos_contribuicao': ReconhecimentoContribuicao.TIPOS_CONTRIBUICAO,
    }
    return render(request, 'listas_verificacao/conquistas/registrar_reconhecimento.html', context)

@login_required
def lista_projetos(request):
    """Lista os projetos colaborativos da turma."""
    if request.user.is_teacher:
        projetos = ProjetoColaborativo.objects.filter(turma__professor=request.user)
    else:
        projetos = ProjetoColaborativo.objects.filter(
            Q(turma__alunos=request.user) | Q(participantes=request.user)
        ).distinct()
    
    context = {
        'projetos': projetos,
        'estados': ProjetoColaborativo.ESTADOS,
    }
    return render(request, 'listas_verificacao/projetos/lista_projetos.html', context)

@login_required
def criar_projeto(request):
    """Cria um novo projeto colaborativo."""
    if request.method == 'POST':
        form = ProjetoColaborativoForm(request.POST)
        if form.is_valid():
            projeto = form.save(commit=False)
            projeto.criador = request.user
            projeto.save()
            form.save_m2m()
            
            # Notifica os participantes
            for participante in projeto.participantes.all():
                if participante != request.user:
                    Notificacao.objects.create(
                        destinatario=participante,
                        remetente=request.user,
                        tipo='projeto',
                        titulo='Novo Projeto Colaborativo',
                        mensagem=f'Você foi adicionado como participante no projeto "{projeto.titulo}"',
                        prioridade='media'
                    )
            
            messages.success(request, 'Projeto colaborativo criado com sucesso!')
            return redirect('listas_verificacao:detalhe_projeto', projeto_id=projeto.id)
    else:
        form = ProjetoColaborativoForm()
    
    # Buscar turmas do professor ou turmas em que o aluno está matriculado
    if request.user.is_teacher:
        turmas = Turma.objects.filter(professor=request.user)
    else:
        turmas = request.user.turmas_aluno.all()
    
    # Buscar alunos das turmas
    alunos = User.objects.filter(turmas_aluno__in=turmas).distinct()
    
    # Buscar aprendizagens das turmas
    aprendizagens = AprendizagemEssencial.objects.filter(
        listas_verificacao__turma__in=turmas
    ).distinct()
    
    context = {
        'form': form,
        'estados': ProjetoColaborativo.ESTADOS,
        'turmas': turmas,
        'alunos': alunos,
        'aprendizagens': aprendizagens
    }
    return render(request, 'listas_verificacao/projetos/criar_projeto.html', context)

@login_required
def detalhe_projeto(request, projeto_id):
    """Exibe os detalhes de um projeto colaborativo."""
    projeto = get_object_or_404(ProjetoColaborativo, id=projeto_id)
    
    # Verifica permissões
    if not (request.user.is_professor or 
            request.user in projeto.participantes.all() or 
            request.user in projeto.turma.alunos.all()):
        raise PermissionDenied
    
    context = {
        'projeto': projeto,
        'conquistas_relacionadas': ConquistaColetiva.objects.filter(
            projetos__in=[projeto]
        ),
    }
    return render(request, 'listas_verificacao/projetos/detalhe_projeto.html', context)

@login_required
def lista_circuitos(request):
    """Lista os circuitos de comunicação da turma."""
    if request.user.is_teacher:
        circuitos = CircuitoComunicacao.objects.filter(turma__professor=request.user)
    else:
        circuitos = CircuitoComunicacao.objects.filter(
            Q(turma__alunos=request.user) | Q(participantes=request.user)
        ).distinct()
    
    context = {
        'circuitos': circuitos,
        'tipos': CircuitoComunicacao.TIPOS,
    }
    return render(request, 'listas_verificacao/circuitos/lista_circuitos.html', context)

@login_required
def criar_circuito(request):
    """Cria um novo circuito de comunicação."""
    if request.method == 'POST':
        form = CircuitoComunicacaoForm(request.POST)
        if form.is_valid():
            circuito = form.save(commit=False)
            circuito.organizador = request.user
            circuito.save()
            form.save_m2m()
            
            # Notifica os participantes
            for participante in circuito.participantes.all():
                if participante != request.user:
                    Notificacao.objects.create(
                        destinatario=participante,
                        remetente=request.user,
                        tipo='circuito',
                        titulo='Novo Circuito de Comunicação',
                        mensagem=f'Você foi convidado para participar do circuito "{circuito.titulo}"',
                        prioridade='media'
                    )
            
            messages.success(request, 'Circuito de comunicação criado com sucesso!')
            return redirect('listas_verificacao:detalhe_circuito', circuito_id=circuito.id)
    else:
        form = CircuitoComunicacaoForm()
    
    # Buscar turmas do professor ou turmas em que o aluno está matriculado
    if request.user.is_teacher:
        turmas = Turma.objects.filter(professor=request.user)
    else:
        turmas = request.user.turmas_aluno.all()
    
    # Buscar alunos das turmas
    alunos = User.objects.filter(turmas_aluno__in=turmas).distinct()
    
    # Buscar aprendizagens das turmas
    aprendizagens = AprendizagemEssencial.objects.filter(
        listas_verificacao__turma__in=turmas
    ).distinct()
    
    context = {
        'form': form,
        'tipos': CircuitoComunicacao.TIPOS,
        'turmas': turmas,
        'alunos': alunos,
        'aprendizagens': aprendizagens
    }
    return render(request, 'listas_verificacao/circuitos/criar_circuito.html', context)

@login_required
def detalhe_circuito(request, circuito_id):
    """Exibe os detalhes de um circuito de comunicação."""
    circuito = get_object_or_404(CircuitoComunicacao, id=circuito_id)
    
    # Verifica permissões
    if not (request.user.is_professor or 
            request.user in circuito.participantes.all() or 
            request.user in circuito.turma.alunos.all()):
        raise PermissionDenied
    
    context = {
        'circuito': circuito,
    }
    return render(request, 'listas_verificacao/circuitos/detalhe_circuito.html', context)

@login_required
def lista_checklists(request):
    checklists = Checklist.objects.filter(usuario=request.user)
    return render(request, 'listas_verificacao/lista_checklists.html', {'checklists': checklists})

@login_required
def criar_checklist(request):
    if request.method == 'POST':
        form = ChecklistForm(request.POST)
        if form.is_valid():
            checklist = form.save(commit=False)
            checklist.usuario = request.user
            checklist.save()
            messages.success(request, 'Checklist criado com sucesso!')
            return redirect('lista_checklists')
    else:
        form = ChecklistForm()
    return render(request, 'listas_verificacao/form_checklist.html', {'form': form})

@login_required
def detalhe_checklist(request, checklist_id):
    checklist = get_object_or_404(Checklist, id=checklist_id, usuario=request.user)
    return render(request, 'listas_verificacao/detalhe_checklist.html', {'checklist': checklist})

@login_required
def editar_checklist(request, checklist_id):
    checklist = get_object_or_404(Checklist, id=checklist_id, usuario=request.user)
    if request.method == 'POST':
        form = ChecklistForm(request.POST, instance=checklist)
        if form.is_valid():
            form.save()
            messages.success(request, 'Checklist atualizado com sucesso!')
            return redirect('lista_checklists')
    else:
        form = ChecklistForm(instance=checklist)
    return render(request, 'listas_verificacao/form_checklist.html', {'form': form, 'checklist': checklist})

@login_required
def excluir_checklist(request, checklist_id):
    checklist = get_object_or_404(Checklist, id=checklist_id, usuario=request.user)
    if request.method == 'POST':
        checklist.delete()
        messages.success(request, 'Checklist excluído com sucesso!')
        return redirect('lista_checklists')
    return render(request, 'listas_verificacao/confirmar_exclusao.html', {'checklist': checklist})

@login_required
def lista_itens(request, checklist_id):
    checklist = get_object_or_404(Checklist, id=checklist_id, usuario=request.user)
    itens = Item.objects.filter(checklist=checklist)
    return render(request, 'listas_verificacao/lista_itens.html', {'checklist': checklist, 'itens': itens})

@login_required
def criar_item(request, checklist_id):
    checklist = get_object_or_404(Checklist, id=checklist_id, usuario=request.user)
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.checklist = checklist
            item.save()
            messages.success(request, 'Item criado com sucesso!')
            return redirect('lista_itens', checklist_id=checklist.id)
    else:
        form = ItemForm()
    return render(request, 'listas_verificacao/form_item.html', {'form': form, 'checklist': checklist})

@login_required
def editar_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, checklist__usuario=request.user)
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item atualizado com sucesso!')
            return redirect('lista_itens', checklist_id=item.checklist.id)
    else:
        form = ItemForm(instance=item)
    return render(request, 'listas_verificacao/form_item.html', {'form': form, 'item': item})

@login_required
def excluir_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, checklist__usuario=request.user)
    if request.method == 'POST':
        checklist_id = item.checklist.id
        item.delete()
        messages.success(request, 'Item excluído com sucesso!')
        return redirect('lista_itens', checklist_id=checklist_id)
    return render(request, 'listas_verificacao/confirmar_exclusao.html', {'item': item})

@login_required
def marcar_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, checklist__usuario=request.user)
    item.concluido = True
    item.save()
    messages.success(request, 'Item marcado como concluído!')
    return redirect('lista_itens', checklist_id=item.checklist.id)

@login_required
def desmarcar_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, checklist__usuario=request.user)
    item.concluido = False
    item.save()
    messages.success(request, 'Item desmarcado!')
    return redirect('lista_itens', checklist_id=item.checklist.id)

@login_required
def lista_categorias(request):
    categorias = Categoria.objects.filter(usuario=request.user)
    return render(request, 'listas_verificacao/lista_categorias.html', {'categorias': categorias})

@login_required
def criar_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.usuario = request.user
            categoria.save()
            messages.success(request, 'Categoria criada com sucesso!')
            return redirect('lista_categorias')
    else:
        form = CategoriaForm()
    return render(request, 'listas_verificacao/form_categoria.html', {'form': form})

@login_required
def editar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id, usuario=request.user)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoria atualizada com sucesso!')
            return redirect('lista_categorias')
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, 'listas_verificacao/form_categoria.html', {'form': form, 'categoria': categoria})

@login_required
def excluir_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id, usuario=request.user)
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, 'Categoria excluída com sucesso!')
        return redirect('lista_categorias')
    return render(request, 'listas_verificacao/confirmar_exclusao.html', {'categoria': categoria})

@login_required
def lista_metas(request):
    """Lista as metas do aluno ou da turma."""
    if request.user.is_teacher:
        # Professores veem metas de suas turmas
        turmas = Turma.objects.filter(professor=request.user)
        metas = MetaAprendizagem.objects.filter(turma__in=turmas)
    else:
        # Alunos veem suas próprias metas e as coletivas da turma
        metas = MetaAprendizagem.objects.filter(
            Q(aluno=request.user) | 
            Q(turma__in=request.user.turmas_aluno.all(), tipo='coletiva')
        ).distinct()
    
    context = {
        'metas': metas,
    }
    return render(request, 'listas_verificacao/metas/lista_metas.html', context)

@login_required
def criar_meta(request):
    if request.method == 'POST':
        form = MetaForm(request.POST)
        if form.is_valid():
            meta = form.save(commit=False)
            meta.usuario = request.user
            meta.save()
            messages.success(request, 'Meta criada com sucesso!')
            return redirect('lista_metas')
    else:
        form = MetaForm()
    return render(request, 'listas_verificacao/form_meta.html', {'form': form})

@login_required
def excluir_meta(request, meta_id):
    meta = get_object_or_404(Meta, id=meta_id, usuario=request.user)
    if request.method == 'POST':
        meta.delete()
        messages.success(request, 'Meta excluída com sucesso!')
        return redirect('lista_metas')
    return render(request, 'listas_verificacao/confirmar_exclusao.html', {'meta': meta})

@login_required
def responder_duvida(request, duvida_id):
    """View para responder a uma dúvida."""
    duvida = get_object_or_404(Duvida, id=duvida_id)
    
    # Verificar permissões
    if not (request.user.is_teacher or request.user in duvida.turma.alunos.all()):
        messages.error(request, 'Você não tem permissão para responder esta dúvida.')
        return redirect('listas_verificacao:lista_duvidas')
    
    if request.method == 'POST':
        texto = request.POST.get('texto')
        anexos = request.FILES.getlist('anexos')
        
        resposta = RespostaDuvida.objects.create(
            duvida=duvida,
            autor=request.user,
            texto=texto
        )
        
        # Processar anexos
        for anexo in anexos:
            resposta.anexos.save(anexo.name, anexo)
        
        # Se for professor respondendo, atualizar estado da dúvida
        if request.user.is_teacher:
            duvida.estado = 'respondida'
            duvida.data_resposta = timezone.now()
            duvida.respondido_por = request.user
            duvida.save()
        
        # Criar notificação
        if request.user.is_teacher:
            destinatario = duvida.autor
            mensagem = f'O professor {request.user.get_full_name()} respondeu sua dúvida.'
        else:
            destinatario = duvida.turma.professor
            mensagem = f'O aluno {request.user.get_full_name()} comentou em uma dúvida.'
        
        Notificacao.objects.create(
            destinatario=destinatario,
            tipo='resposta_duvida',
            titulo=f'Nova resposta - {duvida.titulo}',
            mensagem=mensagem,
            prioridade='media',
            lista_verificacao=None,
            aprendizagem=duvida.aprendizagem
        )
        
        messages.success(request, 'Resposta adicionada com sucesso!')
        return redirect('listas_verificacao:detalhe_duvida', duvida_id=duvida.id)
    
    context = {
        'duvida': duvida,
    }
    return render(request, 'listas_verificacao/duvidas/responder_duvida.html', context)

@login_required
def lista_duvidas_turma(request, turma_id):
    """View para listar todas as dúvidas de uma turma específica."""
    turma = get_object_or_404(Turma, id=turma_id)
    
    # Verificar permissões
    if not (request.user.is_teacher and request.user == turma.professor) and not (request.user.is_student and request.user in turma.alunos.all()):
        messages.error(request, 'Você não tem acesso a esta turma.')
        return redirect('listas_verificacao:lista_aluno')
    
    # Filtros
    estado = request.GET.get('estado')
    categoria = request.GET.get('categoria')
    prioridade = request.GET.get('prioridade')
    
    # Buscar dúvidas da turma
    duvidas = Duvida.objects.filter(turma=turma)
    
    if estado:
        duvidas = duvidas.filter(estado=estado)
    if categoria:
        duvidas = duvidas.filter(categoria=categoria)
    if prioridade:
        duvidas = duvidas.filter(prioridade=prioridade)
    
    # Ordenação
    duvidas = duvidas.order_by('-prioridade', '-data_criacao')
    
    context = {
        'turma': turma,
        'duvidas': duvidas,
        'estados': Duvida.ESTADOS,
        'categorias': Duvida.CATEGORIAS,
        'prioridades': Duvida.PRIORIDADES,
    }
    return render(request, 'listas_verificacao/duvidas/lista_duvidas_turma.html', context)

@login_required
@require_POST
def toggle_partilha(request, diario_id):
    """Alterna o estado de partilha de um diário."""
    diario = get_object_or_404(DiarioAprendizagem, id=diario_id)
    
    # Verificar se o usuário é o autor do diário
    if request.user != diario.aluno:
        return JsonResponse({'success': False, 'error': 'Não autorizado'}, status=403)
    
    # Alternar o estado de partilha
    diario.partilhado = not diario.partilhado
    diario.save()
    
    return JsonResponse({
        'success': True,
        'partilhado': diario.partilhado
    })

@login_required
@require_POST
def adicionar_reflexao_conquista(request, conquista_id):
    """Adiciona uma reflexão sobre o impacto de uma conquista."""
    conquista = get_object_or_404(ConquistaColetiva, id=conquista_id)
    
    # Verificar se o usuário é o criador da conquista
    if request.user != conquista.criador:
        messages.error(request, 'Apenas o criador da conquista pode adicionar reflexões.')
        return redirect('listas_verificacao:detalhe_conquista', conquista_id=conquista.id)
    
    reflexao = request.POST.get('reflexao')
    if reflexao:
        # Atualizar a reflexão de impacto da conquista
        conquista.reflexao_impacto = reflexao
        conquista.save()
        
        # Criar notificação para os participantes
        for participante in conquista.participantes.all():
            if participante != request.user:
                Notificacao.objects.create(
                    destinatario=participante,
                    tipo='conquista',
                    titulo=f'Nova reflexão em conquista - {conquista.titulo}',
                    mensagem=f'{request.user.get_full_name()} adicionou uma reflexão sobre o impacto da conquista.',
                    prioridade='baixa'
                )
        
        messages.success(request, 'Reflexão adicionada com sucesso!')
    else:
        messages.error(request, 'O texto da reflexão é obrigatório.')
    
    return redirect('listas_verificacao:detalhe_conquista', conquista_id=conquista.id)

@login_required
def detalhe_duvida(request, duvida_id):
    """View para visualizar detalhes de uma dúvida e suas respostas."""
    duvida = get_object_or_404(Duvida, id=duvida_id)
    
    # Verificar permissões
    if not (request.user.is_teacher and request.user == duvida.turma.professor) and not (request.user.is_student and request.user in duvida.turma.alunos.all()):
        messages.error(request, 'Você não tem acesso a esta dúvida.')
        return redirect('listas_verificacao:lista_duvidas')
    
    # Buscar respostas ordenadas (melhor resposta primeiro)
    respostas = RespostaDuvida.objects.filter(duvida=duvida).order_by('-melhor_resposta', 'data_criacao')
    
    context = {
        'duvida': duvida,
        'respostas': respostas,
    }
    return render(request, 'listas_verificacao/duvidas/detalhe_duvida.html', context)

@login_required
@require_POST
def marcar_melhor_resposta(request, resposta_id):
    """View para marcar uma resposta como a melhor resposta."""
    resposta = get_object_or_404(RespostaDuvida, id=resposta_id)
    
    # Verificar permissões
    if request.user != resposta.duvida.autor and not request.user.is_teacher:
        messages.error(request, 'Você não tem permissão para marcar a melhor resposta.')
        return redirect('listas_verificacao:detalhe_duvida', duvida_id=resposta.duvida.id)
    
    # Desmarcar outras respostas como melhor resposta
    RespostaDuvida.objects.filter(duvida=resposta.duvida, melhor_resposta=True).update(melhor_resposta=False)
    
    # Marcar esta como melhor resposta
    resposta.melhor_resposta = True
    resposta.save()
    
    # Atualizar estado da dúvida
    resposta.duvida.estado = 'respondida'
    resposta.duvida.data_resposta = timezone.now()
    resposta.duvida.respondido_por = resposta.autor
    resposta.duvida.save()
    
    # Criar notificação para o autor da resposta
    if request.user != resposta.autor:
        Notificacao.objects.create(
            destinatario=resposta.autor,
            tipo='resposta_duvida',
            titulo=f'Sua resposta foi marcada como melhor resposta',
            mensagem=f'Sua resposta para a dúvida "{resposta.duvida.titulo}" foi marcada como a melhor resposta.',
            prioridade='media',
            lista_verificacao=None,
            aprendizagem=resposta.duvida.aprendizagem
        )
    
    messages.success(request, 'Resposta marcada como melhor resposta!')
    return redirect('listas_verificacao:detalhe_duvida', duvida_id=resposta.duvida.id)

@login_required
@require_POST
def atualizar_estado_duvida(request, duvida_id):
    """View para atualizar o estado de uma dúvida."""
    duvida = get_object_or_404(Duvida, id=duvida_id)
    
    # Verificar permissões
    if not (request.user.is_teacher or request.user == duvida.autor):
        return JsonResponse({'success': False, 'error': 'Não autorizado'}, status=403)
    
    try:
        data = json.loads(request.body)
        novo_estado = data.get('estado')
        
        if novo_estado in [estado[0] for estado in Duvida.ESTADOS]:
            duvida.estado = novo_estado
            duvida.save()
            
            # Se o professor está fechando a dúvida, notificar o aluno
            if novo_estado == 'fechada' and request.user.is_teacher:
                Notificacao.objects.create(
                    destinatario=duvida.autor,
                    tipo='resposta_duvida',
                    titulo=f'Dúvida fechada - {duvida.titulo}',
                    mensagem=f'O professor {request.user.get_full_name()} fechou sua dúvida.',
                    prioridade='media',
                    aprendizagem=duvida.aprendizagem
                )
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Estado inválido'}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Dados inválidos'}, status=400)

@login_required
def lista_diarios(request):
    """Lista os diários de aprendizagem do aluno ou da turma."""
    if request.user.is_teacher:
        # Professores veem diários de suas turmas
        turmas = Turma.objects.filter(professor=request.user)
        diarios = DiarioAprendizagem.objects.filter(turma__in=turmas, partilhado=True)
    else:
        # Alunos veem seus próprios diários e os compartilhados da turma
        diarios = DiarioAprendizagem.objects.filter(
            Q(aluno=request.user) | 
            Q(turma__in=request.user.turmas_aluno.all(), partilhado=True)
        ).distinct()
    
    context = {
        'diarios': diarios,
    }
    return render(request, 'listas_verificacao/diario/lista_diarios.html', context)

@login_required
def criar_diario(request):
    """Cria um novo diário de aprendizagem."""
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        turma_id = request.POST.get('turma')
        compartilhado = request.POST.get('compartilhado') == 'on'
        
        turma = get_object_or_404(Turma, id=turma_id)
        
        # Verificar se o aluno pertence à turma
        if not request.user.is_teacher and request.user not in turma.alunos.all():
            messages.error(request, 'Você não tem permissão para criar um diário nesta turma.')
            return redirect('listas_verificacao:lista_diarios')
        
        diario = DiarioAprendizagem.objects.create(
            aluno=request.user,
            titulo=titulo,
            descricao=descricao,
            turma=turma,
            partilhado=compartilhado
        )
        
        messages.success(request, 'Diário criado com sucesso!')
        return redirect('listas_verificacao:detalhe_diario', diario_id=diario.id)
    
    # GET request
    if request.user.is_teacher:
        turmas = Turma.objects.filter(professor=request.user)
    else:
        turmas = request.user.turmas_aluno.all()
    
    context = {
        'turmas': turmas,
    }
    return render(request, 'listas_verificacao/diario/criar_diario.html', context)

@login_required
def detalhe_diario(request, diario_id):
    """Visualiza um diário específico e suas entradas."""
    diario = get_object_or_404(DiarioAprendizagem, id=diario_id)
    
    # Verificar permissões
    if not request.user.is_teacher and request.user != diario.aluno and not diario.partilhado:
        messages.error(request, 'Você não tem permissão para ver este diário.')
        return redirect('listas_verificacao:lista_diarios')
    
    # Buscar todas as entradas do diário
    entradas = diario.entradas.all().order_by('-data_criacao')
    
    context = {
        'diario': diario,
        'entradas': entradas,
    }
    return render(request, 'listas_verificacao/diario/detalhe_diario.html', context)

@login_required
def criar_entrada(request, diario_id):
    """Cria uma nova entrada no diário."""
    diario = get_object_or_404(DiarioAprendizagem, id=diario_id)
    
    # Verificar se o usuário é o autor do diário
    if request.user != diario.aluno:
        messages.error(request, 'Você não tem permissão para adicionar entradas neste diário.')
        return redirect('listas_verificacao:detalhe_diario', diario_id=diario_id)
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        conteudo = request.POST.get('conteudo')
        tipo = request.POST.get('tipo')
        aprendizagens_ids = request.POST.getlist('aprendizagens')
        anexos = request.FILES.getlist('anexos')
        
        entrada = EntradaDiario.objects.create(
            diario=diario,
            titulo=titulo,
            conteudo=conteudo,
            tipo=tipo
        )
        
        # Adicionar aprendizagens relacionadas
        if aprendizagens_ids:
            aprendizagens = AprendizagemEssencial.objects.filter(id__in=aprendizagens_ids)
            entrada.aprendizagens.set(aprendizagens)
        
        # Processar anexos
        for anexo in anexos:
            entrada.anexos.save(anexo.name, anexo)
        
        # Criar notificação para o professor se o diário for compartilhado
        if diario.partilhado:
            Notificacao.objects.create(
                destinatario=diario.turma.professor,
                tipo='feedback',
                titulo=f'Nova entrada no diário - {diario.titulo}',
                mensagem=f'O aluno {request.user.get_full_name()} adicionou uma nova entrada no diário.',
                prioridade='media'
            )
        
        messages.success(request, 'Entrada adicionada com sucesso!')
        return redirect('listas_verificacao:detalhe_diario', diario_id=diario_id)
    
    # GET request
    # Buscar todas as aprendizagens disponíveis para a turma
    aprendizagens = AprendizagemEssencial.objects.filter(
        listas_verificacao__turma=diario.turma
    ).distinct()
    
    context = {
        'diario': diario,
        'tipos_entrada': EntradaDiario.TIPOS,
        'aprendizagens': aprendizagens,
    }
    return render(request, 'listas_verificacao/diario/criar_entrada.html', context)

@login_required
def adicionar_comentario_entrada(request, entrada_id):
    """Adiciona um comentário em uma entrada do diário."""
    entrada = get_object_or_404(EntradaDiario, id=entrada_id)
    
    # Verificar permissões
    if not request.user.is_teacher and request.user not in entrada.diario.turma.alunos.all():
        messages.error(request, 'Você não tem permissão para comentar nesta entrada.')
        return redirect('listas_verificacao:detalhe_diario', diario_id=entrada.diario.id)
    
    if request.method == 'POST':
        conteudo = request.POST.get('conteudo')
        
        if not conteudo:
            messages.error(request, 'O comentário não pode estar vazio.')
            return redirect('listas_verificacao:detalhe_diario', diario_id=entrada.diario.id)
        
        comentario = ComentarioEntrada.objects.create(
            entrada=entrada,
            autor=request.user,
            conteudo=conteudo
        )
        
        # Notificar o autor da entrada se não for ele mesmo comentando
        if request.user != entrada.diario.aluno:
            Notificacao.objects.create(
                destinatario=entrada.diario.aluno,
                tipo='feedback',
                titulo=f'Novo comentário em sua entrada',
                mensagem=f'{request.user.get_full_name()} comentou em sua entrada "{entrada.titulo}".',
                prioridade='baixa',
                lista_verificacao=entrada.diario.turma.lista_verificacao,
            )
        
        messages.success(request, 'Comentário adicionado com sucesso!')
        return redirect('listas_verificacao:detalhe_diario', diario_id=entrada.diario.id)
    
    context = {
        'entrada': entrada,
    }
    return render(request, 'listas_verificacao/diario/adicionar_comentario.html', context)

@login_required
def adicionar_conexao(request, entrada_id):
    """Adiciona uma conexão entre uma entrada e uma aprendizagem."""
    entrada = get_object_or_404(EntradaDiario, id=entrada_id)
    
    # Verificar se o usuário é o autor do diário
    if request.user != entrada.diario.aluno:
        messages.error(request, 'Você não tem permissão para adicionar conexões nesta entrada.')
        return redirect('listas_verificacao:detalhe_diario', diario_id=entrada.diario.id)
    
    if request.method == 'POST':
        aprendizagem_id = request.POST.get('aprendizagem')
        descricao = request.POST.get('descricao')
        
        if not aprendizagem_id:
            messages.error(request, 'Selecione uma aprendizagem para criar a conexão.')
            return redirect('listas_verificacao:detalhe_diario', diario_id=entrada.diario.id)
        
        aprendizagem = get_object_or_404(AprendizagemEssencial, id=aprendizagem_id)
        
        # Verificar se a conexão já existe
        if ConexaoAprendizagem.objects.filter(entrada=entrada, aprendizagem=aprendizagem).exists():
            messages.warning(request, 'Esta conexão já existe.')
            return redirect('listas_verificacao:detalhe_diario', diario_id=entrada.diario.id)
        
        conexao = ConexaoAprendizagem.objects.create(
            entrada=entrada,
            aprendizagem=aprendizagem,
            descricao=descricao
        )
        
        messages.success(request, 'Conexão adicionada com sucesso!')
        return redirect('listas_verificacao:detalhe_diario', diario_id=entrada.diario.id)
    
    # GET request
    # Buscar aprendizagens disponíveis (que ainda não estão conectadas)
    aprendizagens = AprendizagemEssencial.objects.filter(
        listas_verificacao__turma=entrada.diario.turma
    ).exclude(
        id__in=entrada.aprendizagens.values_list('id', flat=True)
    ).distinct()
    
    context = {
        'entrada': entrada,
        'aprendizagens': aprendizagens,
    }
    return render(request, 'listas_verificacao/diario/adicionar_conexao.html', context)

@login_required
def solicitar_alteracao_meta(request, meta_id):
    """Permite que um aluno ou professor solicite uma alteração na meta."""
    meta = get_object_or_404(MetaAprendizagem, id=meta_id)
    
    # Verificar permissões
    if not (request.user == meta.aluno or request.user.is_teacher):
        messages.error(request, 'Você não tem permissão para solicitar alterações nesta meta.')
        return redirect('listas_verificacao:detalhe_meta', meta_id=meta.id)
    
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        descricao = request.POST.get('descricao')
        justificativa = request.POST.get('justificativa')
        
        if not all([tipo, descricao, justificativa]):
            messages.error(request, 'Por favor, preencha todos os campos.')
            return redirect('listas_verificacao:solicitar_alteracao_meta', meta_id=meta.id)
        
        alteracao = AlteracaoMeta.objects.create(
            meta=meta,
            tipo=tipo,
            descricao=descricao,
            justificativa=justificativa
        )
        
        # Notificar o professor se a solicitação foi feita por um aluno
        if request.user == meta.aluno:
            Notificacao.objects.create(
                destinatario=meta.turma.professor,
                tipo='alteracao_meta',
                titulo=f'Nova solicitação de alteração - {meta.titulo}',
                mensagem=f'O aluno {request.user.get_full_name()} solicitou uma alteração na meta.',
                prioridade='media'
            )
        
        messages.success(request, 'Solicitação de alteração enviada com sucesso!')
        return redirect('listas_verificacao:detalhe_meta', meta_id=meta.id)
    
    context = {
        'meta': meta,
        'tipos_alteracao': AlteracaoMeta.TIPOS_ALTERACAO,
    }
    return render(request, 'listas_verificacao/metas/solicitar_alteracao.html', context)

@login_required
def get_turma_dados(request, turma_id):
    """Retorna os dados de uma turma (alunos e aprendizagens) em formato JSON."""
    turma = get_object_or_404(Turma, pk=turma_id)
    
    # Verifica se o usuário tem permissão para acessar os dados da turma
    if not request.user.is_staff and not turma.professores.filter(id=request.user.id).exists():
        return JsonResponse({'error': 'Permissão negada'}, status=403)
    
    # Obtém alunos da turma
    alunos = [{'id': aluno.id, 'nome': str(aluno)} for aluno in turma.alunos.all()]
    
    # Obtém aprendizagens da turma
    aprendizagens = [
        {'id': ap.id, 'texto': str(ap)} 
        for ap in AprendizagemEssencial.objects.filter(listas_verificacao__turma=turma).distinct()
    ]
    
    return JsonResponse({
        'alunos': alunos,
        'aprendizagens': aprendizagens
    })

