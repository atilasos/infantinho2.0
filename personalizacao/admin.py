from django.contrib import admin
from .models import Tema, Layout, Widget, DashboardUsuario, WidgetDashboard, PreferenciaUsuario

@admin.register(Tema)
class TemaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'data_criacao', 'data_atualizacao')
    list_filter = ('ativo',)
    search_fields = ('nome', 'descricao')
    readonly_fields = ('data_criacao', 'data_atualizacao')

@admin.register(Layout)
class LayoutAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'data_criacao', 'data_atualizacao')
    list_filter = ('ativo',)
    search_fields = ('nome', 'descricao')
    readonly_fields = ('data_criacao', 'data_atualizacao')

@admin.register(Widget)
class WidgetAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'ativo', 'data_criacao', 'data_atualizacao')
    list_filter = ('tipo', 'ativo')
    search_fields = ('nome', 'descricao')
    readonly_fields = ('data_criacao', 'data_atualizacao')

@admin.register(DashboardUsuario)
class DashboardUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'data_criacao', 'data_atualizacao')
    search_fields = ('usuario__username', 'usuario__email')
    readonly_fields = ('data_criacao', 'data_atualizacao')

@admin.register(WidgetDashboard)
class WidgetDashboardAdmin(admin.ModelAdmin):
    list_display = ('dashboard', 'widget', 'posicao_x', 'posicao_y', 'ativo', 'data_atualizacao')
    list_filter = ('ativo', 'widget__tipo')
    search_fields = ('dashboard__usuario__username', 'widget__nome')
    readonly_fields = ('data_criacao', 'data_atualizacao')

@admin.register(PreferenciaUsuario)
class PreferenciaUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tema', 'layout', 'tamanho_fonte', 'idioma', 'data_atualizacao')
    list_filter = ('tamanho_fonte', 'idioma', 'alto_contraste', 'reducao_movimento')
    search_fields = ('usuario__username', 'usuario__email')
    readonly_fields = ('data_criacao', 'data_atualizacao')
