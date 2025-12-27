from django.shortcuts import render, get_object_or_404
from .models import Article, Category, District

def home(request):
    # 1. Breaking News Ticker
    breaking_news = Article.objects.filter(is_breaking=True).order_by('-created_at')[:5]
    
    # 2. Hero Section (The big grid)
    # We try to get one designated hero, or fallback to the latest post
    hero_article = Article.objects.filter(is_hero=True).order_by('-created_at').first()
    if not hero_article:
        hero_article = Article.objects.first()
        
    # Get 3 other sub-hero articles excluding the main hero
    sub_hero_articles = Article.objects.exclude(id=hero_article.id if hero_article else 0).order_by('-created_at')[:3]
    
    # 3. Tripura Focus (Filtered by Category 'Tripura')
    # We fetch all Tripura news
    tripura_news = Article.objects.filter(category__name__iexact='Tripura').order_by('-created_at')[:6]
    districts = District.objects.all() # For the filter buttons
    
    # 4. Regional Sections
    northeast_news = Article.objects.filter(category__name__iexact='Northeast')[:5]
    india_news = Article.objects.filter(category__name__iexact='India')[:5]
    global_news = Article.objects.filter(category__name__iexact='Global')[:5]

    context = {
        'breaking_news': breaking_news,
        'hero_article': hero_article,
        'sub_hero_articles': sub_hero_articles,
        'tripura_news': tripura_news,
        'districts': districts,
        'northeast_news': northeast_news,
        'india_news': india_news,
        'global_news': global_news,
    }
    return render(request, 'news/home.html', context)

def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug)
    # Simple "Related News" logic
    related_news = Article.objects.filter(category=article.category).exclude(id=article.id)[:3]
    
    context = {
        'article': article,
        'related_news': related_news
    }
    return render(request, 'news/detail.html', context)