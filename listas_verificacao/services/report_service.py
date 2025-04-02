from django.db.models import Count, Q, Avg, Min, Max
from django.utils import timezone
from datetime import timedelta
from listas_verificacao.models import Turma, ListaVerificacao, ProgressoAluno, AprendizagemEssencial

def gerar_relatorio_progresso_turma(turma):
    """
    Gera um relatório detalhado do progresso de uma turma.
    
    Args:
        turma: Instância do modelo Turma
        
    Returns:
        dict: Dicionário com as métricas do relatório
    """
    # Buscar todas as listas da turma
    listas = ListaVerificacao.objects.filter(turma=turma)
    total_listas = listas.count()
    
    # Buscar todos os alunos da turma
    alunos = turma.alunos.all()
    total_alunos = alunos.count()
    
    # Métricas gerais
    total_aprendizagens = sum(lista.aprendizagens.count() for lista in listas)
    
    # Progresso por lista
    progresso_listas = []
    for lista in listas:
        progressos = ProgressoAluno.objects.filter(
            lista_verificacao=lista,
            aluno__in=alunos
        )
        
        # Calcular métricas da lista
        total_aprendizagens_lista = lista.aprendizagens.count()
        alunos_concluidos = progressos.filter(estado='concluido').count()
        alunos_dificuldade = progressos.filter(estado='dificuldade').count()
        
        # Calcular progresso médio
        if total_alunos > 0 and total_aprendizagens_lista > 0:
            progresso_medio = 0
            for aluno in alunos:
                progressos_aluno = progressos.filter(aluno=aluno)
                aprendizagens_concluidas = progressos_aluno.filter(estado='concluido').count()
                progresso_medio += (aprendizagens_concluidas / total_aprendizagens_lista) * 100
            progresso_medio = progresso_medio / total_alunos
        else:
            progresso_medio = 0
        
        # Calcular tempo médio de conclusão
        tempo_medio = progressos.filter(
            estado='concluido',
            data_atualizacao__isnull=False
        ).aggregate(
            tempo_medio=Avg(
                timezone.now() - timezone.timedelta(days=1) - timezone.now()
            )
        )['tempo_medio']
        
        progresso_listas.append({
            'lista': lista,
            'progresso_medio': round(progresso_medio, 1),
            'total_alunos': total_alunos,
            'alunos_concluidos': alunos_concluidos,
            'alunos_dificuldade': alunos_dificuldade,
            'tempo_medio_conclusao': tempo_medio,
            'total_aprendizagens': total_aprendizagens_lista
        })
    
    # Calcular progresso geral da turma
    if total_alunos > 0 and total_aprendizagens > 0:
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
    
    # Identificar aprendizagens mais difíceis
    aprendizagens_dificeis = []
    for lista in listas:
        for aprendizagem in lista.aprendizagens.all():
            progressos = ProgressoAluno.objects.filter(
                lista_verificacao=lista,
                aprendizagem=aprendizagem,
                aluno__in=alunos
            )
            
            total_progressos = progressos.count()
            if total_progressos > 0:
                dificuldade = progressos.filter(estado='dificuldade').count() / total_progressos
                if dificuldade > 0.3:  # Mais de 30% dos alunos com dificuldade
                    aprendizagens_dificeis.append({
                        'aprendizagem': aprendizagem,
                        'lista': lista,
                        'percentual_dificuldade': round(dificuldade * 100, 1),
                        'total_alunos': total_progressos,
                        'alunos_dificuldade': progressos.filter(estado='dificuldade').count()
                    })
    
    # Ordenar aprendizagens difíceis por percentual de dificuldade
    aprendizagens_dificeis.sort(key=lambda x: x['percentual_dificuldade'], reverse=True)
    
    return {
        'turma': turma,
        'total_alunos': total_alunos,
        'total_listas': total_listas,
        'total_aprendizagens': total_aprendizagens,
        'progresso_geral': round(progresso_geral, 1),
        'progresso_listas': progresso_listas,
        'aprendizagens_dificeis': aprendizagens_dificeis[:5],  # Top 5 mais difíceis
        'data_geracao': timezone.now()
    }

