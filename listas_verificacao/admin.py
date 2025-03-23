from django.contrib import admin
from .models import DominioAprendizagem, ObjetivoAprendizagem, StatusObjetivo, RegistroAvaliacao

@admin.register(DominioAprendizagem)
class DominioAprendizagemAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome')
    search_fields = ('codigo', 'nome')
    ordering = ('codigo',)

@admin.register(ObjetivoAprendizagem)
class ObjetivoAprendizagemAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'dominio', 'ano_escolar', 'disciplina', 'ordem')
    list_filter = ('dominio', 'ano_escolar', 'disciplina')
    search_fields = ('codigo', 'descricao')
    ordering = ('dominio', 'ordem')

@admin.register(StatusObjetivo)
class StatusObjetivoAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'objetivo', 'status', 'data_atualizacao', 'validado_por')
    list_filter = ('status', 'objetivo__dominio', 'objetivo__ano_escolar', 'validado_por')
    search_fields = ('aluno__username', 'objetivo__codigo', 'objetivo__descricao')
    ordering = ('-data_atualizacao',)

@admin.register(RegistroAvaliacao)
class RegistroAvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('status_objetivo', 'avaliador', 'resultado', 'data_avaliacao')
    list_filter = ('resultado', 'avaliador', 'data_avaliacao')
    search_fields = ('status_objetivo__aluno__username', 'status_objetivo__objetivo__codigo')
    ordering = ('-data_avaliacao',)
