from django.urls import path
from . import views

app_name = 'personalizacao'

urlpatterns = [
    # URLs para Temas
    path('temas/', views.lista_temas, name='lista_temas'),
    path('temas/criar/', views.criar_tema, name='criar_tema'),
    path('temas/<int:tema_id>/editar/', views.editar_tema, name='editar_tema'),
    path('temas/<int:tema_id>/excluir/', views.excluir_tema, name='excluir_tema'),
    
    # URLs para Layouts
    path('layouts/', views.lista_layouts, name='lista_layouts'),
    path('layouts/criar/', views.criar_layout, name='criar_layout'),
    path('layouts/<int:layout_id>/editar/', views.editar_layout, name='editar_layout'),
    path('layouts/<int:layout_id>/excluir/', views.excluir_layout, name='excluir_layout'),
    
    # URLs para Widgets
    path('widgets/', views.lista_widgets, name='lista_widgets'),
    path('widgets/criar/', views.criar_widget, name='criar_widget'),
    path('widgets/<int:widget_id>/editar/', views.editar_widget, name='editar_widget'),
    path('widgets/<int:widget_id>/excluir/', views.excluir_widget, name='excluir_widget'),
    
    # URL para Preferências do Usuário
    path('preferencias/', views.preferencias_usuario, name='preferencias_usuario'),
] 