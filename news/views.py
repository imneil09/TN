from django.shortcuts import render
from django.utils.text import slugify
from datetime import datetime, timedelta
import random

# --- Mock Models ---

class MockImage:
    def __init__(self, url):
        self.url = url

class MockCategory:
    def __init__(self, name):
        self.name = name
        self.slug = slugify(name)

class MockDistrict:
    def __init__(self, name):
        self.name = name

class MockArticle:
    def __init__(self, id, title, category_name, district_name=None, is_breaking=False, is_hero=False, is_trending=False, image_url=None):
        self.id = id
        self.title = title
        # FIXED: Use Django's slugify to handle special characters like '&'
        self.slug = slugify(title)
        self.category = MockCategory(category_name)
        self.district = MockDistrict(district_name) if district_name else None
        
        if image_url:
            self.image = MockImage(image_url)
        else:
            seed = random.randint(1, 1000)
            self.image = MockImage(f"https://picsum.photos/seed/{seed}/800/600")

        self.content = """
        <p class="lead"><strong>AGARTALA:</strong> This represents the lead paragraph of the news story, designed to capture the reader's attention immediately. It summarizes the most critical aspects of the event.</p>
        
        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.</p>
        
        <h3>Key Highlights</h3>
        <ul>
            <li>The project is estimated to cost ₹500 Crores.</li>
            <li>Completion is expected by late 2026.</li>
            <li>It will generate over 5,000 direct jobs.</li>
        </ul>

        <p>Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam.</p>
        """
        self.author = random.choice(["Neil Roy", "Anjali Debbarma", "Rahul Das", "Sanjay Ghosh"])
        self.created_at = datetime.now() - timedelta(hours=random.randint(1, 48))
        self.subtitle = "A brief summary of the article that sits right below the headline to give more context before the user clicks."
        self.is_breaking = is_breaking
        self.is_hero = is_hero
        self.is_trending = is_trending

# --- Data Generator ---

def get_dummy_data():
    return [
        MockArticle(1, "State Govt Announces Mega IT Park in Agartala Smart City", "Tripura", "West Tripura", is_hero=True, image_url="https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=80"),
        MockArticle(2, "New Flight Routes: Agartala to Bangkok & Chittagong", "Northeast", is_breaking=True, image_url="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?auto=format&fit=crop&w=800&q=80"),
        MockArticle(3, "TBSE Class 10 & 12 Results: Check Pass Percentage Here", "Tripura", "West Tripura", is_breaking=True, is_trending=True, image_url="https://images.unsplash.com/photo-1434030216411-0b793f4b4173?auto=format&fit=crop&w=800&q=80"),
        MockArticle(4, "Hornbill Festival 2025: Nagaland Ready to Welcome World", "Northeast", is_trending=True, image_url="https://images.unsplash.com/photo-1516820208784-270b250dd066?auto=format&fit=crop&w=800&q=80"),
        MockArticle(5, "India's Digital Rupee Pilot Expands to Retail Sector", "India", image_url="https://images.unsplash.com/photo-1518186285589-2f7649de83e0?auto=format&fit=crop&w=800&q=80"),
        MockArticle(6, "Global Climate Summit: Nations Agree on Carbon Tax", "Global", image_url="https://images.unsplash.com/photo-1569163139599-0f4517e36f51?auto=format&fit=crop&w=800&q=80"),
        MockArticle(7, "Tripura Tea Industry Sees 20% Growth in Exports", "Tripura", "Dhalai", is_trending=True, image_url="https://images.unsplash.com/photo-1597404294360-feeeda04612e?auto=format&fit=crop&w=800&q=80"),
        MockArticle(8, "Border Haats Reopen: Boost for Local Economy", "Tripura", "Sepahijala", image_url="https://images.unsplash.com/photo-1488459716781-31db52582fe9?auto=format&fit=crop&w=800&q=80"),
        MockArticle(9, "ISRO Launches New Satellite for Disaster Management", "India", is_breaking=True, image_url="https://images.unsplash.com/photo-1516849841032-87cbac4d88f7?auto=format&fit=crop&w=800&q=80"),
        MockArticle(10, "New University Campus Inaugurated in North District", "Tripura", "North Tripura", image_url="https://images.unsplash.com/photo-1562774053-701939374585?auto=format&fit=crop&w=800&q=80"),
        MockArticle(11, "Tech Startups in Northeast: A Rising Ecosystem", "Northeast", is_trending=True, image_url="https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=800&q=80"),
        MockArticle(12, "Heavy Rainfall Warning Issued for Next 48 Hours", "Tripura", "South Tripura", is_breaking=True, image_url="https://images.unsplash.com/photo-1515694346937-94d85e41e6f0?auto=format&fit=crop&w=800&q=80"),
    ]

def get_common_context():
    data = get_dummy_data()
    return {
        'breaking_news': [a for a in data if a.is_breaking]
    }

# --- Views ---

def home(request):
    context = get_common_context()
    all_articles = get_dummy_data()
    
    # Hero Logic
    hero_article = next((a for a in all_articles if a.is_hero), all_articles[0])
    sub_hero_articles = [a for a in all_articles if a.id != hero_article.id][:2]
    trending_news = [a for a in all_articles if a.is_trending]
    
    tripura_news = [a for a in all_articles if a.category.name == "Tripura"]
    northeast_news = [a for a in all_articles if a.category.name == "Northeast"]
    india_news = [a for a in all_articles if a.category.name == "India"]
    global_news = [a for a in all_articles if a.category.name == "Global"]
    
    districts = [
        MockDistrict("West Tripura"), MockDistrict("Sepahijala"), 
        MockDistrict("Gomati"), MockDistrict("South Tripura"),
        MockDistrict("Khowai"), MockDistrict("Dhalai"),
        MockDistrict("Unakoti"), MockDistrict("North Tripura")
    ]

    # Group data for the template loop
    region_sections = [
        {'title': 'Northeast', 'articles': northeast_news, 'color': 'orange-500'},
        {'title': 'India', 'articles': india_news, 'color': 'blue-600'},
        {'title': 'Global', 'articles': global_news, 'color': 'indigo-500'},
    ]

    context.update({
        'hero_article': hero_article,
        'sub_hero_articles': sub_hero_articles,
        'trending_news': trending_news,
        'tripura_news': tripura_news,
        'districts': districts,
        'region_sections': region_sections,
    })
    
    return render(request, 'news/index.html', context)

def article_detail(request, slug):
    context = get_common_context()
    all_articles = get_dummy_data()
    # Find article by slug (mock lookup)
    # We use a loose match or fallback for demo stability
    article = next((a for a in all_articles if a.slug == slug), all_articles[0])
    
    context.update({
        'article': article,
        'related_news': all_articles[1:4] # Random 3 articles
    })
    return render(request, 'news/detail.html', context)

def category_detail(request, slug):
    context = get_common_context()
    all_articles = get_dummy_data()
    
    category = MockCategory(slug.capitalize())
    articles = [a for a in all_articles if a.category.name.lower() == slug]
    if not articles: articles = all_articles # Fallback
    
    context.update({
        'category': category,
        'articles': articles,
    })
    return render(request, 'news/category.html', context)

def company_info(request):
    return render(request, 'news/company_info.html')