from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse

def enviar_email_notificacao(notificacao):
    """
    Envia uma notificação por email.
    
    Args:
        notificacao: Instância do modelo Notificacao
    """
    # Contexto para o template
    context = {
        'notificacao': notificacao,
        'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
    }
    
    # Renderiza o template HTML
    html_content = render_to_string(
        f'listas_verificacao/notificacoes/email/{notificacao.tipo}.html',
        context
    )
    
    # Versão em texto plano
    text_content = strip_tags(html_content)
    
    # Cria a mensagem
    msg = EmailMultiAlternatives(
        subject=notificacao.titulo,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[notificacao.destinatario.email]
    )
    
    # Adiciona o conteúdo HTML
    msg.attach_alternative(html_content, "text/html")
    
    # Envia o email
    msg.send()

def enviar_email_baixo_progresso(notificacao):
    """
    Envia um email específico para notificação de baixo progresso.
    """
    context = {
        'notificacao': notificacao,
        'aluno': notificacao.destinatario.get_full_name() or notificacao.destinatario.username,
        'aprendizagem': notificacao.aprendizagem,
        'progresso': notificacao.progresso,
        'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
    }
    
    html_content = render_to_string(
        'listas_verificacao/notificacoes/email/baixo_progresso.html',
        context
    )
    
    text_content = strip_tags(html_content)
    
    msg = EmailMultiAlternatives(
        subject=f'Baixo Progresso - {notificacao.aprendizagem.codigo}',
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[notificacao.destinatario.email]
    )
    
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def enviar_email_confirmacao_pendente(notificacao):
    """
    Envia um email específico para notificação de confirmação pendente.
    """
    context = {
        'notificacao': notificacao,
        'aprendizagem': notificacao.aprendizagem,
        'progresso': notificacao.progresso,
        'aluno': notificacao.progresso.aluno.get_full_name() or notificacao.progresso.aluno.username,
        'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
    }
    
    html_content = render_to_string(
        'listas_verificacao/notificacoes/email/confirmacao_pendente.html',
        context
    )
    
    text_content = strip_tags(html_content)
    
    msg = EmailMultiAlternatives(
        subject=f'Confirmação Pendente - {notificacao.aprendizagem.codigo}',
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[notificacao.destinatario.email]
    )
    
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def enviar_email_nova_duvida(notificacao):
    """
    Envia um email específico para notificação de nova dúvida.
    """
    context = {
        'notificacao': notificacao,
        'remetente': notificacao.remetente.get_full_name() or notificacao.remetente.username,
        'aprendizagem': notificacao.aprendizagem,
        'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
    }
    
    html_content = render_to_string(
        'listas_verificacao/notificacoes/email/nova_duvida.html',
        context
    )
    
    text_content = strip_tags(html_content)
    
    msg = EmailMultiAlternatives(
        subject=f'Nova Dúvida - {notificacao.aprendizagem.codigo}',
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[notificacao.destinatario.email]
    )
    
    msg.attach_alternative(html_content, "text/html")
    msg.send() 