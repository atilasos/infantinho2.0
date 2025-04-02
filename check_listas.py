import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'infantinho.settings')
django.setup()

from listas_verificacao.models import ListaVerificacao, Turma

print('Listas de verificação:', ListaVerificacao.objects.count())
print('Listas com turma:', ListaVerificacao.objects.exclude(turma__isnull=True).count())
print('Turmas:', Turma.objects.count())
print('Listas por turma:')
for turma in Turma.objects.all():
    print(f'- {turma.nome}: {ListaVerificacao.objects.filter(turma=turma).count()}') 