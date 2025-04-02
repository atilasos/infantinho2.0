from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django import forms
from .email_service import (
    enviar_email_baixo_progresso,
    enviar_email_confirmacao_pendente,
    enviar_email_nova_duvida
)

User = get_user_model()

class CategoriaObjetivo(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    ordem = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Categoria de Objetivo'
        verbose_name_plural = 'Categorias de Objetivos'
        ordering = ['ordem']
    
    def __str__(self):
        return self.nome

class ObjetivoPredefinido(models.Model):
    codigo = models.CharField(max_length=10, unique=True)  # e.g., 'OC1', 'OE1', etc.
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    categoria = models.ForeignKey(CategoriaObjetivo, on_delete=models.CASCADE, related_name='objetivos')
    ordem = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Objetivo Predefinido'
        verbose_name_plural = 'Objetivos Predefinidos'
        ordering = ['categoria', 'ordem']
    
    def __str__(self):
        return f'{self.codigo} - {self.titulo}'

class Disciplina(models.Model):
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10, unique=True)
    descricao = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Disciplina'
        verbose_name_plural = 'Disciplinas'
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"

class Domínio(models.Model):
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, related_name='dominios')
    descricao = models.TextField(blank=True)
    ordem = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Domínio'
        verbose_name_plural = 'Domínios'
        ordering = ['ordem']
        unique_together = ['codigo', 'disciplina']
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"

class Subdomínio(models.Model):
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10)
    dominio = models.ForeignKey(Domínio, on_delete=models.CASCADE, related_name='subdominios')
    descricao = models.TextField(blank=True)
    ordem = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Subdomínio'
        verbose_name_plural = 'Subdomínios'
        ordering = ['ordem']
        unique_together = ['codigo', 'dominio']
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"

class AprendizagemEssencial(models.Model):
    codigo = models.CharField(max_length=10)  # Ex: OC1, OE2, etc.
    descricao = models.TextField()
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, related_name='aprendizagens')
    dominio = models.ForeignKey(Domínio, on_delete=models.CASCADE, related_name='aprendizagens')
    subdominio = models.ForeignKey(Subdomínio, on_delete=models.CASCADE, related_name='aprendizagens', null=True, blank=True)
    ano_escolar = models.PositiveIntegerField()
    ordem = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Aprendizagem Essencial'
        verbose_name_plural = 'Aprendizagens Essenciais'
        ordering = ['ano_escolar', 'ordem']
        unique_together = ['codigo', 'disciplina', 'ano_escolar']
    
    def __str__(self):
        return f"{self.codigo} - {self.descricao[:50]}..."

class ListaVerificacao(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    turma = models.ForeignKey('Turma', on_delete=models.CASCADE, related_name='listas_verificacao', null=True, blank=True)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, related_name='listas_verificacao', null=True, blank=True)
    ano_escolar = models.PositiveIntegerField(default=6)  # Valor padrão: 6º ano
    aprendizagens = models.ManyToManyField(AprendizagemEssencial, related_name='listas_verificacao')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Lista de Verificação'
        verbose_name_plural = 'Listas de Verificação'
        ordering = ['-data_atualizacao']
    
    def __str__(self):
        return self.titulo

class Objetivo(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    lista_verificacao = models.ForeignKey(ListaVerificacao, on_delete=models.CASCADE, related_name='objetivos')
    ordem = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Objetivo'
        verbose_name_plural = 'Objetivos'
        ordering = ['ordem']
    
    def __str__(self):
        return self.titulo

class Turma(models.Model):
    nome = models.CharField(max_length=100)
    professor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='turmas_professor')
    alunos = models.ManyToManyField(User, related_name='turmas_aluno', blank=True)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, related_name='turmas', null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Turma'
        verbose_name_plural = 'Turmas'
        ordering = ['-data_criacao']
    
    def __str__(self):
        return self.nome

