from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp

class Command(BaseCommand):
    help = 'Remove apps sociais vazias ou inválidas'

    def handle(self, *args, **options):
        self.stdout.write('=== Removendo Apps Sociais Vazias ===')
        
        # Listar todas as apps antes da remoção
        apps = SocialApp.objects.all()
        self.stdout.write(f'\nTotal de apps antes da remoção: {apps.count()}')
        for app in apps:
            self.stdout.write(f'\nProvedor: {app.provider}')
            self.stdout.write(f'Nome: {app.name}')
            self.stdout.write(f'Client ID: {app.client_id}')
            self.stdout.write(f'Secret: {"*" * len(app.secret) if app.secret else "Vazio"}')
        
        # Remover apps vazias ou inválidas
        empty_apps = SocialApp.objects.filter(
            name__isnull=True,
            provider__isnull=True,
            client_id__isnull=True
        )
        
        count = empty_apps.count()
        empty_apps.delete()
        
        self.stdout.write(f'\nRemovidas {count} apps vazias')
        
        # Listar apps restantes
        remaining_apps = SocialApp.objects.all()
        self.stdout.write(f'\nApps restantes: {remaining_apps.count()}')
        for app in remaining_apps:
            self.stdout.write(f'\nProvedor: {app.provider}')
            self.stdout.write(f'Nome: {app.name}')
            self.stdout.write(f'Client ID: {app.client_id}')
            self.stdout.write(f'Secret: {"*" * len(app.secret) if app.secret else "Vazio"}') 