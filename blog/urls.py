from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # Post views
    path('', views.post_list, name='post_list'),
    
    # Novas URLs para gestão de posts
    path('post/new/', views.post_create, name='post_create'),
    path('my-posts/', views.my_posts, name='my_posts'),
    path('pending-posts/', views.pending_posts, name='pending_posts'),
    
    # URLs com slug
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('post/<slug:slug>/edit/', views.post_edit, name='post_edit'),
    path('post/<slug:slug>/approve/', views.post_approve, name='post_approve'),
    path('post/<slug:slug>/reject/', views.post_reject, name='post_reject'),
    path('post/<slug:slug>/reaction/', views.post_reaction, name='post_reaction'),
    path('post/<slug:slug>/comment/', views.add_comment, name='add_comment'),
    path('post/<slug:slug>/like/', views.like_post, name='like_post'),
    path('post/<slug:slug>/dislike/', views.dislike_post, name='dislike_post'),
    path('post/<slug:slug>/delete/', views.post_delete, name='post_delete'),
    
    # Category views
    path('categories/', views.category_list, name='category_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    
    # Tag views
    path('tags/', views.tag_list, name='tag_list'),
    path('tag/<slug:slug>/', views.tag_detail, name='tag_detail'),
    
    # Author views
    path('author/<str:username>/', views.author_posts, name='author_posts'),
    
    # Search
    path('search/', views.search, name='search'),
] 