class ProgressoAluno(models.Model):
    ESTADOS = [
        ('nao_iniciado', 'Não Iniciado'),
        ('em_progresso', 'Em Progresso'),
        ('concluido', 'Concluído'),
        ('dificuldade', 'Com Dificuldade'),
    ]
    
    aluno = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progressos')
    lista_verificacao = models.ForeignKey(ListaVerificacao, on_delete=models.CASCADE, related_name='progressos')
    aprendizagem = models.ForeignKey(AprendizagemEssencial, on_delete=models.CASCADE, related_name='progressos', null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='nao_iniciado')
    observacoes = models.TextField(blank=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Progresso do Aluno'
        verbose_name_plural = 'Progressos dos Alunos'
        unique_together = ['aluno', 'lista_verificacao', 'aprendizagem']
        ordering = ['-data_atualizacao']
    
    def __str__(self):
        return f"{self.aluno.username} - {self.aprendizagem.codigo}"

class Notificacao(models.Model):
    TIPOS = [
        ('baixo_progresso', 'Baixo Progresso'),
        ('prazo_proximo', 'Prazo Próximo'),
        ('nova_duvida', 'Nova Dúvida'),
        ('conquista', 'Conquista'),
        ('feedback', 'Feedback'),
        ('lembrete', 'Lembrete'),
        ('resposta_duvida', 'Resposta à Dúvida'),
        ('confirmacao_pendente', 'Confirmação Pendente'),
        ('nova_dificuldade', 'Nova Dificuldade'),
        ('intervencao', 'Intervenção Pedagógica'),
    ]
    
    NIVEL_PRIORIDADE = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
    ]
    
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificacoes_recebidas')
    remetente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificacoes_enviadas', null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()
    prioridade = models.CharField(max_length=10, choices=NIVEL_PRIORIDADE, default='media')
    lida = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_leitura = models.DateTimeField(null=True, blank=True)
    
    # Relacionamentos opcionais para contextualizar a notificação
    lista_verificacao = models.ForeignKey(ListaVerificacao, on_delete=models.CASCADE, related_name='notificacoes', null=True, blank=True)
    aprendizagem = models.ForeignKey(AprendizagemEssencial, on_delete=models.CASCADE, related_name='notificacoes', null=True, blank=True)
    progresso = models.ForeignKey(ProgressoAluno, on_delete=models.CASCADE, related_name='notificacoes', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['destinatario', 'lida']),
            models.Index(fields=['tipo', 'data_criacao']),
        ]
    
    def __str__(self):
        return f"{self.tipo} - {self.titulo}"
    
    def marcar_como_lida(self):
        if not self.lida:
            self.lida = True
            self.data_leitura = timezone.now()
            self.save()

