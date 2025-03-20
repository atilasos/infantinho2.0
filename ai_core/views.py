from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from blog.models import Post
from .models import ReadingQuestion, ContentModeration, ContentEnhancement, AISuggestions
from .services import OllamaService, AIService
import json

ollama_service = OllamaService()

@login_required
def generate_ai_suggestions(request, post_id):
    """Generate AI suggestions for a post."""
    post = get_object_or_404(Post, id=post_id)
    
    try:
        # Gerar sugestões
        suggested_title = ollama_service.suggest_title(post.content)
        suggested_introduction = ollama_service.suggest_introduction(post.content)
        suggested_structure = ollama_service.suggest_article_structure(post.content)
        social_summary = ollama_service.generate_social_summary(post.content)
        
        # Criar ou atualizar sugestões
        suggestions, created = AISuggestions.objects.get_or_create(
            post=post,
            defaults={
                'suggested_title': suggested_title,
                'suggested_introduction': suggested_introduction,
                'suggested_structure': suggested_structure,
                'social_summary': social_summary,
                'generated_by': request.user
            }
        )
        
        if not created:
            suggestions.suggested_title = suggested_title
            suggestions.suggested_introduction = suggested_introduction
            suggestions.suggested_structure = suggested_structure
            suggestions.social_summary = social_summary
            suggestions.generated_by = request.user
            suggestions.save()
        
        messages.success(request, 'Sugestões de IA geradas com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao gerar sugestões de IA: {str(e)}')
    
    return redirect('admin:blog_post_change', post_id)

@login_required
def apply_ai_suggestion(request, post_id, suggestion_type):
    """Apply a specific AI suggestion to the post."""
    post = get_object_or_404(Post, id=post_id)
    suggestions = get_object_or_404(AISuggestions, post=post)
    
    try:
        if suggestion_type == 'title':
            post.title = suggestions.suggested_title
        elif suggestion_type == 'introduction':
            # Adicionar a introdução no início do conteúdo
            post.content = f"{suggestions.suggested_introduction}\n\n{post.content}"
        elif suggestion_type == 'structure':
            # Implementar a estrutura sugerida no conteúdo
            structured_content = ""
            for section in suggestions.suggested_structure:
                structured_content += f"## {section['title']}\n\n"
                for subsection in section['subsections']:
                    structured_content += f"### {subsection}\n\n"
            post.content = structured_content + post.content
        
        post.save()
        messages.success(request, f'Sugestão de {suggestion_type} aplicada com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao aplicar sugestão: {str(e)}')
    
    return redirect('admin:blog_post_change', post_id)

@login_required
def enhance_post(request, post_id):
    """Enhance post content for children."""
    post = get_object_or_404(Post, id=post_id)
    
    try:
        enhanced_content = ollama_service.enhance_content(post.content)
        
        # Create or update enhancement
        enhancement, created = ContentEnhancement.objects.get_or_create(
            post=post,
            defaults={
                'original_content': post.content,
                'enhanced_content': enhanced_content,
                'enhanced_by': request.user
            }
        )
        
        if not created:
            enhancement.enhanced_content = enhanced_content
            enhancement.enhanced_by = request.user
            enhancement.save()
        
        messages.success(request, 'Conteúdo melhorado com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao melhorar o conteúdo: {str(e)}')
    
    return redirect('admin:blog_post_change', post_id)

@login_required
def moderate_post(request, post_id):
    """Moderate post content for children."""
    post = get_object_or_404(Post, id=post_id)
    
    try:
        moderation_result = ollama_service.moderate_content(post.content)
        
        # Create or update moderation
        moderation, created = ContentModeration.objects.get_or_create(
            post=post,
            defaults={
                **moderation_result,
                'moderated_by': request.user
            }
        )
        
        if not created:
            for key, value in moderation_result.items():
                setattr(moderation, key, value)
            moderation.moderated_by = request.user
            moderation.save()
        
        messages.success(request, 'Conteúdo moderado com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao moderar o conteúdo: {str(e)}')
    
    return redirect('admin:blog_post_change', post_id)

@login_required
def generate_questions(request, post_id):
    """Generate reading comprehension questions for a post."""
    post = get_object_or_404(Post, id=post_id)
    
    try:
        questions = ollama_service.generate_reading_questions(post.content)
        
        # Create questions
        for question_data in questions:
            ReadingQuestion.objects.create(
                post=post,
                question=question_data['question'],
                answer=question_data['answer'],
                hints=question_data['hints']
            )
        
        messages.success(request, 'Perguntas geradas com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao gerar perguntas: {str(e)}')
    
    return redirect('admin:blog_post_change', post_id)

@login_required
def suggest_tags(request, post_id):
    """Suggest tags for a post."""
    post = get_object_or_404(Post, id=post_id)
    
    try:
        suggested_tags = ollama_service.suggest_tags(post.content)
        return JsonResponse({'tags': suggested_tags})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def generate_suggestions(request):
    """Gera sugestões de IA para o conteúdo."""
    try:
        data = json.loads(request.body)
        content = data.get('content', '')
        
        if not content:
            return JsonResponse({'error': 'O conteúdo não pode estar vazio'}, status=400)
        
        ai_service = AIService()
        suggestions = ai_service.generate_suggestions(content)
        
        if 'error' in suggestions:
            return JsonResponse({'error': suggestions['error']}, status=500)
            
        return JsonResponse(suggestions)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Dados JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def enhance_content(request):
    """Melhora o conteúdo para ser mais adequado para crianças."""
    try:
        data = json.loads(request.body)
        content = data.get('content', '')
        target_age_group = data.get('target_age_group', 8)
        
        if not content:
            return JsonResponse({'error': 'O conteúdo não pode estar vazio'}, status=400)
        
        ai_service = AIService()
        enhanced_content = ai_service.enhance_content(content, target_age_group)
        
        if 'error' in enhanced_content:
            return JsonResponse({'error': enhanced_content['error']}, status=500)
            
        return JsonResponse({'enhanced_content': enhanced_content})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Dados JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def moderate_content(request):
    """Modera o conteúdo para garantir que é apropriado para crianças."""
    try:
        data = json.loads(request.body)
        content = data.get('content', '')
        
        if not content:
            return JsonResponse({'error': 'O conteúdo não pode estar vazio'}, status=400)
        
        ai_service = AIService()
        result = ai_service.moderate_content(content)
        
        if 'error' in result:
            return JsonResponse({'error': result['error']}, status=500)
            
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Dados JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
