from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Sum
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Post, Category, Comment, PostReaction, Class
from .forms import CommentForm, PostForm
from ai_core.agents import blog_agent
from django.utils.text import slugify
import logging
from taggit.models import Tag, TaggedItem
from django.contrib.contenttypes.models import ContentType
import markdown
from django.urls import reverse
from django.contrib.auth.models import Group
from urllib.parse import unquote
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views import View

User = get_user_model()

logger = logging.getLogger(__name__)

def post_list(request):
    """Display a list of published blog posts."""
    posts = Post.objects.filter(status='published').order_by('-created_at')
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query)
        )
    
    # Category filter
    category_slug = request.GET.get('category')
    if category_slug:
        posts = posts.filter(category__slug=category_slug)
    
    # Tag filter
    tag_slug = request.GET.get('tag')
    if tag_slug:
        # Convert the slug to a format that matches taggit's slug format
        tag_slug = tag_slug.replace('-', '_')
        posts = posts.filter(tags__slug=tag_slug)
    
    # Pagination
    paginator = Paginator(posts, 10)  # Show 10 posts per page
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    # Get categories and tags for sidebar
    categories = Category.objects.annotate(
        post_count=Count('posts')
    ).order_by('-post_count')
    tags = Tag.objects.annotate(
        post_count=Count('taggit_taggeditem_items')
    ).order_by('-post_count')[:10]
    
    # Autores em destaque
    featured_authors = User.objects.annotate(
        post_count=Count('blog_posts')
    ).filter(post_count__gt=0).order_by('-post_count')[:5]
    
    context = {
        'posts': posts,
        'categories': categories,
        'tags': tags,
        'query': query,
        'category_slug': category_slug,
        'tag_slug': tag_slug,
        'featured_authors': featured_authors,
    }
    return render(request, 'blog/post_list.html', context)

def post_detail(request, slug):
    """Display a single blog post with its comments."""
    post = get_object_or_404(Post, slug=slug)
    
    # Verifica se o usuário tem permissão para ver o post
    if post.status != 'published' and not (request.user == post.author or request.user.profile.user_type in ['admin', 'teacher']):
        messages.error(request, 'Não tens permissão para ver este post.')
        return redirect('blog:post_list')
    
    # Increment view count
    post.views_count += 1
    post.save()
    
    # Get active comments
    comments = post.comments.filter(status='approved')
    
    # Handle comment submission
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.status = 'pending'  # Comentários começam como pendentes
            comment.save()
            messages.success(request, 'O teu comentário foi submetido para revisão.')
            return redirect('blog:post_detail', slug=slug)
    else:
        comment_form = CommentForm()
    
    # Convert markdown content to HTML
    post.content_html = markdown.markdown(
        post.content,
        extensions=['extra', 'codehilite', 'toc']
    )
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
    }
    return render(request, 'blog/post_detail.html', context)

@login_required
@require_POST
def post_reaction(request, slug):
    """Handle post reactions (like, love, etc.)."""
    post = get_object_or_404(Post, slug=slug)
    reaction_type = request.POST.get('reaction')
    
    # Remove existing reaction if any
    PostReaction.objects.filter(post=post, user=request.user).delete()
    
    if reaction_type in ['like', 'dislike']:
        PostReaction.objects.create(
            post=post,
            user=request.user,
            reaction=reaction_type
        )
        
    return JsonResponse({'status': 'success'})

def category_list(request):
    categories = Category.objects.annotate(
        posts_count=Count('posts'),
        total_views=Sum('posts__views')
    ).order_by('-posts_count')
    
    # Estatísticas totais
    total_posts = Post.objects.count()
    total_views = Post.objects.aggregate(Sum('views'))['views__sum'] or 0
    
    # Categorias populares (top 5)
    popular_categories = categories[:5]
    
    context = {
        'categories': categories,
        'total_posts': total_posts,
        'total_views': total_views,
        'popular_categories': popular_categories,
    }
    
    return render(request, 'blog/category_list.html', context)

