from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.conf import settings

class Command(BaseCommand):
    help = 'Verifica e corrige as configurações do provedor Microsoft'

    def handle(self, *args, **options):
        self.stdout.write('=== Verificando Configurações do Provedor Microsoft ===')
        
        # Obter o site atual
        try:
            site = Site.objects.get(id=1)
            self.stdout.write(f'\nSite atual: {site.domain} (ID: {site.id})')
        except Site.DoesNotExist:
            self.stdout.write('ERRO: Site não encontrado!')
            return
        
        # Listar todas as apps Microsoft
        microsoft_apps = SocialApp.objects.filter(provider='microsoft')
        self.stdout.write(f'\nTotal de apps Microsoft encontradas: {microsoft_apps.count()}')
        
        if microsoft_apps.count() > 1:
            self.stdout.write('\nAVISO: Múltiplas apps Microsoft encontradas!')
            self.stdout.write('Removendo apps duplicadas...')
            
            # Manter apenas a primeira app e remover as outras
            first_app = microsoft_apps.first()
            microsoft_apps.exclude(id=first_app.id).delete()
            
            self.stdout.write(f'\nApps removidas: {microsoft_apps.count() - 1}')
            self.stdout.write(f'App mantida: ID {first_app.id}')
        
        # Verificar se a app está associada ao site correto
        for app in microsoft_apps:
            self.stdout.write('\nDetalhes da app Microsoft:')
            self.stdout.write(f'ID: {app.id}')
            self.stdout.write(f'Nome: {app.name}')
            self.stdout.write(f'Client ID: {app.client_id}')
            self.stdout.write(f'Secret: {"*" * len(app.secret) if app.secret else "Vazio"}')
            
            # Verificar sites associados
            sites = app.sites.all()
            self.stdout.write('\nSites associados:')
            for site in sites:
                self.stdout.write(f'- {site.domain} (ID: {site.id})')
            
            # Se a app não estiver associada ao site atual, associar
            if site not in sites:
                self.stdout.write('\nAssociando app ao site atual...')
                app.sites.add(site)
                self.stdout.write('App associada com sucesso!')
            
            # Verificar configurações
            if not app.settings:
                self.stdout.write('\nConfigurando parâmetros padrão...')
                app.settings = {
                    'scope': 'openid profile email',
                    'auth_params': {
                        'prompt': 'select_account'
                    }
                }
                app.save()
                self.stdout.write('Configurações atualizadas!') 