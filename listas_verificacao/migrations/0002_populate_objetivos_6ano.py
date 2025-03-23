from django.db import migrations

def create_dominios_and_objetivos(apps, schema_editor):
    DominioAprendizagem = apps.get_model('listas_verificacao', 'DominioAprendizagem')
    ObjetivoAprendizagem = apps.get_model('listas_verificacao', 'ObjetivoAprendizagem')
    
    # Create domains
    dominios = {
        'OC': DominioAprendizagem.objects.create(
            codigo='OC',
            nome='Oralidade - Compreensão',
            descricao='Competências de compreensão oral'
        ),
        'OE': DominioAprendizagem.objects.create(
            codigo='OE',
            nome='Oralidade - Expressão',
            descricao='Competências de expressão oral'
        ),
        'L': DominioAprendizagem.objects.create(
            codigo='L',
            nome='Leitura',
            descricao='Competências de leitura'
        ),
        'EL': DominioAprendizagem.objects.create(
            codigo='EL',
            nome='Educação Literária',
            descricao='Competências de educação literária'
        ),
        'E': DominioAprendizagem.objects.create(
            codigo='E',
            nome='Escrita',
            descricao='Competências de escrita'
        ),
        'G': DominioAprendizagem.objects.create(
            codigo='G',
            nome='Gramática',
            descricao='Competências gramaticais'
        ),
    }
    
    # Create objectives
    objetivos = [
        # Oralidade - Compreensão
        ('OC1', dominios['OC'], 'Esclarecer, com fundamentação adequada, sentidos implícitos.', 1),
        ('OC2', dominios['OC'], 'Distinguir factos de opiniões na explicitação de argumentos.', 2),
        
        # Oralidade - Expressão
        ('OE1', dominios['OE'], 'Comunicar, em contexto formal, informação essencial (paráfrase, resumo) e opiniões fundamentadas.', 1),
        ('OE2', dominios['OE'], 'Planificar, produzir e avaliar textos orais (relato, descrição, apreciação crítica), com definição de tema e sequência lógica de tópicos (organização do discurso, correção gramatical), individualmente ou em grupo.', 2),
        ('OE3', dominios['OE'], 'Fazer uma apresentação oral, devidamente estruturada, sobre um tema.', 3),
        ('OE4', dominios['OE'], 'Captar e manter a atenção da audiência (olhar, gesto, recurso eventual a suportes digitais).', 4),
        ('OE5', dominios['OE'], 'Utilizar, de modo intencional e sistemático, processos de coesão textual: anáforas lexicais e pronominais, frases complexas, expressões adverbiais, tempos e modos verbais, conectores frásicos.', 5),
        
        # Leitura
        ('L1', dominios['L'], 'Ler textos com características narrativas de maior complexidade, associados a finalidades várias (lúdicas, estéticas, publicitárias e informativas) e em suportes variados.', 1),
        ('L2', dominios['L'], 'Caraterística expositivas de maior complexidade, associados a finalidades várias (lúdicas, estéticas, publicitárias e informativas) e em suportes variados.', 2),
        ('L3', dominios['L'], 'Realizar leitura em voz alta, silenciosa e autónoma.', 3),
        ('L4', dominios['L'], 'Explicitar o sentido global de um texto.', 4),
        ('L5', dominios['L'], 'Fazer inferências, justificando-as.', 5),
        ('L6', dominios['L'], 'Identificar tema(s), ideias principais e pontos de vista.', 6),
        ('L7', dominios['L'], 'Reconhecer a forma como o texto está estruturado (partes e subpartes).', 7),
        ('L8', dominios['L'], 'Compreender a utilização de recursos expressivos para a construção de sentido do texto.', 8),
        ('L9', dominios['L'], 'Utilizar procedimentos de registo e tratamento de informação.', 9),
        ('L10', dominios['L'], 'Distinguir nos textos características da notícia, da entrevista, do anúncio publicitário e do roteiro (estruturação, finalidade).', 10),
        ('L11', dominios['L'], 'Conhecer os objetivos e as formas de publicidade na sociedade atual.', 11),
        
        # Educação Literária
        ('EL1', dominios['EL'], 'Ler integralmente obras literárias narrativas, poéticas e dramáticas.', 1),
        ('EL2', dominios['EL'], 'Interpretar adequadamente os textos de acordo com o género literário.', 2),
        ('EL3', dominios['EL'], 'Analisar o sentido conotativo de palavras e expressões.', 3),
        ('EL4', dominios['EL'], 'Identificar marcas formais do texto poético: estrofe, rima, esquema rimático, métrica.', 4),
        ('EL5', dominios['EL'], 'Reconhecer, na organização do texto dramático: ato, cena, fala, indicações cénicas.', 5),
        ('EL6', dominios['EL'], 'Analisar o modo como os temas, as experiências e os valores são representados.', 6),
        ('EL7', dominios['EL'], 'Valorizar a diversidade de culturas, de vivências e de mundivisões presente nos textos.', 7),
        ('EL8', dominios['EL'], 'Explicar recursos expressivos utilizados na construção de textos literários (anáfora e metáfora).', 8),
        ('EL9', dominios['EL'], 'Expressar reações aos livros lidos e partilhar leituras através de declamações, representações teatrais, escrita criativa, apresentações orais.', 9),
        ('EL10', dominios['EL'], 'Desenvolver um projeto de leitura que integre explicitação de objetivos de leitura pessoais e comparação de temas comuns em obras, em géneros e em manifestações artísticas diferentes.', 10),
        
        # Escrita
        ('E1', dominios['E'], 'Escrever textos de caráter narrativo, integrando o diálogo e a descrição.', 1),
        ('E2', dominios['E'], 'Utilizar sistematicamente processos de planificação, textualização e revisão de textos.', 2),
        ('E3', dominios['E'], 'Utilizar processadores de texto e recursos da Web para a escrita, revisão e partilha de textos.', 3),
        ('E4', dominios['E'], 'Intervir em blogues e em fóruns, por meio de textos adequados ao género e à situação de comunicação.', 4),
        ('E5', dominios['E'], 'Redigir textos de âmbito escolar, como a exposição e o resumo.', 5),
        ('E6', dominios['E'], 'Produzir textos de opinião com juízos de valor sobre situações vividas e sobre leituras feitas.', 6),
        
        # Gramática
        ('G1', dominios['G'], 'Identificar a classe de palavras: nome próprio, comum e comum coletivo, verbo copulativo, verbo auxiliar, conjunção, locução conjuncional, determinante indefinido, pronome indefinido, quantificador.', 1),
        ('G2', dominios['G'], 'Conjugar verbos regulares e irregulares no presente, no pretérito imperfeito e no futuro do modo conjuntivo.', 2),
        ('G3', dominios['G'], 'Conjugar verbos regulares e irregulares no modo condicional.', 3),
        ('G4', dominios['G'], 'Utilizar apropriadamente os tempos verbais na construção de frases complexas e de textos.', 4),
        ('G5', dominios['G'], 'Empregar adequadamente o modo conjuntivo como forma superlativa do imperativo.', 5),
        ('G6', dominios['G'], 'Identificar funções sintáticas: predicativo do sujeito, complementos (oblíquo e agente da passiva) e modificador (do grupo verbal).', 6),
        ('G7', dominios['G'], 'Transformar a frase ativa em frase passiva (e vice-versa).', 7),
        ('G8', dominios['G'], 'Transformar o discurso direto em discurso indireto (e vice-versa).', 8),
        ('G9', dominios['G'], 'Colocar corretamente as formas átonas do pronome pessoal adjacentes ao verbo (próclise, ênclise e mesóclise).', 9),
        ('G10', dominios['G'], 'Compreender a ligação de orações por coordenação e por subordinação.', 10),
        ('G11', dominios['G'], 'Classificar orações coordenadas copulativas e adversativas e orações subordinadas adverbiais temporais e causais.', 11),
        ('G12', dominios['G'], 'Distinguir derivação de composição.', 12),
        ('G13', dominios['G'], 'Explicar a utilização de sinais de pontuação em função da construção da frase.', 13),
        ('G14', dominios['G'], 'Mobilizar no relacionamento interpessoal formas de tratamento adequadas a contextos formais.', 14),
    ]
    
    for codigo, dominio, descricao, ordem in objetivos:
        ObjetivoAprendizagem.objects.create(
            dominio=dominio,
            codigo=codigo,
            descricao=descricao,
            ano_escolar=6,
            disciplina='Português',
            ordem=ordem
        )

def delete_dominios_and_objetivos(apps, schema_editor):
    DominioAprendizagem = apps.get_model('listas_verificacao', 'DominioAprendizagem')
    DominioAprendizagem.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('listas_verificacao', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_dominios_and_objetivos, delete_dominios_and_objetivos),
    ] 