def gerar_relatorio_progresso_aluno(aluno, turma):
    """
    Gera um relatório detalhado do progresso de um aluno em uma turma.
    
    Args:
        aluno: Instância do modelo User (aluno)
        turma: Instância do modelo Turma
        
    Returns:
        dict: Dicionário com as métricas do relatório
    """
    # Buscar todas as listas da turma
    listas = ListaVerificacao.objects.filter(turma=turma)
    total_listas = listas.count()
    
    # Métricas gerais
    total_aprendizagens = sum(lista.aprendizagens.count() for lista in listas)
    
    # Progresso por lista
    progresso_listas = []
    for lista in listas:
        progressos = ProgressoAluno.objects.filter(
            lista_verificacao=lista,
            aluno=aluno
        )
        
        # Calcular métricas da lista
        total_aprendizagens_lista = lista.aprendizagens.count()
        aprendizagens_concluidas = progressos.filter(estado='concluido').count()
        aprendizagens_dificuldade = progressos.filter(estado='dificuldade').count()
        
        # Calcular progresso
        if total_aprendizagens_lista > 0:
            progresso = (aprendizagens_concluidas / total_aprendizagens_lista) * 100
        else:
            progresso = 0
        
        # Calcular tempo médio de conclusão
        tempo_medio = progressos.filter(
            estado='concluido',
            data_atualizacao__isnull=False
        ).aggregate(
            tempo_medio=Avg(
                timezone.now() - timezone.timedelta(days=1) - timezone.now()
            )
        )['tempo_medio']
        
        progresso_listas.append({
            'lista': lista,
            'progresso': round(progresso, 1),
            'total_aprendizagens': total_aprendizagens_lista,
            'aprendizagens_concluidas': aprendizagens_concluidas,
            'aprendizagens_dificuldade': aprendizagens_dificuldade,
            'tempo_medio_conclusao': tempo_medio
        })
    
    # Calcular progresso geral
    if total_aprendizagens > 0:
        progresso_geral = 0
        for lista in listas:
            progressos = ProgressoAluno.objects.filter(
                lista_verificacao=lista,
                aluno=aluno
            )
            aprendizagens_concluidas = progressos.filter(estado='concluido').count()
            progresso_geral += (aprendizagens_concluidas / lista.aprendizagens.count()) * 100
        progresso_geral = progresso_geral / total_listas
    else:
        progresso_geral = 0
    
    # Identificar aprendizagens com dificuldade
    aprendizagens_dificuldade = []
    for lista in listas:
        for aprendizagem in lista.aprendizagens.all():
            progresso = ProgressoAluno.objects.filter(
                lista_verificacao=lista,
                aprendizagem=aprendizagem,
                aluno=aluno
            ).first()
            
            if progresso and progresso.estado == 'dificuldade':
                aprendizagens_dificuldade.append({
                    'aprendizagem': aprendizagem,
                    'lista': lista,
                    'data_atualizacao': progresso.data_atualizacao
                })
    
    # Ordenar aprendizagens com dificuldade por data de atualização
    aprendizagens_dificuldade.sort(key=lambda x: x['data_atualizacao'], reverse=True)
    
    return {
        'aluno': aluno,
        'turma': turma,
        'total_listas': total_listas,
        'total_aprendizagens': total_aprendizagens,
        'progresso_geral': round(progresso_geral, 1),
        'progresso_listas': progresso_listas,
        'aprendizagens_dificuldade': aprendizagens_dificuldade,
        'data_geracao': timezone.now()
    }

def gerar_relatorio_tempo_conclusao(turma):
    """
    Gera um relatório detalhado do tempo médio de conclusão das listas por turma.
    
    Args:
        turma: Instância do modelo Turma
        
    Returns:
        dict: Dicionário com as métricas do relatório
    """
    # Buscar todas as listas da turma
    listas = ListaVerificacao.objects.filter(turma=turma)
    total_listas = listas.count()
    
    # Buscar todos os alunos da turma
    alunos = turma.alunos.all()
    total_alunos = alunos.count()
    
    # Métricas por lista
    tempo_listas = []
    for lista in listas:
        progressos = ProgressoAluno.objects.filter(
            lista_verificacao=lista,
            aluno__in=alunos,
            estado='concluido',
            data_atualizacao__isnull=False
        )
        
        # Calcular tempo médio de conclusão
        tempo_medio = progressos.aggregate(
            tempo_medio=Avg(
                timezone.now() - timezone.timedelta(days=1) - timezone.now()
            )
        )['tempo_medio']
        
        # Contar alunos que concluíram
        alunos_concluidos = progressos.values('aluno').distinct().count()
        
        # Calcular tempo mínimo e máximo
        tempo_min = progressos.aggregate(
            tempo_min=Min(
                timezone.now() - timezone.timedelta(days=1) - timezone.now()
            )
        )['tempo_min']
        
        tempo_max = progressos.aggregate(
            tempo_max=Max(
                timezone.now() - timezone.timedelta(days=1) - timezone.now()
            )
        )['tempo_max']
        
        tempo_listas.append({
            'lista': lista,
            'tempo_medio': tempo_medio,
            'tempo_min': tempo_min,
            'tempo_max': tempo_max,
            'alunos_concluidos': alunos_concluidos,
            'total_alunos': total_alunos
        })
    
    # Calcular tempo médio geral da turma
    tempo_medio_geral = sum(
        item['tempo_medio'] for item in tempo_listas if item['tempo_medio']
    ) / len([item for item in tempo_listas if item['tempo_medio']]) if tempo_listas else 0
    
    return {
        'turma': turma,
        'total_listas': total_listas,
        'total_alunos': total_alunos,
        'tempo_medio_geral': tempo_medio_geral,
        'tempo_listas': tempo_listas,
        'data_geracao': timezone.now()
    }