def tag_list(request):
    """Display all tags used in blog posts."""

    # Obtém o ContentType para o modelo Post
    try:
        post_content_type = ContentType.objects.get_for_model(Post)
    except ContentType.DoesNotExist:
        post_content_type = None
        logger.warning("ContentType for Post model not found.")

    tags = Tag.objects.none() # Start with an empty queryset
    if post_content_type:
        # Obtém os IDs das tags que estão associadas a pelo menos um Post
        used_tag_ids = TaggedItem.objects.filter(
            content_type=post_content_type
        ).values_list('tag_id', flat=True).distinct()

        # Filtra as Tags para incluir apenas as usadas em Posts
        tags = Tag.objects.filter(id__in=used_tag_ids).annotate(
            # Conta quantas vezes cada tag é usada em Posts
            posts_count=Count('taggit_taggeditem_items', filter=Q(taggit_taggeditem_items__content_type=post_content_type))
        ).order_by('-posts_count')

    # Estatísticas totais
    total_posts = Post.objects.filter(status='published').count()
    # total_views = Post.objects.filter(status='published').aggregate(Sum('views'))['views__sum'] or 0

    # Tags populares (top 5)
    popular_tags = tags[:5]

    context = {
        'tags': tags,
        'total_posts': total_posts,
        # 'total_views': total_views, # Omitindo por enquanto
        'popular_tags': popular_tags,
    }

    return render(request, 'blog/tag_list.html', context)

@login_required
def post_create(request):
    """View para criar um novo post."""
    if not request.user.is_teacher:
        messages.error(request, 'Você não tem permissão para criar posts.')
        return redirect('blog:post_list')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            try:
                post = form.save(commit=False)
                post.author = request.user
                post.status = 'draft'
                
                # Gera o slug a partir do título
                post.slug = slugify(post.title, allow_unicode=True)
                
                # Se não houver turma selecionada, usa a turma "Geral"
                if not post.class_group:
                    geral_class, created = Class.objects.get_or_create(
                        name='Geral',
                        defaults={
                            'slug': 'geral',
                            'description': 'Turma para posts gerais',
                            'teacher': request.user
                        }
                    )
                    post.class_group = geral_class
                    if created:
                        messages.info(request, 'Uma turma "Geral" foi criada para posts sem turma específica.')
                
                # Gera sugestões de IA
                suggestions = None
                try:
                    suggestions = blog_agent.suggest_categories_and_tags(post.content)
                except Exception as e:
                    logger.error(f"Erro ao gerar sugestões: {str(e)}")
                
                # Se não houver categoria selecionada e houver sugestões, tenta usar a sugerida
                if not post.category_id and suggestions and suggestions.get('category'):
                    try:
                        suggested_category = suggestions['category']
                        
                        # Procura por categorias existentes similares
                        existing_categories = Category.objects.all()
                        best_match = None
                        highest_similarity = 0
                        
                        for category in existing_categories:
                            similarity = blog_agent.calculate_similarity(suggested_category, category.name)
                            if similarity > highest_similarity and similarity > 0.7:  # 70% de similaridade mínima
                                highest_similarity = similarity
                                best_match = category
                        
                        if best_match:
                            post.category = best_match
                            messages.info(request, f'Categoria "{best_match.name}" foi selecionada automaticamente.')
                        else:
                            # Se não encontrou similaridade suficiente, cria nova categoria
                            category, created = Category.objects.get_or_create(
                                name=suggested_category,
                                defaults={'slug': slugify(suggested_category, allow_unicode=True)}
                            )
                            post.category = category
                            if created:
                                messages.info(request, f'Categoria "{suggested_category}" foi criada automaticamente.')
                            else:
                                messages.info(request, f'Categoria "{suggested_category}" foi selecionada automaticamente.')
                    except Exception as e:
                        messages.warning(request, 'Não foi possível criar ou selecionar a categoria sugerida.')
                        return render(request, 'blog/post_form.html', {'form': form})
                
                # Gera resumo automaticamente
                try:
                    excerpt = blog_agent.generate_excerpt(post.content)
                    if excerpt:
                        post.excerpt = excerpt
                    else:
                        post.excerpt = post.content[:200] + "..."
                except Exception as e:
                    post.excerpt = post.content[:200] + "..."
                
                # Salva o post primeiro
                post.save()
                
                # Adiciona as tags selecionadas do formulário
                try:
                    selected_tags = form.cleaned_data.get('tags', [])
                    if selected_tags:
                        # Adiciona as tags selecionadas
                        for tag_name in selected_tags:
                            tag_name = tag_name.strip()
                            if tag_name:
                                post.tags.add(tag_name)
                    else:
                        # Se não houver tags selecionadas e houver sugestões, usa as sugeridas
                        if suggestions and suggestions.get('tags'):
                            existing_tags = Tag.objects.all()
                            for suggested_tag in suggestions['tags']:
                                # Normaliza o nome da tag
                                suggested_tag = suggested_tag.strip().lower()
                                
                                # Procura por tags existentes similares
                                best_match = None
                                highest_similarity = 0
                                
                                for tag in existing_tags:
                                    similarity = blog_agent.calculate_similarity(suggested_tag, tag.name)
                                    if similarity > highest_similarity and similarity > 0.7:  # 70% de similaridade mínima
                                        highest_similarity = similarity
                                        best_match = tag
                                
                                if best_match:
                                    post.tags.add(best_match)
                                else:
                                    # Se não encontrou similaridade suficiente, adiciona nova tag
                                    # Usa slugify para garantir um formato consistente
                                    tag_slug = slugify(suggested_tag, allow_unicode=True)
                                    post.tags.add(suggested_tag, slug=tag_slug)
                except Exception as e:
                    messages.warning(request, 'Não foi possível adicionar as tags.')
                
                messages.success(request, 'Post criado com sucesso! Aguarde a aprovação de um professor.')
                return redirect('blog:post_detail', slug=post.slug)
                
            except Exception as e:
                messages.error(request, f'Erro ao criar o post: {str(e)}')
                return render(request, 'blog/post_form.html', {'form': form})
    else:
        form = PostForm(user=request.user)
    
    return render(request, 'blog/post_form.html', {'form': form})

