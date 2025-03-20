from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Post, Category, Tag, Comment, PostReaction, UserProfile, Class
from .forms import CommentForm, PostForm
from ai_core.services import AIService
from django.utils.text import slugify

ai_service = AIService()

def post_list(request):
    """Display a list of published blog posts."""
    posts = Post.objects.filter(status='published')
    
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
    categories = Category.objects.all()
    tags = Tag.objects.all()
    
    context = {
        'posts': posts,
        'categories': categories,
        'tags': tags,
        'query': query,
        'category_slug': category_slug,
        'tag_slug': tag_slug,
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
    
    # Get approved comments
    comments = post.comments.filter(is_approved=True)
    
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
    
    if reaction_type not in dict(PostReaction.REACTION_CHOICES):
        return JsonResponse({'error': 'Invalid reaction type'}, status=400)
    
    # Get or create reaction
    reaction, created = PostReaction.objects.get_or_create(
        post=post,
        user=request.user,
        defaults={'reaction': reaction_type}
    )
    
    if not created:
        if reaction.reaction == reaction_type:
            # Remove reaction if clicking the same type
            reaction.delete()
            post.likes_count -= 1
        else:
            # Update reaction if changing type
            reaction.reaction = reaction_type
            reaction.save()
    
    post.save()
    
    return JsonResponse({
        'likes_count': post.likes_count,
        'reaction': reaction_type if created else None
    })

def category_list(request, slug):
    """Display posts filtered by category."""
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(category=category, status='published')
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'posts': posts,
    }
    return render(request, 'blog/category_list.html', context)

def tag_list(request, slug):
    """Display posts filtered by tag."""
    tag = get_object_or_404(Tag, slug=slug)
    posts = Post.objects.filter(tags=tag, status='published')
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    context = {
        'tag': tag,
        'posts': posts,
    }
    return render(request, 'blog/tag_list.html', context)

@login_required
def post_create(request):
    """View para criar um novo post."""
    print("POST data:", request.POST)  # Debug log
    print("FILES data:", request.FILES)  # Debug log
    
    if request.method == 'POST':
        form = PostForm(request.POST)
        print("Form is valid:", form.is_valid())  # Debug log
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.status = 'pending'  # Define o status inicial como pendente
            
            # Gera resumo automaticamente
            try:
                print("Gerando excerpt para o conteúdo:", post.content[:100])  # Debug log
                excerpt = ai_service.generate_excerpt(post.content)
                print("Excerpt gerado:", excerpt)  # Debug log
                if excerpt:
                    post.excerpt = excerpt
                else:
                    # Se não conseguir gerar o excerpt, usa os primeiros 200 caracteres do conteúdo
                    post.excerpt = post.content[:200] + "..."
            except Exception as e:
                print("Erro ao gerar excerpt:", str(e))  # Debug log
                post.excerpt = post.content[:200] + "..."  # Fallback para um resumo simples
            
            # Gera categoria automaticamente se não foi selecionada
            try:
                category_name = ai_service.generate_category(post.content)
                print("Categoria gerada:", category_name)  # Debug log
                if category_name:
                    category, _ = Category.objects.get_or_create(
                        name=category_name,
                        defaults={'slug': slugify(category_name)}
                    )
                    post.category = category
            except Exception as e:
                print("Erro ao gerar categoria:", str(e))  # Debug log
            
            # Gera o slug a partir do título
            post.slug = slugify(post.title)
            print("Slug gerado:", post.slug)  # Debug log
            
            # Verifica se já existe um post com o mesmo slug
            base_slug = post.slug
            counter = 1
            while Post.objects.filter(slug=post.slug).exists():
                post.slug = f"{base_slug}-{counter}"
                counter += 1
                print("Slug atualizado para:", post.slug)  # Debug log
            
            try:
                print("Tentando salvar o post...")  # Debug log
                post.save()  # Salva primeiro para gerar o slug
                print("Post salvo com sucesso!")  # Debug log
                
                # Gera e adiciona tags automaticamente
                try:
                    tags = ai_service.generate_tags(post.content)
                    print("Tags geradas:", tags)  # Debug log
                    for tag_name in tags:
                        tag, _ = Tag.objects.get_or_create(
                            name=tag_name,
                            defaults={'slug': slugify(tag_name)}
                        )
                        post.tags.add(tag)
                except Exception as e:
                    print("Erro ao gerar tags:", str(e))  # Debug log
                
                # Adiciona mensagem de sucesso
                messages.success(request, 'Post criado com sucesso! Aguardando aprovação.')
                
                # Redireciona para a lista de posts do usuário
                return redirect('blog:my_posts')
            except Exception as e:
                print("Erro ao salvar post:", str(e))  # Debug log
                messages.error(request, f'Erro ao criar o post: {str(e)}')
                return render(request, 'blog/post_form.html', {'form': form})
        else:
            print("Form errors:", form.errors)  # Debug log
            messages.error(request, 'Por favor, corrija os erros no formulário.')
            return render(request, 'blog/post_form.html', {'form': form})
    else:
        form = PostForm()
    
    return render(request, 'blog/post_form.html', {
        'form': form,
        'post': None
    })

@login_required
def post_edit(request, slug):
    """View para editar um post existente."""
    post = get_object_or_404(Post, slug=slug, author=request.user)
    
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save()
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
    posts = Post.objects.filter(author=request.user)
    return render(request, 'blog/my_posts.html', {'posts': posts})

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