def gerar_relatorio_objetivos_dificeis(turma):
    """
    Gera um relatório detalhado dos objetivos que apresentam mais dificuldades.
    Considera apenas objetivos que foram iniciados por pelo menos um aluno.
    
    Args:
        turma: Instância do modelo Turma
        
    Returns:
        dict: Dicionário com as métricas do relatório
    """
    # Buscar todas as listas da turma
    listas = ListaVerificacao.objects.filter(turma=turma)
    total_listas = listas.count()
    
    # Buscar todos os alunos da turma
    alunos = turma.alunos.all()
    total_alunos = alunos.count()
    
    # Métricas por objetivo
    objetivos_dificeis = []
    for lista in listas:
        for aprendizagem in lista.aprendizagens.all():
            # Buscar progressos iniciados (não iniciado não é considerado)
            progressos = ProgressoAluno.objects.filter(
                lista_verificacao=lista,
                aprendizagem=aprendizagem,
                aluno__in=alunos,
                estado__in=['em_progresso', 'concluido', 'dificuldade']
            )
            
            total_progressos = progressos.count()
            if total_progressos > 0:
                # Calcular percentual de dificuldade
                dificuldade = progressos.filter(estado='dificuldade').count() / total_progressos
                
                # Calcular tempo médio de conclusão
                tempo_medio = progressos.filter(
                    estado='concluido',
                    data_atualizacao__isnull=False
                ).aggregate(
                    tempo_medio=Avg(
                        timezone.now() - timezone.timedelta(days=1) - timezone.now()
                    )
                )['tempo_medio']
                
                # Contar alunos que concluíram
                alunos_concluidos = progressos.filter(estado='concluido').count()
                
                objetivos_dificeis.append({
                    'aprendizagem': aprendizagem,
                    'lista': lista,
                    'percentual_dificuldade': round(dificuldade * 100, 1),
                    'total_progressos': total_progressos,
                    'alunos_dificuldade': progressos.filter(estado='dificuldade').count(),
                    'alunos_concluidos': alunos_concluidos,
                    'tempo_medio': tempo_medio
                })
    
    # Ordenar objetivos por percentual de dificuldade
    objetivos_dificeis.sort(key=lambda x: x['percentual_dificuldade'], reverse=True)
    
    # Calcular métricas gerais
    total_objetivos = len(objetivos_dificeis)
    media_dificuldade = sum(item['percentual_dificuldade'] for item in objetivos_dificeis) / total_objetivos if total_objetivos > 0 else 0
    
    return {
        'turma': turma,
        'total_listas': total_listas,
        'total_alunos': total_alunos,
        'total_objetivos': total_objetivos,
        'media_dificuldade': round(media_dificuldade, 1),
        'objetivos_dificeis': objetivos_dificeis,
        'data_geracao': timezone.now()
    }

