from django.core.management.base import BaseCommand
from listas_verificacao.models import DominioAprendizagem, ObjetivoAprendizagem

class Command(BaseCommand):
    help = 'Popula a base de dados com os objetivos de aprendizagem do 6º ano'

    def handle(self, *args, **options):
        # Dicionário com os domínios de aprendizagem
        dominios = {
            'OC': 'Oralidade - Compreensão',
            'OE': 'Oralidade - Expressão',
            'L': 'Leitura',
            'EL': 'Educação Literária',
            'E': 'Escrita',
            'G': 'Gramática'
        }

        # Criar domínios
        for codigo, nome in dominios.items():
            dominio, created = DominioAprendizagem.objects.get_or_create(
                codigo=codigo,
                defaults={'nome': nome}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Domínio "{nome}" criado com sucesso'))

        # Dicionário com os objetivos de aprendizagem por domínio
        objetivos = {
            'OC': [
                'OC1 - Compreender discursos orais breves, identificando a intenção do locutor e o assunto principal.',
                'OC2 - Identificar diferentes tipos de texto oral (narrativo, descritivo, informativo, argumentativo).',
                'OC3 - Reconhecer elementos paralinguísticos (entonação, ritmo, pausas) e sua função no discurso.',
                'OC4 - Identificar recursos de coesão e coerência em textos orais.',
                'OC5 - Compreender instruções e orientações orais para realizar tarefas.',
            ],
            'OE': [
                'OE1 - Produzir discursos orais breves, adequando a linguagem ao contexto e ao interlocutor.',
                'OE2 - Narrar experiências pessoais e fatos do cotidiano de forma clara e organizada.',
                'OE3 - Participar de debates e discussões, respeitando turnos de fala e opiniões diferentes.',
                'OE4 - Apresentar trabalhos escolares com clareza e objetividade.',
                'OE5 - Utilizar recursos paralinguísticos adequadamente na expressão oral.',
            ],
            'L': [
                'L1 - Identificar o tema central e os subtemas de textos variados.',
                'L2 - Localizar informações explícitas e implícitas em textos.',
                'L3 - Identificar diferentes tipos de texto e suas características.',
                'L4 - Reconhecer elementos de coesão e coerência em textos escritos.',
                'L5 - Inferir o sentido de palavras e expressões pelo contexto.',
            ],
            'EL': [
                'EL1 - Identificar elementos da narrativa (personagens, tempo, espaço, enredo).',
                'EL2 - Reconhecer diferentes gêneros literários (conto, crônica, poema).',
                'EL3 - Identificar recursos expressivos (metáfora, comparação, personificação).',
                'EL4 - Relacionar textos literários com seu contexto histórico e social.',
                'EL5 - Expressar opiniões sobre textos literários lidos.',
            ],
            'E': [
                'E1 - Produzir textos narrativos com elementos básicos da narrativa.',
                'E2 - Produzir textos descritivos com riqueza de detalhes.',
                'E3 - Produzir textos informativos com clareza e objetividade.',
                'E4 - Produzir textos argumentativos com opiniões fundamentadas.',
                'E5 - Revisar e reescrever textos, considerando aspectos ortográficos e gramaticais.',
            ],
            'G': [
                'G1 - Identificar classes de palavras e suas funções no texto.',
                'G2 - Reconhecer e utilizar diferentes tipos de sujeito e predicado.',
                'G3 - Identificar e utilizar recursos de coesão (pronomes, conectivos).',
                'G4 - Aplicar regras de acentuação e pontuação.',
                'G5 - Identificar e utilizar diferentes tipos de frase (declarativa, interrogativa, exclamativa, imperativa).',
            ]
        }

        # Criar objetivos
        for codigo_dominio, lista_objetivos in objetivos.items():
            dominio = DominioAprendizagem.objects.get(codigo=codigo_dominio)
            for i, descricao in enumerate(lista_objetivos, 1):
                codigo = f"{codigo_dominio}{i}"
                objetivo, created = ObjetivoAprendizagem.objects.get_or_create(
                    codigo=codigo,
                    ano_escolar=6,
                    disciplina='Português',
                    defaults={
                        'dominio': dominio,
                        'descricao': descricao,
                        'ordem': i
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Objetivo "{codigo}" criado com sucesso'))

        self.stdout.write(self.style.SUCCESS('Base de dados populada com sucesso!')) 