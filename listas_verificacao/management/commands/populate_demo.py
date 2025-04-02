from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from listas_verificacao.models import (
    Turma, Disciplina, Domínio, AprendizagemEssencial, ListaVerificacao,
    ProgressoAluno, Duvida, RespostaDuvida, DiarioAprendizagem,
    EntradaDiario, MetaAprendizagem, ConquistaColetiva
)
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Popula o sistema com dados de demonstração'

    def __init__(self):
        super().__init__()
        self.teachers = []
        self.students = []
        self.turmas = []
        self.disciplinas = {}
        self.dominios = {}
        self.aprendizagens = {}

    def handle(self, *args, **options):
        self.stdout.write('Iniciando população do sistema com dados de demonstração...')
        
        self.criar_usuarios_demo()
        self.criar_turmas_demo()
        self.criar_disciplinas_e_dominios()
        self.criar_aprendizagens_essenciais()
        self.criar_listas_verificacao()
        self.criar_duvidas_e_respostas()
        self.criar_diarios_e_entradas()
        self.criar_metas_e_conquistas()
        
        self.stdout.write(self.style.SUCCESS('Sistema populado com sucesso!'))

    def criar_usuarios_demo(self):
        # Criar grupo de professores se não existir
        teacher_group, _ = Group.objects.get_or_create(name='teacher')
        
        # Criar professores demo
        for teacher_data in [
            {'username': 'prof.portugues', 'first_name': 'Professor', 'last_name': 'Português'},
            {'username': 'prof.matematica', 'first_name': 'Professor', 'last_name': 'Matemática'}
        ]:
            teacher, created = User.objects.get_or_create(
                username=teacher_data['username'],
                defaults={
                    'first_name': teacher_data['first_name'],
                    'last_name': teacher_data['last_name'],
                    'email': f"{teacher_data['username']}@demo.com"
                }
            )
            if created:
                teacher.set_password('Demo@123')
                teacher.save()
                teacher.groups.add(teacher_group)
                self.stdout.write(f'Professor criado: {teacher.username}')
            self.teachers.append(teacher)

        # Criar alunos demo
        for i in range(1, 6):
            student, created = User.objects.get_or_create(
                username=f'aluno{i}',
                defaults={
                    'first_name': f'Aluno {i}',
                    'last_name': 'Demo',
                    'email': f'aluno{i}@demo.com'
                }
            )
            if created:
                student.set_password('Demo@123')
                student.save()
                self.stdout.write(f'Aluno criado: {student.username}')
            self.students.append(student)

    def criar_turmas_demo(self):
        # Criar turmas demo
        for i, (teacher, name) in enumerate([
            (self.teachers[0], 'Turma 6ºA - Português'),
            (self.teachers[1], 'Turma 6ºB - Matemática')
        ]):
            turma, created = Turma.objects.get_or_create(
                nome=name,
                defaults={
                    'professor': teacher,
                    'ano_letivo': '2024/2025',
                    'ano_escolar': 6
                }
            )
            if created:
                # Adicionar alunos à turma
                for student in self.students:
                    turma.alunos.add(student)
                self.stdout.write(f'Turma criada: {turma.nome}')
            self.turmas.append(turma)

    def criar_disciplinas_e_dominios(self):
        # Criar disciplinas
        for disc_data in [
            {
                'nome': 'Português',
                'codigo': 'PORT',
                'dominios': [
                    {'nome': 'Oralidade', 'codigo': 'OR'},
                    {'nome': 'Leitura', 'codigo': 'LE'},
                    {'nome': 'Escrita', 'codigo': 'ES'},
                    {'nome': 'Gramática', 'codigo': 'GR'}
                ]
            },
            {
                'nome': 'Matemática',
                'codigo': 'MAT',
                'dominios': [
                    {'nome': 'Números', 'codigo': 'NUM'},
                    {'nome': 'Geometria', 'codigo': 'GEO'},
                    {'nome': 'Álgebra', 'codigo': 'ALG'},
                    {'nome': 'Dados e Probabilidades', 'codigo': 'DAT'}
                ]
            }
        ]:
            disciplina, created = Disciplina.objects.get_or_create(
                codigo=disc_data['codigo'],
                defaults={'nome': disc_data['nome']}
            )
            if created:
                self.stdout.write(f'Disciplina criada: {disciplina.nome}')
            self.disciplinas[disciplina.codigo] = disciplina
            
            # Criar domínios para a disciplina
            for i, dom_data in enumerate(disc_data['dominios']):
                dominio, created = Domínio.objects.get_or_create(
                    codigo=dom_data['codigo'],
                    disciplina=disciplina,
                    defaults={
                        'nome': dom_data['nome'],
                        'ordem': i + 1
                    }
                )
                if created:
                    self.stdout.write(f'Domínio criado: {dominio.nome}')
                self.dominios[f"{disciplina.codigo}_{dominio.codigo}"] = dominio

    def criar_aprendizagens_essenciais(self):
        # Criar aprendizagens essenciais para cada disciplina e domínio
        aprendizagens_data = {
            'PORT': {
                'OR': [
                    ('OR1', 'Compreender textos orais identificando assunto, tema e intenção comunicativa.'),
                    ('OR2', 'Destacar o essencial de um texto audiovisual.')
                ],
                'LE': [
                    ('LE1', 'Ler textos com características narrativas e expositivas.'),
                    ('LE2', 'Fazer inferências a partir da informação contida no texto.')
                ],
                'ES': [
                    ('ES1', 'Planificar a escrita por meio de procedimentos adequados.'),
                    ('ES2', 'Redigir textos coesos e coerentes.')
                ],
                'GR': [
                    ('GR1', 'Identificar classes de palavras e suas funções sintáticas.'),
                    ('GR2', 'Empregar corretamente os tempos e modos verbais.')
                ]
            },
            'MAT': {
                'NUM': [
                    ('NUM1', 'Identificar números primos e realizar a decomposição em fatores.'),
                    ('NUM2', 'Resolver problemas com números racionais não negativos.')
                ],
                'GEO': [
                    ('GEO1', 'Reconhecer propriedades de triângulos e paralelogramos.'),
                    ('GEO2', 'Calcular perímetros e áreas de polígonos.')
                ],
                'ALG': [
                    ('ALG1', 'Usar expressões numéricas envolvendo números racionais.'),
                    ('ALG2', 'Resolver problemas envolvendo sequências e regularidades.')
                ],
                'DAT': [
                    ('DAT1', 'Organizar e representar dados em tabelas e gráficos.'),
                    ('DAT2', 'Resolver problemas envolvendo a média aritmética.')
                ]
            }
        }

        for disc_code, dominios in aprendizagens_data.items():
            disciplina = self.disciplinas[disc_code]
            for dom_code, aprendizagens in dominios.items():
                dominio = self.dominios[f"{disc_code}_{dom_code}"]
                for ordem, (codigo, descricao) in enumerate(aprendizagens, 1):
                    aprendizagem, created = AprendizagemEssencial.objects.get_or_create(
                        codigo=codigo,
                        disciplina=disciplina,
                        defaults={
                            'descricao': descricao,
                            'dominio': dominio,
                            'ano_escolar': 6,
                            'ordem': ordem
                        }
                    )
                    if created:
                        self.stdout.write(f'Aprendizagem criada: {aprendizagem.codigo}')
                    self.aprendizagens[aprendizagem.codigo] = aprendizagem

    def criar_listas_verificacao(self):
        # Criar listas de verificação para cada turma
        for turma in self.turmas:
            disciplina = self.disciplinas['PORT'] if 'Português' in turma.nome else self.disciplinas['MAT']
            lista, created = ListaVerificacao.objects.get_or_create(
                titulo=f'Lista de Verificação - {turma.nome}',
                turma=turma,  # Add turma to uniquely identify the list
                defaults={
                    'descricao': f'Lista de verificação para {turma.nome}',
                    'disciplina': disciplina,
                    'ano_escolar': 6
                }
            )
            if created:
                # Adicionar aprendizagens relevantes à lista
                aprendizagens_disc = [a for a in self.aprendizagens.values() if a.disciplina == disciplina]
                lista.aprendizagens.add(*aprendizagens_disc)
                self.stdout.write(f'Lista de verificação criada para {turma.nome}')

                # Criar progressos para cada aluno
                for aluno in turma.alunos.all():
                    for aprendizagem in aprendizagens_disc:
                        ProgressoAluno.objects.get_or_create(
                            aluno=aluno,
                            lista_verificacao=lista,
                            aprendizagem=aprendizagem,
                            defaults={'estado': 'em_progresso'}
                        )

    def criar_duvidas_e_respostas(self):
        # Criar dúvidas e respostas para cada turma
        for turma in self.turmas:
            disciplina = self.disciplinas['PORT'] if 'Português' in turma.nome else self.disciplinas['MAT']
            aprendizagens_disc = [a for a in self.aprendizagens.values() if a.disciplina == disciplina]
            
            for aluno in turma.alunos.all():
                for i, aprendizagem in enumerate(aprendizagens_disc[:2]):  # Criar 2 dúvidas por aluno
                    duvida, created = Duvida.objects.get_or_create(
                        titulo=f'Dúvida {i+1} - {aluno.first_name}',
                        autor=aluno,
                        aprendizagem=aprendizagem,
                        turma=turma,
                        defaults={
                            'descricao': f'Esta é uma dúvida sobre {turma.nome} criada para demonstração.',
                            'categoria': 'conceito',
                            'prioridade': 'baixa',
                            'estado': 'aberta'
                        }
                    )
                    if created:
                        self.stdout.write(f'Dúvida criada: {duvida.titulo}')
                        
                        # Criar resposta do professor
                        RespostaDuvida.objects.get_or_create(
                            duvida=duvida,
                            autor=turma.professor,
                            defaults={
                                'texto': f'Esta é uma resposta de demonstração do professor {turma.professor.get_full_name()}.',
                                'melhor_resposta': True
                            }
                        )
                        
                        # Atualizar estado da dúvida
                        duvida.estado = 'respondida'
                        duvida.data_resposta = timezone.now()
                        duvida.respondido_por = turma.professor
                        duvida.save()

    def criar_diarios_e_entradas(self):
        # Criar diários e entradas para cada aluno
        for aluno in self.students:
            for turma in self.turmas:
                if aluno in turma.alunos.all():
                    titulo = f'Diário de Aprendizagem - {aluno.first_name} - {turma.nome}'
                    diario, created = DiarioAprendizagem.objects.get_or_create(
                        aluno=aluno,
                        turma=turma,
                        titulo=titulo,  # Add titulo to uniquely identify the diary
                        defaults={'titulo': titulo}
                    )
                    if created:
                        self.stdout.write(f'Diário criado para {aluno.username} em {turma.nome}')
                        
                        # Criar algumas entradas no diário
                        for tipo in ['reflexao', 'conceito', 'descoberta']:
                            entrada = EntradaDiario.objects.create(
                                diario=diario,
                                titulo=f'Entrada de {tipo}',
                                conteudo=f'Esta é uma entrada de {tipo} criada para demonstração.',
                                tipo=tipo
                            )
                            # Adicionar algumas aprendizagens relacionadas
                            disciplina = self.disciplinas['PORT'] if 'Português' in turma.nome else self.disciplinas['MAT']
                            aprendizagens_disc = [a for a in self.aprendizagens.values() if a.disciplina == disciplina]
                            entrada.aprendizagens.add(*aprendizagens_disc[:2])

    def criar_metas_e_conquistas(self):
        # Criar metas e conquistas para cada aluno
        for aluno in self.students:
            for turma in self.turmas:
                if aluno in turma.alunos.all():
                    # Criar meta de aprendizagem
                    disciplina = self.disciplinas['PORT'] if 'Português' in turma.nome else self.disciplinas['MAT']
                    aprendizagens_disc = [a for a in self.aprendizagens.values() if a.disciplina == disciplina]
                    
                    meta = MetaAprendizagem.objects.create(
                        titulo=f'Meta de Aprendizagem - {aluno.first_name}',
                        descricao=f'Esta é uma meta criada para demonstração em {turma.nome}',
                        tipo='individual',
                        estado='em_andamento',
                        aluno=aluno,
                        turma=turma,
                        data_inicio=timezone.now().date(),
                        data_fim=(timezone.now() + timedelta(days=30)).date()
                    )
                    meta.aprendizagens.add(*aprendizagens_disc[:2])
                    meta.participantes.add(aluno)
                    
                    # Criar conquista coletiva
                    conquista = ConquistaColetiva.objects.create(
                        titulo=f'Conquista da Turma - {turma.nome}',
                        descricao='Projeto colaborativo bem-sucedido',
                        tipo='projeto',
                        criador=aluno,
                        turma=turma,
                        impacto='grupo',
                        contribuicoes='Todos os alunos participaram ativamente',
                        beneficiarios='Toda a turma se beneficiou'
                    )
                    conquista.participantes.set(turma.alunos.all())
                    conquista.aprendizagens.add(*aprendizagens_disc[:2])
                    
                    self.stdout.write(f'Meta e conquista criadas para {aluno.get_full_name()} em {turma.nome}') 