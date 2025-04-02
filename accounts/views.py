from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.backends import ModelBackend

# Create your views here.

class DemoAuthenticationBackend(ModelBackend):
    """
    Authentication backend specifically for demo accounts.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
            
        # Only authenticate users that start with 'prof.' or 'aluno'
        if not (username.startswith('prof.') or username.startswith('aluno')):
            return None
            
        return super().authenticate(request, username=username, password=password, **kwargs)

def demo_login(request):
    """View for demo login."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Specify the authentication backend
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Login realizado com sucesso!')
            return redirect('blog:post_list')
        else:
            messages.error(request, 'Usuário ou senha incorretos.')
    
    return render(request, 'account/demo_login.html')
