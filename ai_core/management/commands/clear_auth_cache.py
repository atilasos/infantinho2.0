from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Limpa o cache de autenticação e sessões'

    def handle(self, *args, **options):
        self.stdout.write('=== Limpando Cache de Autenticação ===')
        
        # Limpar cache do Django
        cache.clear()
        self.stdout.write('Cache do Django limpo')
        
        # Limpar todas as sessões
        Session.objects.all().delete()
        self.stdout.write('Todas as sessões foram removidas')
        
        # Verificar usuários ativos
        User = get_user_model()
        active_users = User.objects.filter(is_active=True)
        self.stdout.write(f'\nUsuários ativos: {active_users.count()}')
        for user in active_users:
            self.stdout.write(f'- {user.email}') 