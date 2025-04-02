from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import DashboardUsuario, PreferenciaUsuario

@receiver(post_save, sender=User)
def criar_dashboard_usuario(sender, instance, created, **kwargs):
    """Cria um dashboard para o usuário quando ele é criado."""
    if created:
        DashboardUsuario.objects.create(usuario=instance)

@receiver(post_save, sender=User)
def criar_preferencias_usuario(sender, instance, created, **kwargs):
    """Cria preferências padrão para o usuário quando ele é criado."""
    if created:
        PreferenciaUsuario.objects.create(usuario=instance) 