@login_required
def post_edit(request, slug):
    """View para editar um post."""
    post = get_object_or_404(Post, slug=slug)
    if not request.user.is_teacher and request.user != post.author:
        messages.error(request, 'Você não tem permissão para editar este post.')
        return redirect('blog:post_list')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            post.slug = slugify(post.title)
            post.save()
            form.save_m2m()  # Save tags
            messages.success(request, 'Post atualizado com sucesso!')
            return redirect('blog:post_detail', slug=post.slug)
    else:
        form = PostForm(instance=post, user=request.user)
    
    # Busca todas as categorias e tags para o formulário
    categories = Category.objects.all()
    tags = Tag.objects.all()
    
    return render(request, 'blog/post_form.html', {
        'form': form,
        'categories': categories,
        'tags': tags,
        'post': post
    })

@login_required
def post_approve(request, slug):
    post = get_object_or_404(Post, slug=slug)
    
    if not post.can_approve(request.user):
        messages.error(request, 'Não tens permissão para aprovar este post.')
        return redirect('blog:post_detail', slug=slug)
    
    post.status = 'published'
    post.published_at = timezone.now()
    post.save()
    
    messages.success(request, 'Post aprovado com sucesso!')
    return redirect('blog:post_detail', slug=slug)

@login_required
def post_reject(request, slug):
    post = get_object_or_404(Post, slug=slug)
    
    if not post.can_approve(request.user):
        messages.error(request, 'Não tens permissão para rejeitar este post.')
        return redirect('blog:post_detail', slug=slug)
    
    post.status = 'rejected'
    post.save()
    
    messages.success(request, 'Post rejeitado.')
    return redirect('blog:post_detail', slug=slug)

