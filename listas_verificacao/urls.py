from django.urls import path
from . import views

app_name = 'listas_verificacao'

urlpatterns = [
    path('', views.lista_aluno, name='lista_aluno'),
    path('registrar-progresso/<int:lista_id>/', views.registrar_progresso, name='registrar_progresso'),
    path('dashboard/professor/', views.dashboard_professor, name='dashboard_professor'),
    path('dashboard/turma/<int:turma_id>/', views.dashboard_turma, name='dashboard_turma'),
    path('turmas/', views.lista_turmas, name='lista_turmas'),
    path('turmas/criar/', views.criar_turma, name='criar_turma'),
    path('turmas/<int:turma_id>/editar/', views.editar_turma, name='editar_turma'),
    path('turmas/<int:turma_id>/excluir/', views.excluir_turma, name='excluir_turma'),
    path('turmas/<int:turma_id>/adicionar-aluno/', views.adicionar_aluno, name='adicionar_aluno'),
    path('turmas/<int:turma_id>/remover-aluno/<int:aluno_id>/', views.remover_aluno, name='remover_aluno'),
    path('objetivo/<int:objetivo_id>/atualizar-status/', views.atualizar_status_objetivo, name='atualizar_status'),
    path('objetivo/<int:objetivo_id>/', views.detalhe_objetivo, name='detalhe_objetivo'),
    path('categorias/', views.gerenciar_categorias, name='gerenciar_categorias'),
    path('categorias/<int:categoria_id>/editar/', views.editar_categoria, name='editar_categoria'),
    path('categorias/<int:categoria_id>/excluir/', views.excluir_categoria, name='excluir_categoria'),
    path('objetivos-predefinidos/', views.gerenciar_objetivos_predefinidos, name='gerenciar_objetivos_predefinidos'),
    path('objetivos-predefinidos/<int:objetivo_id>/editar/', views.editar_objetivo_predefinido, name='editar_objetivo_predefinido'),
    path('objetivos-predefinidos/<int:objetivo_id>/excluir/', views.excluir_objetivo_predefinido, name='excluir_objetivo_predefinido'),
    path('listas/criar/', views.criar_lista_verificacao, name='criar_lista_verificacao'),
    path('listas/<int:lista_id>/editar/', views.editar_lista_verificacao, name='editar_lista_verificacao'),
    path('listas/<int:lista_id>/excluir/', views.excluir_lista_verificacao, name='excluir_lista_verificacao'),
    path('aprendizagens/', views.gerenciar_aprendizagens, name='gerenciar_aprendizagens'),
    path('aprendizagens/importar/', views.importar_aprendizagens, name='importar_aprendizagens'),
    path('aprendizagens/<int:aprendizagem_id>/editar/', views.editar_aprendizagem, name='editar_aprendizagem'),
    path('aprendizagens/<int:aprendizagem_id>/excluir/', views.excluir_aprendizagem, name='excluir_aprendizagem'),
    path('notificacoes/', views.lista_notificacoes, name='lista_notificacoes'),
    path('notificacoes/<int:notificacao_id>/marcar-lida/', views.marcar_notificacao_lida, name='marcar_notificacao_lida'),
    path('notificacoes/configurar/', views.configurar_notificacoes, name='configurar_notificacoes'),
] 