from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
import os

class Command(BaseCommand):
    help = 'Reseta completamente a configuração do provedor Microsoft'

    def handle(self, *args, **options):
        self.stdout.write('=== Resetando Provedor Microsoft ===')
        
        # Obter o site atual
        try:
            site = Site.objects.get(id=1)
            self.stdout.write(f'\nSite atual: {site.domain} (ID: {site.id})')
        except Site.DoesNotExist:
            self.stdout.write('ERRO: Site não encontrado!')
            return
        
        # Remover todas as apps Microsoft existentes
        microsoft_apps = SocialApp.objects.filter(provider='microsoft')
        count = microsoft_apps.count()
        microsoft_apps.delete()
        self.stdout.write(f'\nRemovidas {count} apps Microsoft existentes')
        
        # Criar nova app Microsoft
        try:
            client_id = os.environ.get('MICROSOFT_CLIENT_ID')
            secret = os.environ.get('MICROSOFT_SECRET')
            
            if not client_id or not secret:
                self.stdout.write('ERRO: Variáveis de ambiente MICROSOFT_CLIENT_ID e/ou MICROSOFT_SECRET não encontradas!')
                return
            
            app = SocialApp.objects.create(
                provider='microsoft',
                name='Microsoft',
                client_id=client_id,
                secret=secret,
                settings={
                    'scope': 'openid profile email',
                    'auth_params': {
                        'prompt': 'select_account'
                    }
                }
            )
            
            # Associar ao site
            app.sites.add(site)
            
            self.stdout.write('\nNova app Microsoft criada com sucesso!')
            self.stdout.write(f'ID: {app.id}')
            self.stdout.write(f'Nome: {app.name}')
            self.stdout.write(f'Client ID: {app.client_id}')
            self.stdout.write(f'Secret: {"*" * len(app.secret)}')
            self.stdout.write('\nSites associados:')
            for site in app.sites.all():
                self.stdout.write(f'- {site.domain} (ID: {site.id})')
                
        except Exception as e:
            self.stdout.write(f'ERRO ao criar nova app: {str(e)}') 