def gerar_relatorio_dificuldades_aluno(aluno, turma):
    """
    Gera um relatório detalhado das aprendizagens com dificuldade de um aluno.
    
    Args:
        aluno: Instância do modelo User (aluno)
        turma: Instância do modelo Turma
        
    Returns:
        dict: Dicionário com as métricas do relatório
    """
    # Buscar todas as listas da turma
    listas = ListaVerificacao.objects.filter(turma=turma)
    total_listas = listas.count()
    
    # Métricas gerais
    total_aprendizagens = sum(lista.aprendizagens.count() for lista in listas)
    
    # Progresso por lista
    progresso_listas = []
    for lista in listas:
        progressos = ProgressoAluno.objects.filter(
            lista_verificacao=lista,
            aluno=aluno
        )
        
        # Calcular métricas da lista
        total_aprendizagens_lista = lista.aprendizagens.count()
        aprendizagens_concluidas = progressos.filter(estado='concluido').count()
        aprendizagens_dificuldade = progressos.filter(estado='dificuldade').count()
        
        # Calcular progresso
        if total_aprendizagens_lista > 0:
            progresso = (aprendizagens_concluidas / total_aprendizagens_lista) * 100
        else:
            progresso = 0
        
        # Calcular tempo médio de conclusão
        tempo_medio = progressos.filter(
            estado='concluido',
            data_atualizacao__isnull=False
        ).aggregate(
            tempo_medio=Avg(
                timezone.now() - timezone.timedelta(days=1) - timezone.now()
            )
        )['tempo_medio']
        
        progresso_listas.append({
            'lista': lista,
            'progresso': round(progresso, 1),
            'total_aprendizagens': total_aprendizagens_lista,
            'aprendizagens_concluidas': aprendizagens_concluidas,
            'aprendizagens_dificuldade': aprendizagens_dificuldade,
            'tempo_medio_conclusao': tempo_medio
        })
    
    # Calcular progresso geral
    if total_aprendizagens > 0:
        progresso_geral = 0
        for lista in listas:
            progressos = ProgressoAluno.objects.filter(
                lista_verificacao=lista,
                aluno=aluno
            )
            aprendizagens_concluidas = progressos.filter(estado='concluido').count()
            progresso_geral += (aprendizagens_concluidas / lista.aprendizagens.count()) * 100
        progresso_geral = progresso_geral / total_listas
    else:
        progresso_geral = 0
    
    # Identificar aprendizagens com dificuldade
    aprendizagens_dificuldade = []
    for lista in listas:
        for aprendizagem in lista.aprendizagens.all():
            progresso = ProgressoAluno.objects.filter(
                lista_verificacao=lista,
                aprendizagem=aprendizagem,
                aluno=aluno,
                estado='dificuldade'
            ).first()
            
            if progresso:
                # Calcular tempo na dificuldade
                tempo_dificuldade = timezone.now() - progresso.data_atualizacao if progresso.data_atualizacao else None
                
                aprendizagens_dificuldade.append({
                    'aprendizagem': aprendizagem,
                    'lista': lista,
                    'data_atualizacao': progresso.data_atualizacao,
                    'tempo_dificuldade': tempo_dificuldade
                })
    
    # Ordenar aprendizagens com dificuldade por tempo na dificuldade
    aprendizagens_dificuldade.sort(key=lambda x: x['data_atualizacao'] if x['data_atualizacao'] else timezone.now(), reverse=True)
    
    return {
        'aluno': aluno,
        'turma': turma,
        'total_listas': total_listas,
        'total_aprendizagens': total_aprendizagens,
        'progresso_geral': round(progresso_geral, 1),
        'progresso_listas': progresso_listas,
        'aprendizagens_dificuldade': aprendizagens_dificuldade,
        'data_geracao': timezone.now()
    }

def gerar_relatorio_aprendizagens_pendentes(turma):
    """
    Gera um relatório detalhado das aprendizagens pendentes de confirmação por aluno.
    
    Args:
        turma: Instância do modelo Turma
        
    Returns:
        dict: Dicionário com as métricas do relatório
    """
    # Buscar todas as listas da turma
    listas = ListaVerificacao.objects.filter(turma=turma)
    total_listas = listas.count()
    
    # Buscar todos os alunos da turma
    alunos = turma.alunos.all()
    total_alunos = alunos.count()
    
    # Métricas por aluno
    aprendizagens_pendentes = []
    for aluno in alunos:
        # Buscar todas as aprendizagens marcadas como concluídas pelo aluno
        progressos_concluidos = ProgressoAluno.objects.filter(
            aluno=aluno,
            lista_verificacao__in=listas,
            estado='concluido'
        )
        
        # Filtrar apenas as que não foram confirmadas pelo professor
        pendentes = progressos_concluidos.filter(confirmado=False)
        
        if pendentes.exists():
            # Agrupar por lista
            for lista in listas:
                pendentes_lista = pendentes.filter(lista_verificacao=lista)
                if pendentes_lista.exists():
                    aprendizagens_pendentes.append({
                        'aluno': aluno,
                        'lista': lista,
                        'total_pendentes': pendentes_lista.count(),
                        'aprendizagens': pendentes_lista.select_related('aprendizagem'),
                        'data_mais_recente': pendentes_lista.order_by('-data_atualizacao').first().data_atualizacao
                    })
    
    # Ordenar por data mais recente
    aprendizagens_pendentes.sort(key=lambda x: x['data_mais_recente'], reverse=True)
    
    # Calcular métricas gerais
    total_pendentes = sum(item['total_pendentes'] for item in aprendizagens_pendentes)
    alunos_com_pendentes = len(set(item['aluno'] for item in aprendizagens_pendentes))
    
    return {
        'turma': turma,
        'total_listas': total_listas,
        'total_alunos': total_alunos,
        'total_pendentes': total_pendentes,
        'alunos_com_pendentes': alunos_com_pendentes,
        'aprendizagens_pendentes': aprendizagens_pendentes,
        'data_geracao': timezone.now()
    }

