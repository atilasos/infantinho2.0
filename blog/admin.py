from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db import transaction
from django.db.models import ProtectedError
from .models import Category, Post, Comment, Class, PostReaction
from django.utils.html import mark_safe
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from ai_core.services import OllamaService
from taggit.admin import TagAdmin
from taggit.models import Tag
from microsoft_auth.models import MicrosoftProfile

User = get_user_model()
ollama_service = OllamaService()

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    filter_horizontal = ('students',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'class_group', 'status', 'created_at', 'published_at')
    list_filter = ('status', 'category', 'class_group', 'created_at', 'published_at')
    search_fields = ('title', 'content', 'author__username', 'author__first_name', 'author__last_name')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    filter_horizontal = ('likes',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'status', 'created_at', 'moderated_at')
    list_filter = ('status', 'created_at', 'moderated_at')
    search_fields = ('content', 'author__username', 'post__title')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(PostReaction)
class PostReactionAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'reaction', 'created_at')
    list_filter = ('reaction', 'created_at')
    search_fields = ('post__title', 'user__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

class CustomUserAdmin(BaseUserAdmin):
    def delete_model(self, request, obj):
        try:
            with transaction.atomic():
                # Clear many-to-many relationships first
                obj.classes_enrolled.clear()
                obj.liked_posts.clear()
                obj.disliked_posts.clear()
                obj.turmas_aluno.clear()
                
                # Delete related profiles using filter
                MicrosoftProfile.objects.filter(user=obj).delete()
                
                # Delete the user last
                obj.delete()
        except ProtectedError as e:
            # Handle protected foreign key error
            raise ProtectedError(
                f"Cannot delete user because they have related protected objects: {e.protected_objects}",
                e.protected_objects
            )
        except Exception as e:
            # Re-raise any other exception
            raise e

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.delete_model(request, obj)

# Unregister the default UserAdmin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
