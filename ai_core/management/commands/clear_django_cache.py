from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.contrib.sessions.models import Session

class Command(BaseCommand):
    help = 'Limpa o cache do Django e todas as sessões'

    def handle(self, *args, **options):
        self.stdout.write('=== Limpando Cache e Sessões ===')
        
        # Limpar cache
        cache.clear()
        self.stdout.write('Cache limpo com sucesso!')
        
        # Limpar sessões
        count = Session.objects.count()
        Session.objects.all().delete()
        self.stdout.write(f'{count} sessões removidas!')
        
        self.stdout.write('\nOperação concluída com sucesso!') 