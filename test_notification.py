import os
import django

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'infantinho.settings')
django.setup()

from django.contrib.auth import get_user_model
from listas_verificacao.models import Notificacao, AprendizagemEssencial, ProgressoAluno, ListaVerificacao, Disciplina, Domínio, Subdomínio

def criar_dados_teste():
    # Criar um usuário de teste (se não existir)
    User = get_user_model()
    professor, created = User.objects.get_or_create(
        username='professor_teste',
        email='professor@teste.com',
        defaults={'is_staff': True}
    )
    print(f"Professor {'criado' if created else 'já existe'}: {professor.email}")
    
    aluno, created = User.objects.get_or_create(
        username='aluno_teste',
        email='aluno@teste.com'
    )
    print(f"Aluno {'criado' if created else 'já existe'}: {aluno.email}")

    # Criar uma disciplina de teste
    disciplina, created = Disciplina.objects.get_or_create(
        nome='Matemática',
        codigo='MAT',
        defaults={'descricao': 'Matemática'}
    )
    print(f"Disciplina {'criada' if created else 'já existe'}: {disciplina.nome}")

    # Criar um domínio de teste
    dominio, created = Domínio.objects.get_or_create(
        nome='Números e Operações',
        codigo='NO',
        disciplina=disciplina,
        defaults={'descricao': 'Números e Operações'}
    )
    print(f"Domínio {'criado' if created else 'já existe'}: {dominio.nome}")

    # Criar um subdomínio de teste
    subdominio, created = Subdomínio.objects.get_or_create(
        nome='Números Naturais',
        codigo='NN',
        dominio=dominio,
        defaults={'descricao': 'Números Naturais'}
    )
    print(f"Subdomínio {'criado' if created else 'já existe'}: {subdominio.nome}")

    # Criar uma aprendizagem essencial de teste
    aprendizagem, created = AprendizagemEssencial.objects.get_or_create(
        codigo='MAT6NO1',
        descricao='Compreender e usar números naturais em diferentes contextos',
        disciplina=disciplina,
        dominio=dominio,
        subdominio=subdominio,
        ano_escolar=6
    )
    print(f"Aprendizagem {'criada' if created else 'já existe'}: {aprendizagem.codigo}")

    # Criar uma lista de verificação de teste
    lista, created = ListaVerificacao.objects.get_or_create(
        titulo='Lista de Verificação - Matemática 6º Ano',
        descricao='Lista de verificação para Matemática do 6º ano',
        disciplina=disciplina,
        ano_escolar=6,
        defaults={'turma': None}
    )
    print(f"Lista {'criada' if created else 'já existe'}: {lista.titulo}")

    # Criar um progresso de teste
    progresso, created = ProgressoAluno.objects.get_or_create(
        aluno=aluno,
        lista_verificacao=lista,
        aprendizagem=aprendizagem,
        defaults={
            'estado': 'dificuldade',
            'observacoes': 'Estou tendo dificuldades com números naturais'
        }
    )
    print(f"Progresso {'criado' if created else 'já existe'}: {progresso.estado}")

    # Criar uma notificação de teste
    notificacao = Notificacao.objects.create(
        destinatario=professor,
        remetente=aluno,
        tipo='baixo_progresso',
        titulo='Aluno com Baixo Progresso',
        mensagem='O aluno está tendo dificuldades com números naturais',
        prioridade='alta',
        lista_verificacao=lista,
        aprendizagem=aprendizagem,
        progresso=progresso
    )
    print(f"Notificação criada com ID: {notificacao.id}")
    print("Email deve ter sido enviado para o console")

if __name__ == '__main__':
    criar_dados_teste() 