class ConfiguracaoNotificacao(models.Model):
    FREQUENCIA_CHOICES = [
        ('imediato', 'Imediatamente'),
        ('diario', 'Resumo Diário'),
        ('semanal', 'Resumo Semanal'),
        ('desativado', 'Desativado'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='config_notificacoes')
    
    # Notificações por tipo
    notif_baixo_progresso = models.BooleanField('Alertas de Baixo Progresso', default=True)
    notif_prazos = models.BooleanField('Notificações de Prazos', default=True)
    notif_duvidas = models.BooleanField('Notificações de Dúvidas', default=True)
    notif_conquistas = models.BooleanField('Notificações de Conquistas', default=True)
    notif_feedback = models.BooleanField('Notificações de Feedback', default=True)
    
    # Configurações de email
    receber_emails = models.BooleanField('Receber Emails', default=True)
    frequencia_emails = models.CharField(
        'Frequência de Emails',
        max_length=20,
        choices=FREQUENCIA_CHOICES,
        default='imediato'
    )
    
    # Horários permitidos (para evitar notificações em horários indesejados)
    horario_inicio = models.TimeField('Horário de Início', default='08:00')
    horario_fim = models.TimeField('Horário de Fim', default='18:00')
    
    # Dias da semana permitidos
    dias_semana = models.CharField(
        'Dias da Semana',
        max_length=20,
        default='1,2,3,4,5',  # Segunda a Sexta por padrão
        help_text='Dias da semana (1-7, separados por vírgula. 1=Segunda, 7=Domingo)'
    )
    
    class Meta:
        verbose_name = 'Configuração de Notificação'
        verbose_name_plural = 'Configurações de Notificações'
    
    def __str__(self):
        return f'Configurações de {self.usuario.username}'
    
    @property
    def dias_semana_list(self):
        """Retorna a lista de dias da semana como inteiros."""
        return [int(d) for d in self.dias_semana.split(',') if d.strip()]
    
    def pode_enviar_agora(self):
        """Verifica se pode enviar notificação no momento atual."""
        agora = timezone.localtime()
        
        # Verifica se está dentro do horário permitido
        hora_atual = agora.time()
        if not (self.horario_inicio <= hora_atual <= self.horario_fim):
            return False
        
        # Verifica se é um dia da semana permitido (1=Segunda, 7=Domingo)
        if agora.isoweekday() not in self.dias_semana_list:
            return False
        
        return True
    
    def deve_enviar_email(self, tipo_notificacao):
        """Verifica se deve enviar email para um tipo específico de notificação."""
        if not self.receber_emails:
            return False
            
        # Mapeia os tipos de notificação para os campos do modelo
        mapa_tipos = {
            'baixo_progresso': self.notif_baixo_progresso,
            'prazo_proximo': self.notif_prazos,
            'nova_duvida': self.notif_duvidas,
            'conquista': self.notif_conquistas,
            'feedback': self.notif_feedback,
        }
        
        # Verifica se o tipo de notificação está ativado
        return mapa_tipos.get(tipo_notificacao, True)

@receiver(post_save, sender=User)
def criar_configuracao_notificacao(sender, instance, created, **kwargs):
    """Cria configuração de notificação padrão para novos usuários."""
    if created:
        ConfiguracaoNotificacao.objects.create(usuario=instance)

# Atualiza o signal de notificação para usar as configurações
@receiver(post_save, sender=Notificacao)
def enviar_notificacao_email(sender, instance, created, **kwargs):
    """
    Envia um email quando uma nova notificação é criada, respeitando as configurações do usuário.
    """
    if not created or not instance.destinatario.email:
        return
        
    try:
        config = instance.destinatario.config_notificacoes
        
        # Verifica se deve enviar email
        if not config.receber_emails or not config.deve_enviar_email(instance.tipo):
            return
            
        # Verifica horário/dia permitido
        if not config.pode_enviar_agora():
            return
            
        # Envia o email apropriado
        if instance.tipo == 'baixo_progresso':
            enviar_email_baixo_progresso(instance)
        elif instance.tipo == 'confirmacao_pendente':
            enviar_email_confirmacao_pendente(instance)
        elif instance.tipo == 'nova_duvida':
            enviar_email_nova_duvida(instance)
    except ConfiguracaoNotificacao.DoesNotExist:
        # Se não tem configuração, usa o comportamento padrão
        if instance.tipo == 'baixo_progresso':
            enviar_email_baixo_progresso(instance)
        elif instance.tipo == 'confirmacao_pendente':
            enviar_email_confirmacao_pendente(instance)
        elif instance.tipo == 'nova_duvida':
            enviar_email_nova_duvida(instance)

class AvaliacaoAprendizagem(models.Model):
    ESTADOS = [
        ('nao_iniciado', 'Não Iniciado'),
        ('mais_trabalho', 'Mais Trabalho'),
        ('aguardando_avaliacao', 'Aguardando Avaliação'),
        ('avaliado_aprovado', 'Avaliado e Aprovado'),
        ('monitor_disponivel', 'Monitor Disponível'),
    ]
    
    progresso = models.OneToOneField(ProgressoAluno, on_delete=models.CASCADE, related_name='avaliacao')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='nao_iniciado')
    data_solicitacao_avaliacao = models.DateTimeField(null=True, blank=True)
    data_avaliacao = models.DateTimeField(null=True, blank=True)
    avaliador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='avaliacoes_realizadas')
    observacoes_avaliador = models.TextField(blank=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Avaliação de Aprendizagem'
        verbose_name_plural = 'Avaliações de Aprendizagens'
    
    def __str__(self):
        return f"Avaliação de {self.progresso.aluno.username} - {self.progresso.aprendizagem.codigo}"

class ComentarioAprendizagem(models.Model):
    TIPOS = [
        ('autoavaliacao', 'Autoavaliação'),
        ('feedback_professor', 'Feedback do Professor'),
        ('comentario_monitor', 'Comentário de Monitor'),
    ]
    
    progresso = models.ForeignKey(ProgressoAluno, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comentarios_feitos')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    texto = models.TextField()
    anexos = models.FileField(upload_to='anexos_comentarios/', null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Comentário de Aprendizagem'
        verbose_name_plural = 'Comentários de Aprendizagens'
        ordering = ['-data_criacao']
    
    def __str__(self):
        return f"Comentário de {self.autor.username} em {self.progresso.aprendizagem.codigo}"

class Duvida(models.Model):
    PRIORIDADES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    CATEGORIAS = [
        ('conceito', 'Conceito'),
        ('exercicio', 'Exercício'),
        ('recurso', 'Recurso'),
        ('outro', 'Outro'),
    ]
    
    ESTADOS = [
        ('aberta', 'Aberta'),
        ('em_andamento', 'Em Andamento'),
        ('respondida', 'Respondida'),
        ('fechada', 'Fechada'),
    ]
    
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='duvidas_criadas')
    aprendizagem = models.ForeignKey(AprendizagemEssencial, on_delete=models.CASCADE, related_name='duvidas')
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='duvidas')
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='conceito')
    prioridade = models.CharField(max_length=20, choices=PRIORIDADES, default='media')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='aberta')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    data_resposta = models.DateTimeField(null=True, blank=True)
    respondido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='duvidas_respondidas')
    
    class Meta:
        verbose_name = 'Dúvida'
        verbose_name_plural = 'Dúvidas'
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['estado', 'data_criacao']),
            models.Index(fields=['categoria', 'prioridade']),
        ]
    
    def __str__(self):
        return self.titulo
    
    def marcar_como_respondida(self, respondido_por):
        self.estado = 'respondida'
        self.data_resposta = timezone.now()
        self.respondido_por = respondido_por
        self.save()
        
        # Criar notificação para o autor
        Notificacao.objects.create(
            destinatario=self.autor,
            tipo='resposta_duvida',
            titulo=f'Sua dúvida foi respondida: {self.titulo}',
            mensagem=f'Sua dúvida sobre {self.aprendizagem.codigo} foi respondida por {respondido_por.get_full_name()}.',
            prioridade='media',
            lista_verificacao=None,
            aprendizagem=self.aprendizagem
        )

