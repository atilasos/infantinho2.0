from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinLengthValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.html import mark_safe
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from taggit.managers import TaggableManager

User = get_user_model()

class Category(models.Model):
    """Categoria de um post."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('admin', 'Administrador'),
        ('teacher', 'Professor'),
        ('student', 'Aluno'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_user_type_display()})"

    class Meta:
        verbose_name = 'Perfil de Utilizador'
        verbose_name_plural = 'Perfis de Utilizadores'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Cria um perfil de usuário quando um novo usuário é criado"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Salva o perfil do usuário quando o usuário é salvo"""
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)

class Class(models.Model):
    name = models.CharField(max_length=100)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='classes_taught')
    students = models.ManyToManyField(User, related_name='classes_enrolled', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.teacher.get_full_name()}"

    class Meta:
        verbose_name = 'Turma'
        verbose_name_plural = 'Turmas'

class Post(models.Model):
    """Post do blog."""
    STATUS_CHOICES = (
        ('draft', 'Rascunho'),
        ('published', 'Publicado'),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    content = models.TextField()
    excerpt = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts')
    tags = TaggableManager()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    dislikes = models.ManyToManyField(User, related_name='disliked_posts', blank=True)
    views = models.PositiveIntegerField(default=0)
    class_group = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    dislikes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=200, blank=True)
    is_featured = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:post_detail', args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def can_edit(self, user):
        return user == self.author or user.profile.user_type == 'admin'

    def can_approve(self, user):
        return user.profile.user_type in ['admin', 'teacher'] and self.status == 'pending'

    def can_delete(self, user):
        return user == self.author or user.profile.user_type == 'admin'

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def dislikes_count(self):
        return self.dislikes.count()

    @property
    def comments_count(self):
        return self.comments.filter(active=True).count()

class Comment(models.Model):
    """Comentário em um post."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comentário de {self.author.username} em {self.post.title}'

    def get_absolute_url(self):
        return f"{self.post.get_absolute_url()}#comment-{self.id}"

class PostReaction(models.Model):
    REACTION_CHOICES = [
        ('like', _('Like')),
        ('love', _('Love')),
        ('laugh', _('Laugh')),
        ('wow', _('Wow')),
        ('sad', _('Sad')),
        ('angry', _('Angry')),
    ]

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_reactions')
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['post', 'user']

    def __str__(self):
        return f'{self.user.username} reacted {self.reaction} to {self.post.title}'
