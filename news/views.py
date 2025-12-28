from django.shortcuts import render, get_object_or_404
from .models import Article, Category, District

def get_common_context():
    """Helper to get data needed on every page (like the ticker)"""
    return {
        'breaking_news': Article.objects.filter(is_breaking=True).order_by('-created_at')[:5]
    }

def home(request):
    context = get_common_context()
    
    # 1. Hero Section (The big main article)
    hero_article = Article.objects.filter(is_hero=True).order_by('-created_at').first()
    
    # Exclude hero from other lists to avoid duplication
    exclude_ids = [hero_article.id] if hero_article else []
    
    # Sub-hero articles (next to the main one)
    sub_hero_articles = Article.objects.exclude(id__in=exclude_ids).order_by('-created_at')[:3]
    exclude_ids += [a.id for a in sub_hero_articles] # Update exclusion list
    
    # 2. Trending (For the sidebar)
    trending_news = Article.objects.filter(is_trending=True).exclude(id__in=exclude_ids)[:5]

    # 3. Categorized News
    tripura_news = Article.objects.filter(category__name__iexact='Tripura').order_by('-created_at')[:4]
    northeast_news = Article.objects.filter(category__name__iexact='Northeast')[:5]
    india_news = Article.objects.filter(category__name__iexact='India')[:5]
    global_news = Article.objects.filter(category__name__iexact='Global')[:5]
    
    context.update({
        'hero_article': hero_article,
        'sub_hero_articles': sub_hero_articles,
        'trending_news': trending_news, 
        'tripura_news': tripura_news,
        'districts': District.objects.all(), # For the filter buttons
        'northeast_news': northeast_news,
        'india_news': india_news,
        'global_news': global_news,
    })
    
    return render(request, 'news/index.html', context)

def article_detail(request, slug):
    context = get_common_context()
    article = get_object_or_404(Article, slug=slug)
    # Get 3 other articles from the same category
    related_news = Article.objects.filter(category=article.category).exclude(id=article.id)[:3]
    
    context.update({
        'article': article,
        'related_news': related_news
    })
    return render(request, 'news/detail.html', context)

def category_detail(request, slug):
    context = get_common_context()
    category = get_object_or_404(Category, slug=slug)
    articles = Article.objects.filter(category=category).order_by('-created_at')
    
    context.update({
        'category': category,
        'articles': articles,
    })
    return render(request, 'news/category.html', context)