from django.urls import path
from . import views

app_name = 'microsoft'

urlpatterns = [
    path('to-auth-redirect/', views.to_auth_redirect, name='to_auth_redirect'),
    path('from-auth-redirect/', views.from_auth_redirect, name='from_auth_redirect'),
    path('logout/', views.logout, name='logout'),
] 