@login_required
def my_posts(request):
    posts = Post.objects.filter(author=request.user).order_by('-created_at')
    
    # Estatísticas totais
    total_posts = posts.count()
    total_views = posts.aggregate(Sum('views'))['views__sum'] or 0
    total_likes = posts.aggregate(Count('likes'))['likes__count']
    total_comments = Comment.objects.filter(post__in=posts).count()
    
    # Paginação
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    context = {
        'posts': posts,
        'total_posts': total_posts,
        'total_views': total_views,
        'total_likes': total_likes,
        'total_comments': total_comments,
    }
    
    return render(request, 'blog/my_posts.html', context)

@login_required
def pending_posts(request):
    """View para listar posts pendentes."""
    if not request.user.is_teacher:
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('blog:post_list')
    
    # Busca posts pendentes ordenados por data de criação
    pending_posts = Post.objects.filter(status='draft').order_by('-created_at')
    
    if request.method == 'POST':
        post_id = request.POST.get('post_id')
        action = request.POST.get('action')
        
        if post_id and action:
            post = get_object_or_404(Post, id=post_id)
            
            if action == 'approve':
                post.status = 'published'
                post.published_at = timezone.now()
                post.save()
                messages.success(request, f'Post "{post.title}" foi aprovado e publicado.')
                
                # Notifica o autor
                messages.success(request, f'O autor {post.author.get_full_name()} será notificado.')
                
            elif action == 'reject':
                post.status = 'rejected'
                post.save()
                messages.warning(request, f'Post "{post.title}" foi rejeitado.')
                
                # Notifica o autor
                messages.warning(request, f'O autor {post.author.get_full_name()} será notificado.')
    
    context = {
        'pending_posts': pending_posts,
    }
    return render(request, 'blog/pending_posts.html', context)

@login_required
@require_POST
def add_comment(request, slug):
    post = get_object_or_404(Post, slug=slug)
    form = CommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        messages.success(request, 'Comentário adicionado com sucesso!')
    else:
        messages.error(request, 'Erro ao adicionar comentário.')
    
    return redirect('blog:post_detail', slug=slug)

