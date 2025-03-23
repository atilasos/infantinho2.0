from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db import transaction
from django.db.models import ProtectedError
from .models import Category, Post, Comment, UserProfile, Class, PostReaction
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
    list_display = ('name', 'slug', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'created_at', 'published_at')
    list_filter = ('status', 'created_at', 'published_at', 'author')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author',)
    date_hierarchy = 'published_at'
    ordering = ('-created_at',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'created_at', 'active')
    list_filter = ('active', 'created_at', 'updated_at')
    search_fields = ('content', 'author__username', 'post__title')
    raw_id_fields = ('author', 'post')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'created_at')
    list_filter = ('user_type', 'created_at')
    search_fields = ('user__username', 'bio')
    raw_id_fields = ('user',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'teacher__username')
    raw_id_fields = ('teacher',)
    filter_horizontal = ('students',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(PostReaction)
class PostReactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'reaction', 'created_at')
    list_filter = ('reaction', 'created_at')
    search_fields = ('user__username', 'post__title')
    raw_id_fields = ('user', 'post')
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
                UserProfile.objects.filter(user=obj).delete()
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
