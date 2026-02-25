from django.shortcuts import render, get_object_or_404
from .models import Article, Category, District

def get_common_context():
    return {
        'breaking_news': Article.objects.filter(is_breaking=True).order_by('-created_at')[:5]
    }

def home(request):
    context = get_common_context()
    all_articles = Article.objects.all().order_by('-created_at')
    
    # Hero Logic (Featured Article)
    hero_article = all_articles.filter(is_hero=True).first()
    if not hero_article and all_articles.exists():
        hero_article = all_articles[0]
        
    sub_articles = []
    if hero_article:
        sub_articles = all_articles.exclude(id=hero_article.id)[:2]

    # Region Sections (Prioritized List for Homepage)
    region_sections = [
        {'title': 'Northeast', 'articles': all_articles.filter(category__name='Northeast')[:3], 'color': 'orange-500'},
        {'title': 'India', 'articles': all_articles.filter(category__name='India')[:3], 'color': 'blue-600'},
        {'title': 'Global', 'articles': all_articles.filter(category__name='Global')[:3], 'color': 'indigo-500'},
        {'title': 'Tech & Lifestyle', 'articles': all_articles.filter(category__name='Others')[:3], 'color': 'green-500'},
    ]

    context.update({
        'hero_article': hero_article,
        'sub_hero_articles': sub_articles,
        'trending_news': all_articles.filter(is_trending=True)[:8],
        # Showing more news for Tripura (Priority 1)
        'tripura_news': all_articles.filter(category__name='Tripura')[:6],
        'districts': District.objects.all(),
        'region_sections': region_sections,
    })
    
    return render(request, 'news/index.html', context)

def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug)
    context = get_common_context()
    context.update({
        'article': article,
        'related_news': Article.objects.filter(category=article.category).exclude(id=article.id)[:3]
    })
    return render(request, 'news/detail.html', context)

def category_detail(request, slug):
    category = get_object_or_404(Category, slug__iexact=slug)
    articles = Article.objects.filter(category=category).order_by('-created_at')
    context = get_common_context()
    context.update({'category': category, 'articles': articles})
    return render(request, 'news/category.html', context)

def company_info(request):
    return render(request, 'news/company_info.html')