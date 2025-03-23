from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.db import transaction

class Command(BaseCommand):
    help = 'Verifica e corrige problemas com apps sociais'

    def handle(self, *args, **options):
        self.stdout.write('=== Verificando e Corrigindo Apps Sociais ===')
        
        # Obter o site atual
        site = Site.objects.get(id=1)
        self.stdout.write(f'\nSite atual: {site.domain}')
        
        # Listar todas as apps sociais
        apps = SocialApp.objects.all()
        self.stdout.write(f'\nTotal de apps sociais: {apps.count()}')
        
        # Verificar apps por provedor
        providers = {}
        for app in apps:
            if app.provider not in providers:
                providers[app.provider] = []
            providers[app.provider].append(app)
        
        # Corrigir apps duplicadas
        with transaction.atomic():
            for provider, provider_apps in providers.items():
                if len(provider_apps) > 1:
                    self.stdout.write(f'\nEncontradas múltiplas apps para o provedor {provider}:')
                    # Manter a primeira app e remover as outras
                    keep_app = provider_apps[0]
                    for app in provider_apps[1:]:
                        self.stdout.write(f'Removendo app duplicada: {app.name} (ID: {app.id})')
                        app.delete()
                    
                    # Garantir que a app restante está associada ao site
                    if site not in keep_app.sites.all():
                        keep_app.sites.add(site)
                        self.stdout.write(f'Associando app {keep_app.name} ao site {site.domain}')
                else:
                    app = provider_apps[0]
                    if site not in app.sites.all():
                        app.sites.add(site)
                        self.stdout.write(f'Associando app {app.name} ao site {site.domain}')
        
        self.stdout.write('\n=== Verificação Final ===')
        for provider, apps in providers.items():
            self.stdout.write(f'\nProvedor: {provider}')
            for app in apps:
                self.stdout.write(f'- Nome: {app.name}')
                self.stdout.write(f'  ID: {app.id}')
                self.stdout.write(f'  Client ID: {app.client_id}')
                self.stdout.write(f'  Sites: {", ".join(site.domain for site in app.sites.all())}') 