from django.contrib import admin
from .models import ListaVerificacao, Objetivo, Turma, ProgressoAluno

@admin.register(ListaVerificacao)
class ListaVerificacaoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'turma', 'data_criacao', 'data_atualizacao')
    list_filter = ('turma', 'data_criacao')
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
    list_display = ('aluno', 'lista_verificacao', 'get_porcentagem_conclusao', 'data_atualizacao')
    list_filter = ('aluno', 'lista_verificacao', 'data_atualizacao')
    search_fields = ('aluno__username', 'aluno__first_name', 'aluno__last_name', 'lista_verificacao__titulo')
    date_hierarchy = 'data_atualizacao'
    
    def get_porcentagem_conclusao(self, obj):
        return f'{obj.porcentagem_conclusao:.1f}%'
    get_porcentagem_conclusao.short_description = 'Progresso'
