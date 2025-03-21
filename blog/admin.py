from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from .models import Category, Post, Comment, PostReaction, UserProfile, Class
from ai_core.services import OllamaService
from taggit.admin import TagAdmin
from taggit.models import Tag

ollama_service = OllamaService()

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'created_at', 'views_count')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    filter_horizontal = ('likes', 'dislikes')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'content', 'excerpt')
        }),
        ('Media', {
            'fields': ('featured_image',)
        }),
        ('Organization', {
            'fields': ('category', 'tags')
        }),
        ('Publishing', {
            'fields': ('status', 'published_at', 'is_featured')
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords')
        }),
        ('Settings', {
            'fields': ('allow_comments',)
        }),
        ('Statistics', {
            'fields': ('views_count', 'likes_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:post_id>/enhance/',
                self.admin_site.admin_view(self.enhance_post),
                name='post-enhance',
            ),
            path(
                '<int:post_id>/moderate/',
                self.admin_site.admin_view(self.moderate_post),
                name='post-moderate',
            ),
            path(
                '<int:post_id>/generate-questions/',
                self.admin_site.admin_view(self.generate_questions),
                name='post-generate-questions',
            ),
        ]
        return custom_urls + urls

    def enhance_post(self, request, post_id):
        post = self.get_object(request, post_id)
        try:
            enhanced_content = ollama_service.enhance_content(post.content)
            post.content = enhanced_content
            post.save()
            messages.success(request, 'Conteúdo melhorado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao melhorar o conteúdo: {str(e)}')
        return redirect('admin:blog_post_change', post_id)

    def moderate_post(self, request, post_id):
        post = self.get_object(request, post_id)
        try:
            moderation_result = ollama_service.moderate_content(post.content)
            if all(moderation_result.values()):
                messages.success(request, 'Conteúdo aprovado para crianças!')
            else:
                messages.warning(request, 'Conteúdo pode precisar de revisão.')
        except Exception as e:
            messages.error(request, f'Erro ao moderar o conteúdo: {str(e)}')
        return redirect('admin:blog_post_change', post_id)

    def generate_questions(self, request, post_id):
        post = self.get_object(request, post_id)
        try:
            questions = ollama_service.generate_reading_questions(post.content)
            messages.success(request, f'{len(questions)} perguntas geradas com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao gerar perguntas: {str(e)}')
        return redirect('admin:blog_post_change', post_id)

    def ai_enhanced_content(self, obj):
        if hasattr(obj, 'enhancement'):
            return format_html(
                '<a class="button" href="{}">Ver conteúdo melhorado</a>',
                f'/admin/ai_core/contentenhancement/{obj.enhancement.id}/change/'
            )
        return format_html(
            '<a class="button" href="{}">Melhorar conteúdo</a>',
            f'/admin/blog/post/{obj.id}/enhance/'
        )
    ai_enhanced_content.short_description = 'Conteúdo Melhorado'

    def ai_moderation_status(self, obj):
        if hasattr(obj, 'moderation'):
            status = '✅ Aprovado' if obj.moderation.is_appropriate else '⚠️ Precisa de revisão'
            return format_html(
                '<span style="color: {}">{}</span>',
                'green' if obj.moderation.is_appropriate else 'orange',
                status
            )
        return format_html(
            '<a class="button" href="{}">Verificar conteúdo</a>',
            f'/admin/blog/post/{obj.id}/moderate/'
        )
    ai_moderation_status.short_description = 'Status de Moderação'

    def ai_questions(self, obj):
        if obj.reading_questions.exists():
            return format_html(
                '<a class="button" href="{}">Ver perguntas ({})</a>',
                f'/admin/ai_core/readingquestion/?post__id={obj.id}',
                obj.reading_questions.count()
            )
        return format_html(
            '<a class="button" href="{}">Gerar perguntas</a>',
            f'/admin/blog/post/{obj.id}/generate-questions/'
        )
    ai_questions.short_description = 'Perguntas de Leitura'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'created_at', 'active')
    list_filter = ('active', 'created_at')
    search_fields = ('content', 'author__username', 'post__title')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'created_at')
    list_filter = ('user_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'bio')
    ordering = ('-created_at',)

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'teacher__username')
    filter_horizontal = ('students',)
    ordering = ('-created_at',)

@admin.register(PostReaction)
class PostReactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'reaction', 'created_at')
    list_filter = ('reaction', 'created_at')
    search_fields = ('user__username', 'post__title')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