class RespostaDuvida(models.Model):
    duvida = models.ForeignKey(Duvida, on_delete=models.CASCADE, related_name='respostas')
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='respostas_duvidas')
    texto = models.TextField()
    anexos = models.FileField(upload_to='anexos_duvidas/', null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    melhor_resposta = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Resposta de Dúvida'
        verbose_name_plural = 'Respostas de Dúvidas'
        ordering = ['-melhor_resposta', 'data_criacao']
    
    def __str__(self):
        return f"Resposta para: {self.duvida.titulo}"
    
    def marcar_como_melhor_resposta(self):
        # Desmarcar outras respostas como melhor resposta
        RespostaDuvida.objects.filter(duvida=self.duvida, melhor_resposta=True).update(melhor_resposta=False)
        
        # Marcar esta como melhor resposta
        self.melhor_resposta = True
        self.save()
        
        # Atualizar estado da dúvida
        self.duvida.estado = 'respondida'
        self.duvida.data_resposta = timezone.now()
        self.duvida.respondido_por = self.autor
        self.duvida.save()
        
        # Criar notificação para o autor da dúvida
        Notificacao.objects.create(
            destinatario=self.duvida.autor,
            tipo='resposta_duvida',
            titulo=f'Sua dúvida foi respondida: {self.duvida.titulo}',
            mensagem=f'Sua dúvida sobre {self.duvida.aprendizagem.codigo} foi respondida por {self.autor.get_full_name()}.',
            prioridade='media',
            lista_verificacao=None,
            aprendizagem=self.duvida.aprendizagem
        )

class DiarioAprendizagem(models.Model):
    """Modelo para o diário de aprendizagem colaborativo."""
    aluno = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diarios_aprendizagem')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    partilhado = models.BooleanField(default=False)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='diarios_aprendizagem')
    
    class Meta:
        verbose_name = 'Diário de Aprendizagem'
        verbose_name_plural = 'Diários de Aprendizagem'
        ordering = ['-data_atualizacao']
    
    def __str__(self):
        return f"Diário de {self.aluno.get_full_name()} - {self.titulo}"

class EntradaDiario(models.Model):
    """Modelo para as entradas do diário de aprendizagem."""
    TIPOS = [
        ('reflexao', 'Reflexão'),
        ('conceito', 'Conceito'),
        ('duvida', 'Dúvida'),
        ('descoberta', 'Descoberta'),
        ('conexao', 'Conexão'),
    ]
    
    diario = models.ForeignKey(DiarioAprendizagem, on_delete=models.CASCADE, related_name='entradas')
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    aprendizagens = models.ManyToManyField(AprendizagemEssencial, related_name='entradas_diario', blank=True)
    anexos = models.FileField(upload_to='anexos_diario/', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Entrada do Diário'
        verbose_name_plural = 'Entradas do Diário'
        ordering = ['-data_criacao']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.titulo}"

class ComentarioEntrada(models.Model):
    """Modelo para comentários nas entradas do diário."""
    entrada = models.ForeignKey(EntradaDiario, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comentarios_diario')
    conteudo = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Comentário de Entrada'
        verbose_name_plural = 'Comentários de Entradas'
        ordering = ['data_criacao']
    
    def __str__(self):
        return f"Comentário de {self.autor.get_full_name()} em {self.entrada.titulo}"

class ConexaoAprendizagem(models.Model):
    """Modelo para conexões entre entradas do diário e aprendizagens."""
    entrada = models.ForeignKey(EntradaDiario, on_delete=models.CASCADE, related_name='conexoes')
    aprendizagem = models.ForeignKey(AprendizagemEssencial, on_delete=models.CASCADE, related_name='conexoes_diario')
    descricao = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Conexão de Aprendizagem'
        verbose_name_plural = 'Conexões de Aprendizagem'
        unique_together = ['entrada', 'aprendizagem']
    
    def __str__(self):
        return f"Conexão: {self.entrada.titulo} - {self.aprendizagem.codigo}"

class MetaAprendizagem(models.Model):
    """Modelo para metas de aprendizagem definidas de forma partilhada."""
    TIPOS_META = [
        ('individual', 'Individual'),
        ('coletiva', 'Coletiva'),
        ('projeto', 'Projeto de Grupo'),
    ]
    
    ESTADOS_META = [
        ('proposta', 'Proposta'),
        ('negociacao', 'Em Negociação'),
        ('aprovada', 'Aprovada'),
        ('em_andamento', 'Em Andamento'),
        ('concluida', 'Concluída'),
        ('ajustada', 'Ajustada'),
    ]
    
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS_META)
    estado = models.CharField(max_length=20, choices=ESTADOS_META, default='proposta')
    
    # Relacionamentos
    aluno = models.ForeignKey(User, on_delete=models.CASCADE, related_name='metas_propostas')
    turma = models.ForeignKey('Turma', on_delete=models.CASCADE)
    aprendizagens = models.ManyToManyField('AprendizagemEssencial', related_name='metas')
    participantes = models.ManyToManyField(User, related_name='metas_participacao', blank=True)
    
    # Datas
    data_proposta = models.DateTimeField(auto_now_add=True)
    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)
    data_conclusao = models.DateField(null=True, blank=True)
    
    # Campos para negociação
    justificativa = models.TextField(blank=True)
    plano_acao = models.TextField(blank=True)
    recursos_necessarios = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-data_proposta']
        verbose_name = 'Meta de Aprendizagem'
        verbose_name_plural = 'Metas de Aprendizagem'
    
    def __str__(self):
        return f"{self.titulo} - {self.get_tipo_display()}"

