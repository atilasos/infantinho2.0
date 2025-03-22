from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Sum
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Post, Category, Comment, PostReaction, UserProfile, Class
from .forms import CommentForm, PostForm
from ai_core.agents import blog_agent
from django.utils.text import slugify
import logging
from taggit.models import Tag
import markdown

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
    comments = post.comments.filter(active=True)
    
    # Handle comment submission
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, 'Your comment has been submitted for review.')
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
    """Display all tags."""
    tags = Tag.objects.annotate(
        posts_count=Count('taggit_taggeditem_items'),
        total_views=Sum('taggit_taggeditem_items__content_object__views')
    ).order_by('-posts_count')
    
    # Estatísticas totais
    total_posts = Post.objects.count()
    total_views = Post.objects.aggregate(Sum('views'))['views__sum'] or 0
    
    # Tags populares (top 5)
    popular_tags = tags[:5]
    
    context = {
        'tags': tags,
        'total_posts': total_posts,
        'total_views': total_views,
        'popular_tags': popular_tags,
    }
    
    return render(request, 'blog/tag_list.html', context)

@login_required
def post_create(request):
    """View para criar um novo post."""
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.status = 'draft'
            
            # Se não houver categoria selecionada, tenta sugerir uma
            if not post.category_id:  # Usando category_id em vez de category
                try:
                    suggested_category = form.suggest_category()
                    if suggested_category:
                        # Cria ou obtém a categoria sugerida
                        category, created = Category.objects.get_or_create(
                            name=suggested_category,
                            defaults={'slug': slugify(suggested_category)}
                        )
                        post.category = category
                        if created:
                            messages.info(request, f'Categoria "{suggested_category}" foi criada automaticamente.')
                        else:
                            messages.info(request, f'Categoria "{suggested_category}" foi selecionada automaticamente.')
                    else:
                        # Se não conseguir sugerir uma categoria, cria uma temporária
                        temp_category, created = Category.objects.get_or_create(
                            name='Temporária',
                            defaults={'slug': 'temporaria'}
                        )
                        post.category = temp_category
                        if created:
                            messages.warning(request, 'Uma categoria temporária foi criada.')
                        else:
                            messages.warning(request, 'Uma categoria temporária foi selecionada.')
                except Exception as e:
                    # Cria uma categoria temporária em caso de erro
                    temp_category, _ = Category.objects.get_or_create(
                        name='Temporária',
                        defaults={'slug': 'temporaria'}
                    )
                    post.category = temp_category
                    messages.error(request, 'Ocorreu um erro ao sugerir categoria. Uma categoria temporária foi selecionada.')
            
            # Gera resumo automaticamente
            try:
                excerpt = blog_agent.generate_excerpt(post.content)
                if excerpt:
                    post.excerpt = excerpt
                else:
                    post.excerpt = post.content[:200] + "..."
            except Exception as e:
                post.excerpt = post.content[:200] + "..."
            
            # Gera o slug a partir do título
            post.slug = slugify(post.title)
            
            # Verifica se já existe um post com o mesmo slug
            base_slug = post.slug
            counter = 1
            while Post.objects.filter(slug=post.slug).exists():
                post.slug = f"{base_slug}-{counter}"
                counter += 1
            
            try:
                post.save()
                
                # Processa as tags do formulário
                tags = form.cleaned_data.get('tags', [])
                if tags:
                    # Se as tags vierem como string, converte para lista
                    if isinstance(tags, str):
                        tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
                    
                    # Adiciona cada tag ao post
                    for tag_name in tags:
                        tag, _ = Tag.objects.get_or_create(
                            name=tag_name,
                            defaults={'slug': slugify(tag_name)}
                        )
                        post.tags.add(tag)
                
                messages.success(request, 'Post criado com sucesso!')
                return redirect('blog:post_detail', slug=post.slug)
            except Exception as e:
                messages.error(request, f'Erro ao salvar o post: {str(e)}')
                return render(request, 'blog/post_form.html', {'form': form})
    else:
        form = PostForm()
    
    return render(request, 'blog/post_form.html', {'form': form})

@login_required
def post_edit(request, slug):
    """View para editar um post existente."""
    post = get_object_or_404(Post, slug=slug, author=request.user)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.slug = slugify(post.title)
            post.save()
            form.save_m2m()  # Save tags
            messages.success(request, 'Post atualizado com sucesso!')
            return redirect('blog:post_detail', slug=post.slug)
    else:
        form = PostForm(instance=post)
    
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
    if request.user.profile.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Não tens permissão para ver posts pendentes.')
        return redirect('blog:post_list')
    
    posts = Post.objects.filter(status='pending')
    return render(request, 'blog/pending_posts.html', {'posts': posts})

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
    category = get_object_or_404(Category, slug=slug)
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
    tag = get_object_or_404(Tag, slug=slug)
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
    total_likes = posts.aggregate(Sum('likes_count'))['likes_count__sum'] or 0
    
    # Categorias mais usadas pelo autor
    author_categories = Category.objects.filter(posts__author=author).annotate(
        posts_count=Count('posts')
    ).order_by('-posts_count')[:5]
    
    # Tags mais usadas pelo autor
    author_tags = Tag.objects.filter(taggit_taggeditem_items__content_object__author=author).annotate(
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
