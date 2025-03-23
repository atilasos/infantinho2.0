from django.conf import settings

def microsoft(request):
    """Add Microsoft Auth related context variables to the context."""
    return {
        'microsoft_login_enabled': True,
        'microsoft_client_id': settings.MICROSOFT_AUTH_CLIENT_ID,
        'microsoft_login_type': settings.MICROSOFT_AUTH_LOGIN_TYPE,
    } 