@login_required
@require_POST
def like_post(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        post.likes_count -= 1
    else:
        if request.user in post.dislikes.all():
            post.dislikes.remove(request.user)
            post.dislikes_count -= 1
        post.likes.add(request.user)
        post.likes_count += 1
    post.save()
    return JsonResponse({
        'likes_count': post.likes_count,
        'dislikes_count': post.dislikes_count
    })

@login_required
@require_POST
def dislike_post(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if request.user in post.dislikes.all():
        post.dislikes.remove(request.user)
        post.dislikes_count -= 1
    else:
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            post.likes_count -= 1
        post.dislikes.add(request.user)
        post.dislikes_count += 1
    post.save()
    return JsonResponse({
        'likes_count': post.likes_count,
        'dislikes_count': post.dislikes_count
    })

@login_required
def post_delete(request, slug):
    """Remove um post."""
    post = get_object_or_404(Post, slug=slug, author=request.user)
    
    if request.method == 'POST':
        try:
            post.delete()
            messages.success(request, 'Post removido com sucesso!')
        except Exception as e:
            logger.error(f"Erro ao remover post: {str(e)}")
            messages.error(request, 'Erro ao remover o post. Por favor, tente novamente.')
    
    return redirect('blog:my_posts')

def search(request):
    query = request.GET.get('q', '')
    posts = Post.objects.filter(status='published')
    
    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(tags__name__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
    
    # Ordenar por data de criação (mais recentes primeiro)
    posts = posts.order_by('-created_at')
    
    # Paginação
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    # Categorias populares
    popular_categories = Category.objects.annotate(
        post_count=Count('posts')
    ).order_by('-post_count')[:5]
    
    # Tags populares
    popular_tags = Tag.objects.annotate(
        post_count=Count('taggit_taggeditem_items')
    ).order_by('-post_count')[:10]
    
    context = {
        'posts': posts,
        'query': query,
        'popular_categories': popular_categories,
        'popular_tags': popular_tags,
    }
    
    return render(request, 'blog/search.html', context)

def category_detail(request, slug):
    """Display posts filtered by category."""
    # Decode the URL-encoded slug and normalize it
    decoded_slug = slugify(unquote(slug), allow_unicode=True)
    
    try:
        # Try to find the category by normalized slug
        category = Category.objects.get(slug=decoded_slug)
    except Category.DoesNotExist:
        # If not found, try to find by name
        category = get_object_or_404(Category, name__iexact=decoded_slug)
    
    posts = Post.objects.filter(category=category, status='published').order_by('-created_at')
    
    # Estatísticas
    unique_authors = posts.values('author').distinct().count()
    total_views = posts.aggregate(Sum('views'))['views__sum'] or 0
    
    # Categorias relacionadas (excluindo a atual)
    related_categories = Category.objects.exclude(id=category.id).annotate(
        post_count=Count('posts')
    ).order_by('-post_count')[:5]
    
    # Paginação
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    context = {
        'category': category,
        'posts': posts,
        'unique_authors': unique_authors,
        'total_views': total_views,
        'related_categories': related_categories,
    }
    
    return render(request, 'blog/category_detail.html', context)

def tag_detail(request, slug):
    """Display posts filtered by tag."""
    # Decode the URL-encoded slug and normalize it
    decoded_slug = slugify(unquote(slug), allow_unicode=True)
    
    try:
        # Try to find the tag by normalized slug
        tag = Tag.objects.get(slug=decoded_slug)
    except Tag.DoesNotExist:
        # If not found, try to find by name
        tag = get_object_or_404(Tag, name__iexact=decoded_slug)
    
    posts = Post.objects.filter(tags=tag, status='published').order_by('-created_at')
    
    # Estatísticas
    unique_authors = posts.values('author').distinct().count()
    total_views = posts.aggregate(Sum('views'))['views__sum'] or 0
    total_likes = posts.aggregate(Count('likes'))['likes__count']
    
    # Tags relacionadas (excluindo a atual)
    related_tags = Tag.objects.exclude(id=tag.id).annotate(
        post_count=Count('taggit_taggeditem_items')
    ).order_by('-post_count')[:5]
    
    # Paginação
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    context = {
        'tag': tag,
        'posts': posts,
        'unique_authors': unique_authors,
        'total_views': total_views,
        'total_likes': total_likes,
        'related_tags': related_tags,
    }
    
    return render(request, 'blog/tag_detail.html', context)

def author_posts(request, username):
    """Display posts by a specific author."""
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author, status='published').order_by('-created_at')
    
    # Estatísticas do autor
    total_posts = posts.count()
    total_views = posts.aggregate(Sum('views'))['views__sum'] or 0
    total_likes = sum(post.likes.count() for post in posts)
    
    # Categorias mais usadas pelo autor
    author_categories = Category.objects.filter(posts__author=author).annotate(
        posts_count=Count('posts')
    ).order_by('-posts_count')[:5]
    
    # Tags mais usadas pelo autor
    author_tags = Tag.objects.filter(
        taggit_taggeditem_items__content_type__model='post',
        taggit_taggeditem_items__object_id__in=posts.values_list('id', flat=True)
    ).annotate(
        posts_count=Count('taggit_taggeditem_items')
    ).order_by('-posts_count')[:10]
    
    # Pagination
    paginator = Paginator(posts, 10)  # Show 10 posts per page
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    context = {
        'author': author,
        'posts': posts,
        'total_posts': total_posts,
        'total_views': total_views,
        'total_likes': total_likes,
        'author_categories': author_categories,
        'author_tags': author_tags,
    }
    
    return render(request, 'blog/author_posts.html', context)

@require_POST
def suggest_categories_and_tags(request):
    if request.method == 'POST':
        content = request.POST.get('content', '')
        if content:
            try:
                from ai_core.agents import blog_agent
                suggestions = blog_agent.suggest_categories_and_tags(content)
                return JsonResponse(suggestions)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        return JsonResponse({'error': 'No content provided'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def profile(request):
    user_posts = Post.objects.filter(author=request.user).order_by('-created_at')
    user_comments = Comment.objects.filter(author=request.user).order_by('-created_at')
    context = {
        'user_posts': user_posts,
        'user_comments': user_comments,
    }
    return render(request, 'blog/profile.html', context)

@login_required
def profile_edit(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.bio = request.POST.get('bio')
        
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
        
        user.save()
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('blog:profile')
    
    return render(request, 'blog/profile_edit.html')

@login_required
def approve_post(request, post_id):
    """View para aprovar um post específico."""
    if request.user.profile.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Não tens permissão para aprovar posts.')
        return redirect('blog:post_list')
    
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        post.status = 'published'
        post.published_at = timezone.now()
        post.save()
        messages.success(request, f'Post "{post.title}" foi aprovado e publicado.')
        return redirect('blog:pending_posts')
    
    context = {
        'post': post,
    }
    return render(request, 'blog/approve_post.html', context)

@login_required
def moderate_comments(request):
    """View para moderar comentários."""
    if not request.user.is_teacher:
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('blog:post_list')
    
    # Busca comentários pendentes ordenados por data de criação
    pending_comments = Comment.objects.filter(status='pending').order_by('-created_at')
    
    if request.method == 'POST':
        comment_id = request.POST.get('comment_id')
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if comment_id and action:
            comment = get_object_or_404(Comment, id=comment_id)
            
            if action == 'approve':
                comment.approve(request.user)
                messages.success(request, f'Comentário de {comment.author.get_full_name()} foi aprovado.')
                
            elif action == 'reject':
                comment.reject(request.user, notes)
                messages.warning(request, f'Comentário de {comment.author.get_full_name()} foi rejeitado.')
    
    context = {
        'pending_comments': pending_comments,
    }
    return render(request, 'blog/moderate_comments.html', context)

@login_required
def manage_users(request):
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    # Buscar usuários convidados (que pertencem ao grupo 'guest')
    guest_users = User.objects.filter(groups__name='guest').order_by('-date_joined')
    
    context = {
        'guest_users': guest_users,
    }
    return render(request, 'blog/manage_users.html', context)

@login_required
def convert_to_student(request, user_id):
    if not request.user.is_teacher:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('blog:post_list')
    
    user = get_object_or_404(User, id=user_id)
    
    # Verificar se o usuário é um convidado
    if not user.is_guest:
        messages.error(request, 'Este usuário não é um convidado.')
        return redirect('blog:manage_users')
    
    # Remover do grupo 'guest' e adicionar ao grupo 'student'
    guest_group = Group.objects.get(name='guest')
    student_group = Group.objects.get(name='student')
    
    user.groups.remove(guest_group)
    user.groups.add(student_group)
    
    messages.success(request, f'Usuário {user.get_full_name()} convertido para aluno com sucesso!')
    return redirect('blog:manage_users')

@method_decorator(require_POST, name='dispatch')
class CreateCategoryView(View):
    def post(self, request):
        name = request.POST.get('name')
        if not name:
            return JsonResponse({'error': 'Nome da categoria é obrigatório'}, status=400)
            
        try:
            # Tenta encontrar uma categoria existente com o mesmo nome
            category = Category.objects.get(name=name)
        except Category.DoesNotExist:
            # Se não existir, cria uma nova categoria
            category = Category.objects.create(name=name)
            
        return JsonResponse({
            'id': category.id,
            'name': category.name
        })
