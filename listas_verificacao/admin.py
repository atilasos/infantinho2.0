from django.contrib import admin
from .models import (
    ListaVerificacao, Objetivo, Turma, ProgressoAluno,
    Disciplina, Domínio, Subdomínio, AprendizagemEssencial
)

@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome')
    search_fields = ('codigo', 'nome')

@admin.register(Domínio)
class DominioAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'disciplina', 'ordem')
    list_filter = ('disciplina',)
    search_fields = ('codigo', 'nome')
    ordering = ('disciplina', 'ordem')

@admin.register(Subdomínio)
class SubdominioAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'dominio', 'ordem')
    list_filter = ('dominio',)
    search_fields = ('codigo', 'nome')
    ordering = ('dominio', 'ordem')

@admin.register(AprendizagemEssencial)
class AprendizagemEssencialAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descricao', 'disciplina', 'dominio', 'ano_escolar', 'ordem')
    list_filter = ('disciplina', 'dominio', 'ano_escolar')
    search_fields = ('codigo', 'descricao')
    ordering = ('disciplina', 'ano_escolar', 'ordem')

@admin.register(ListaVerificacao)
class ListaVerificacaoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'turma', 'disciplina', 'ano_escolar', 'data_criacao', 'data_atualizacao')
    list_filter = ('turma', 'disciplina', 'ano_escolar', 'data_criacao')
    search_fields = ('titulo', 'descricao')
    date_hierarchy = 'data_criacao'

@admin.register(Objetivo)
class ObjetivoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'lista_verificacao', 'ordem')
    list_filter = ('lista_verificacao',)
    search_fields = ('titulo', 'descricao')
    ordering = ('lista_verificacao', 'ordem')

@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'professor', 'get_alunos_count', 'data_criacao')
    list_filter = ('professor', 'data_criacao')
    search_fields = ('nome', 'professor__username', 'professor__first_name', 'professor__last_name')
    filter_horizontal = ('alunos',)
    date_hierarchy = 'data_criacao'
    
    def get_alunos_count(self, obj):
        return obj.alunos.count()
    get_alunos_count.short_description = 'Número de Alunos'

@admin.register(ProgressoAluno)
class ProgressoAlunoAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'lista_verificacao', 'aprendizagem', 'estado', 'data_atualizacao')
    list_filter = ('estado', 'data_atualizacao')
    search_fields = ('aluno__username', 'aprendizagem__codigo')
    ordering = ('-data_atualizacao',)