class AlteracaoMeta(models.Model):
    """Modelo para registrar alterações e negociações de metas."""
    TIPOS_ALTERACAO = [
        ('prazo', 'Alteração de Prazo'),
        ('escopo', 'Alteração de Âmbito'),
        ('recursos', 'Alteração de Recursos'),
        ('participantes', 'Alteração de Participantes'),
    ]
    
    meta = models.ForeignKey(MetaAprendizagem, on_delete=models.CASCADE, related_name='alteracoes')
    tipo = models.CharField(max_length=20, choices=TIPOS_ALTERACAO)
    descricao = models.TextField()
    justificativa = models.TextField()
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_aprovacao = models.DateTimeField(null=True, blank=True)
    
    # Campos para negociação
    aprovada = models.BooleanField(default=False)
    aprovada_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='alteracoes_aprovadas')
    comentarios = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-data_solicitacao']
        verbose_name = 'Alteração de Meta'
        verbose_name_plural = 'Alterações de Metas'
    
    def __str__(self):
        return f"Alteração de {self.get_tipo_display()} - {self.meta.titulo}"

class ReflexaoMeta(models.Model):
    """Modelo para registrar reflexões sobre o progresso das metas."""
    meta = models.ForeignKey(MetaAprendizagem, on_delete=models.CASCADE, related_name='reflexoes')
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    conteudo = models.TextField()
    data = models.DateTimeField(auto_now_add=True)
    
    # Campos para autoavaliação
    nivel_satisfacao = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    dificuldades_encontradas = models.TextField(blank=True)
    estrategias_sucesso = models.TextField(blank=True)
    sugestoes_melhoria = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-data']
        verbose_name = 'Reflexão de Meta'
        verbose_name_plural = 'Reflexões de Metas'
    
    def __str__(self):
        return f"Reflexão - {self.meta.titulo} - {self.data.strftime('%d/%m/%Y')}"

