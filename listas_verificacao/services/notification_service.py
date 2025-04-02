from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from listas_verificacao.models import Notificacao, ListaVerificacao, ProgressoAluno, Duvida
from listas_verificacao.email_service import (
    enviar_email_prazo_proximo, 
    enviar_email_conquista,
    enviar_email_resposta_duvida
)

def verificar_prazos_proximos():
    """
    Verifica listas de verificação com prazos próximos e cria notificações.
    """
    # Define o que é considerado "próximo" (3 dias)
    prazo_proximo = timezone.now() + timedelta(days=3)
    
    # Busca listas com prazo próximo
    listas_proximas = ListaVerificacao.objects.filter(
        data_limite__lte=prazo_proximo,
        data_limite__gt=timezone.now()
    )
    
    for lista in listas_proximas:
        # Busca alunos que ainda não completaram a lista
        alunos_incompletos = ProgressoAluno.objects.filter(
            lista_verificacao=lista,
            estado__in=['nao_iniciado', 'em_andamento']
        ).select_related('aluno')
        
        for progresso in alunos_incompletos:
            # Verifica se já existe notificação recente
            notificacao_existente = Notificacao.objects.filter(
                destinatario=progresso.aluno,
                tipo='prazo_proximo',
                lista_verificacao=lista,
                data_criacao__gte=timezone.now() - timedelta(days=1)
            ).exists()
            
            if not notificacao_existente:
                # Cria nova notificação
                notificacao = Notificacao.objects.create(
                    destinatario=progresso.aluno,
                    tipo='prazo_proximo',
                    titulo=f'Prazo Próximo: {lista.titulo}',
                    mensagem=f'O prazo para completar a lista de verificação "{lista.titulo}" está próximo.',
                    prioridade='alta',
                    lista_verificacao=lista
                )
                
                # Envia email se configurado
                enviar_email_prazo_proximo(notificacao)

def verificar_conquistas():
    """
    Verifica progressos dos alunos e cria notificações de conquistas.
    """
    # Busca progressos recentemente completados
    progressos_completos = ProgressoAluno.objects.filter(
        estado='concluido',
        data_atualizacao__gte=timezone.now() - timedelta(days=1)
    ).select_related('aluno', 'lista_verificacao', 'aprendizagem')
    
    for progresso in progressos_completos:
        # Verifica se já existe notificação de conquista
        notificacao_existente = Notificacao.objects.filter(
            destinatario=progresso.aluno,
            tipo='conquista',
            progresso=progresso,
            data_criacao__gte=timezone.now() - timedelta(days=1)
        ).exists()
        
        if not notificacao_existente:
            # Cria nova notificação
            notificacao = Notificacao.objects.create(
                destinatario=progresso.aluno,
                tipo='conquista',
                titulo=f'Conquista Alcançada: {progresso.aprendizagem.codigo}',
                mensagem=f'Parabéns! Você completou a aprendizagem "{progresso.aprendizagem.descricao}" com sucesso!',
                prioridade='media',
                lista_verificacao=progresso.lista_verificacao,
                aprendizagem=progresso.aprendizagem,
                progresso=progresso
            )
            
            # Envia email se configurado
            enviar_email_conquista(notificacao)
            
            # Notifica o professor sobre a conquista do aluno
            if progresso.lista_verificacao.professor:
                notificacao_professor = Notificacao.objects.create(
                    destinatario=progresso.lista_verificacao.professor,
                    tipo='conquista',
                    titulo=f'Conquista do Aluno: {progresso.aluno.get_full_name()}',
                    mensagem=f'O aluno {progresso.aluno.get_full_name()} completou a aprendizagem "{progresso.aprendizagem.descricao}" com sucesso!',
                    prioridade='baixa',
                    lista_verificacao=progresso.lista_verificacao,
                    aprendizagem=progresso.aprendizagem,
                    progresso=progresso
                )
                
                # Envia email para o professor se configurado
                enviar_email_conquista(notificacao_professor)

def verificar_respostas_duvidas():
    """
    Verifica dúvidas recentemente respondidas e cria notificações.
    """
    # Busca dúvidas respondidas nas últimas 24 horas
    duvidas_respondidas = Duvida.objects.filter(
        data_resposta__gte=timezone.now() - timedelta(days=1),
        data_resposta__isnull=False
    ).select_related('aluno', 'aprendizagem', 'lista_verificacao', 'resposta_por')
    
    for duvida in duvidas_respondidas:
        # Verifica se já existe notificação de resposta
        notificacao_existente = Notificacao.objects.filter(
            destinatario=duvida.aluno,
            tipo='resposta_duvida',
            data_criacao__gte=timezone.now() - timedelta(days=1)
        ).exists()
        
        if not notificacao_existente:
            # Cria nova notificação
            notificacao = Notificacao.objects.create(
                destinatario=duvida.aluno,
                remetente=duvida.resposta_por,
                tipo='resposta_duvida',
                titulo=f'Resposta à sua dúvida sobre {duvida.aprendizagem.codigo}',
                mensagem=f'Sua dúvida sobre "{duvida.aprendizagem.descricao}" foi respondida: {duvida.resposta}',
                prioridade='media',
                lista_verificacao=duvida.lista_verificacao,
                aprendizagem=duvida.aprendizagem
            )
            
            # Envia email se configurado
            enviar_email_resposta_duvida(notificacao) 