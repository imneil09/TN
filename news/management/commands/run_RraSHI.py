import requests
import json
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from duckduckgo_search import DDGS
from news.models import Article, Category, District
from google import genai 

# Your official API Key
GEMINI_API_KEY = "AIzaSyBrs3OFHheLrDPdQXX8AL6P0YUrEVas8lA" 

class Command(BaseCommand):
    help = 'Worker script that fetches and writes the news article.'

    def add_arguments(self, parser):
        parser.add_argument('topic', type=str, help='Topic to search for')

    def handle(self, *args, **options):
        topic = options['topic']
        self.stdout.write(f"🔍 Worker Searching: {topic}...")

        # --- SAFETY NET FOR DUCKDUCKGO RATE LIMITS ---
        try:
            results = DDGS().text(f"{topic} latest news", max_results=5)
            # Convert generator to list to check if DuckDuckGo blocked us
            results = list(results)
            if not results:
                self.stdout.write(self.style.WARNING("   ⚠️ No search results found (DuckDuckGo Rate Limit). Skipping cycle."))
                return
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   ⚠️ Search Engine Error: {e}. Skipping cycle."))
            return
        
        # Initialize the NEW Gemini Client
        client = genai.Client(api_key=GEMINI_API_KEY)

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
            self.stdout.write("   🤖 RraSHI AI is writing...")
            
            prompt = f"""
            You are "RraSHI AI", a senior editor for "Tripura Now".
            Rewrite the text below into a professional news article.

            RULES:
            1. CATEGORY: ONE of ["Tripura", "Northeast", "India", "Global", "Others"]
            2. DISTRICT: If Tripura, pick one from ["West Tripura", "Sepahijala", "Gomati", "South Tripura", "Khowai", "Dhalai", "Unakoti", "North Tripura"]. Else null.
            3. FORMAT: JSON Only. Title, Subtitle, Body (HTML), Category, District.

            RAW TEXT:
            {raw_text[:4500]}...
            """
            
            try:
                # NEW Gemini API Call Syntax (Using 2.5 Flash for speed and accuracy)
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                
                # Clean up the JSON if Gemini adds Markdown formatting
                clean_json = response.text.strip()
                if clean_json.startswith('```json'):
                    clean_json = clean_json[7:]
                if clean_json.endswith('```'):
                    clean_json = clean_json[:-3]
                    
                data = json.loads(clean_json.strip())
                
                # Pass the extracted image URL to save_article
                self.save_article(data, url, extracted_image_url)
                self.stdout.write(self.style.SUCCESS(f"   ✅ Published by RraSHI AI: {data['title']}"))
                processed_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ AI/Save Error: {e}"))

    def fetch_page_content(self, url):
        # Adding a more robust User-Agent to avoid getting blocked by news sites
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/'
        }
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
            author="RraSHI AI", 
            is_breaking=True,
            is_trending=True
        )