from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

class MicrosoftAuthenticationBackend(ModelBackend):
    """
    Authentication backend for Microsoft OAuth2.
    """
    def authenticate(self, request, token=None, **kwargs):
        """
        Authenticate a user based on the Microsoft OAuth2 token.
        """
        if not token:
            return None

        UserModel = get_user_model()
        
        try:
            # O usuário já deve ter sido criado pela view from_auth_redirect
            return UserModel.objects.get(username=token.get('userPrincipalName'))
        except UserModel.DoesNotExist:
            return None

    def get_user(self, user_id):
        """
        Get a user by their ID.
        """
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None 