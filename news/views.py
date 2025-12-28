from django.shortcuts import render, get_object_or_404
from .models import Article, Category, District

def get_common_context():
    """Helper to get data needed on every page (like the ticker)"""
    return {
        'breaking_news': Article.objects.filter(is_breaking=True).order_by('-created_at')[:5]
    }

def home(request):
    context = get_common_context()
    
    # 1. Hero Section
    hero_article = Article.objects.filter(is_hero=True).order_by('-created_at').first()
    if not hero_article:
        hero_article = Article.objects.first()
        
    sub_hero_articles = Article.objects.exclude(id=hero_article.id if hero_article else 0).order_by('-created_at')[:3]
    
    # 2. Sections
    tripura_news = Article.objects.filter(category__name__iexact='Tripura').order_by('-created_at')[:6]
    northeast_news = Article.objects.filter(category__name__iexact='Northeast')[:5]
    india_news = Article.objects.filter(category__name__iexact='India')[:5]
    global_news = Article.objects.filter(category__name__iexact='Global')[:5]
    
    context.update({
        'hero_article': hero_article,
        'sub_hero_articles': sub_hero_articles,
        'tripura_news': tripura_news,
        'districts': District.objects.all(),
        'northeast_news': northeast_news,
        'india_news': india_news,
        'global_news': global_news,
    })
    return render(request, 'news/home.html', context)

def article_detail(request, slug):
    context = get_common_context() # Keep the ticker visible
    article = get_object_or_404(Article, slug=slug)
    related_news = Article.objects.filter(category=article.category).exclude(id=article.id)[:3]
    
    context.update({
        'article': article,
        'related_news': related_news
    })
    return render(request, 'news/detail.html', context)

def category_detail(request, slug):
    context = get_common_context()
    # Support lookup by name (slugified)
    category = get_object_or_404(Category, slug=slug)
    articles = Article.objects.filter(category=category).order_by('-created_at')
    
    context.update({
        'category': category,
        'articles': articles,
    })
    return render(request, 'news/category.html', context)