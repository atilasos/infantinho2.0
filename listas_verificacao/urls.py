from django.urls import path
from . import views

app_name = 'listas_verificacao'

urlpatterns = [
    path('dashboard/', views.dashboard_professor, name='dashboard_professor'),
    path('', views.lista_checklists, name='lista_checklists'),
    path('criar/', views.criar_checklist, name='criar_checklist'),
    path('lista/criar/', views.criar_checklist, name='criar_lista_verificacao'),
    path('<int:checklist_id>/', views.detalhe_checklist, name='detalhe_checklist'),
    path('<int:checklist_id>/editar/', views.editar_checklist, name='editar_checklist'),
    path('<int:checklist_id>/excluir/', views.excluir_checklist, name='excluir_checklist'),
    path('<int:checklist_id>/itens/', views.lista_itens, name='lista_itens'),
    path('<int:checklist_id>/itens/criar/', views.criar_item, name='criar_item'),
    path('itens/<int:item_id>/editar/', views.editar_item, name='editar_item'),
    path('itens/<int:item_id>/excluir/', views.excluir_item, name='excluir_item'),
    path('itens/<int:item_id>/marcar/', views.marcar_item, name='marcar_item'),
    path('itens/<int:item_id>/desmarcar/', views.desmarcar_item, name='desmarcar_item'),
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/criar/', views.criar_categoria, name='criar_categoria'),
    path('categorias/<int:categoria_id>/editar/', views.editar_categoria, name='editar_categoria'),
    path('categorias/<int:categoria_id>/excluir/', views.excluir_categoria, name='excluir_categoria'),
    path('metas/', views.lista_metas, name='lista_metas'),
    path('metas/criar/', views.criar_meta, name='criar_meta'),
    path('metas/<int:meta_id>/excluir/', views.excluir_meta, name='excluir_meta'),
    path('turmas/', views.lista_turmas, name='lista_turmas'),
    path('turmas/criar/', views.criar_turma, name='criar_turma'),
    path('turmas/<int:turma_id>/editar/', views.editar_turma, name='editar_turma'),
    path('turmas/<int:turma_id>/excluir/', views.excluir_turma, name='excluir_turma'),
    path('turmas/<int:turma_id>/dashboard/', views.dashboard_turma, name='dashboard_turma'),
    path('turmas/<int:turma_id>/adicionar-aluno/', views.adicionar_aluno, name='adicionar_aluno'),
    path('aprendizagens/', views.gerenciar_aprendizagens, name='gerenciar_aprendizagens'),
    path('aprendizagens/criar/', views.criar_aprendizagem, name='criar_aprendizagem'),
    path('aprendizagens/importar/', views.importar_aprendizagens, name='importar_aprendizagens'),
    path('aprendizagens/<int:aprendizagem_id>/editar/', views.editar_aprendizagem, name='editar_aprendizagem'),
    path('aprendizagens/<int:aprendizagem_id>/excluir/', views.excluir_aprendizagem, name='excluir_aprendizagem'),
    path('notificacoes/', views.lista_notificacoes, name='lista_notificacoes'),
    path('notificacoes/configurar/', views.configurar_notificacoes, name='configurar_notificacoes'),
    path('notificacoes/<int:notificacao_id>/marcar-lida/', views.marcar_notificacao_lida, name='marcar_notificacao_lida'),
    
    # URLs para relatórios e visualizações
    path('turmas/<int:turma_id>/relatorio-progresso/', views.relatorio_progresso_turma, name='relatorio_progresso_turma'),
    path('turmas/<int:turma_id>/relatorio-tempo/', views.relatorio_tempo_conclusao, name='relatorio_tempo_conclusao'),
    path('turmas/<int:turma_id>/relatorio-dificuldades/', views.relatorio_objetivos_dificeis, name='relatorio_objetivos_dificeis'),
    path('turmas/<int:turma_id>/relatorio-pendencias/', views.relatorio_aprendizagens_pendentes, name='relatorio_aprendizagens_pendentes'),
    path('turmas/<int:turma_id>/relatorio-tendencias/', views.relatorio_tendencias_progresso, name='relatorio_tendencias_progresso'),
    path('turmas/<int:turma_id>/relatorio-preditivo/', views.relatorio_analise_preditiva, name='relatorio_analise_preditiva'),
    path('turmas/<int:turma_id>/relatorio-engajamento/', views.relatorio_engajamento, name='relatorio_engajamento'),
    path('turmas/<int:turma_id>/relatorio-cooperacao/', views.relatorio_cooperacao, name='relatorio_cooperacao'),
    path('turmas/<int:turma_id>/visualizacao-progresso/', views.visualizacao_progresso_turma, name='visualizacao_progresso_turma'),
    path('turmas/<int:turma_id>/visualizacao-heatmap/', views.visualizacao_heatmap_atividade, name='visualizacao_heatmap_atividade'),
    path('turmas/<int:turma_id>/visualizacao-tendencias/', views.visualizacao_tendencias, name='visualizacao_tendencias'),
    path('turmas/<int:turma_id>/dashboard-interativo/', views.dashboard_interativo, name='dashboard_interativo'),
    
    # URLs para relatórios de alunos
    path('turmas/<int:turma_id>/alunos/<int:aluno_id>/relatorio-progresso/', views.relatorio_progresso_aluno, name='relatorio_progresso_aluno'),
    path('turmas/<int:turma_id>/alunos/<int:aluno_id>/relatorio-dificuldades/', views.relatorio_dificuldades_aluno, name='relatorio_dificuldades_aluno'),
    path('turmas/<int:turma_id>/alunos/<int:aluno_id>/remover/', views.remover_aluno, name='remover_aluno'),
    
    # URLs para listas de verificação
    path('lista/<int:lista_id>/editar/', views.editar_checklist, name='editar_lista_verificacao'),
    path('lista/<int:lista_id>/excluir/', views.excluir_checklist, name='excluir_lista_verificacao'),
    path('lista/<int:lista_id>/registrar-progresso/', views.registrar_progresso, name='registrar_progresso'),
    path('aluno/minhas-aprendizagens/', views.lista_aluno, name='lista_aluno'),

    # Sistema de Dúvidas
    path('duvidas/', views.lista_duvidas, name='lista_duvidas'),
    path('duvidas/criar/', views.criar_duvida, name='criar_duvida'),
    path('duvidas/<int:duvida_id>/', views.detalhe_duvida, name='detalhe_duvida'),
    path('duvidas/<int:duvida_id>/responder/', views.responder_duvida, name='responder_duvida'),
    path('duvidas/respostas/<int:resposta_id>/marcar-melhor/', views.marcar_melhor_resposta, name='marcar_melhor_resposta'),
    path('duvidas/<int:duvida_id>/atualizar-estado/', views.atualizar_estado_duvida, name='atualizar_estado_duvida'),
    path('turmas/<int:turma_id>/duvidas/', views.lista_duvidas_turma, name='lista_duvidas_turma'),

    # Diário de Aprendizagem
    path('diario/', views.lista_diarios, name='lista_diarios'),
    path('diario/criar/', views.criar_diario, name='criar_diario'),
    path('diario/<int:diario_id>/', views.detalhe_diario, name='detalhe_diario'),
    path('diario/<int:diario_id>/entrada/criar/', views.criar_entrada, name='criar_entrada'),
    path('diario/entrada/<int:entrada_id>/comentar/', views.adicionar_comentario_entrada, name='adicionar_comentario_entrada'),
    path('diario/entrada/<int:entrada_id>/conexao/', views.adicionar_conexao, name='adicionar_conexao'),
    path('diario/<int:diario_id>/toggle-partilha/', views.toggle_partilha, name='toggle_partilha'),

    # Metas e Conquistas
    path('metas/<int:meta_id>/', views.detalhe_meta, name='detalhe_meta'),
    path('metas/<int:meta_id>/alteracao/', views.solicitar_alteracao_meta, name='solicitar_alteracao_meta'),
    path('metas/<int:meta_id>/reflexao/', views.adicionar_reflexao, name='adicionar_reflexao'),
    path('metas/<int:meta_id>/acompanhamento/', views.adicionar_acompanhamento, name='adicionar_acompanhamento'),
    path('metas/<int:meta_id>/conquista/', views.registrar_conquista, name='registrar_conquista'),

    # Conquistas
    path('conquistas/', views.lista_conquistas, name='lista_conquistas'),
    path('conquistas/criar/', views.criar_conquista, name='criar_conquista'),
    path('conquistas/<int:conquista_id>/', views.detalhe_conquista, name='detalhe_conquista'),
    path('conquistas/<int:conquista_id>/validar/', views.validar_conquista, name='validar_conquista'),
    path('conquistas/reconhecimento/', views.registrar_reconhecimento, name='registrar_reconhecimento'),
    path('conquistas/<int:conquista_id>/reflexao/', views.adicionar_reflexao_conquista, name='adicionar_reflexao_conquista'),

    # Projetos
    path('projetos/', views.lista_projetos, name='lista_projetos'),
    path('projetos/criar/', views.criar_projeto, name='criar_projeto'),
    path('projetos/<int:projeto_id>/', views.detalhe_projeto, name='detalhe_projeto'),

    # Circuitos de Comunicação
    path('circuitos/', views.lista_circuitos, name='lista_circuitos'),
    path('circuitos/criar/', views.criar_circuito, name='criar_circuito'),
    path('circuitos/<int:circuito_id>/', views.detalhe_circuito, name='detalhe_circuito'),

    # Avaliação e Confirmação
    path('progresso/<int:progresso_id>/avaliar/', views.avaliar_aprendizagem, name='avaliar_aprendizagem'),
    path('progresso/<int:progresso_id>/comentar/', views.adicionar_comentario, name='adicionar_comentario'),
    path('progresso/<int:progresso_id>/detalhe/', views.detalhe_aprendizagem, name='detalhe_aprendizagem'),

    path('turma/<int:turma_id>/dados/', views.get_turma_dados, name='get_turma_dados'),
] 