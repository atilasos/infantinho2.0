"""
URL configuration for infantinho project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView
from django.contrib.auth import views as auth_views
from allauth.account import views as allauth_views

urlpatterns = [
    # URL padrão que redireciona para a página de blog em vez da página de login
    path('', RedirectView.as_view(url='/blog/', permanent=False), name='home'),
    
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),  # URLs do django-allauth
    path('accounts/', include('accounts.urls')),
    path('pit/', include('pit.urls')),
    path('tea/', include('tea.urls')),
    path('gestao-cooperada/', include('gestao_cooperada.urls')),
    path('khanmigo/', include('khanmigo_clone.urls')),
    path('blog/', include('blog.urls')),
    path('ai/', include('ai_core.urls')),
    path('microsoft/', include('microsoft_auth.urls', namespace='microsoft')),
    path('listas-verificacao/', include('listas_verificacao.urls', namespace='listas_verificacao')),  # Learning checklists URLs
    path('exportacao-backup/', include('exportacao_backup.urls')),
    path('personalizacao/', include('personalizacao.urls')),
]

# Adiciona as URLs do Debug Toolbar em ambiente de desenvolvimento
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

# Adiciona as URLs de arquivos de mídia em ambiente de desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