class AcompanhamentoMeta(models.Model):
    """Modelo para registrar o acompanhamento colaborativo das metas."""
    meta = models.ForeignKey(MetaAprendizagem, on_delete=models.CASCADE, related_name='acompanhamentos')
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    data = models.DateTimeField(auto_now_add=True)
    
    # Campos para acompanhamento
    progresso = models.IntegerField(choices=[(i, i) for i in range(0, 101)])
    observacoes = models.TextField()
    sugestoes = models.TextField(blank=True)
    recursos_sugeridos = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-data']
        verbose_name = 'Acompanhamento de Meta'
        verbose_name_plural = 'Acompanhamentos de Metas'
    
    def __str__(self):
        return f"Acompanhamento - {self.meta.titulo} - {self.data.strftime('%d/%m/%Y')}"

class ConquistaMeta(models.Model):
    """Modelo para registrar conquistas relacionadas às metas, com foco na cooperação e aprendizagem social."""
    TIPOS_CONQUISTA = [
        ('tutoria', 'Tutoria e Interajuda'),
        ('partilha', 'Partilha de Recursos'),
        ('cooperacao', 'Trabalho Cooperativo'),
        ('comunicacao', 'Comunicação e Discussão'),
        ('gestao', 'Gestão Partilhada'),
        ('social', 'Responsabilidade Social'),
        ('inovacao', 'Inovação Colaborativa'),
        ('mediacao', 'Mediação e Resolução'),
    ]

    IMPACTO = [
        ('individual', 'Individual'),
        ('grupo', 'Grupo de Trabalho'),
        ('turma', 'Turma'),
        ('escola', 'Escola'),
        ('comunidade', 'Comunidade'),
    ]

    meta = models.ForeignKey(MetaAprendizagem, on_delete=models.CASCADE, related_name='conquistas')
    tipo = models.CharField(max_length=20, choices=TIPOS_CONQUISTA)
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    data = models.DateTimeField(auto_now_add=True)
    
    # Campos para dimensão cooperativa
    participantes = models.ManyToManyField(User, related_name='conquistas_meta_participacao')
    contribuicoes = models.TextField(help_text='Descreva as contribuições de cada participante')
    impacto = models.CharField(max_length=20, choices=IMPACTO)
    beneficiarios = models.TextField(help_text='Quem se beneficiou desta conquista?')
    
    # Campos para validação coletiva
    validadores = models.ManyToManyField(User, related_name='conquistas_meta_validadas', blank=True)
    feedback_comunidade = models.TextField(blank=True)
    reflexao_impacto = models.TextField(help_text='Reflexão sobre o impacto na comunidade')
    
    # Campos para evidências e celebração
    evidencias = models.FileField(upload_to='conquistas/', blank=True)
    links_relacionados = models.TextField(blank=True, help_text='Links para trabalhos, recursos ou projetos relacionados')
    momento_celebracao = models.DateTimeField(null=True, blank=True)
    
    # Campos para conexões e continuidade
    inspirou_outros = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='inspirado_por')
    proximos_passos = models.TextField(blank=True, help_text='Como esta conquista pode evoluir ou inspirar novas iniciativas?')
    
    class Meta:
        ordering = ['-data']
        verbose_name = 'Conquista de Meta'
        verbose_name_plural = 'Conquistas de Metas'
    
    def __str__(self):
        return f"{self.titulo} - {self.meta}"
    
    def validar(self, usuario, feedback=''):
        """Adiciona um validador à conquista."""
        if usuario not in self.validadores.all():
            self.validadores.add(usuario)
            if feedback:
                self.feedback_comunidade += f"\n\nValidação por {usuario.username}:\n{feedback}"
            self.save()
    
    def registrar_celebracao(self, data, descricao=''):
        """Registra um momento de celebração da conquista."""
        self.momento_celebracao = data
        if descricao:
            self.feedback_comunidade += f"\n\nCelebração em {data}:\n{descricao}"
        self.save()
    
    def adicionar_inspiracao(self, conquista_inspirada):
        """Adiciona uma conquista que foi inspirada por esta."""
        self.inspirou_outros.add(conquista_inspirada)

