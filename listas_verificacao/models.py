from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

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
