from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
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
