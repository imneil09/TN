import requests
import json
import google.generativeai as genai
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from duckduckgo_search import DDGS
from news.models import Article, Category, District

# !!! PASTE YOUR API KEY HERE !!!
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE" 

class Command(BaseCommand):
    help = 'Worker script that fetches and writes the news article.'

    def add_arguments(self, parser):
        parser.add_argument('topic', type=str, help='Topic to search for')

    def handle(self, *args, **options):
        topic = options['topic']
        self.stdout.write(f"🔍 Worker Searching: {topic}...")

        # Search for latest news
        results = DDGS().text(f"{topic} latest news", max_results=5)
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')

        processed_count = 0
        
        for result in results:
            if processed_count >= 1: break # Process only 1 new article per run

            url = result['href']
            title = result['title']

            # 1. Deduplication Check
            if Article.objects.filter(source_url=url).exists():
                self.stdout.write(self.style.WARNING(f"   Skipping (Duplicate): {title}"))
                continue
            
            # 2. Content & Image Fetching
            try:
                content_data = self.fetch_page_content(url)
                if not content_data: 
                    continue
                
                raw_text, extracted_image_url = content_data
                
                if len(raw_text) < 600:
                    self.stdout.write("   Skipping (Content too short)")
                    continue

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   Fetch Error: {e}"))
                continue

            # 3. AI Writing
            self.stdout.write("   🤖 RaShi AI is writing...")
            
            prompt = f"""
            You are "RaShi AI", a senior editor for "Tripura Now".
            Rewrite the text below into a professional news article.

            RULES:
            1. CATEGORY: ONE of ["Tripura", "Northeast", "India", "Global", "Others"]
            2. DISTRICT: If Tripura, pick one from ["West Tripura", "Sepahijala", "Gomati", "South Tripura", "Khowai", "Dhalai", "Unakoti", "North Tripura"]. Else null.
            3. FORMAT: JSON Only. Title, Subtitle, Body (HTML), Category, District.

            RAW TEXT:
            {raw_text[:4500]}...
            """
            
            try:
                response = model.generate_content(prompt)
                clean_json = response.text.replace('```json', '').replace('```', '')
                data = json.loads(clean_json)
                
                # Pass the extracted image URL to save_article
                self.save_article(data, url, extracted_image_url)
                self.stdout.write(self.style.SUCCESS(f"   ✅ Published: {data['title']}"))
                processed_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ AI/Save Error: {e}"))

    def fetch_page_content(self, url):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Extract Text
            paragraphs = [p.get_text() for p in soup.find_all('p')]
            text = " ".join(paragraphs)
            
            # Extract Image (Priority: og:image -> twitter:image -> None)
            image_url = None
            og_image = soup.find("meta", property="og:image")
            if og_image:
                image_url = og_image.get("content")
            
            if not image_url:
                tw_image = soup.find("meta", name="twitter:image")
                if tw_image:
                    image_url = tw_image.get("content")

            return text, image_url
            
        except Exception:
            return None

    def save_article(self, data, source_url, extracted_image_url):
        # Category & District Logic
        cat_name = data.get('category', 'Others').capitalize()
        valid_cats = ["Tripura", "Northeast", "India", "Global", "Others"]
        if cat_name not in valid_cats: cat_name = "Others"
        
        category, _ = Category.objects.get_or_create(name=cat_name)
        
        district_obj = None
        if cat_name == "Tripura":
            dist_name = data.get('district')
            if dist_name:
                district_obj, _ = District.objects.get_or_create(name=dist_name)
            else:
                district_obj, _ = District.objects.get_or_create(name="West Tripura")

        # Image Logic: Prefer extracted, fallback to placeholder
        final_image = extracted_image_url if extracted_image_url else "https://source.unsplash.com/random/800x600/?news"

        Article.objects.create(
            title=data['title'],
            subtitle=data['subtitle'],
            content=data['body'],
            category=category,
            district=district_obj,
            source_url=source_url,
            image_url=final_image,
            is_breaking=True,
            is_trending=True
        )