def gerar_relatorio_tendencias_progresso(turma):
    """
    Gera um relatório detalhado das tendências de progresso da turma ao longo do tempo.
    
    Args:
        turma: Instância do modelo Turma
        
    Returns:
        dict: Dicionário com as métricas do relatório
    """
    # Buscar todas as listas da turma
    listas = ListaVerificacao.objects.filter(turma=turma)
    total_listas = listas.count()
    
    # Buscar todos os alunos da turma
    alunos = turma.alunos.all()
    total_alunos = alunos.count()
    
    # Calcular progresso por período
    progresso_periodos = []
    for lista in listas:
        # Buscar progressos ordenados por data
        progressos = ProgressoAluno.objects.filter(
            lista_verificacao=lista,
            aluno__in=alunos,
            data_atualizacao__isnull=False
        ).order_by('data_atualizacao')
        
        if progressos.exists():
            # Agrupar por mês
            progresso_mensal = {}
            for progresso in progressos:
                mes = progresso.data_atualizacao.strftime('%Y-%m')
                if mes not in progresso_mensal:
                    progresso_mensal[mes] = {
                        'total_aprendizagens': lista.aprendizagens.count(),
                        'aprendizagens_concluidas': 0,
                        'aprendizagens_dificuldade': 0,
                        'total_alunos': total_alunos,
                        'alunos_concluidos': 0,
                        'alunos_dificuldade': 0
                    }
                
                if progresso.estado == 'concluido':
                    progresso_mensal[mes]['aprendizagens_concluidas'] += 1
                    if progresso_mensal[mes]['aprendizagens_concluidas'] == progresso_mensal[mes]['total_aprendizagens']:
                        progresso_mensal[mes]['alunos_concluidos'] += 1
                elif progresso.estado == 'dificuldade':
                    progresso_mensal[mes]['aprendizagens_dificuldade'] += 1
                    if progresso_mensal[mes]['aprendizagens_dificuldade'] == progresso_mensal[mes]['total_aprendizagens']:
                        progresso_mensal[mes]['alunos_dificuldade'] += 1
            
            # Calcular percentuais e adicionar ao progresso da lista
            for mes, dados in progresso_mensal.items():
                progresso_periodos.append({
                    'lista': lista,
                    'mes': mes,
                    'total_aprendizagens': dados['total_aprendizagens'],
                    'aprendizagens_concluidas': dados['aprendizagens_concluidas'],
                    'aprendizagens_dificuldade': dados['aprendizagens_dificuldade'],
                    'total_alunos': dados['total_alunos'],
                    'alunos_concluidos': dados['alunos_concluidos'],
                    'alunos_dificuldade': dados['alunos_dificuldade'],
                    'percentual_conclusao': round((dados['aprendizagens_concluidas'] / dados['total_aprendizagens']) * 100, 1) if dados['total_aprendizagens'] > 0 else 0,
                    'percentual_dificuldade': round((dados['aprendizagens_dificuldade'] / dados['total_aprendizagens']) * 100, 1) if dados['total_aprendizagens'] > 0 else 0,
                    'percentual_alunos_concluidos': round((dados['alunos_concluidos'] / dados['total_alunos']) * 100, 1) if dados['total_alunos'] > 0 else 0,
                    'percentual_alunos_dificuldade': round((dados['alunos_dificuldade'] / dados['total_alunos']) * 100, 1) if dados['total_alunos'] > 0 else 0
                })
    
    # Ordenar por data
    progresso_periodos.sort(key=lambda x: x['mes'])
    
    # Calcular tendências
    tendencias = []
    for lista in listas:
        progressos_lista = [p for p in progresso_periodos if p['lista'] == lista]
        if len(progressos_lista) >= 2:
            # Calcular variação do progresso
            progresso_inicial = progressos_lista[0]['percentual_conclusao']
            progresso_final = progressos_lista[-1]['percentual_conclusao']
            variacao = progresso_final - progresso_inicial
            
            # Calcular velocidade média de progresso
            meses = len(progressos_lista)
            velocidade_media = variacao / meses if meses > 0 else 0
            
            tendencias.append({
                'lista': lista,
                'progresso_inicial': progresso_inicial,
                'progresso_final': progresso_final,
                'variacao': round(variacao, 1),
                'velocidade_media': round(velocidade_media, 1),
                'tendencia': 'positiva' if variacao > 0 else 'negativa' if variacao < 0 else 'estável'
            })
    
    # Ordenar tendências por velocidade média
    tendencias.sort(key=lambda x: x['velocidade_media'], reverse=True)
    
    return {
        'turma': turma,
        'total_listas': total_listas,
        'total_alunos': total_alunos,
        'progresso_periodos': progresso_periodos,
        'tendencias': tendencias,
        'data_geracao': timezone.now()
    }

