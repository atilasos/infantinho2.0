from django.core.management.base import BaseCommand
from listas_verificacao.services.notification_service import (
    verificar_prazos_proximos,
    verificar_conquistas,
    verificar_respostas_duvidas
)

class Command(BaseCommand):
    help = 'Verifica e cria notificações de prazos próximos, conquistas e respostas às dúvidas'

    def handle(self, *args, **options):
        self.stdout.write('Verificando prazos próximos...')
        verificar_prazos_proximos()
        self.stdout.write(self.style.SUCCESS('Verificação de prazos concluída'))

        self.stdout.write('Verificando conquistas...')
        verificar_conquistas()
        self.stdout.write(self.style.SUCCESS('Verificação de conquistas concluída'))

        self.stdout.write('Verificando respostas às dúvidas...')
        verificar_respostas_duvidas()
        self.stdout.write(self.style.SUCCESS('Verificação de respostas às dúvidas concluída')) 