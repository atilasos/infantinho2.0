from django.contrib import admin
from .models import ReadingQuestion, ContentModeration, ContentEnhancement, AISuggestions

@admin.register(ReadingQuestion)
class ReadingQuestionAdmin(admin.ModelAdmin):
    list_display = ('post', 'question', 'created_at')
    list_filter = ('created_at', 'post')
    search_fields = ('question', 'answer', 'hints', 'post__title')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ContentModeration)
class ContentModerationAdmin(admin.ModelAdmin):
    list_display = ('post', 'is_appropriate', 'moderated_at', 'moderated_by')
    list_filter = ('appropriate_language', 'educational_content', 'no_harmful_content', 'appropriate_complexity', 'moderated_at')
    search_fields = ('post__title', 'moderated_by__username')
    readonly_fields = ('moderated_at',)

@admin.register(ContentEnhancement)
class ContentEnhancementAdmin(admin.ModelAdmin):
    list_display = ('post', 'target_age', 'enhanced_at', 'enhanced_by')
    list_filter = ('target_age', 'enhanced_at')
    search_fields = ('post__title', 'enhanced_by__username')
    readonly_fields = ('enhanced_at',)

@admin.register(AISuggestions)
class AISuggestionsAdmin(admin.ModelAdmin):
    list_display = ('post', 'created_at', 'generated_by')
    list_filter = ('created_at',)
    search_fields = ('post__title', 'suggested_title', 'generated_by__username')