def gerar_relatorio_analise_preditiva(turma):
    """
    Gera um relatório de análise preditiva de desempenho da turma.
    Usa dados históricos para prever o desempenho futuro e identificar riscos.
    
    Args:
        turma: Instância do modelo Turma
        
    Returns:
        dict: Dicionário com as métricas do relatório
    """
    # Buscar todas as listas da turma
    listas = ListaVerificacao.objects.filter(turma=turma)
    total_listas = listas.count()
    
    # Buscar todos os alunos da turma
    alunos = turma.alunos.all()
    total_alunos = alunos.count()
    
    # Análise por aluno
    analise_alunos = []
    for aluno in alunos:
        # Buscar progressos do aluno
        progressos = ProgressoAluno.objects.filter(
            aluno=aluno,
            lista_verificacao__in=listas,
            data_atualizacao__isnull=False
        ).order_by('data_atualizacao')
        
        if progressos.exists():
            # Calcular métricas de progresso
            total_aprendizagens = sum(lista.aprendizagens.count() for lista in listas)
            aprendizagens_concluidas = progressos.filter(estado='concluido').count()
            aprendizagens_dificuldade = progressos.filter(estado='dificuldade').count()
            
            # Calcular progresso geral
            progresso_geral = (aprendizagens_concluidas / total_aprendizagens * 100) if total_aprendizagens > 0 else 0
            
            # Calcular velocidade de progresso
            primeiro_progresso = progressos.first()
            ultimo_progresso = progressos.last()
            dias_total = (ultimo_progresso.data_atualizacao - primeiro_progresso.data_atualizacao).days
            velocidade_progresso = progresso_geral / dias_total if dias_total > 0 else 0
            
            # Calcular tendência de dificuldades
            dificuldades_por_mes = {}
            for progresso in progressos.filter(estado='dificuldade'):
                mes = progresso.data_atualizacao.strftime('%Y-%m')
                if mes not in dificuldades_por_mes:
                    dificuldades_por_mes[mes] = 0
                dificuldades_por_mes[mes] += 1
            
            # Calcular tendência de dificuldades
            tendencia_dificuldades = 'estável'
            if len(dificuldades_por_mes) >= 2:
                meses = sorted(dificuldades_por_mes.keys())
                ultimo_mes = dificuldades_por_mes[meses[-1]]
                penultimo_mes = dificuldades_por_mes[meses[-2]]
                if ultimo_mes > penultimo_mes:
                    tendencia_dificuldades = 'aumentando'
                elif ultimo_mes < penultimo_mes:
                    tendencia_dificuldades = 'diminuindo'
            
            # Prever desempenho futuro
            previsao = {
                'probabilidade_conclusao': min(100, progresso_geral + (velocidade_progresso * 30)),  # Projeção para 30 dias
                'risco_dificuldade': 'baixo',
                'tempo_estimado_conclusao': None
            }
            
            # Calcular risco de dificuldade
            if tendencia_dificuldades == 'aumentando':
                previsao['risco_dificuldade'] = 'alto'
            elif tendencia_dificuldades == 'diminuindo':
                previsao['risco_dificuldade'] = 'baixo'
            else:
                previsao['risco_dificuldade'] = 'médio'
            
            # Calcular tempo estimado para conclusão
            if velocidade_progresso > 0:
                tempo_restante = (100 - progresso_geral) / velocidade_progresso
                previsao['tempo_estimado_conclusao'] = round(tempo_restante)
            
            analise_alunos.append({
                'aluno': aluno,
                'progresso_geral': round(progresso_geral, 1),
                'velocidade_progresso': round(velocidade_progresso, 2),
                'tendencia_dificuldades': tendencia_dificuldades,
                'previsao': previsao,
                'total_aprendizagens': total_aprendizagens,
                'aprendizagens_concluidas': aprendizagens_concluidas,
                'aprendizagens_dificuldade': aprendizagens_dificuldade
            })
    
    # Ordenar alunos por progresso geral
    analise_alunos.sort(key=lambda x: x['progresso_geral'], reverse=True)
    
    # Calcular métricas gerais da turma
    media_progresso = sum(a['progresso_geral'] for a in analise_alunos) / len(analise_alunos) if analise_alunos else 0
    alunos_risco_alto = len([a for a in analise_alunos if a['previsao']['risco_dificuldade'] == 'alto'])
    alunos_risco_medio = len([a for a in analise_alunos if a['previsao']['risco_dificuldade'] == 'médio'])
    alunos_risco_baixo = len([a for a in analise_alunos if a['previsao']['risco_dificuldade'] == 'baixo'])
    
    return {
        'turma': turma,
        'total_listas': total_listas,
        'total_alunos': total_alunos,
        'media_progresso': round(media_progresso, 1),
        'alunos_risco_alto': alunos_risco_alto,
        'alunos_risco_medio': alunos_risco_medio,
        'alunos_risco_baixo': alunos_risco_baixo,
        'analise_alunos': analise_alunos,
        'data_geracao': timezone.now()
    }

