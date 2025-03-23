from django.shortcuts import redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import MicrosoftProfile
from .backends import MicrosoftAuthenticationBackend
import requests
import json
import logging

logger = logging.getLogger(__name__)

def to_auth_redirect(request):
    """Redirect to Microsoft authentication."""
    auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    params = {
        'client_id': settings.MICROSOFT_AUTH_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': request.build_absolute_uri(reverse('microsoft:from_auth_redirect')),
        'scope': 'openid profile email',
        'response_mode': 'form_post',
    }
    return redirect(f"{auth_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}")

@csrf_exempt
def from_auth_redirect(request):
    """Handle the redirect from Microsoft authentication."""
    if request.method == 'POST':
        code = request.POST.get('code')
        if code:
            # Exchange code for token
            token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
            token_data = {
                'client_id': settings.MICROSOFT_AUTH_CLIENT_ID,
                'client_secret': settings.MICROSOFT_AUTH_CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': request.build_absolute_uri(reverse('microsoft:from_auth_redirect')),
            }
            token_response = requests.post(token_url, data=token_data)
            if token_response.status_code == 200:
                token_info = token_response.json()
                access_token = token_info.get('access_token')
                
                # Get user info
                user_info_url = "https://graph.microsoft.com/v1.0/me"
                headers = {'Authorization': f'Bearer {access_token}'}
                user_response = requests.get(user_info_url, headers=headers)
                if user_response.status_code == 200:
                    user_info = user_response.json()
                    
                    # Split display name into first and last name
                    display_name = user_info.get('displayName', '')
                    name_parts = display_name.split(' ', 1)
                    first_name = name_parts[0] if name_parts else ''
                    last_name = name_parts[1] if len(name_parts) > 1 else ''
                    
                    # Create or update user
                    User = get_user_model()
                    try:
                        user = User.objects.get(username=user_info['userPrincipalName'])
                        # Update names if they changed
                        user.first_name = first_name
                        user.last_name = last_name
                        user.save()
                    except User.DoesNotExist:
                        # Create new user with display name parts
                        user = User.objects.create(
                            username=user_info['userPrincipalName'],
                            email=user_info['userPrincipalName'],
                            first_name=first_name,
                            last_name=last_name
                        )
                    
                    # Create or update Microsoft profile
                    MicrosoftProfile.objects.update_or_create(
                        user=user,
                        defaults={
                            'microsoft_id': user_info.get('id', ''),
                            'email': user_info['userPrincipalName'],
                            'display_name': display_name
                        }
                    )
                    
                    # Log the user in using the Microsoft backend
                    user.backend = 'microsoft_auth.backends.MicrosoftAuthenticationBackend'
                    login(request, user)
                    
                    return redirect('/')
    
    return redirect('/')

def logout(request):
    """Logout the user."""
    auth_logout(request)
    return redirect('/') 