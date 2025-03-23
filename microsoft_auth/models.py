from django.db import models
from django.contrib.auth import get_user_model

class MicrosoftProfile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='microsoft_profile')
    microsoft_id = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Microsoft Profile" 