class ConquistaColetiva(models.Model):
    """Modelo para conquistas que envolvem cooperação e trabalho em grupo."""
    TIPOS_CONQUISTA = [
        ('tutoria', 'Tutoria e Interajuda'),
        ('partilha', 'Partilha de Recursos'),
        ('cooperacao', 'Trabalho Cooperativo'),
        ('comunicacao', 'Comunicação e Discussão'),
        ('gestao', 'Gestão Partilhada'),
        ('social', 'Responsabilidade Social'),
        ('inovacao', 'Inovação Colaborativa'),
        ('mediacao', 'Mediação e Resolução'),
    ]

    IMPACTO = [
        ('individual', 'Individual'),
        ('grupo', 'Grupo de Trabalho'),
        ('turma', 'Turma'),
        ('escola', 'Escola'),
        ('comunidade', 'Comunidade'),
    ]

    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS_CONQUISTA)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    # Relacionamentos
    criador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conquistas_criadas')
    turma = models.ForeignKey('Turma', on_delete=models.CASCADE, related_name='conquistas')
    participantes = models.ManyToManyField(User, related_name='conquistas_coletivas_participacao')
    aprendizagens = models.ManyToManyField('AprendizagemEssencial', related_name='conquistas')
    
    # Campos para dimensão cooperativa
    contribuicoes = models.TextField(help_text='Descreva as contribuições de cada participante')
    impacto = models.CharField(max_length=20, choices=IMPACTO)
    beneficiarios = models.TextField(help_text='Quem se beneficiou desta conquista?')
    
    # Campos para validação coletiva
    validadores = models.ManyToManyField(User, related_name='conquistas_coletivas_validadas', blank=True)
    feedback_comunidade = models.TextField(blank=True)
    reflexao_impacto = models.TextField(help_text='Reflexão sobre o impacto na comunidade')
    
    # Campos para evidências e celebração
    evidencias = models.FileField(upload_to='conquistas/', blank=True)
    links_relacionados = models.TextField(blank=True, help_text='Links para trabalhos, recursos ou projetos relacionados')
    momento_celebracao = models.DateTimeField(null=True, blank=True)
    
    # Campos para conexões e continuidade
    inspirou_outros = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='inspirado_por')
    proximos_passos = models.TextField(blank=True, help_text='Como esta conquista pode evoluir ou inspirar novas iniciativas?')
    
    class Meta:
        ordering = ['-data_criacao']
        verbose_name = 'Conquista Coletiva'
        verbose_name_plural = 'Conquistas Coletivas'
    
    def __str__(self):
        return self.titulo
    
    def validar(self, usuario, feedback=''):
        """Adiciona um validador à conquista."""
        if usuario not in self.validadores.all():
            self.validadores.add(usuario)
            if feedback:
                self.feedback_comunidade += f"\n\nValidação por {usuario.username}:\n{feedback}"
            self.save()
    
    def registrar_celebracao(self, data, descricao=''):
        """Registra um momento de celebração da conquista."""
        self.momento_celebracao = data
        if descricao:
            self.feedback_comunidade += f"\n\nCelebração em {data}:\n{descricao}"
        self.save()
    
    def adicionar_inspiracao(self, conquista_inspirada):
        """Adiciona uma conquista que foi inspirada por esta."""
        self.inspirou_outros.add(conquista_inspirada)
        self.save()

class ReconhecimentoContribuicao(models.Model):
    """Modelo para reconhecer contribuições individuais para a comunidade."""
    TIPOS_CONTRIBUICAO = [
        ('tutoria', 'Tutoria'),
        ('partilha', 'Partilha de Recursos'),
        ('organizacao', 'Organização de Atividades'),
        ('mediacao', 'Mediação'),
        ('inovacao', 'Inovação'),
        ('apoio', 'Apoio a Colegas'),
        ('lideranca', 'Liderança'),
        ('outro', 'Outro'),
    ]
    
    contribuidor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contribuicoes_reconhecidas')
    tipo = models.CharField(max_length=20, choices=TIPOS_CONTRIBUICAO)
    descricao = models.TextField()
    data_reconhecimento = models.DateTimeField(auto_now_add=True)
    
    # Relacionamentos
    reconhecido_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reconhecimentos_feitos')
    turma = models.ForeignKey('Turma', on_delete=models.CASCADE, related_name='reconhecimentos')
    conquista = models.ForeignKey(ConquistaColetiva, on_delete=models.CASCADE, related_name='reconhecimentos', null=True, blank=True)
    
    # Impacto e evidências
    impacto = models.TextField(help_text='Como esta contribuição impactou a comunidade?')
    evidencias = models.FileField(upload_to='reconhecimentos/', blank=True)
    
    class Meta:
        ordering = ['-data_reconhecimento']
        verbose_name = 'Reconhecimento de Contribuição'
        verbose_name_plural = 'Reconhecimentos de Contribuições'
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.contribuidor.get_full_name()}"

