from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # URLs específicas do app accounts podem ser adicionadas aqui
    path('demo-login/', views.demo_login, name='demo_login'),
] 