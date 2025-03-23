from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class DominioAprendizagem(models.Model):
    """Modelo para representar os domínios de aprendizagem (OC, OE, L, EL, E, G)"""
    codigo = models.CharField(max_length=10, unique=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"

    class Meta:
        verbose_name = "Domínio de Aprendizagem"
        verbose_name_plural = "Domínios de Aprendizagem"

class ObjetivoAprendizagem(models.Model):
    """Modelo para representar os objetivos de aprendizagem específicos"""
    dominio = models.ForeignKey(DominioAprendizagem, on_delete=models.CASCADE, related_name='objetivos')
    codigo = models.CharField(max_length=10)
    descricao = models.TextField()
    ano_escolar = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    disciplina = models.CharField(max_length=50)
    ordem = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.codigo} - {self.descricao[:50]}..."

    class Meta:
        verbose_name = "Objetivo de Aprendizagem"
        verbose_name_plural = "Objetivos de Aprendizagem"
        unique_together = ['codigo', 'ano_escolar', 'disciplina']
        ordering = ['dominio', 'ordem']

class Turma(models.Model):
    nome = models.CharField(max_length=100)
    professor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='turmas')
    ano_escolar = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    disciplina = models.CharField(max_length=50)
    alunos = models.ManyToManyField(User, related_name='turmas_aluno', blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    ativa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome} - {self.ano_escolar}º Ano - {self.disciplina}"

    class Meta:
        verbose_name = "Turma"
        verbose_name_plural = "Turmas"
        unique_together = ['nome', 'professor', 'ano_escolar', 'disciplina']

class StatusObjetivo(models.Model):
    """Modelo para representar o status de um objetivo para um aluno específico"""
    STATUS_CHOICES = [
        ('nao_iniciado', 'Não Iniciado'),
        ('em_progresso', 'Em Progresso'),
        ('concluido', 'Concluído'),
        ('validado', 'Validado'),
    ]
    
    aluno = models.ForeignKey(User, on_delete=models.CASCADE, related_name='status_objetivos')
    objetivo = models.ForeignKey(ObjetivoAprendizagem, on_delete=models.CASCADE, related_name='status_alunos')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='nao_iniciado')
    data_atualizacao = models.DateTimeField(auto_now=True)
    observacoes = models.TextField(blank=True)
    validado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='validacoes')
    data_validacao = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.aluno.username} - {self.objetivo.codigo} - {self.get_status_display()}"

    class Meta:
        verbose_name = "Status do Objetivo"
        verbose_name_plural = "Status dos Objetivos"
        unique_together = ['aluno', 'objetivo']

class RegistroAvaliacao(models.Model):
    """Modelo para registrar avaliações específicas de um objetivo"""
    status_objetivo = models.ForeignKey(StatusObjetivo, on_delete=models.CASCADE, related_name='avaliacoes')
    avaliador = models.ForeignKey(User, on_delete=models.CASCADE)
    data_avaliacao = models.DateTimeField(auto_now_add=True)
    resultado = models.BooleanField()
    comentarios = models.TextField(blank=True)
    evidencias = models.TextField(blank=True)
    
    def __str__(self):
        return f"Avaliação de {self.status_objetivo.aluno.username} - {self.status_objetivo.objetivo.codigo}"

    class Meta:
        verbose_name = "Registro de Avaliação"
        verbose_name_plural = "Registros de Avaliação"
        ordering = ['-data_avaliacao']
