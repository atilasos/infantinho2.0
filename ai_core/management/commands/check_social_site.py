from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings

class Command(BaseCommand):
    help = 'Verifica e corrige configurações do site para autenticação social'

    def handle(self, *args, **options):
        self.stdout.write('=== Verificando Configurações do Site ===')
        
        # Verificar se o site ID nas configurações corresponde ao site no banco
        configured_site_id = getattr(settings, 'SITE_ID', 1)
        self.stdout.write(f'\nSite ID configurado: {configured_site_id}')
        
        try:
            site = Site.objects.get(id=configured_site_id)
            self.stdout.write(f'Site encontrado: {site.domain}')
            
            # Verificar apps sociais associadas ao site
            apps = SocialApp.objects.filter(sites=site)
            self.stdout.write(f'\nApps sociais associadas ao site: {apps.count()}')
            
            for app in apps:
                self.stdout.write(f'\nProvedor: {app.provider}')
                self.stdout.write(f'Nome: {app.name}')
                self.stdout.write(f'Client ID: {app.client_id}')
                
                # Verificar se há outras apps com o mesmo provedor
                duplicate_apps = SocialApp.objects.filter(provider=app.provider).exclude(id=app.id)
                if duplicate_apps.exists():
                    self.stdout.write('AVISO: Encontradas outras apps com o mesmo provedor!')
                    for dup in duplicate_apps:
                        self.stdout.write(f'- ID: {dup.id}, Nome: {dup.name}')
                        
        except Site.DoesNotExist:
            self.stdout.write('ERRO: Site configurado não encontrado no banco de dados!')
            self.stdout.write('Criando novo site...')
            site = Site.objects.create(
                domain='localhost:8000',
                name='Infantinho 2.0'
            )
            self.stdout.write(f'Site criado com ID: {site.id}')
            
            # Associar apps sociais ao novo site
            apps = SocialApp.objects.all()
            for app in apps:
                app.sites.add(site)
                self.stdout.write(f'App {app.provider} associada ao site') 