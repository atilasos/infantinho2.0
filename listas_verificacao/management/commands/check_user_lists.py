from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from listas_verificacao.models import ListaVerificacao, ProgressoAluno
from django.db.models import Q

User = get_user_model()

class Command(BaseCommand):
    help = 'Check user lists and permissions'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to check')

    def handle(self, *args, **options):
        username = options['username']
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'Checking user: {user.username}')
            self.stdout.write(f'Is student: {getattr(user, "is_student", False)}')
            
            # Check lists assigned to user
            listas = ListaVerificacao.objects.filter(
                Q(turma__alunos=user) | 
                Q(turma__isnull=True)
            ).distinct()
            
            self.stdout.write(f'\nTotal lists found: {listas.count()}')
            
            for lista in listas:
                self.stdout.write(f'\nLista: {lista.titulo}')
                self.stdout.write(f'Turma: {lista.turma}')
                self.stdout.write(f'Disciplina: {lista.disciplina}')
                
                # Check progress
                progressos = ProgressoAluno.objects.filter(
                    aluno=user,
                    lista_verificacao=lista
                )
                self.stdout.write(f'Progress records: {progressos.count()}')
                
                # Check if user is in the class
                if lista.turma:
                    self.stdout.write(f'User in class: {user in lista.turma.alunos.all()}')
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {username} not found')) 