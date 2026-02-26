import requests
import json
import urllib.parse
import re
import base64
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
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
        self.stdout.write(f"🔍 Worker Searching on Google News: {topic}...")

        try:
            query = urllib.parse.quote(f"{topic}")
            url = f"https://news.google.com/rss/search?q={query}+when:1d&hl=en-IN&gl=IN&ceid=IN:en"
            
            resp = requests.get(url, timeout=10)
            soup = BeautifulSoup(resp.content, 'xml')
            items = soup.find_all('item')

            if not items:
                self.stdout.write(self.style.WARNING("   ⚠️ No recent news found on Google. Skipping cycle."))
                return
            
            results = []
            for item in items[:5]:
                results.append({
                    'title': item.title.text,
                    'href': item.link.text
                })
                
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   ⚠️ Search Engine Error: {e}. Skipping cycle."))
            return
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        processed_count = 0
        
        for result in results:
            if processed_count >= 1: break 

            url = result['href']
            title = result['title']

            if Article.objects.filter(source_url=url).exists():
                self.stdout.write(self.style.WARNING(f"   Skipping (Duplicate): {title}"))
                continue
            
            try:
                content_data = self.fetch_page_content(url)
                if not content_data: 
                    continue
                
                raw_text, extracted_image_url = content_data
                
                # Check if we got enough text to work with
                if len(raw_text) < 400:
                    self.stdout.write(f"   Skipping (Content too short: {len(raw_text)} chars)")
                    continue

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   Fetch Error: {e}"))
                continue

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
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                
                clean_json = response.text.strip()
                if clean_json.startswith('```json'):
                    clean_json = clean_json[7:]
                if clean_json.endswith('```'):
                    clean_json = clean_json[:-3]
                    
                data = json.loads(clean_json.strip())
                
                # Use the decoded URL for the database so it's a clean link
                real_url = self.decode_google_news_url(url)
                self.save_article(data, real_url, extracted_image_url)
                
                self.stdout.write(self.style.SUCCESS(f"   ✅ Published by RraSHI AI: {data['title']}"))
                processed_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ AI/Save Error: {e}"))

    def decode_google_news_url(self, url):
        """Extracts the real target URL from the Google News Base64 string to bypass bot detection."""
        try:
            if '/articles/' in url:
                article_id = url.split('/articles/')[1].split('?')[0]
                # Add padding for Base64 decoding
                padding = 4 - (len(article_id) % 4)
                article_id += "=" * padding
                decoded_bytes = base64.urlsafe_b64decode(article_id)
                decoded_str = decoded_bytes.decode('latin1', errors='ignore')
                
                # Find the first occurrence of an http/https URL inside the decoded protobuf
                match = re.search(r'(https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+)', decoded_str)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return url

    def fetch_page_content(self, url):
        # 1. Bypass Google News redirect completely
        real_url = self.decode_google_news_url(url)
        self.stdout.write(f"   🔗 Target URL -> {real_url[:60]}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        try:
            # 2. Fetch the real news site
            resp = requests.get(real_url, headers=headers, timeout=15, allow_redirects=True)
            # Ensure correct encoding (fixes weird characters)
            resp.encoding = resp.apparent_encoding 
            soup = BeautifulSoup(resp.text, 'html.parser')

            # 3. Clean the DOM (Remove Menus, Ads, Headers, Footers)
            for element in soup(["script", "style", "nav", "header", "footer", "aside", "form", "noscript", "iframe", "button"]):
                element.decompose()

            # 4. Extract Text
            # We grab all text directly from the body, removing the need to guess if they use <p> or <div> tags
            raw_text = soup.body.get_text(separator=' ', strip=True) if soup.body else soup.get_text(separator=' ', strip=True)
            
            # Clean excessive whitespace
            raw_text = re.sub(r'\s+', ' ', raw_text).strip()

            # 5. Extract Image
            image_url = None
            og_image = soup.find("meta", property="og:image")
            if og_image:
                image_url = og_image.get("content")
            if not image_url:
                tw_image = soup.find("meta", name="twitter:image")
                if tw_image:
                    image_url = tw_image.get("content")

            return raw_text, image_url
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   Scraping Error: {e}"))
            return None

    def save_article(self, data, source_url, extracted_image_url):
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

        final_image = extracted_image_url if extracted_image_url else "https://picsum.photos/seed/news/800/600"

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