def gerar_relatorio_engajamento(turma):
    """
    Gera um relatório detalhado do engajamento dos alunos com as listas de verificação.
    
    Args:
        turma: Instância do modelo Turma
        
    Returns:
        dict: Dicionário com as métricas do relatório
    """
    # Buscar todas as listas da turma
    listas = ListaVerificacao.objects.filter(turma=turma)
    total_listas = listas.count()
    
    # Buscar todos os alunos da turma
    alunos = turma.alunos.all()
    total_alunos = alunos.count()
    
    # Análise por aluno
    engajamento_alunos = []
    for aluno in alunos:
        # Buscar progressos do aluno
        progressos = ProgressoAluno.objects.filter(
            aluno=aluno,
            lista_verificacao__in=listas,
            data_atualizacao__isnull=False
        ).order_by('data_atualizacao')
        
        if progressos.exists():
            # Calcular métricas de engajamento
            total_aprendizagens = sum(lista.aprendizagens.count() for lista in listas)
            aprendizagens_concluidas = progressos.filter(estado='concluido').count()
            aprendizagens_em_progresso = progressos.filter(estado='em_progresso').count()
            aprendizagens_dificuldade = progressos.filter(estado='dificuldade').count()
            
            # Calcular frequência de atualizações
            primeiro_progresso = progressos.first()
            ultimo_progresso = progressos.last()
            dias_total = (ultimo_progresso.data_atualizacao - primeiro_progresso.data_atualizacao).days
            total_atualizacoes = progressos.count()
            frequencia_atualizacoes = total_atualizacoes / dias_total if dias_total > 0 else 0
            
            # Calcular consistência (regularidade das atualizações)
            atualizacoes_por_mes = {}
            for progresso in progressos:
                mes = progresso.data_atualizacao.strftime('%Y-%m')
                if mes not in atualizacoes_por_mes:
                    atualizacoes_por_mes[mes] = 0
                atualizacoes_por_mes[mes] += 1
            
            # Calcular desvio padrão da frequência mensal
            media_mensal = sum(atualizacoes_por_mes.values()) / len(atualizacoes_por_mes) if atualizacoes_por_mes else 0
            desvio_padrao = 0
            if atualizacoes_por_mes:
                desvio_padrao = (sum((v - media_mensal) ** 2 for v in atualizacoes_por_mes.values()) / len(atualizacoes_por_mes)) ** 0.5
            
            # Calcular nível de engajamento
            nivel_engajamento = 'baixo'
            if frequencia_atualizacoes >= 0.5 and desvio_padrao <= 2:
                nivel_engajamento = 'alto'
            elif frequencia_atualizacoes >= 0.2:
                nivel_engajamento = 'médio'
            
            # Calcular progresso geral
            progresso_geral = (aprendizagens_concluidas / total_aprendizagens * 100) if total_aprendizagens > 0 else 0
            
            engajamento_alunos.append({
                'aluno': aluno,
                'progresso_geral': round(progresso_geral, 1),
                'frequencia_atualizacoes': round(frequencia_atualizacoes, 2),
                'consistencia': round(1 - (desvio_padrao / media_mensal if media_mensal > 0 else 0), 2),
                'nivel_engajamento': nivel_engajamento,
                'total_atualizacoes': total_atualizacoes,
                'aprendizagens_concluidas': aprendizagens_concluidas,
                'aprendizagens_em_progresso': aprendizagens_em_progresso,
                'aprendizagens_dificuldade': aprendizagens_dificuldade,
                'ultima_atualizacao': ultimo_progresso.data_atualizacao
            })
    
    # Ordenar alunos por nível de engajamento
    engajamento_alunos.sort(key=lambda x: (
        {'alto': 3, 'médio': 2, 'baixo': 1}[x['nivel_engajamento']],
        x['progresso_geral']
    ), reverse=True)
    
    # Calcular métricas gerais da turma
    alunos_engajamento_alto = len([a for a in engajamento_alunos if a['nivel_engajamento'] == 'alto'])
    alunos_engajamento_medio = len([a for a in engajamento_alunos if a['nivel_engajamento'] == 'médio'])
    alunos_engajamento_baixo = len([a for a in engajamento_alunos if a['nivel_engajamento'] == 'baixo'])
    
    media_frequencia = sum(a['frequencia_atualizacoes'] for a in engajamento_alunos) / len(engajamento_alunos) if engajamento_alunos else 0
    media_consistencia = sum(a['consistencia'] for a in engajamento_alunos) / len(engajamento_alunos) if engajamento_alunos else 0
    
    return {
        'turma': turma,
        'total_listas': total_listas,
        'total_alunos': total_alunos,
        'alunos_engajamento_alto': alunos_engajamento_alto,
        'alunos_engajamento_medio': alunos_engajamento_medio,
        'alunos_engajamento_baixo': alunos_engajamento_baixo,
        'media_frequencia': round(media_frequencia, 2),
        'media_consistencia': round(media_consistencia, 2),
        'engajamento_alunos': engajamento_alunos,
        'data_geracao': timezone.now()
    }

