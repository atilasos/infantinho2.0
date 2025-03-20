from django.db import models
from django.conf import settings
from blog.models import Post

class ReadingQuestion(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reading_questions')
    question = models.TextField()
    answer = models.TextField()
    hints = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Pergunta para: {self.post.title}"

class ContentModeration(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='moderation')
    appropriate_language = models.BooleanField(default=False)
    educational_content = models.BooleanField(default=False)
    no_harmful_content = models.BooleanField(default=False)
    appropriate_complexity = models.BooleanField(default=False)
    moderated_at = models.DateTimeField(auto_now=True)
    moderated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Moderação para: {self.post.title}"

    @property
    def is_appropriate(self):
        return all([
            self.appropriate_language,
            self.educational_content,
            self.no_harmful_content,
            self.appropriate_complexity
        ])

class ContentEnhancement(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='enhancement')
    original_content = models.TextField()
    enhanced_content = models.TextField()
    target_age = models.PositiveIntegerField(default=8)
    enhanced_at = models.DateTimeField(auto_now=True)
    enhanced_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Melhorias para: {self.post.title}"

class AISuggestions(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='ai_suggestions')
    suggested_title = models.CharField(max_length=200, blank=True)
    suggested_introduction = models.TextField(blank=True)
    suggested_structure = models.JSONField(default=dict)  # Armazena a estrutura do artigo
    social_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Sugestões de IA para: {self.post.title}"

    class Meta:
        verbose_name = 'Sugestão de IA'
        verbose_name_plural = 'Sugestões de IA'
