from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

class Command(BaseCommand):
    help = 'Lista detalhadamente todas as apps sociais e suas configurações'

    def handle(self, *args, **options):
        self.stdout.write('=== Detalhes das Apps Sociais ===')
        
        # Listar todos os sites
        self.stdout.write('\nSites disponíveis:')
        for site in Site.objects.all():
            self.stdout.write(f'- {site.domain} (ID: {site.id})')
        
        # Listar todas as apps sociais com detalhes
        apps = SocialApp.objects.all()
        self.stdout.write(f'\nTotal de apps sociais: {apps.count()}')
        
        for app in apps:
            self.stdout.write('\n' + '='*50)
            self.stdout.write(f'ID: {app.id}')
            self.stdout.write(f'Provedor: {app.provider}')
            self.stdout.write(f'Nome: {app.name}')
            self.stdout.write(f'Client ID: {app.client_id}')
            self.stdout.write(f'Secret: {"*" * len(app.secret) if app.secret else "Vazio"}')
            self.stdout.write(f'Configurações: {app.settings}')
            self.stdout.write('\nSites associados:')
            for site in app.sites.all():
                self.stdout.write(f'- {site.domain} (ID: {site.id})')
            
            # Verificar se há apps duplicadas com o mesmo provedor
            duplicates = SocialApp.objects.filter(provider=app.provider).exclude(id=app.id)
            if duplicates.exists():
                self.stdout.write('\nAVISO: Encontradas apps duplicadas com o mesmo provedor!')
                for dup in duplicates:
                    self.stdout.write(f'- ID: {dup.id}, Nome: {dup.name}') 