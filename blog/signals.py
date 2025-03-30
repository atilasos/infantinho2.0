from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth.models import Group

User = get_user_model()

@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    """Atualiza o perfil do usuário quando o usuário é salvo."""
    if created:
        # Adiciona o usuário ao grupo 'guest' por padrão
        guest_group, _ = Group.objects.get_or_create(name='guest')
        instance.groups.add(guest_group) 