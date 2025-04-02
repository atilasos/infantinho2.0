from django import template
from listas_verificacao.models import Notificacao

register = template.Library()

@register.filter
def unread_notifications_count(user):
    """Retorna o número de notificações não lidas do usuário."""
    if not user.is_authenticated:
        return 0
    return Notificacao.objects.filter(destinatario=user, lida=False).count() 