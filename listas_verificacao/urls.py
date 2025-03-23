from django.urls import path
from . import views

app_name = 'listas_verificacao'

urlpatterns = [
    path('', views.lista_objetivos, name='lista_objetivos'),
    path('aluno/', views.lista_aluno, name='lista_aluno'),
    path('objetivo/<int:pk>/', views.detalhe_objetivo, name='detalhe_objetivo'),
    path('objetivo/<int:pk>/atualizar-status/', views.atualizar_status, name='atualizar_status'),
    path('objetivo/<int:pk>/registrar-avaliacao/', views.registrar_avaliacao, name='registrar_avaliacao'),
    path('objetivo/<int:objetivo_id>/', views.detalhe_objetivo, name='detalhe_objetivo'),
    path('objetivo/<int:objetivo_id>/atualizar-status/', views.atualizar_status, name='atualizar_status'),
    path('objetivo/<int:objetivo_id>/registrar-avaliacao/', views.registrar_avaliacao, name='registrar_avaliacao'),
    path('dashboard/', views.dashboard_professor, name='dashboard_professor'),
    path('turmas/', views.lista_turmas, name='lista_turmas'),
    path('turmas/criar/', views.criar_turma, name='criar_turma'),
    path('turmas/<int:turma_id>/', views.gerenciar_turma, name='gerenciar_turma'),
    path('turmas/<int:turma_id>/dashboard/', views.dashboard_turma, name='dashboard_turma'),
] 