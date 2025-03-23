from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

class Command(BaseCommand):
    help = 'Lista todas as configurações de provedores sociais'

    def handle(self, *args, **options):
        self.stdout.write('=== Configurações de Provedores Sociais ===')
        
        # Listar todos os sites
        self.stdout.write('\nSites disponíveis:')
        for site in Site.objects.all():
            self.stdout.write(f'- {site.domain} (ID: {site.id})')
        
        # Listar todas as apps sociais
        self.stdout.write('\nApps sociais:')
        for app in SocialApp.objects.all():
            self.stdout.write(f'\nProvedor: {app.provider}')
            self.stdout.write(f'Nome: {app.name}')
            self.stdout.write(f'Client ID: {app.client_id}')
            self.stdout.write(f'Sites associados:')
            for site in app.sites.all():
                self.stdout.write(f'  - {site.domain} (ID: {site.id})') 