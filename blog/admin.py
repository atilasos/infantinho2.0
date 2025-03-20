from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from .models import Category, Tag, Post, Comment, PostReaction
from ai_core.services import OllamaService

ollama_service = OllamaService()

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'published_at', 'is_featured')
    list_filter = ('status', 'category', 'is_featured', 'created_at', 'published_at')
    search_fields = ('title', 'content', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    ordering = ('-published_at', '-created_at')
    filter_horizontal = ('tags',)
    readonly_fields = ('views_count', 'likes_count', 'created_at', 'updated_at')
    
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
    list_display = ('post', 'author', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('content', 'author__username', 'post__title')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_comments.short_description = "Aprovar comentários selecionados"

@admin.register(PostReaction)
class PostReactionAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'reaction', 'created_at')
    list_filter = ('reaction', 'created_at')
    search_fields = ('post__title', 'user__username')
    readonly_fields = ('created_at',)
