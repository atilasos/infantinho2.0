from django.urls import path
from . import views

app_name = 'ai_core'

urlpatterns = [
    path('generate-suggestions/', views.generate_suggestions, name='generate_suggestions'),
    path('enhance-content/', views.enhance_content, name='enhance_content'),
    path('moderate-content/', views.moderate_content, name='moderate_content'),
    # URLs específicas do app ai_core podem ser adicionadas aqui
] 