class ProjetoColaborativo(models.Model):
    """Modelo para projetos que envolvem trabalho cooperativo."""
    ESTADOS = [
        ('planeamento', 'Em Planeamento'),
        ('em_decorrer', 'Em Decorrer'),
        ('concluido', 'Concluído'),
        ('apresentado', 'Apresentado'),
    ]
    
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    objetivo = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='planeamento')
    data_inicio = models.DateField()
    data_fim_prevista = models.DateField()
    data_conclusao = models.DateField(null=True, blank=True)
    
    # Relacionamentos
    criador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projetos_criados')
    turma = models.ForeignKey('Turma', on_delete=models.CASCADE, related_name='projetos')
    participantes = models.ManyToManyField(User, related_name='projetos_participacao')
    aprendizagens = models.ManyToManyField('AprendizagemEssencial', related_name='projetos')
    
    # Campos para gestão colaborativa
    responsabilidades = models.TextField(help_text='Distribuição de responsabilidades entre os participantes')
    recursos_necessarios = models.TextField(blank=True)
    desafios = models.TextField(blank=True)
    solucoes = models.TextField(blank=True)
    
    # Resultados e avaliação
    resultados = models.TextField(blank=True)
    aprendizagens_alcancadas = models.TextField(blank=True)
    feedback_comunidade = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-data_inicio']
        verbose_name = 'Projeto Colaborativo'
        verbose_name_plural = 'Projetos Colaborativos'
    
    def __str__(self):
        return self.titulo

class CircuitoComunicacao(models.Model):
    """Modelo para circuitos de comunicação e partilha de ideias."""
    TIPOS = [
        ('debate', 'Debate'),
        ('apresentacao', 'Apresentação'),
        ('reflexao', 'Reflexão Coletiva'),
        ('feedback', 'Feedback Grupal'),
        ('planeamento', 'Planeamento Partilhado'),
    ]
    
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS)
    data_realizacao = models.DateTimeField()
    duracao = models.IntegerField(help_text='Duração em minutos')
    
    # Relacionamentos
    organizador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='circuitos_organizados')
    turma = models.ForeignKey('Turma', on_delete=models.CASCADE, related_name='circuitos')
    participantes = models.ManyToManyField(User, related_name='circuitos_participacao')
    aprendizagens = models.ManyToManyField('AprendizagemEssencial', related_name='circuitos')
    
    # Campos para documentação
    pontos_principais = models.TextField(blank=True)
    conclusoes = models.TextField(blank=True)
    acoes_decorrentes = models.TextField(blank=True)
    evidencias = models.FileField(upload_to='circuitos/', blank=True)
    
    class Meta:
        ordering = ['-data_realizacao']
        verbose_name = 'Circuito de Comunicação'
        verbose_name_plural = 'Circuitos de Comunicação'
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.titulo}"

class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    cor = models.CharField(max_length=7, default='#000000')  # Formato: #RRGGBB
    icone = models.CharField(max_length=50, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']

    def __str__(self):
        return self.nome

class Checklist(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    concluido = models.BooleanField(default=False)
    prioridade = models.IntegerField(default=0)  # 0: Baixa, 1: Média, 2: Alta

    class Meta:
        verbose_name = 'Checklist'
        verbose_name_plural = 'Checklists'
        ordering = ['-prioridade', 'data_criacao']

    def __str__(self):
        return self.titulo

    def calcular_progresso(self):
        total_itens = self.item_set.count()
        if total_itens == 0:
            return 0
        itens_concluidos = self.item_set.filter(concluido=True).count()
        return (itens_concluidos / total_itens) * 100

class Item(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE)
    texto = models.CharField(max_length=500)
    descricao = models.TextField(blank=True)
    concluido = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    ordem = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Itens'
        ordering = ['ordem', 'data_criacao']

    def __str__(self):
        return self.texto

class Meta(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    progresso = models.IntegerField(default=0)  # 0 a 100
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    checklist = models.ForeignKey(Checklist, on_delete=models.SET_NULL, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Meta'
        verbose_name_plural = 'Metas'
        ordering = ['-data_criacao']

    def __str__(self):
        return self.titulo

class ImportarAprendizagensForm(forms.Form):
    disciplina = forms.ModelChoiceField(
        queryset=Disciplina.objects.all(),
        label='Disciplina'
    )
    ano_escolar = forms.ChoiceField(
        choices=[(i, f'{i}º Ano') for i in range(1, 13)],
        label='Ano Escolar'
    )
    ficheiro_csv = forms.FileField(
        label='Ficheiro CSV',
        help_text='O ficheiro deve conter duas colunas: código da aprendizagem e descrição'
    )