def gerar_relatorio_cooperacao(turma):
    """
    Gera um relatório de cooperação e partilha de experiências entre turmas.
    
    Args:
        turma: Instância do modelo Turma
        
    Returns:
        dict: Dicionário com as métricas do relatório
    """
    # Buscar todas as listas da turma
    listas = ListaVerificacao.objects.filter(turma=turma)
    total_listas = listas.count()
    
    # Buscar todos os alunos da turma
    alunos = turma.alunos.all()
    total_alunos = alunos.count()
    
    # Análise de práticas cooperativas
    praticas_cooperativas = []
    
    # 1. Análise de grupos de estudo
    grupos_estudo = []
    for lista in listas:
        # Identificar alunos que trabalham juntos frequentemente
        progressos = ProgressoAluno.objects.filter(
            lista_verificacao=lista,
            data_atualizacao__isnull=False
        ).order_by('data_atualizacao')
        
        # Agrupar alunos por proximidade de progresso
        grupos = {}
        for progresso in progressos:
            progresso_percentual = (progresso.aprendizagens_concluidas / lista.aprendizagens.count() * 100) if lista.aprendizagens.exists() else 0
            grupo_chave = round(progresso_percentual / 20) * 20  # Agrupa em faixas de 20%
            
            if grupo_chave not in grupos:
                grupos[grupo_chave] = []
            grupos[grupo_chave].append(progresso.aluno)
        
        # Identificar grupos de estudo naturais
        for grupo_chave, alunos_grupo in grupos.items():
            if len(alunos_grupo) >= 2:
                grupos_estudo.append({
                    'lista': lista,
                    'alunos': alunos_grupo,
                    'faixa_progresso': f"{grupo_chave}% - {grupo_chave + 20}%"
                })
    
    # 2. Análise de partilha de experiências
    experiencias_compartilhadas = []
    for lista in listas:
        # Identificar alunos que compartilham estratégias de superação de dificuldades
        dificuldades = ProgressoAluno.objects.filter(
            lista_verificacao=lista,
            estado='dificuldade',
            data_atualizacao__isnull=False
        )
        
        for dificuldade in dificuldades:
            # Verificar se outros alunos superaram a mesma dificuldade
            superacoes = ProgressoAluno.objects.filter(
                lista_verificacao=lista,
                aprendizagem=dificuldade.aprendizagem,
                estado='concluido',
                data_atualizacao__gt=dificuldade.data_atualizacao
            )
            
            if superacoes.exists():
                experiencias_compartilhadas.append({
                    'lista': lista,
                    'aprendizagem': dificuldade.aprendizagem,
                    'aluno_dificuldade': dificuldade.aluno,
                    'alunos_superacao': [p.aluno for p in superacoes]
                })
    
    # 3. Análise de projetos colaborativos
    projetos_colaborativos = []
    for lista in listas:
        # Identificar aprendizagens que requerem trabalho em grupo
        aprendizagens_grupo = lista.aprendizagens.filter(
            Q(descricao__icontains='grupo') |
            Q(descricao__icontains='equipe') |
            Q(descricao__icontains='colaborativo')
        )
        
        for aprendizagem in aprendizagens_grupo:
            # Verificar progresso conjunto
            progressos = ProgressoAluno.objects.filter(
                lista_verificacao=lista,
                aprendizagem=aprendizagem,
                data_atualizacao__isnull=False
            )
            
            if progressos.exists():
                projetos_colaborativos.append({
                    'lista': lista,
                    'aprendizagem': aprendizagem,
                    'alunos': [p.aluno for p in progressos],
                    'progresso_conjunto': sum(1 for p in progressos if p.estado == 'concluido') / len(progressos) * 100
                })
    
    # 4. Métricas de cooperação
    total_grupos_estudo = len(grupos_estudo)
    total_experiencias_compartilhadas = len(experiencias_compartilhadas)
    total_projetos_colaborativos = len(projetos_colaborativos)
    
    # Calcular percentual de alunos envolvidos em práticas cooperativas
    alunos_cooperativos = set()
    for grupo in grupos_estudo:
        alunos_cooperativos.update(grupo['alunos'])
    for exp in experiencias_compartilhadas:
        alunos_cooperativos.add(exp['aluno_dificuldade'])
        alunos_cooperativos.update(exp['alunos_superacao'])
    for projeto in projetos_colaborativos:
        alunos_cooperativos.update(projeto['alunos'])
    
    percentual_cooperacao = (len(alunos_cooperativos) / total_alunos * 100) if total_alunos > 0 else 0
    
    return {
        'turma': turma,
        'total_listas': total_listas,
        'total_alunos': total_alunos,
        'grupos_estudo': grupos_estudo,
        'experiencias_compartilhadas': experiencias_compartilhadas,
        'projetos_colaborativos': projetos_colaborativos,
        'total_grupos_estudo': total_grupos_estudo,
        'total_experiencias_compartilhadas': total_experiencias_compartilhadas,
        'total_projetos_colaborativos': total_projetos_colaborativos,
        'percentual_cooperacao': round(percentual_cooperacao, 1),
        'data_geracao': timezone.now()
    } 