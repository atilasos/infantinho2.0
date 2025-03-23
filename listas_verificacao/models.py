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

class ListaVerificacao(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    turma = models.ForeignKey('Turma', on_delete=models.CASCADE, related_name='listas_verificacao', null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    objetivos_predefinidos = models.ManyToManyField(ObjetivoPredefinido, related_name='listas_verificacao', blank=True)
    
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
        ('validado', 'Validado'),
    ]

    aluno = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progressos')
    lista_verificacao = models.ForeignKey(ListaVerificacao, on_delete=models.CASCADE, related_name='progressos')
    objetivos_estado = models.JSONField(default=dict)  # {objetivo_id: estado}
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['aluno', 'lista_verificacao']
        verbose_name = 'Progresso do Aluno'
        verbose_name_plural = 'Progressos dos Alunos'
    
    def __str__(self):
        return f'Progresso de {self.aluno.get_full_name()} em {self.lista_verificacao.titulo}'
    
    @property
    def porcentagem_conclusao(self):
        """Retorna a porcentagem de objetivos concluídos"""
        total_objetivos = self.lista_verificacao.objetivos.count()
        if total_objetivos == 0:
            return 0
        objetivos_concluidos = sum(1 for estado in self.objetivos_estado.values() if estado == 'concluido')
        return (objetivos_concluidos / total_objetivos) * 100

    def get_estado_objetivo(self, objetivo_id):
        """Retorna o estado atual de um objetivo"""
        return self.objetivos_estado.get(str(objetivo_id), 'nao_iniciado')

    def set_estado_objetivo(self, objetivo_id, estado):
        """Define o estado de um objetivo"""
        if estado in dict(self.ESTADOS):
            self.objetivos_estado[str(objetivo_id)] = estado
            self.save()
            return True
        return False
